"""Quality gates for marker-board anchoring."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable


@dataclass(frozen=True)
class QualityGateStats:
    frame_count: int
    accepted_frame_count: int
    mean_reproj_err_px: float
    p95_reproj_err_px: float
    rejected_count: int


@dataclass(frozen=True)
class QualityGateConfig:
    min_frames_with_pose: int = 10
    max_mean_reproj_err_px: float = 2.0
    max_p95_reproj_err_px: float = 4.0


def _mad(values: list[float]) -> float:
    med = median(values)
    deviations = [abs(value - med) for value in values]
    return median(deviations)


def reject_outliers_mad(values: Iterable[float], threshold: float = 3.5) -> tuple[list[float], int]:
    items = list(values)
    if not items:
        return [], 0
    med = median(items)
    mad = _mad(items)
    if mad == 0:
        return items, 0
    filtered = [value for value in items if abs(value - med) / mad <= threshold]
    return filtered, len(items) - len(filtered)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    index = int(round((len(values_sorted) - 1) * percentile))
    return values_sorted[index]


def evaluate_quality_gates(
    reproj_errors: Iterable[float],
    config: QualityGateConfig,
) -> tuple[bool, str | None, QualityGateStats]:
    values = list(reproj_errors)
    filtered, rejected = reject_outliers_mad(values)
    if not filtered:
        stats = QualityGateStats(
            frame_count=len(values),
            accepted_frame_count=0,
            mean_reproj_err_px=0.0,
            p95_reproj_err_px=0.0,
            rejected_count=rejected,
        )
        return False, "no_valid_reprojection_errors", stats

    mean_err = sum(filtered) / len(filtered)
    p95_err = _percentile(filtered, 0.95)
    stats = QualityGateStats(
        frame_count=len(values),
        accepted_frame_count=len(filtered),
        mean_reproj_err_px=mean_err,
        p95_reproj_err_px=p95_err,
        rejected_count=rejected,
    )

    if stats.accepted_frame_count < config.min_frames_with_pose:
        return False, "min_frames_with_pose", stats
    if stats.mean_reproj_err_px > config.max_mean_reproj_err_px:
        return False, "mean_reproj_error", stats
    if stats.p95_reproj_err_px > config.max_p95_reproj_err_px:
        return False, "p95_reproj_error", stats

    return True, None, stats
