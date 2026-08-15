from pathlib import Path
import unittest


class IbsScreenerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).parents[1] / "tradingview" / "VWAPPlus_IBS_5pct_Screener.pine").read_text()

    def test_is_indicator_not_strategy(self):
        self.assertIn('indicator("VWAPPlus IBS 5% Swing Screener"', self.source)
        self.assertNotIn("strategy(", self.source)

    def test_uses_completed_daily_data_without_lookahead(self):
        self.assertIn('"1D"', self.source)
        self.assertIn("close[1]", self.source)
        self.assertIn("barmerge.lookahead_off", self.source)
        self.assertNotIn("lookahead_on", self.source)

    def test_matches_strategy_defaults(self):
        self.assertIn('ibsThreshold = input.float(0.30', self.source)
        self.assertIn('highLookback = input.int(10', self.source)
        self.assertIn('rangeLookback = input.int(25', self.source)
        self.assertIn('declineMultiple = input.float(2.5', self.source)
        self.assertIn('targetPercent = input.float(5.0', self.source)

    def test_exposes_screener_columns_and_alerts(self):
        for name in ["Setup ready", "New BUY event", "IBS value", "Decline strength", "Entry reference", "5% target", "Bars since signal"]:
            self.assertIn(f'"{name}"', self.source)
        self.assertIn('alertcondition(completedSetup, "IBS setup ready"', self.source)
        self.assertIn('alertcondition(newBuyEvent, "IBS new BUY"', self.source)

    def test_uses_one_request_and_no_unsupported_screener_inputs(self):
        self.assertEqual(self.source.count("request.security("), 1)
        self.assertNotIn("input.time(", self.source)
        self.assertNotIn("input.symbol(", self.source)
        self.assertNotIn("input.timeframe(", self.source)


if __name__ == "__main__":
    unittest.main()

