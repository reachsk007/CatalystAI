"""Command-line interface for transparent fixture scoring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_compounder_config
from .io import load_observations, result_to_dict
from .scoring import CompounderScorer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="catalystai")
    subparsers = parser.add_subparsers(dest="command", required=True)
    rank = subparsers.add_parser("rank", help="rank company fixture observations")
    rank.add_argument("--config", type=Path, required=True)
    rank.add_argument("--input", type=Path, required=True)
    rank.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "rank":
        return 2

    scorer = CompounderScorer(load_compounder_config(args.config))
    results = sorted(
        (scorer.score(item) for item in load_observations(args.input)),
        key=lambda result: result.score,
        reverse=True,
    )
    if args.as_json:
        print(json.dumps([result_to_dict(result) for result in results], indent=2))
        return 0

    print("Rank  Ticker  Score  Coverage  Confidence  As of")
    for rank, result in enumerate(results, start=1):
        print(
            f"{rank:>4}  {result.ticker:<6}  {result.score:>5.1f}  "
            f"{result.coverage:>8.0%}  {result.confidence:>10.0%}  "
            f"{result.as_of_date.isoformat()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

