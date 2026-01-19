"""Camera intrinsics loading and validation."""

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
    dist: tuple[float, float, float, float, float] = (0.0, 0.0, 0.0, 0.0, 0.0)

    def to_dict(self) -> dict[str, float | list[float]]:
        return {
            "fx": self.fx,
            "fy": self.fy,
            "cx": self.cx,
            "cy": self.cy,
            "dist": list(self.dist),
        }


def _parse_distortion(dist: Iterable[float] | None) -> tuple[float, float, float, float, float]:
    if dist is None:
        return (0.0, 0.0, 0.0, 0.0, 0.0)
    values = [float(value) for value in dist]
    if len(values) not in (4, 5):
        raise ValueError("dist must have 4 or 5 coefficients")
    if len(values) == 4:
        values.append(0.0)
    return tuple(values)  # type: ignore[return-value]


def load_intrinsics_json(path: str | Path) -> Intrinsics:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [key for key in ("fx", "fy", "cx", "cy") if key not in payload]
    if missing:
        raise ValueError(f"Intrinsics file missing required keys: {', '.join(missing)}")

    fx = float(payload["fx"])
    fy = float(payload["fy"])
    cx = float(payload["cx"])
    cy = float(payload["cy"])
    dist = _parse_distortion(payload.get("dist"))

    return Intrinsics(fx=fx, fy=fy, cx=cx, cy=cy, dist=dist)
