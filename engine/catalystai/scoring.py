"""Deterministic, confidence-aware scoring."""

from __future__ import annotations

from .config import CompounderConfig
from .models import CompanyObservation, FactorContribution, ScoreResult


class CompounderScorer:
    """Calculate long-duration business quality without entry-timing signals."""

    score_name = "compounder"

    def __init__(self, config: CompounderConfig) -> None:
        self.config = config

    def score(self, observation: CompanyObservation) -> ScoreResult:
        unknown = set(observation.factors) - set(self.config.weights)
        if unknown:
            raise ValueError(f"unconfigured factors: {', '.join(sorted(unknown))}")

        available_weight = 0.0
        confidence_weight = 0.0
        weighted_score = 0.0
        contributions: list[FactorContribution] = []

        for factor, configured_weight in self.config.weights.items():
            item = observation.factors.get(factor)
            if item is None or item.score is None:
                contributions.append(
                    FactorContribution(
                        factor=factor,
                        raw_score=None,
                        confidence=0.0 if item is None else item.confidence,
                        configured_weight=configured_weight,
                        effective_weight=0.0,
                        contribution=0.0,
                        evidence="No observation supplied" if item is None else item.evidence,
                        source="missing" if item is None else item.source,
                        status="missing",
                    )
                )
                continue

            available_weight += configured_weight
            confidence_weight += configured_weight * item.confidence
            weighted_score += configured_weight * item.score * item.confidence
            contributions.append(
                FactorContribution(
                    factor=factor,
                    raw_score=item.score,
                    confidence=item.confidence,
                    configured_weight=configured_weight,
                    effective_weight=configured_weight * item.confidence,
                    contribution=configured_weight * item.score * item.confidence,
                    evidence=item.evidence,
                    source=item.source,
                    status="observed",
                )
            )

        coverage = available_weight
        if coverage < self.config.minimum_coverage:
            raise ValueError(
                f"coverage {coverage:.0%} is below required "
                f"{self.config.minimum_coverage:.0%}"
            )
        if confidence_weight == 0:
            raise ValueError("effective confidence is zero")

        composite = weighted_score / confidence_weight
        return ScoreResult(
            ticker=observation.ticker,
            score_name=self.score_name,
            score=round(composite, 2),
            coverage=round(coverage, 4),
            confidence=round(confidence_weight / available_weight, 4),
            as_of_date=observation.as_of_date,
            contributions=tuple(contributions),
        )

