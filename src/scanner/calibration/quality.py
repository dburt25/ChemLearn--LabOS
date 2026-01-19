"""Quality gates for camera calibration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

import numpy as np


@dataclass
class QualitySummary:
    passed: bool
    warnings: List[str] = field(default_factory=list)
    rejected_indices: List[int] = field(default_factory=list)
    p95_error: float | None = None


def reject_outliers(per_view_errors: Sequence[float]) -> tuple[list[int], float | None]:
    if not per_view_errors:
        return [], None
    p95 = float(np.percentile(per_view_errors, 95))
    rejected = [idx for idx, err in enumerate(per_view_errors) if err > p95]
    return rejected, p95


def assess_quality(
    num_views: int,
    rms_error: float | None,
    per_view_errors: Sequence[float],
    min_views: int,
    rms_threshold_px: float,
) -> QualitySummary:
    warnings: list[str] = []
    passed = True

    if num_views < min_views:
        warnings.append(
            f"Only {num_views} valid views; need at least {min_views} distinct views for robust intrinsics."
        )
        passed = False

    if rms_error is None:
        warnings.append("RMS reprojection error could not be computed.")
        passed = False
    elif rms_error > rms_threshold_px:
        warnings.append(
            f"RMS reprojection error {rms_error:.3f}px exceeds threshold {rms_threshold_px:.3f}px."
        )
        passed = False

    rejected, p95 = reject_outliers(per_view_errors)
    if rejected:
        warnings.append(
            f"Rejected {len(rejected)} view(s) above p95 reprojection error threshold {p95:.3f}px."
        )

    return QualitySummary(passed=passed, warnings=warnings, rejected_indices=rejected, p95_error=p95)
