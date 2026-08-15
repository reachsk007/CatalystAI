from pathlib import Path
import unittest


class DualUtStcContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).parents[1] / "tradingview" / "UTBot_Dual_STC_Research_Strategy.pine").read_text()

    def test_exact_published_inputs_are_exposed(self):
        self.assertIn('buyAtrLength = input.int(300', self.source)
        self.assertIn('sellAtrLength = input.int(1', self.source)
        self.assertIn('stcLength = input.int(80', self.source)
        self.assertIn('stcFast = input.int(27', self.source)
        self.assertIn('stcSlow = input.int(50', self.source)

    def test_no_lookahead_and_confirmed_bars(self):
        self.assertNotIn("lookahead_on", self.source)
        self.assertIn("barstate.isconfirmed", self.source)

    def test_costs_oos_and_risk_are_explicit(self):
        self.assertIn("commission_value = 0.05", self.source)
        self.assertIn("slippage = 1", self.source)
        self.assertIn('"Out-of-sample"', self.source)
        self.assertIn("Nearest structure lookback", self.source)

    def test_signals_are_visible_and_alertable(self):
        self.assertIn('plotshape(buySignal, "BUY signal"', self.source)
        self.assertIn('plotshape(sellSignal, "SELL signal"', self.source)
        self.assertIn("alertcondition(buySignal", self.source)


if __name__ == "__main__":
    unittest.main()

