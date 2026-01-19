"""Camera intrinsics handling for marker anchoring."""
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
