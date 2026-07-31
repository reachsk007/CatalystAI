# CatalystAI / VWAPPlus PRO

CatalystAI is an evidence-driven investment research and execution project. It combines long-term business quality, temporary mispricing, credible catalysts, market expectations, and asymmetric return potential with VWAPPlus PRO technical execution.

> Status: early development. Nothing in this repository is investment advice, and no score or signal should be used with real capital before validation.

## What we are building

The system is designed to answer two separate questions:

1. **What deserves capital?** CatalystAI evaluates compounder quality, opportunity, catalysts, expectations, asymmetry, macro conditions, institutional evidence, and industry cycles.
2. **When is the entry actionable?** VWAPPlus PRO evaluates VWAP structure, relative strength, volume, liquidity events, accumulation, market regime, entries, invalidation, and position sizing.

## Repository map

```text
docs/          Investment philosophy, methodology, data, and specifications
tradingview/   Pine Script indicators and strategies
engine/        Fundamental, ranking, and signal engines
dashboard/     Research dashboard and thesis tracking
backtesting/   Point-in-time validation and portfolio simulations
tests/         Automated tests and test fixtures
```

## First milestone

The first milestone is a transparent, testable scoring framework:

- Define every score and its inputs.
- Separate slow-moving quality from fast-moving opportunity.
- Record data dates, sources, confidence, and missing inputs.
- Prevent look-ahead bias in historical tests.
- Produce explainable rankings rather than unexplained buy/sell labels.
- Connect scores to VWAPPlus PRO only after each layer is validated.

See [ROADMAP.md](ROADMAP.md) for the staged build plan.

## Development principles

- Evidence before intuition
- Point-in-time data before backtest claims
- Explainable scores before model complexity
- Risk and thesis invalidation before upside targets
- Human review before capital allocation
- Small, reviewable changes with tests and documentation

## Local setup

The first Engine milestone targets Python 3.11+ and has no runtime dependencies.

```powershell
python -m pip install -e .
catalystai rank --config config/compounder.v1.json --input fixtures/companies.v1.json
python -m unittest discover -s tests -v
```

See [docs/Engine.md](docs/Engine.md) for the scoring contract, confidence and
missing-data behavior, and fixture limitations. Pine Script remains the planned
TradingView execution layer.

## TradingView execution

VWAPPlus PRO now includes separate Pine v6 indicator and strategy scripts:

- `tradingview/VWAPPlus_PRO_Indicator.pine`
- `tradingview/VWAPPlus_PRO_Strategy.pine`

The strategy is the combined CatalystAI/VWAPPlus PRO decision engine: CatalystAI
research approval is mandatory before VWAP, market/sector, volume, trend,
multi-timeframe, risk, and staged-exit logic can authorize a simulated trade.

Both scripts accept explicit CatalystAI score and confidence inputs, support
session, weekly, monthly, and manually anchored VWAP, and use confirmed-bar,
lookahead-disabled execution evidence. See
[docs/VWAPPlus_User_Guide.md](docs/VWAPPlus_User_Guide.md).

## License

No license has been selected yet. See [LICENSE](LICENSE). Until a license is chosen, all rights are reserved.
