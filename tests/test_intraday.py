from datetime import datetime, timedelta
import unittest

from catalystai.intraday import Anchor, AnchorReason, IntradayBar, anchored_vwap, liquidity_failure, opening_range, relative_strength, select_meaningful_anchor, volume_participation, walk_forward


def bar(index: int, *, price: float = 100, volume: float = 100, benchmark: float = 100, high: float | None = None, low: float | None = None, close: float | None = None) -> IntradayBar:
    actual_close = price if close is None else close
    return IntradayBar(datetime(2026, 1, 2, 9, 30) + timedelta(minutes=5 * index), price, max(price, actual_close) + 1 if high is None else high, min(price, actual_close) - 1 if low is None else low, actual_close, volume, benchmark)


class IntradayEvidenceTests(unittest.TestCase):
    def test_manual_anchor_and_vwap_use_only_later_bars(self) -> None:
        bars = [bar(0, price=10), bar(1, price=20), bar(2, price=30)]
        anchor = select_meaningful_anchor(bars, manual_time=bars[1].timestamp)
        points = anchored_vwap(bars, anchor)
        self.assertEqual(anchor.reason, AnchorReason.MANUAL_EVENT)
        self.assertEqual([x.timestamp for x in points], [bars[1].timestamp, bars[2].timestamp])
        self.assertAlmostEqual(points[-1].value, 25)

    def test_latest_observable_event_is_selected(self) -> None:
        bars = [bar(index) for index in range(3)] + [bar(3, price=105, volume=400)]
        anchor = select_meaningful_anchor(bars, gap_threshold=.03, volume_lookback=3, volume_shock_ratio=2)
        self.assertEqual(anchor.index, 3)
        self.assertIn(anchor.reason, {AnchorReason.GAP, AnchorReason.VOLUME_SHOCK})

    def test_opening_range_waits_for_completion(self) -> None:
        bars = [bar(0, high=101, low=99), bar(1, high=102, low=98)]
        self.assertFalse(opening_range(bars, range_bars=2).complete)
        self.assertEqual(opening_range(bars + [bar(2, close=103, high=104)], range_bars=2).breakout, 1)

    def test_relative_strength_is_excess_return(self) -> None:
        context = relative_strength([bar(0, price=100, benchmark=100), bar(1, price=110, benchmark=105)], lookback=1)
        self.assertTrue(context.leading)
        self.assertAlmostEqual(context.excess_return, .05)

    def test_failed_breakout_closes_back_inside_prior_high(self) -> None:
        bars = [bar(0, high=101, low=99), bar(1, high=102, low=99), bar(2, high=103, low=100, close=101)]
        context = liquidity_failure(bars, lookback=2)
        self.assertTrue(context.swept_high and context.failed_breakout)
        self.assertFalse(context.failed_breakdown)

    def test_relative_volume_excludes_current_bar(self) -> None:
        context = volume_participation([bar(0, volume=100), bar(1, volume=100), bar(2, volume=250)], lookback=2, minimum_ratio=2)
        self.assertEqual(context.relative_volume, 2.5)
        self.assertTrue(context.expanding)

    def test_walk_forward_never_includes_future_bar(self) -> None:
        bars = [bar(index) for index in range(3)]
        windows = list(walk_forward(bars))
        self.assertEqual([len(x) for x in windows], [1, 2, 3])
        self.assertEqual(windows[1][-1].timestamp, bars[1].timestamp)

    def test_invalid_bar_and_anchor_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            IntradayBar(datetime.now(), 100, 99, 98, 100, 1)
        with self.assertRaisesRegex(ValueError, "anchor"):
            anchored_vwap([bar(0)], Anchor(0, datetime(2020, 1, 1), AnchorReason.MANUAL_EVENT))


if __name__ == "__main__":
    unittest.main()

