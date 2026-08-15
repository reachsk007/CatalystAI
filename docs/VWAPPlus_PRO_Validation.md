# VWAPPlus PRO validation

`tradingview/VWAPPlus_PRO_Strategy.pine` preserves the Combined
Engine's VWAP, relative-strength, trend, structure, risk-budget, partial-exit,
and runner concepts while correcting the audit findings from the TradingView
version:

- historical fills use standard next-tick processing with no recalculation on
  fills or ticks;
- initial protective brackets are submitted with the entry order;
- the three confirmation periods adapt above the active chart timeframe;
- manual confirmation periods block entries if any period is not higher than
  the chart;
- the manual "CatalystAI score" and "research confidence" inputs are removed;
- research approval is computed from point-in-time evidence availability,
  evidence strength, and confirmed higher-timeframe data;
- the volume baseline excludes the current bar; and
- fixed in-sample/OOS and repeating walk-forward OOS segments are selectable.

Pine cannot optimize parameters in a training fold and automatically freeze
the chosen values for the next test fold. The walk-forward mode therefore
isolates test windows only; settings must be frozen before viewing each OOS
window. Do not tune parameters from OOS results.

## Multi-symbol and regime promotion gate

The minimum cross-sectional matrix is MU, TSLA, NVDA, AMD, WDC, SNDK, PLTR,
CRWV, and UNH. Use the correct sector benchmark for each stock. This deliberately
mixes semiconductor, software, emerging-growth, and healthcare behavior; add
broad-market controls such as SPY and QQQ rather than removing difficult names.

Export normalized trade results with these columns:

```text
symbol,entry_time,exit_time,return_pct,regime,sample
```

`regime` is one of `bull`, `bear`, `sideways`, or `high_volatility`; `sample`
is `in_sample`, `out_of_sample`, or `walk_forward_oos`. Regimes must be assigned
from benchmark return and realized volatility known at the trade time, not from
later price action. Run:

```text
python -m catalystai.validation PATH_TO_TRADES.csv
```

The report compounds returns, measures drawdown, and separates the portfolio by
symbol and regime. Promotion fails by default unless at least three symbols are
represented and the portfolio, every symbol, and every represented regime have
at least 20 OOS trades, positive net return, profit factor of at least 1.05, and
maximum drawdown no greater than 20%. These are minimum research gates, not
evidence of future profitability.

No live-trading claim may be made from contract tests or synthetic fixtures.
Market-data exports are required before the strategy can pass this gate.

