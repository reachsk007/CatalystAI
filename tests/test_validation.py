from datetime import datetime, timedelta
from math import isinf
import unittest

from catalystai.validation import MarketRegime, TradeRecord, classify_regime, out_of_sample_matrix, promotion_decision, summarize_trades, walk_forward_folds


BASE = datetime(2024, 1, 1)


def trade(index: int, result: float, *, symbol: str = "MU", regime: MarketRegime = MarketRegime.BULL, sample: str = "walk_forward_oos") -> TradeRecord:
    entry = BASE + timedelta(days=index)
    return TradeRecord(symbol, entry, entry + timedelta(days=1), result, regime, sample)


class ValidationTests(unittest.TestCase):
    def test_walk_forward_folds_never_overlap_training_and_test(self) -> None:
        folds = walk_forward_folds(15, training_bars=6, test_bars=3)
        self.assertEqual([(fold.training_end, fold.test_start, fold.test_end) for fold in folds], [(6, 6, 9), (9, 9, 12), (12, 12, 15)])
        self.assertTrue(all(fold.training_end == fold.test_start for fold in folds))

    def test_regime_classification_is_data_driven(self) -> None:
        self.assertEqual(classify_regime(.10, .15), MarketRegime.BULL)
        self.assertEqual(classify_regime(-.10, .15), MarketRegime.BEAR)
        self.assertEqual(classify_regime(.01, .15), MarketRegime.SIDEWAYS)
        self.assertEqual(classify_regime(.10, .40), MarketRegime.HIGH_VOLATILITY)

    def test_summary_compounds_and_measures_drawdown(self) -> None:
        summary = summarize_trades([trade(0, .10), trade(1, -.10), trade(2, .05)])
        self.assertAlmostEqual(summary.net_return, 1.10 * .90 * 1.05 - 1)
        self.assertAlmostEqual(summary.win_rate, 2 / 3)
        self.assertAlmostEqual(summary.profit_factor, 1.5)
        self.assertAlmostEqual(summary.maximum_drawdown, .10)

    def test_no_loss_profit_factor_is_infinite(self) -> None:
        self.assertTrue(isinf(summarize_trades([trade(0, .01)]).profit_factor))

    def test_matrix_excludes_in_sample_trades(self) -> None:
        matrix = out_of_sample_matrix([
            trade(0, 1.0, sample="in_sample"),
            trade(1, .02, symbol="MU", regime=MarketRegime.BULL),
            trade(2, -.01, symbol="TSLA", regime=MarketRegime.BEAR),
        ])
        self.assertEqual(matrix["portfolio"].trades, 2)
        self.assertEqual(matrix["symbol:MU"].trades, 1)
        self.assertEqual(matrix["regime:bear"].trades, 1)

    def test_promotion_requires_every_regime_to_survive(self) -> None:
        trades = [trade(index, .01 if index % 2 == 0 else -.002, symbol="MU", regime=MarketRegime.BULL) for index in range(20)]
        trades += [trade(100 + index, -.01, symbol="TSLA", regime=MarketRegime.BEAR) for index in range(20)]
        trades += [trade(200 + index, .01, symbol="NVDA", regime=MarketRegime.BULL) for index in range(20)]
        approved, reasons = promotion_decision(out_of_sample_matrix(trades), minimum_trades=10)
        self.assertFalse(approved)
        self.assertTrue(any("regime:bear" in reason for reason in reasons))

    def test_promotion_requires_multiple_symbols(self) -> None:
        trades = [trade(index, .01, symbol="MU") for index in range(20)]
        approved, reasons = promotion_decision(out_of_sample_matrix(trades))
        self.assertFalse(approved)
        self.assertTrue(any("symbols represented" in reason for reason in reasons))

    def test_invalid_trade_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TradeRecord("MU", BASE, BASE, -1.0, MarketRegime.BULL, "out_of_sample")


if __name__ == "__main__":
    unittest.main()

