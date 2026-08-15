from pathlib import Path
import unittest


class CatalystReversalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).parents[1] / "tradingview"
        cls.strategy = (root / "Catalyst_Reversal_Acceleration_Research_Strategy.pine").read_text()
        cls.screener = (root / "Catalyst_Reversal_Acceleration_Screener.pine").read_text()

    def test_strategy_is_costed_and_oos_controlled(self):
        self.assertIn("commission_value = 0.05", self.strategy)
        self.assertIn("slippage = 1", self.strategy)
        self.assertIn('"Out-of-sample"', self.strategy)

    def test_signal_uses_completed_daily_data_without_lookahead(self):
        for source in [self.strategy, self.screener]:
            self.assertIn('"1D"', source)
            self.assertIn("close[1]", source)
            self.assertIn("dailyState()", source)
            self.assertIn("barmerge.lookahead_off", source)
            self.assertNotIn("lookahead_on", source)

    def test_relative_strength_turn_is_daily_on_every_chart_timeframe(self):
        for source in [self.strategy, self.screener]:
            self.assertIn("priorAssetReturn", source)
            self.assertIn("priorBenchmarkReturn", source)
            self.assertIn("excessReturn > priorExcessReturn", source)
            self.assertNotIn("excessReturn > nz(excessReturn[1])", source)

    def test_signal_requires_capitulation_reclaim_and_relative_turn(self):
        self.assertIn("recentCapitulation and dailyReclaim", self.strategy)
        self.assertIn("recentCapitulation and reclaim and relativeTurn", self.screener)
        self.assertIn("Minimum capitulation relative volume", self.strategy)

    def test_risk_is_bounded_for_stock_research(self):
        self.assertIn('strategy.exit("First target"', self.strategy)
        self.assertIn('strategy.exit("Runner"', self.strategy)
        self.assertIn("Maximum holding days", self.strategy)

    def test_screener_exposes_independent_evidence(self):
        for name in ["Entry ready", "CRA score", "Phase 0-4", "Drawdown %", "Minimum recent RSI", "Maximum relative volume", "5-day excess return %", "Rising trend"]:
            self.assertIn(f'"{name}"', self.screener)
        self.assertIn('alertcondition(entryReady, "CRA entry ready"', self.screener)


if __name__ == "__main__":
    unittest.main()

