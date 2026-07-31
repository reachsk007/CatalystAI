"""JSON fixture loading and result serialization."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .models import CompanyObservation, FactorObservation, ScoreResult


def load_observations(path: str | Path) -> list[CompanyObservation]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    observations: list[CompanyObservation] = []
    for item in payload["companies"]:
        factors = {
            name: FactorObservation(
                score=value.get("score"),
                confidence=float(value["confidence"]),
                evidence=value["evidence"],
                source=value["source"],
            )
            for name, value in item["factors"].items()
        }
        observations.append(
            CompanyObservation(
                ticker=item["ticker"],
                company_name=item["company_name"],
                as_of_date=date.fromisoformat(item["as_of_date"]),
                factors=factors,
            )
        )
    return observations


def result_to_dict(result: ScoreResult) -> dict[str, object]:
    payload = asdict(result)
    payload["as_of_date"] = result.as_of_date.isoformat()
    return payload

