# VWAPPlus research modules

This research architecture is separate from the production Pine scripts. Existing
indicator and strategy signals remain unchanged until a module survives
walk-forward, multi-symbol, and out-of-sample testing.

## Meaningful-anchor AVWAP

Anchored VWAP estimates volume-weighted participant cost basis after an observable
event; it is not a causal signal by itself. Supported anchors are a manual event,
session open, material gap, abnormal-volume bar, and liquidity sweep followed by
a close back through the prior boundary. Selection uses only bars known then.

## Isolated components

- Opening range freezes a first-N-bar high/low and waits for completion.
- Relative strength compares matched-window asset and benchmark returns.
- Liquidity context separates a boundary sweep from a failed breakout/breakdown.
- Volume participation excludes the current observation from its own baseline.

Each component returns context rather than an order. Use `walk_forward` for
expanding point-in-time evaluation. Define fills, costs, and missing-data policy
before testing; test modules alone before interactions; retain failed variants;
and report trade count, turnover, drawdown, exposure, and benchmark-relative
results. Promotion to Pine requires reproduction across symbols and regimes.

No module is investment advice, and no production default changes at this stage.

