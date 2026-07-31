from datetime import date, timedelta
import unittest

from catalystai.backtest import (
    BacktestConfig,
    PortfolioBacktester,
    PriceBar,
    SignalSnapshot,
    Timeframe,
    run_all_timeframes,
)


def bars(count: int, daily_return: float = 0.01) -> list[PriceBar]:
    start = date(2025, 1, 1)
    result = []
    price = 100.0
    for index in range(count):
        if index:
            price *= 1 + daily_return
        result.append(
            PriceBar(
                session=start + timedelta(days=index),
                prices={"AAA": price, "BBB": 100.0},
                benchmark=100.0,
            )
        )
    return result


class BacktestTests(unittest.TestCase):
    def test_signal_is_only_used_after_its_date(self) -> None:
        price_bars = bars(4)
        future_signal = SignalSnapshot(price_bars[2].session, {"AAA": 100})
        result = PortfolioBacktester(
            BacktestConfig(Timeframe.DAILY, transaction_cost_bps=0)
        ).run(price_bars, [future_signal])
        self.assertEqual(result.rebalances, 1)
        self.assertAlmostEqual(result.total_return, 0.01, places=6)

    def test_transaction_cost_is_charged_on_turnover(self) -> None:
        price_bars = bars(2, daily_return=0)
        signal = SignalSnapshot(price_bars[0].session, {"AAA": 100})
        result = PortfolioBacktester(
            BacktestConfig(Timeframe.DAILY, transaction_cost_bps=100)
        ).run(price_bars, [signal])
        self.assertEqual(result.ending_equity, 0.99)
        self.assertEqual(result.turnover, 1.0)

    def test_score_threshold_can_hold_cash(self) -> None:
        price_bars = bars(3)
        signal = SignalSnapshot(price_bars[0].session, {"AAA": 49})
        result = PortfolioBacktester(
            BacktestConfig(
                Timeframe.DAILY,
                minimum_score=50,
                transaction_cost_bps=0,
            )
        ).run(price_bars, [signal])
        self.assertEqual(result.total_return, 0)
        self.assertEqual(result.turnover, 0)

    def test_top_ranked_security_is_selected(self) -> None:
        price_bars = bars(3)
        signal = SignalSnapshot(
            price_bars[0].session,
            {"AAA": 90, "BBB": 50},
        )
        result = PortfolioBacktester(
            BacktestConfig(Timeframe.DAILY, top_n=1, transaction_cost_bps=0)
        ).run(price_bars, [signal])
        self.assertGreater(result.total_return, 0)

    def test_all_supported_timeframes_run(self) -> None:
        price_bars = bars(300, daily_return=0.0001)
        signal = SignalSnapshot(price_bars[0].session, {"AAA": 100})
        results = run_all_timeframes(
            price_bars, [signal], transaction_cost_bps=0
        )
        self.assertEqual(
            [result.timeframe for result in results],
            list(Timeframe),
        )
        self.assertGreater(
            results[0].rebalances,
            results[-1].rebalances,
        )

    def test_duplicate_or_unsorted_dates_are_rejected(self) -> None:
        price_bars = bars(2)
        with self.assertRaisesRegex(ValueError, "unique ascending"):
            PortfolioBacktester(BacktestConfig(Timeframe.DAILY)).run(
                list(reversed(price_bars)),
                [SignalSnapshot(price_bars[0].session, {"AAA": 100})],
            )

    def test_drawdown_is_reported_as_negative(self) -> None:
        price_bars = [
            PriceBar(date(2025, 1, 1), {"AAA": 100}, 100),
            PriceBar(date(2025, 1, 2), {"AAA": 120}, 100),
            PriceBar(date(2025, 1, 3), {"AAA": 90}, 100),
        ]
        result = PortfolioBacktester(
            BacktestConfig(Timeframe.DAILY, transaction_cost_bps=0)
        ).run(
            price_bars,
            [SignalSnapshot(price_bars[0].session, {"AAA": 100})],
        )
        self.assertAlmostEqual(result.maximum_drawdown, -0.25)


if __name__ == "__main__":
    unittest.main()

