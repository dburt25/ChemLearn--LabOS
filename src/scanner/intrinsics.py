"""Camera intrinsics data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List
"""Camera intrinsics parsing and validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable, Optional
"""Camera intrinsics loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Intrinsics:
    """Intrinsic camera parameters used by marker-board anchoring."""

    fx: float
    fy: float
    cx: float
    cy: float
    distortion_coeffs: List[float] = field(default_factory=list)
    image_width: int = 0
    image_height: int = 0
    model: str = "pinhole"
    distortion_model: str = "opencv"

    def with_distortion(self, coeffs: Iterable[float]) -> "Intrinsics":
        return Intrinsics(
            fx=self.fx,
            fy=self.fy,
            cx=self.cx,
            cy=self.cy,
            distortion_coeffs=list(coeffs),
            image_width=self.image_width,
            image_height=self.image_height,
            model=self.model,
            distortion_model=self.distortion_model,
        )

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "distortion_model": self.distortion_model,
            "image_width": self.image_width,
            "image_height": self.image_height,
    dist: tuple[float, ...] = ()

    def camera_matrix(self):
        return [[self.fx, 0.0, self.cx], [0.0, self.fy, self.cy], [0.0, 0.0, 1.0]]

    def dist_coeffs(self):
        return list(self.dist)


def _validate_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}.")


def _validate_non_negative(name: str, value: float) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value}.")


def _validate_dist(dist: Iterable[float]) -> tuple[float, ...]:
    coeffs = tuple(float(item) for item in dist)
    if coeffs and len(coeffs) != 5:
        raise ValueError("dist must contain 5 values (k1,k2,p1,p2,k3) when provided.")
    return coeffs
    dist: tuple[float, float, float, float, float] = (0.0, 0.0, 0.0, 0.0, 0.0)

    def to_dict(self) -> dict[str, float | list[float]]:
        return {
            "fx": self.fx,
            "fy": self.fy,
            "cx": self.cx,
            "cy": self.cy,
            "distortion_coeffs": list(self.distortion_coeffs),
        }
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
    if not isinstance(payload, dict):
        raise ValueError("Intrinsics JSON must be an object.")

    required = ["fx", "fy", "cx", "cy"]
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Missing intrinsics fields: {', '.join(missing)}")
    missing = [key for key in ("fx", "fy", "cx", "cy") if key not in payload]
    if missing:
        raise ValueError(f"Intrinsics file missing required keys: {', '.join(missing)}")

    fx = float(payload["fx"])
    fy = float(payload["fy"])
    cx = float(payload["cx"])
    cy = float(payload["cy"])
    _validate_positive("fx", fx)
    _validate_positive("fy", fy)
    _validate_non_negative("cx", cx)
    _validate_non_negative("cy", cy)

    dist: Optional[Iterable[float]] = payload.get("dist")
    coeffs = _validate_dist(dist or ())

    return Intrinsics(fx=fx, fy=fy, cx=cx, cy=cy, dist=coeffs)


def parse_intrinsics_string(value: str, dist: Optional[str] = None) -> Intrinsics:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if len(parts) != 4:
        raise ValueError("Intrinsics string must be 'fx,fy,cx,cy'.")
    fx, fy, cx, cy = (float(part) for part in parts)
    _validate_positive("fx", fx)
    _validate_positive("fy", fy)
    _validate_non_negative("cx", cx)
    _validate_non_negative("cy", cy)

    dist_coeffs = ()
    if dist:
        dist_parts = [part.strip() for part in dist.split(",") if part.strip()]
        dist_coeffs = _validate_dist(dist_parts)

    return Intrinsics(fx=fx, fy=fy, cx=cx, cy=cy, dist=dist_coeffs)
    dist = _parse_distortion(payload.get("dist"))

    return Intrinsics(fx=fx, fy=fy, cx=cx, cy=cy, dist=dist)
