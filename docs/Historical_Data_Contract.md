# Historical Data Contract

A result may be called a historical backtest only after the readiness gate accepts
all five normalized datasets:

1. `security_master.csv` — permanent identifiers, ticker-effective dates, and
   delisting dates.
2. `prices.csv` — unadjusted point-in-time closes and volume by permanent ID.
3. `corporate_actions.csv` — splits and dividends needed to calculate total
   returns without silently mixing adjustment conventions.
4. `financials.csv` — observations keyed by both period end and public filing
   date. Strategies may use `filed_on`, never merely `period_end`.
5. `universe_membership.csv` — effective-dated membership including securities
   that later left the universe or delisted.

## Required providers

- SEC EDGAR supplies public filing dates, accession numbers, and XBRL company
  facts without an API key.
- A licensed market-data provider must supply prices, corporate actions, stable
  security identifiers, delisted securities, and historical universe membership.

The Engine intentionally rejects incomplete data rather than reporting a biased
performance result. Free current-ticker lists and adjusted-price downloads do not
meet this contract because they cannot establish historical membership or
delisting completeness.

## CSV columns

```text
security_master.csv:
permanent_id,ticker,effective_from,effective_to,delisted_on

prices.csv:
permanent_id,session,close,volume

corporate_actions.csv:
permanent_id,action_date,action_type,value

financials.csv:
permanent_id,metric,period_end,filed_on,value,accession_number

universe_membership.csv:
universe,permanent_id,effective_from,effective_to
```

