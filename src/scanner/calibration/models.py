"""Calibration data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from scanner.intrinsics import Intrinsics


@dataclass
class CalibrationResult:
    intrinsics: Intrinsics | None
    rms_reproj_err_px: float | None
    per_view_errors: List[float] = field(default_factory=list)
    num_images_used: int = 0
    warnings: List[str] = field(default_factory=list)
    passed_quality_gates: bool = False
