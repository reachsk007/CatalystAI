from datetime import date
import unittest

from catalystai.historical_data import (
    CorporateAction,
    FinancialObservation,
    HistoricalDataset,
    PriceObservation,
    SecurityRecord,
    UniverseMembership,
    validate_historical_dataset,
)


class HistoricalDataReadinessTests(unittest.TestCase):
    def complete_dataset(self) -> HistoricalDataset:
        return HistoricalDataset(
            securities=(
                SecurityRecord("A-1", "AAA", date(2019, 1, 1), None, None),
                SecurityRecord(
                    "B-1",
                    "BBB",
                    date(2019, 1, 1),
                    date(2021, 6, 1),
                    date(2021, 6, 1),
                ),
            ),
            prices=(
                PriceObservation("A-1", date(2020, 1, 2), 10, 1000),
                PriceObservation("B-1", date(2020, 1, 2), 20, 500),
            ),
            corporate_actions=(
                CorporateAction("A-1", date(2020, 6, 1), "split", 2),
            ),
            financials=(
                FinancialObservation(
                    "A-1", "revenue", date(2019, 12, 31),
                    date(2020, 2, 1), 100, "0001",
                ),
                FinancialObservation(
                    "B-1", "revenue", date(2019, 12, 31),
                    date(2020, 2, 2), 50, "0002",
                ),
            ),
            memberships=(
                UniverseMembership("TEST", "A-1", date(2020, 1, 1), None),
                UniverseMembership(
                    "TEST", "B-1", date(2020, 1, 1), date(2021, 6, 1)
                ),
            ),
        )

    def test_complete_dataset_is_ready(self) -> None:
        report = validate_historical_dataset(
            self.complete_dataset(),
            start=date(2020, 1, 1),
            end=date(2022, 1, 1),
            universe="TEST",
        )
        self.assertTrue(report.ready)
        self.assertEqual(report.errors, ())

    def test_survivorship_gap_fails_closed(self) -> None:
        dataset = self.complete_dataset()
        incomplete = HistoricalDataset(
            securities=dataset.securities,
            prices=(dataset.prices[0],),
            corporate_actions=dataset.corporate_actions,
            financials=dataset.financials,
            memberships=dataset.memberships,
        )
        report = validate_historical_dataset(
            incomplete,
            start=date(2020, 1, 1),
            end=date(2022, 1, 1),
            universe="TEST",
        )
        self.assertFalse(report.ready)
        self.assertIn("one or more historical members have no prices", report.errors)
        with self.assertRaisesRegex(ValueError, "not ready"):
            report.require_ready()

    def test_financial_filing_date_cannot_precede_period(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot precede"):
            FinancialObservation(
                "A-1",
                "revenue",
                date(2020, 12, 31),
                date(2020, 1, 1),
                100,
                "0001",
            )

    def test_unknown_universe_security_fails(self) -> None:
        dataset = self.complete_dataset()
        incomplete = HistoricalDataset(
            securities=dataset.securities,
            prices=dataset.prices,
            corporate_actions=dataset.corporate_actions,
            financials=dataset.financials,
            memberships=dataset.memberships
            + (UniverseMembership("TEST", "MISSING", date(2020, 1, 1), None),),
        )
        report = validate_historical_dataset(
            incomplete,
            start=date(2020, 1, 1),
            end=date(2022, 1, 1),
            universe="TEST",
        )
        self.assertFalse(report.ready)
        self.assertIn(
            "universe contains securities absent from the security master",
            report.errors,
        )


if __name__ == "__main__":
    unittest.main()

