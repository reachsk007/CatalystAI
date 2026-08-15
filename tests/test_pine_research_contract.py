from pathlib import Path
import unittest


class PineResearchContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = (Path(__file__).parents[1] / "tradingview" / "VWAPPlus_Evidence_Research_Strategy.pine").read_text()

    def test_is_separate_strategy_with_costs(self) -> None:
        self.assertIn('strategy("VWAPPlus Evidence Research"', self.source)
        self.assertIn("commission_value = 0.05", self.source)
        self.assertIn("slippage = 1", self.source)

    def test_modules_are_independently_selectable(self) -> None:
        for name in ("AVWAP reclaim", "Opening range", "Relative strength", "Failed breakout", "Volume participation"):
            self.assertIn(name, self.source)

    def test_no_lookahead_or_unconfirmed_entry(self) -> None:
        self.assertIn("barmerge.lookahead_off", self.source)
        self.assertIn("barstate.isconfirmed", self.source)
        self.assertNotIn("barmerge.lookahead_on", self.source)

    def test_volume_baseline_excludes_current_bar(self) -> None:
        self.assertIn("ta.sma(volume[1]", self.source)


if __name__ == "__main__":
    unittest.main()

