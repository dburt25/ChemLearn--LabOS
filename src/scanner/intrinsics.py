"""Camera intrinsics handling for marker anchoring."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Intrinsics:
    fx: float
    fy: float
    cx: float
    cy: float
    dist: list[float]

    def __post_init__(self) -> None:
        if len(self.dist) != 5:
            raise ValueError("dist must contain 5 coefficients: k1,k2,p1,p2,k3")

    @classmethod
    def from_json(cls, path: Path | str) -> "Intrinsics":
        data = json.loads(Path(path).read_text())
        dist = data.get("dist") or data.get("distortion") or [
            data.get("k1", 0.0),
            data.get("k2", 0.0),
            data.get("p1", 0.0),
            data.get("p2", 0.0),
            data.get("k3", 0.0),
        ]
        return cls(
            fx=float(data["fx"]),
            fy=float(data["fy"]),
            cx=float(data["cx"]),
            cy=float(data["cy"]),
            dist=[float(value) for value in dist],
        )


def add_intrinsics_argument(parser) -> None:
    parser.add_argument(
        "--intrinsics-file",
        type=Path,
        help="Path to camera intrinsics JSON (fx, fy, cx, cy, dist).",
    )


def load_intrinsics(path: Path | str | None) -> Intrinsics | None:
    if path is None:
        return None
    return Intrinsics.from_json(path)


def require_intrinsics_for_mode(
    mode: str,
    intrinsics: Intrinsics | None,
    *,
    allow_fallback: bool = False,
) -> None:
    """Require intrinsics for SMALL_OBJECT mode unless fallback is explicit."""

    if mode == "SMALL_OBJECT" and intrinsics is None and not allow_fallback:
        raise ValueError("Intrinsics are required for SMALL_OBJECT mode without fallback")
