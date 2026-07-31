"""Run the deterministic backtest validation scenario."""

from catalystai.backtest import run_all_timeframes

from synthetic import build_synthetic_scenario


def main() -> None:
    bars, signals = build_synthetic_scenario()
    results = run_all_timeframes(
        bars,
        signals,
        top_n=1,
        minimum_score=60,
        transaction_cost_bps=10,
    )
    print(
        "Timeframe  Sessions  Rebalances  Total return  Annualized  "
        "Max drawdown  Benchmark  Turnover"
    )
    for result in results:
        print(
            f"{result.timeframe.name:<10} {result.sessions:>8} "
            f"{result.rebalances:>11} {result.total_return:>12.2%} "
            f"{result.annualized_return:>10.2%} "
            f"{result.maximum_drawdown:>12.2%} "
            f"{result.benchmark_return:>9.2%} {result.turnover:>9.2f}"
        )


if __name__ == "__main__":
    main()

