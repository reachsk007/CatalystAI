# VWAPPlus PRO User Guide

VWAPPlus PRO is CatalystAI's execution layer. CatalystAI determines what deserves
research capital; VWAPPlus determines whether current price, volume, relative
strength, and risk structure provide an actionable entry.

## Scripts

- `VWAPPlus_PRO_Indicator.pine` provides visual VWAP structure, research gating,
  relative strength, accumulation/distribution, liquidity sweeps, invalidation,
  target, position-size guidance, and alerts.
- `VWAPPlus_PRO_Strategy.pine` mirrors the core confirmed-bar entry logic and adds
  next-bar execution, commissions, slippage, ATR/VWAP stops, profit targets,
  dynamic risk sizing, and date-range controls.

## CatalystAI integration

Enter the current CatalystAI composite score and research confidence in the script
settings. These are explicit manual inputs in version 1 because Pine scripts
cannot query CatalystAI's local Python process directly. A setup is blocked when
either input falls below its configured threshold.

## VWAP modes

- Session resets each trading day.
- Weekly resets at the first bar of each week.
- Monthly resets at the first bar of each month.
- Anchored begins at the user-selected timestamp.

The bands use volume-weighted dispersion around the active VWAP.

## Validation rules

- Use standard OHLC candles for strategy testing.
- Compare daily, weekly, monthly, and anchored configurations separately.
- Use Deep Backtesting where available.
- Keep commission and slippage enabled.
- Test multiple symbols and market regimes; one Pine strategy runs on one symbol
  at a time.
- Treat manual CatalystAI inputs as known only from their real publication date.
- Do not optimize parameters on the same interval used for final evaluation.

Nothing in these scripts is investment advice. Backtests are simulations and may
not represent achievable fills or future results.

