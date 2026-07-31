# Roadmap

This roadmap is intentionally staged. Later phases depend on evidence produced by earlier phases.

## Phase 0 — Foundation

- [x] Initialize repository structure
- [x] Add project overview, roadmap, ignore rules, and license placeholder
- [x] Add documentation placeholders
- [x] Select the initial Python toolchain and supported version
- [ ] Add contribution and coding standards
- [ ] Add continuous integration

## Phase 1 — Scoring specification

- [x] Define Compounder Score
- [ ] Define Opportunity Score
- [ ] Define Catalyst Score
- [ ] Define Expectations Risk
- [ ] Define Asymmetry Score
- [ ] Define Macro, Institutional, Sector Rotation, and Cycle scores
- [x] Define missing-data and confidence rules
- [ ] Define ranking weights without double-counting correlated factors
- [ ] Create worked examples for META and a second contrasting company

**Exit criterion:** every score can be reproduced from documented inputs.

## Phase 2 — Core engine

- [x] Create initial typed company, observation, and score models
- [x] Implement the deterministic Compounder scoring module
- [x] Add Compounder score explanations and data-lineage metadata
- [x] Add Compounder configuration and weight versioning
- [x] Build an initial command-line ranking workflow
- [x] Add Compounder unit tests

**Exit criterion:** a fixed fixture produces stable, explainable rankings.

## Phase 3 — Data pipeline

- [x] Define normalized source contracts and licensing constraints
- [ ] Add price and volume history
- [ ] Add SEC company filings and Form 4 activity
- [ ] Add financial statements and valuation history
- [ ] Add earnings estimates and revision history
- [ ] Add 13F institutional holdings
- [ ] Add options and short-interest data where legally and commercially available
- [ ] Add macro and sector-cycle observations
- [ ] Track effective date, publication date, ingestion date, and revisions

**Exit criterion:** the engine can run from dated, auditable snapshots without silently filling missing data.

## Phase 4 — VWAPPlus PRO execution layer

- [ ] Import and baseline the current VWAPPlus master Pine Script
- [ ] Add weekly, monthly, session, and anchored VWAP modes
- [ ] Add relative strength versus market and sector benchmarks
- [ ] Add accumulation, liquidity sweep, and crash-reclaim evidence
- [ ] Add manual CatalystAI score inputs
- [ ] Add entry zone, invalidation, target, and position-size outputs
- [ ] Separate indicator alerts from strategy backtests

**Exit criterion:** signals are non-repainting, documented, and reproducible on agreed test charts.

## Phase 5 — Dashboard and thesis tracking

- [ ] Ranked watchlist with score history
- [ ] Company scorecards with evidence and confidence
- [ ] Thesis, invalidation, catalyst, and decision journal
- [ ] Alerts for material score changes
- [ ] Portfolio exposure and risk view

## Phase 6 — Validation lab

- [ ] Build point-in-time universe membership
- [x] Add a fail-closed historical dataset readiness gate
- [x] Prevent signal-date look-ahead in the backtest engine
- [x] Add configurable transaction costs and turnover
- [ ] Add liquidity constraints and delistings
- [x] Add daily, weekly, monthly, quarterly, and annual rebalance tests
- [ ] Run walk-forward and out-of-sample tests
- [ ] Compare against simple quality, value, momentum, and benchmark baselines
- [ ] Publish failures and sensitivity analysis alongside successes

**Exit criterion:** claims are supported by repeatable out-of-sample evidence.

## Phase 7 — Iteration

- [ ] Automate scheduled refreshes
- [ ] Add model and data monitoring
- [ ] Review factor usefulness and redundancy
- [ ] Add AI-generated research summaries grounded in cited evidence
