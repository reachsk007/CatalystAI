"""Deterministic scenario data used to validate backtest mechanics.

This is not historical market data and its outputs are not performance claims.
"""

from __future__ import annotations

from datetime import date, timedelta
from math import sin

from catalystai.backtest import PriceBar, SignalSnapshot


def build_synthetic_scenario(
    sessions: int = 756,
) -> tuple[list[PriceBar], list[SignalSnapshot]]:
    bars: list[PriceBar] = []
    signals: list[SignalSnapshot] = []
    current_date = date(2023, 1, 2)
    meta = ford = benchmark = 100.0

    for index in range(sessions):
        while current_date.weekday() >= 5:
            current_date += timedelta(days=1)
        if index:
            meta_leads = (index // 126) % 2 == 0
            meta_drift = 0.00065 if meta_leads else -0.00005
            ford_drift = -0.00005 if meta_leads else 0.00065
            meta *= 1 + meta_drift + 0.008 * sin(index / 11)
            ford *= 1 + ford_drift + 0.012 * sin(index / 7 + 1)
            benchmark *= 1 + 0.0003 + 0.006 * sin(index / 13)
        bars.append(
            PriceBar(
                session=current_date,
                prices={"META": meta, "F": ford},
                benchmark=benchmark,
            )
        )
        if index % 63 == 0:
            meta_leads = (index // 126) % 2 == 0
            signals.append(
                SignalSnapshot(
                    as_of_date=current_date,
                    scores=(
                        {"META": 88.9, "F": 47.0}
                        if meta_leads
                        else {"META": 47.0, "F": 88.9}
                    ),
                )
            )
        current_date += timedelta(days=1)
    return bars, signals
