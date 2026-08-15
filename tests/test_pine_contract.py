from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDICATOR = ROOT / "tradingview" / "VWAPPlus_PRO_Indicator.pine"
STRATEGY = ROOT / "tradingview" / "VWAPPlus_PRO_Strategy.pine"


class VwapPlusProContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = STRATEGY.read_text(encoding="utf-8")

    def test_existing_indicator_contract_is_preserved(self) -> None:
        if not INDICATOR.exists():
            self.skipTest("production indicator is not present in the branch snapshot")
        indicator = INDICATOR.read_text(encoding="utf-8")
        self.assertIn("//@version=6", indicator)
        self.assertIn("indicator(", indicator)
        self.assertIn("barmerge.lookahead_off", indicator)
        self.assertNotIn("barmerge.lookahead_on", indicator)

    def test_strategy_identity_and_anchor_modes_are_preserved(self) -> None:
        self.assertIn("//@version=6", self.source)
        self.assertIn('strategy("CatalystAI VWAPPlus PRO — Combined Decision Engine"', self.source)
        for mode in ("Session", "Weekly", "Monthly", "Anchored"):
            self.assertIn(f'"{mode}"', self.source)

    def test_standard_order_processing_avoids_fill_recalculation_bias(self) -> None:
        self.assertIn("calc_on_order_fills = false", self.source)
        self.assertIn("calc_on_every_tick = false", self.source)
        self.assertIn("process_orders_on_close = false", self.source)
        self.assertIn('strategy.exit("Long T1"', self.source)
        self.assertIn('strategy.exit("Short T1"', self.source)

    def test_confirmed_data_has_no_future_lookahead(self) -> None:
        self.assertIn("barstate.isconfirmed", self.source)
        self.assertIn("close[1]", self.source)
        self.assertIn("barmerge.lookahead_off", self.source)
        self.assertNotIn("barmerge.lookahead_on", self.source)

    def test_adaptive_confirmations_remain_above_chart_timeframe(self) -> None:
        self.assertIn('timeframeProfile = input.string("Adaptive"', self.source)
        self.assertIn("adaptiveTimeframe1", self.source)
        self.assertIn("adaptiveTimeframe2", self.source)
        self.assertIn("adaptiveTimeframe3", self.source)
        self.assertIn("timeframe.in_seconds(confirmationTimeframe1) > chartSeconds", self.source)
        self.assertIn("confirmationTimeframesValid and dataConfidence", self.source)

    def test_manual_ai_gate_is_replaced_by_computed_evidence(self) -> None:
        self.assertNotIn("catalystScore = input", self.source)
        self.assertNotIn("catalystConfidence = input", self.source)
        self.assertIn("computedLongScore = longEvidence * dataConfidence", self.source)
        self.assertIn("computedShortScore = shortEvidence * dataConfidence", self.source)
        self.assertIn("longResearchApproved = dataApproved and longEvidence", self.source)

    def test_volume_baseline_does_not_include_current_bar(self) -> None:
        self.assertIn("ta.sma(volume[1], volumeLength)", self.source)

    def test_validation_modes_isolate_oos_trades(self) -> None:
        for mode in ("All data", "In-sample", "Out-of-sample", "Walk-forward OOS"):
            self.assertIn(f'"{mode}"', self.source)
        self.assertIn("inWalkForwardTest", self.source)
        self.assertIn("sampleEligible", self.source)
        self.assertIn('"Validation boundary"', self.source)

    def test_risk_and_cost_assumptions_are_explicit(self) -> None:
        self.assertIn("commission_value = 0.05", self.source)
        self.assertIn("slippage = 1", self.source)
        self.assertIn("riskBudget = input.float(1.0", self.source)
        self.assertIn("maximumAllocation = input.float(20.0", self.source)


if __name__ == "__main__":
    unittest.main()

