"""Leakage-resistant aggregation for exported VWAPPlus strategy trades.

The module deliberately does not optimize parameters.  It evaluates parameters
that were frozen before the out-of-sample trades were generated in TradingView.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from math import inf, isfinite
from pathlib import Path
from typing import Iterable, Sequence


class MarketRegime(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"


@dataclass(frozen=True)
class WalkForwardFold:
    number: int
    training_start: int
    training_end: int
    test_start: int
    test_end: int


@dataclass(frozen=True)
class TradeRecord:
    symbol: str
    entry_time: datetime
    exit_time: datetime
    return_fraction: float
    regime: MarketRegime
    sample: str

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol is required")
        if self.exit_time < self.entry_time:
            raise ValueError("exit_time cannot precede entry_time")
        if not isfinite(self.return_fraction) or self.return_fraction <= -1:
            raise ValueError("return_fraction must be finite and greater than -1")
        if self.sample not in {"in_sample", "out_of_sample", "walk_forward_oos"}:
            raise ValueError("sample must identify an isolated validation segment")


@dataclass(frozen=True)
class PerformanceSummary:
    trades: int
    net_return: float
    win_rate: float
    profit_factor: float
    maximum_drawdown: float
    average_trade: float


def walk_forward_folds(total_bars: int, *, training_bars: int, test_bars: int) -> list[WalkForwardFold]:
    """Return non-overlapping expanding-origin train/test folds.

    The Pine strategy uses repeating fixed windows for visual isolation.  The
    offline evaluator uses expanding training history and the same disjoint test
    blocks so every test observation occurs strictly after its training data.
    """
    if total_bars < 0 or training_bars < 1 or test_bars < 1:
        raise ValueError("bar counts must be positive")
    folds: list[WalkForwardFold] = []
    test_start = training_bars
    number = 1
    while test_start < total_bars:
        test_end = min(test_start + test_bars, total_bars)
        folds.append(WalkForwardFold(number, 0, test_start, test_start, test_end))
        number += 1
        test_start = test_end
    return folds


def classify_regime(
    benchmark_return: float,
    realized_volatility: float,
    *,
    trend_threshold: float = 0.05,
    high_volatility_threshold: float = 0.30,
) -> MarketRegime:
    """Classify a regime from point-in-time benchmark return and volatility."""
    if not all(isfinite(value) for value in (benchmark_return, realized_volatility)):
        raise ValueError("regime inputs must be finite")
    if trend_threshold < 0 or high_volatility_threshold <= 0 or realized_volatility < 0:
        raise ValueError("regime thresholds are invalid")
    if realized_volatility >= high_volatility_threshold:
        return MarketRegime.HIGH_VOLATILITY
    if benchmark_return >= trend_threshold:
        return MarketRegime.BULL
    if benchmark_return <= -trend_threshold:
        return MarketRegime.BEAR
    return MarketRegime.SIDEWAYS


def summarize_trades(trades: Sequence[TradeRecord]) -> PerformanceSummary:
    ordered = sorted(trades, key=lambda trade: (trade.exit_time, trade.symbol))
    if not ordered:
        return PerformanceSummary(0, 0.0, 0.0, 0.0, 0.0, 0.0)
    equity = peak = 1.0
    maximum_drawdown = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    winners = 0
    for trade in ordered:
        equity *= 1 + trade.return_fraction
        peak = max(peak, equity)
        maximum_drawdown = max(maximum_drawdown, 1 - equity / peak)
        if trade.return_fraction > 0:
            winners += 1
            gross_profit += trade.return_fraction
        elif trade.return_fraction < 0:
            gross_loss += abs(trade.return_fraction)
    profit_factor = gross_profit / gross_loss if gross_loss else inf if gross_profit else 0.0
    return PerformanceSummary(
        trades=len(ordered),
        net_return=equity - 1,
        win_rate=winners / len(ordered),
        profit_factor=profit_factor,
        maximum_drawdown=maximum_drawdown,
        average_trade=sum(trade.return_fraction for trade in ordered) / len(ordered),
    )


def out_of_sample_matrix(trades: Iterable[TradeRecord]) -> dict[str, PerformanceSummary]:
    """Summarize OOS trades by portfolio, symbol, and point-in-time regime."""
    selected = [trade for trade in trades if trade.sample in {"out_of_sample", "walk_forward_oos"}]
    groups: dict[str, list[TradeRecord]] = {"portfolio": selected}
    for trade in selected:
        groups.setdefault(f"symbol:{trade.symbol}", []).append(trade)
        groups.setdefault(f"regime:{trade.regime.value}", []).append(trade)
        groups.setdefault(f"symbol_regime:{trade.symbol}:{trade.regime.value}", []).append(trade)
    return {name: summarize_trades(group) for name, group in sorted(groups.items())}


def promotion_decision(
    matrix: dict[str, PerformanceSummary],
    *,
    minimum_trades: int = 20,
    minimum_symbols: int = 3,
    minimum_profit_factor: float = 1.05,
    maximum_drawdown: float = 0.20,
) -> tuple[bool, list[str]]:
    """Require positive, sufficiently sampled OOS results in every reported bucket."""
    reasons: list[str] = []
    symbol_groups = {name: summary for name, summary in matrix.items() if name.startswith("symbol:")}
    required = {name: summary for name, summary in matrix.items() if name == "portfolio" or name.startswith("regime:") or name.startswith("symbol:")}
    if not required or required.get("portfolio", PerformanceSummary(0, 0, 0, 0, 0, 0)).trades == 0:
        reasons.append("no out-of-sample trades")
    if len(symbol_groups) < minimum_symbols:
        reasons.append(f"only {len(symbol_groups)} symbols represented; require {minimum_symbols}")
    for name, summary in required.items():
        if summary.trades < minimum_trades:
            reasons.append(f"{name} has only {summary.trades} trades")
        if summary.net_return <= 0:
            reasons.append(f"{name} net return is not positive")
        if summary.profit_factor < minimum_profit_factor:
            reasons.append(f"{name} profit factor is below {minimum_profit_factor:.2f}")
        if summary.maximum_drawdown > maximum_drawdown:
            reasons.append(f"{name} drawdown exceeds {maximum_drawdown:.0%}")
    return not reasons, reasons


def load_trade_csv(path: str | Path) -> list[TradeRecord]:
    """Load normalized TradingView exports.

    Required columns: symbol, entry_time, exit_time, return_pct, regime, sample.
    Timestamps must be ISO-8601 and return_pct is expressed in percentage points.
    """
    result: list[TradeRecord] = []
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            result.append(
                TradeRecord(
                    symbol=row["symbol"].strip().upper(),
                    entry_time=datetime.fromisoformat(row["entry_time"]),
                    exit_time=datetime.fromisoformat(row["exit_time"]),
                    return_fraction=float(row["return_pct"]) / 100,
                    regime=MarketRegime(row["regime"].strip().lower()),
                    sample=row["sample"].strip().lower(),
                )
            )
    return result


def _json_safe(summary: PerformanceSummary) -> dict[str, float | int | str]:
    values = asdict(summary)
    if summary.profit_factor == inf:
        values["profit_factor"] = "Infinity"
    return values


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate VWAPPlus walk-forward/OOS trade exports")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--minimum-trades", type=int, default=20)
    parser.add_argument("--minimum-symbols", type=int, default=3)
    parser.add_argument("--minimum-profit-factor", type=float, default=1.05)
    parser.add_argument("--maximum-drawdown", type=float, default=0.20)
    args = parser.parse_args(argv)
    matrix = out_of_sample_matrix(load_trade_csv(args.csv))
    approved, reasons = promotion_decision(
        matrix,
        minimum_trades=args.minimum_trades,
        minimum_symbols=args.minimum_symbols,
        minimum_profit_factor=args.minimum_profit_factor,
        maximum_drawdown=args.maximum_drawdown,
    )
    print(json.dumps({"approved": approved, "reasons": reasons, "results": {key: _json_safe(value) for key, value in matrix.items()}}, indent=2))
    return 0 if approved else 1


if __name__ == "__main__":
    raise SystemExit(main())

