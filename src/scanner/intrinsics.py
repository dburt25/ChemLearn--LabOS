"""Camera intrinsics data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


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
            "fx": self.fx,
            "fy": self.fy,
            "cx": self.cx,
            "cy": self.cy,
            "distortion_coeffs": list(self.distortion_coeffs),
        }
