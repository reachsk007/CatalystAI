"""Typed domain models for point-in-time scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class FactorObservation:
    """A normalized factor assessment backed by dated evidence."""

    score: float | None
    confidence: float
    evidence: str
    source: str

    def __post_init__(self) -> None:
        if self.score is not None and not 0 <= self.score <= 100:
            raise ValueError("factor score must be between 0 and 100")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not self.evidence.strip():
            raise ValueError("evidence is required")
        if not self.source.strip():
            raise ValueError("source is required")


@dataclass(frozen=True)
class CompanyObservation:
    """A company snapshot containing only information known as of a date."""

    ticker: str
    company_name: str
    as_of_date: date
    factors: dict[str, FactorObservation] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = self.ticker.strip().upper()
        if not normalized:
            raise ValueError("ticker is required")
        if not self.company_name.strip():
            raise ValueError("company_name is required")
        object.__setattr__(self, "ticker", normalized)


@dataclass(frozen=True)
class FactorContribution:
    """Explainable contribution from one factor to a composite score."""

    factor: str
    raw_score: float | None
    confidence: float
    configured_weight: float
    effective_weight: float
    contribution: float
    evidence: str
    source: str
    status: str


@dataclass(frozen=True)
class ScoreResult:
    """Composite score plus its complete audit trail."""

    ticker: str
    score_name: str
    score: float
    coverage: float
    confidence: float
    as_of_date: date
    contributions: tuple[FactorContribution, ...]

