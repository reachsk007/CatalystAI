from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDICATOR = ROOT / "tradingview" / "VWAPPlus_PRO_Indicator.pine"
STRATEGY = ROOT / "tradingview" / "VWAPPlus_PRO_Strategy.pine"


class PineContractTests(unittest.TestCase):
    def test_scripts_target_pine_v6(self) -> None:
        self.assertIn("//@version=6", INDICATOR.read_text(encoding="utf-8"))
        self.assertIn("//@version=6", STRATEGY.read_text(encoding="utf-8"))

    def test_indicator_and_strategy_are_separate(self) -> None:
        self.assertIn("indicator(", INDICATOR.read_text(encoding="utf-8"))
        self.assertIn("strategy(", STRATEGY.read_text(encoding="utf-8"))

    def test_no_security_request_uses_lookahead(self) -> None:
        for path in (INDICATOR, STRATEGY):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("barmerge.lookahead_on", source)
            self.assertIn("barmerge.lookahead_off", source)

    def test_catalystai_gate_is_present_in_both_scripts(self) -> None:
        for path in (INDICATOR, STRATEGY):
            source = path.read_text(encoding="utf-8")
            self.assertIn("catalystScore", source)
            self.assertIn("catalystConfidence", source)
            self.assertIn("researchApproved", source)

    def test_all_vwap_anchor_modes_are_present(self) -> None:
        for path in (INDICATOR, STRATEGY):
            source = path.read_text(encoding="utf-8")
            for mode in ("Session", "Weekly", "Monthly", "Anchored"):
                self.assertIn(f'"{mode}"', source)

    def test_combined_strategy_contains_production_controls(self) -> None:
        source = STRATEGY.read_text(encoding="utf-8")
        for required in (
            "researchApproved",
            "allowShorts",
            "minimumMtfVotes",
            "minimumEvidence",
            'strategy.exit("Long T1"',
            'strategy.exit("Long runner"',
            'strategy.exit("Short T1"',
            'strategy.exit("Short runner"',
            "maximumBarsInTrade",
            "process_orders_on_close = false",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
