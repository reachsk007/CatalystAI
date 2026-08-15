# Catalyst Reversal Acceleration (CRA) research

## Objective

Find high-risk stocks that may be transitioning from forced selling or capitulation into a sustained recovery. The model is a candidate detector, not a claim that a stock or option will achieve a particular return.

## Evidence translated into testable modules

1. **Capitulation context:** at least a 15% decline from the prior 60-day high, RSI(14) at or below 30, and relative volume of at least 1.5 on the completed daily bar.
2. **Price confirmation:** the stock must reclaim its 10-day EMA and the prior day's high.
3. **Relative-strength turn:** the completed five-day return must exceed SPY by at least two percentage points and improve versus the prior completed daily observation.
4. **Recovery breakout:** optional close above the prior ten-day high. This improved the tested portfolio and is required by the screener.
5. **Rising trend:** optional close above a rising 20-day EMA. This did not materially improve the holdout portfolio, so it remains an independent diagnostic instead of a required strategy default. The screener requires it for its strict `Entry ready` state.
6. **Catalyst review:** optional human gate for earnings/guidance, regulatory decisions, contracts, product launches, sector shocks, or other verifiable information. Pine cannot reliably infer catalyst quality.

The signal uses completed daily data with `barmerge.lookahead_off`, including when viewed from an intraday chart. It does not use the current incomplete daily bar.

## Backtest controls

- TradingView daily data through 2026-08-14
- Initial capital: $100,000
- Commission: 0.05%
- Slippage: one tick
- Risk budget: 0.75% of strategy equity per trade
- Initial stop: 2.5 ATR
- First objective: +20% on half the position
- Runner objective: +50%, with a 3 ATR trailing stop
- Maximum hold: 126 days
- Holdout begins 2025-01-01

## Results

### Strict confirmation, all available data

| Symbol | Net P&L | Trades | Win rate | Profit factor |
|---|---:|---:|---:|---:|
| MU | +1.51% | 3 | 100.00% | no losing trades |
| WDC | +1.71% | 10 | 50.00% | 2.298 |
| PLTR | +0.88% | 5 | 60.00% | 4.451 |
| UNH | -1.07% | 11 | 36.36% | 0.605 |
| CRWV | -0.57% | 2 | 0.00% | 0.000 |
| TSLA | +0.38% | 9 | 44.44% | 1.331 |
| MSFT | +2.04% | 1 | 100.00% | 423.927 |

SNDK and AAPL did not produce usable strategy-report samples under the strict settings.

### 2025-01-01 onward holdout

| Symbol | Net P&L | Trades | Win rate | Profit factor |
|---|---:|---:|---:|---:|
| MU | +1.51% | 3 | 100.00% | no losing trades |
| WDC | +1.87% | 2 | 100.00% | no losing trades |
| UNH | -2.50% | 9 | 22.22% | 0.062 |
| CRWV | -0.57% | 2 | 0.00% | 0.000 |
| TSLA | -0.55% | 3 | 33.33% | 0.066 |
| MSFT | +2.04% | 1 | 100.00% | 423.927 |

PLTR, SNDK, and AAPL did not produce usable holdout samples under the strict settings.

## Decision

The strict breakout filter materially improved the all-data test but did not produce consistent holdout performance across sectors. A rising 20-day EMA reduced some UNH trades without repairing the holdout loss and did not affect the other key failures. Therefore:

- keep the strategy labeled **research**;
- use the screener as a shortlist generator;
- require manual catalyst and liquidity review before any options analysis;
- do not infer a 50%-500% option outcome from the stock backtest;
- reject claims of a guaranteed win rate or minimum return.

## Files

- `tradingview/Catalyst_Reversal_Acceleration_Research_Strategy.pine`
- `tradingview/Catalyst_Reversal_Acceleration_Screener.pine`
- `tests/test_cra_contract.py`


