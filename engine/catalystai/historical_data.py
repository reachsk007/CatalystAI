"""Historical-data contracts and fail-closed backtest readiness checks."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class SecurityRecord:
    permanent_id: str
    ticker: str
    effective_from: date
    effective_to: date | None
    delisted_on: date | None

    def __post_init__(self) -> None:
        if not self.permanent_id.strip() or not self.ticker.strip():
            raise ValueError("permanent_id and ticker are required")
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot precede effective_from")


@dataclass(frozen=True)
class PriceObservation:
    permanent_id: str
    session: date
    close: float
    volume: float

    def __post_init__(self) -> None:
        if self.close <= 0 or self.volume < 0:
            raise ValueError("close must be positive and volume non-negative")


@dataclass(frozen=True)
class CorporateAction:
    permanent_id: str
    action_date: date
    action_type: str
    value: float

    def __post_init__(self) -> None:
        if self.action_type not in {"split", "dividend"}:
            raise ValueError("action_type must be split or dividend")
        if self.value <= 0:
            raise ValueError("corporate action value must be positive")


@dataclass(frozen=True)
class FinancialObservation:
    permanent_id: str
    metric: str
    period_end: date
    filed_on: date
    value: float
    accession_number: str

    def __post_init__(self) -> None:
        if self.filed_on < self.period_end:
            raise ValueError("filed_on cannot precede period_end")
        if not self.metric.strip() or not self.accession_number.strip():
            raise ValueError("metric and accession_number are required")


@dataclass(frozen=True)
class UniverseMembership:
    universe: str
    permanent_id: str
    effective_from: date
    effective_to: date | None

    def active_on(self, session: date) -> bool:
        return self.effective_from <= session and (
            self.effective_to is None or session <= self.effective_to
        )


@dataclass(frozen=True)
class HistoricalDataset:
    securities: tuple[SecurityRecord, ...]
    prices: tuple[PriceObservation, ...]
    corporate_actions: tuple[CorporateAction, ...]
    financials: tuple[FinancialObservation, ...]
    memberships: tuple[UniverseMembership, ...]


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def require_ready(self) -> None:
        if not self.ready:
            raise ValueError("historical dataset is not ready: " + "; ".join(self.errors))


def validate_historical_dataset(
    dataset: HistoricalDataset,
    *,
    start: date,
    end: date,
    universe: str,
) -> ReadinessReport:
    errors: list[str] = []
    warnings: list[str] = []
    if start >= end:
        errors.append("start must precede end")
    if not dataset.securities:
        errors.append("security master is missing")
    if not dataset.prices:
        errors.append("point-in-time prices are missing")
    if not dataset.financials:
        errors.append("dated financial observations are missing")
    if not dataset.memberships:
        errors.append("historical universe membership is missing")

    security_ids = {item.permanent_id for item in dataset.securities}
    membership_ids = {
        item.permanent_id
        for item in dataset.memberships
        if item.universe == universe
        and item.effective_from <= end
        and (item.effective_to is None or item.effective_to >= start)
    }
    if dataset.memberships and not membership_ids:
        errors.append(f"no {universe} members overlap the requested period")
    unknown_members = membership_ids - security_ids
    if unknown_members:
        errors.append("universe contains securities absent from the security master")

    price_ids = {
        item.permanent_id
        for item in dataset.prices
        if start <= item.session <= end
    }
    missing_prices = membership_ids - price_ids
    if missing_prices:
        errors.append("one or more historical members have no prices")

    financial_ids = {
        item.permanent_id
        for item in dataset.financials
        if item.filed_on <= end
    }
    missing_financials = membership_ids - financial_ids
    if missing_financials:
        errors.append("one or more historical members have no filed financial observations")

    delisted_ids = {
        item.permanent_id
        for item in dataset.securities
        if item.delisted_on and start <= item.delisted_on <= end
    }
    if not delisted_ids:
        warnings.append(
            "no delistings occur in the requested slice; verify the provider includes them"
        )

    action_ids = {item.permanent_id for item in dataset.corporate_actions}
    if not action_ids:
        warnings.append(
            "no corporate actions are present; verify adjusted-return assumptions"
        )

    return ReadinessReport(not errors, tuple(errors), tuple(warnings))


def load_csv_dataset(directory: str | Path) -> HistoricalDataset:
    """Load the normalized five-file dataset contract."""

    root = Path(directory)

    def rows(name: str) -> list[dict[str, str]]:
        with (root / name).open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    securities = tuple(
        SecurityRecord(
            permanent_id=row["permanent_id"],
            ticker=row["ticker"],
            effective_from=date.fromisoformat(row["effective_from"]),
            effective_to=_optional_date(row.get("effective_to")),
            delisted_on=_optional_date(row.get("delisted_on")),
        )
        for row in rows("security_master.csv")
    )
    prices = tuple(
        PriceObservation(
            permanent_id=row["permanent_id"],
            session=date.fromisoformat(row["session"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
        )
        for row in rows("prices.csv")
    )
    actions = tuple(
        CorporateAction(
            permanent_id=row["permanent_id"],
            action_date=date.fromisoformat(row["action_date"]),
            action_type=row["action_type"],
            value=float(row["value"]),
        )
        for row in rows("corporate_actions.csv")
    )
    financials = tuple(
        FinancialObservation(
            permanent_id=row["permanent_id"],
            metric=row["metric"],
            period_end=date.fromisoformat(row["period_end"]),
            filed_on=date.fromisoformat(row["filed_on"]),
            value=float(row["value"]),
            accession_number=row["accession_number"],
        )
        for row in rows("financials.csv")
    )
    memberships = tuple(
        UniverseMembership(
            universe=row["universe"],
            permanent_id=row["permanent_id"],
            effective_from=date.fromisoformat(row["effective_from"]),
            effective_to=_optional_date(row.get("effective_to")),
        )
        for row in rows("universe_membership.csv")
    )
    return HistoricalDataset(securities, prices, actions, financials, memberships)


def _optional_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None

