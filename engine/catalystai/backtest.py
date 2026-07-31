"""Point-in-time, multi-horizon portfolio backtesting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from math import sqrt
from statistics import fmean, pstdev


class Timeframe(Enum):
    """Approximate trading-session rebalance intervals."""

    DAILY = 1
    WEEKLY = 5
    MONTHLY = 21
    QUARTERLY = 63
    ANNUAL = 252


@dataclass(frozen=True)
class PriceBar:
    session: date
    prices: dict[str, float]
    benchmark: float

    def __post_init__(self) -> None:
        if not self.prices:
            raise ValueError("at least one security price is required")
        if any(price <= 0 for price in self.prices.values()) or self.benchmark <= 0:
            raise ValueError("prices must be positive")


@dataclass(frozen=True)
class SignalSnapshot:
    """Scores known after the close of the stated date."""

    as_of_date: date
    scores: dict[str, float]

    def __post_init__(self) -> None:
        if not self.scores:
            raise ValueError("at least one score is required")
        if any(not 0 <= score <= 100 for score in self.scores.values()):
            raise ValueError("scores must be between 0 and 100")


@dataclass(frozen=True)
class BacktestConfig:
    timeframe: Timeframe
    top_n: int = 1
    minimum_score: float = 0
    transaction_cost_bps: float = 10
    periods_per_year: int = 252

    def __post_init__(self) -> None:
        if self.top_n < 1:
            raise ValueError("top_n must be positive")
        if not 0 <= self.minimum_score <= 100:
            raise ValueError("minimum_score must be between 0 and 100")
        if self.transaction_cost_bps < 0:
            raise ValueError("transaction_cost_bps cannot be negative")
        if self.periods_per_year < 1:
            raise ValueError("periods_per_year must be positive")


@dataclass(frozen=True)
class BacktestResult:
    timeframe: Timeframe
    sessions: int
    rebalances: int
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    maximum_drawdown: float
    benchmark_return: float
    excess_return: float
    turnover: float
    ending_equity: float


class PortfolioBacktester:
    """Equal-weight the highest point-in-time scores at each rebalance."""

    def __init__(self, config: BacktestConfig) -> None:
        self.config = config

    def run(
        self,
        bars: list[PriceBar],
        signals: list[SignalSnapshot],
    ) -> BacktestResult:
        self._validate_inputs(bars, signals)
        weights: dict[str, float] = {}
        equity = 1.0
        benchmark_equity = 1.0
        equity_curve = [equity]
        returns: list[float] = []
        total_turnover = 0.0
        rebalances = 0

        for index in range(1, len(bars)):
            current = bars[index]
            previous = bars[index - 1]
            if (index - 1) % self.config.timeframe.value == 0:
                eligible = [
                    snapshot
                    for snapshot in signals
                    if snapshot.as_of_date < current.session
                ]
                if eligible:
                    latest = eligible[-1]
                    target = self._target_weights(latest, current.prices)
                    turnover = self._turnover(weights, target)
                    total_turnover += turnover
                    equity *= 1 - turnover * self.config.transaction_cost_bps / 10_000
                    weights = target
                    rebalances += 1

            daily_return = sum(
                weight * (current.prices[ticker] / previous.prices[ticker] - 1)
                for ticker, weight in weights.items()
                if ticker in previous.prices and ticker in current.prices
            )
            benchmark_return = current.benchmark / previous.benchmark - 1
            equity *= 1 + daily_return
            benchmark_equity *= 1 + benchmark_return
            returns.append(daily_return)
            equity_curve.append(equity)

        total_return = equity - 1
        years = len(returns) / self.config.periods_per_year
        annualized_return = equity ** (1 / years) - 1 if years > 0 else 0.0
        volatility = (
            pstdev(returns) * sqrt(self.config.periods_per_year)
            if len(returns) > 1
            else 0.0
        )
        sharpe = (
            fmean(returns) / pstdev(returns) * sqrt(self.config.periods_per_year)
            if len(returns) > 1 and pstdev(returns) > 0
            else 0.0
        )
        maximum_drawdown = self._maximum_drawdown(equity_curve)
        benchmark_total = benchmark_equity - 1
        return BacktestResult(
            timeframe=self.config.timeframe,
            sessions=len(returns),
            rebalances=rebalances,
            total_return=round(total_return, 6),
            annualized_return=round(annualized_return, 6),
            annualized_volatility=round(volatility, 6),
            sharpe_ratio=round(sharpe, 6),
            maximum_drawdown=round(maximum_drawdown, 6),
            benchmark_return=round(benchmark_total, 6),
            excess_return=round(total_return - benchmark_total, 6),
            turnover=round(total_turnover, 6),
            ending_equity=round(equity, 6),
        )

    def _target_weights(
        self, snapshot: SignalSnapshot, current_prices: dict[str, float]
    ) -> dict[str, float]:
        ranked = sorted(
            (
                (ticker, score)
                for ticker, score in snapshot.scores.items()
                if ticker in current_prices and score >= self.config.minimum_score
            ),
            key=lambda item: (-item[1], item[0]),
        )[: self.config.top_n]
        if not ranked:
            return {}
        equal_weight = 1 / len(ranked)
        return {ticker: equal_weight for ticker, _ in ranked}

    @staticmethod
    def _turnover(current: dict[str, float], target: dict[str, float]) -> float:
        tickers = set(current) | set(target)
        return sum(abs(target.get(ticker, 0) - current.get(ticker, 0)) for ticker in tickers)

    @staticmethod
    def _maximum_drawdown(equity_curve: list[float]) -> float:
        peak = equity_curve[0]
        worst = 0.0
        for equity in equity_curve:
            peak = max(peak, equity)
            worst = min(worst, equity / peak - 1)
        return worst

    @staticmethod
    def _validate_inputs(
        bars: list[PriceBar], signals: list[SignalSnapshot]
    ) -> None:
        if len(bars) < 2:
            raise ValueError("at least two price bars are required")
        sessions = [bar.session for bar in bars]
        if sessions != sorted(set(sessions)):
            raise ValueError("price bars must have unique ascending sessions")
        signal_dates = [signal.as_of_date for signal in signals]
        if signal_dates != sorted(set(signal_dates)):
            raise ValueError("signals must have unique ascending dates")


def run_all_timeframes(
    bars: list[PriceBar],
    signals: list[SignalSnapshot],
    *,
    top_n: int = 1,
    minimum_score: float = 0,
    transaction_cost_bps: float = 10,
) -> list[BacktestResult]:
    """Run one comparable test for each supported rebalance horizon."""

    return [
        PortfolioBacktester(
            BacktestConfig(
                timeframe=timeframe,
                top_n=top_n,
                minimum_score=minimum_score,
                transaction_cost_bps=transaction_cost_bps,
            )
        ).run(bars, signals)
        for timeframe in Timeframe
    ]

