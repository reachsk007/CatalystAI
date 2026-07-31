"""Configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CompounderConfig:
    version: str
    weights: dict[str, float]
    minimum_coverage: float

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("configuration version is required")
        if not self.weights or any(weight <= 0 for weight in self.weights.values()):
            raise ValueError("all factor weights must be positive")
        if abs(sum(self.weights.values()) - 1.0) > 1e-9:
            raise ValueError("factor weights must sum to 1.0")
        if not 0 <= self.minimum_coverage <= 1:
            raise ValueError("minimum_coverage must be between 0 and 1")


def load_compounder_config(path: str | Path) -> CompounderConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return CompounderConfig(
        version=str(payload["version"]),
        weights={key: float(value) for key, value in payload["weights"].items()},
        minimum_coverage=float(payload.get("minimum_coverage", 0.75)),
    )

