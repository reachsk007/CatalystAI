"""Pure point-in-time intraday evidence components for VWAPPlus research."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import isfinite
from statistics import fmean
from typing import Iterable, Sequence


class AnchorReason(str, Enum):
    MANUAL_EVENT = "manual_event"
    SESSION_OPEN = "session_open"
    GAP = "gap"
    VOLUME_SHOCK = "volume_shock"
    LIQUIDITY_EVENT = "liquidity_event"


@dataclass(frozen=True)
class IntradayBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    benchmark_close: float | None = None

    def __post_init__(self) -> None:
        prices = (self.open, self.high, self.low, self.close)
        if not all(isfinite(value) and value > 0 for value in prices):
            raise ValueError("OHLC prices must be finite and positive")
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close) or self.high < self.low:
            raise ValueError("bar high/low must contain the open and close")
        if not isfinite(self.volume) or self.volume < 0:
            raise ValueError("volume must be finite and non-negative")
        if self.benchmark_close is not None and self.benchmark_close <= 0:
            raise ValueError("benchmark_close must be positive")

    @property
    def typical_price(self) -> float:
        return (self.high + self.low + self.close) / 3


@dataclass(frozen=True)
class Anchor:
    index: int
    timestamp: datetime
    reason: AnchorReason


@dataclass(frozen=True)
class AnchoredVwapPoint:
    timestamp: datetime
    value: float
    deviation: float
    cumulative_volume: float


@dataclass(frozen=True)
class OpeningRangeContext:
    high: float
    low: float
    complete: bool
    breakout: int


@dataclass(frozen=True)
class RelativeStrengthContext:
    asset_return: float
    benchmark_return: float
    excess_return: float
    leading: bool


@dataclass(frozen=True)
class LiquidityContext:
    swept_high: bool
    swept_low: bool
    failed_breakout: bool
    failed_breakdown: bool


@dataclass(frozen=True)
class VolumeParticipationContext:
    relative_volume: float
    dollar_volume: float
    expanding: bool


def validate_bars(bars: Sequence[IntradayBar]) -> None:
    if not bars:
        raise ValueError("at least one intraday bar is required")
    timestamps = [bar.timestamp for bar in bars]
    if timestamps != sorted(set(timestamps)):
        raise ValueError("bars must have unique ascending timestamps")


def select_meaningful_anchor(
    bars: Sequence[IntradayBar], *, manual_time: datetime | None = None,
    gap_threshold: float = 0.03, volume_lookback: int = 20,
    volume_shock_ratio: float = 2.0, liquidity_lookback: int = 20,
) -> Anchor:
    """Select the latest observable event, with manual events taking priority."""
    validate_bars(bars)
    if volume_lookback < 1 or liquidity_lookback < 1:
        raise ValueError("lookbacks must be positive")
    if gap_threshold < 0 or volume_shock_ratio <= 0:
        raise ValueError("thresholds are invalid")
    if manual_time is not None:
        for index, bar in enumerate(bars):
            if bar.timestamp >= manual_time:
                return Anchor(index, bar.timestamp, AnchorReason.MANUAL_EVENT)
        raise ValueError("manual anchor is after the available bars")
    candidates: list[Anchor] = []
    for index, bar in enumerate(bars):
        if index and abs(bar.open / bars[index - 1].close - 1) >= gap_threshold:
            candidates.append(Anchor(index, bar.timestamp, AnchorReason.GAP))
        prior_volume = [item.volume for item in bars[max(0, index - volume_lookback):index]]
        baseline = fmean(prior_volume) if prior_volume else 0.0
        if baseline and bar.volume / baseline >= volume_shock_ratio:
            candidates.append(Anchor(index, bar.timestamp, AnchorReason.VOLUME_SHOCK))
        prior = bars[max(0, index - liquidity_lookback):index]
        if prior:
            prior_high, prior_low = max(x.high for x in prior), min(x.low for x in prior)
            if (bar.high > prior_high and bar.close < prior_high) or (bar.low < prior_low and bar.close > prior_low):
                candidates.append(Anchor(index, bar.timestamp, AnchorReason.LIQUIDITY_EVENT))
    return candidates[-1] if candidates else Anchor(0, bars[0].timestamp, AnchorReason.SESSION_OPEN)


def anchored_vwap(bars: Sequence[IntradayBar], anchor: Anchor) -> list[AnchoredVwapPoint]:
    """Estimate participant cost basis from an already-known event anchor."""
    validate_bars(bars)
    if not 0 <= anchor.index < len(bars) or bars[anchor.index].timestamp != anchor.timestamp:
        raise ValueError("anchor does not identify a supplied bar")
    volume = pv = pv2 = 0.0
    result: list[AnchoredVwapPoint] = []
    for bar in bars[anchor.index:]:
        price = bar.typical_price
        volume += bar.volume
        pv += price * bar.volume
        pv2 += price * price * bar.volume
        if volume:
            value = pv / volume
            result.append(AnchoredVwapPoint(bar.timestamp, value, max(pv2 / volume - value * value, 0.0) ** 0.5, volume))
    return result


def opening_range(bars: Sequence[IntradayBar], *, range_bars: int = 5) -> OpeningRangeContext:
    validate_bars(bars)
    if range_bars < 1:
        raise ValueError("range_bars must be positive")
    observed = bars[:range_bars]
    high, low = max(x.high for x in observed), min(x.low for x in observed)
    complete = len(bars) > range_bars
    breakout = 1 if complete and bars[-1].close > high else -1 if complete and bars[-1].close < low else 0
    return OpeningRangeContext(high, low, complete, breakout)


def relative_strength(bars: Sequence[IntradayBar], *, lookback: int = 5) -> RelativeStrengthContext:
    validate_bars(bars)
    if lookback < 1 or len(bars) <= lookback:
        raise ValueError("relative-strength lookback requires one additional bar")
    start, end = bars[-lookback - 1], bars[-1]
    if start.benchmark_close is None or end.benchmark_close is None:
        raise ValueError("benchmark closes are required")
    asset_return = end.close / start.close - 1
    benchmark_return = end.benchmark_close / start.benchmark_close - 1
    excess = asset_return - benchmark_return
    return RelativeStrengthContext(asset_return, benchmark_return, excess, excess > 0)


def liquidity_failure(bars: Sequence[IntradayBar], *, lookback: int = 20) -> LiquidityContext:
    validate_bars(bars)
    if lookback < 1 or len(bars) < 2:
        raise ValueError("liquidity context requires prior bars")
    current = bars[-1]
    prior = bars[max(0, len(bars) - lookback - 1):-1]
    prior_high, prior_low = max(x.high for x in prior), min(x.low for x in prior)
    swept_high, swept_low = current.high > prior_high, current.low < prior_low
    return LiquidityContext(swept_high, swept_low, swept_high and current.close < prior_high, swept_low and current.close > prior_low)


def volume_participation(bars: Sequence[IntradayBar], *, lookback: int = 20, minimum_ratio: float = 1.5) -> VolumeParticipationContext:
    validate_bars(bars)
    if lookback < 1 or len(bars) < 2 or minimum_ratio <= 0:
        raise ValueError("volume context requires prior bars and a positive ratio")
    prior = bars[max(0, len(bars) - lookback - 1):-1]
    baseline = fmean(x.volume for x in prior)
    ratio = bars[-1].volume / baseline if baseline else 0.0
    return VolumeParticipationContext(ratio, bars[-1].typical_price * bars[-1].volume, ratio >= minimum_ratio)


def walk_forward(values: Sequence[IntradayBar]) -> Iterable[Sequence[IntradayBar]]:
    """Yield expanding windows for leakage-resistant evaluation."""
    validate_bars(values)
    for end in range(1, len(values) + 1):
        yield values[:end]

