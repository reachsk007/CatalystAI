from datetime import date
import unittest

from catalystai.config import CompounderConfig
from catalystai.models import CompanyObservation, FactorObservation
from catalystai.scoring import CompounderScorer


def factor(score: float | None, confidence: float = 1.0) -> FactorObservation:
    return FactorObservation(
        score=score,
        confidence=confidence,
        evidence="Test evidence",
        source="Test fixture",
    )


class CompounderScorerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = CompounderConfig(
            version="test",
            weights={"quality": 0.6, "resilience": 0.4},
            minimum_coverage=0.5,
        )
        self.scorer = CompounderScorer(self.config)

    def observation(self, factors: dict[str, FactorObservation]) -> CompanyObservation:
        return CompanyObservation("abc", "ABC Corp", date(2026, 1, 1), factors)

    def test_weighted_score_is_deterministic(self) -> None:
        result = self.scorer.score(
            self.observation({"quality": factor(80), "resilience": factor(50)})
        )
        self.assertEqual(result.score, 68.0)
        self.assertEqual(result.coverage, 1.0)
        self.assertEqual(result.ticker, "ABC")

    def test_confidence_changes_effective_weight(self) -> None:
        result = self.scorer.score(
            self.observation(
                {"quality": factor(100, 0.5), "resilience": factor(0, 1.0)}
            )
        )
        self.assertEqual(result.score, 42.86)
        self.assertEqual(result.confidence, 0.7)

    def test_missing_factor_is_reported_and_renormalized(self) -> None:
        result = self.scorer.score(self.observation({"quality": factor(75)}))
        self.assertEqual(result.score, 75.0)
        self.assertEqual(result.coverage, 0.6)
        self.assertEqual(result.contributions[1].status, "missing")

    def test_insufficient_coverage_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "below required"):
            self.scorer.score(self.observation({"resilience": factor(75)}))

    def test_unconfigured_factor_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unconfigured factors"):
            self.scorer.score(
                self.observation(
                    {
                        "quality": factor(75),
                        "resilience": factor(75),
                        "surprise": factor(75),
                    }
                )
            )

    def test_factor_validation_rejects_invalid_values(self) -> None:
        with self.assertRaises(ValueError):
            factor(101)
        with self.assertRaises(ValueError):
            factor(50, 1.1)


if __name__ == "__main__":
    unittest.main()

