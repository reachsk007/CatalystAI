# Engine

The first Engine milestone implements an explainable Compounder Score using only
dated, manually reviewed fixture data. It deliberately does not fetch live data
or produce buy and sell signals.

## Score factors

Version 1 uses six normalized factors:

- moat,
- growth durability,
- capital efficiency,
- balance-sheet strength,
- management execution, and
- cash generation.

Each observation includes a 0–100 assessment, confidence from 0–1, evidence,
source, and as-of date. Confidence changes a factor's effective weight. Missing
factors reduce reported coverage, and the scorer fails closed below the
configured minimum coverage.

The initial META and Ford values are illustrative research fixtures, not verified
financial data or investment recommendations.

## Run locally

Python 3.11 or newer is required.

```powershell
python -m pip install -e .
catalystai rank --config config/compounder.v1.json --input fixtures/companies.v1.json
python -m unittest discover -s tests -v
```

Use `--json` on the ranking command to obtain the complete contribution and
evidence audit trail.

## Backtesting

The backtester supports daily, weekly, monthly, quarterly, and annual rebalance
horizons. Every trade uses only a signal dated before the trade session, which
prevents same-day and future information from leaking into a result. It reports
returns, annualized volatility, Sharpe ratio, maximum drawdown, benchmark-relative
return, turnover, and transaction costs.

Run the deterministic three-year validation scenario:

```powershell
$env:PYTHONPATH = "engine"
python backtesting/run_timeframes.py
```

The scenario is synthetic and exists only to validate calculation mechanics
across horizons. Real performance evaluation requires licensed, point-in-time
prices, corporate actions, universe membership, delistings, and dated fundamental
snapshots.

The normalized production-data requirements and fail-closed readiness rules are
defined in [Historical_Data_Contract.md](Historical_Data_Contract.md).
