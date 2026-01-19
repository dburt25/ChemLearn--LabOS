"""Quality gates for marker-board anchoring."""
"""Quality gate evaluation for anchor estimation."""

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
from typing import Iterable

import numpy as np


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
@dataclass(frozen=True)
class QualityGateResult:
    passed: bool
    failure_reasons: list[str]
    stats: dict[str, float]


def _mad_filter(values: np.ndarray, threshold: float = 3.5) -> np.ndarray:
    if values.size == 0:
        return values
    median = np.median(values)
    mad = np.median(np.abs(values - median))
    if mad == 0:
        return values
    modified_z = 0.6745 * (values - median) / mad
    return values[np.abs(modified_z) <= threshold]


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
) -> QualityGateResult:
    errors = np.array([float(value) for value in reproj_errors], dtype=np.float64)
    filtered = _mad_filter(errors)
    stats = {
        "total_frames": float(errors.size),
        "kept_frames": float(filtered.size),
        "mean_reproj_err_px": float(np.mean(filtered)) if filtered.size else float("inf"),
        "p95_reproj_err_px": float(np.percentile(filtered, 95)) if filtered.size else float("inf"),
        "median_reproj_err_px": float(np.median(filtered)) if filtered.size else float("inf"),
        "mad_reproj_err_px": float(np.median(np.abs(filtered - np.median(filtered))))
        if filtered.size
        else float("inf"),
    }

    failures: list[str] = []
    if filtered.size < config.min_frames_with_pose:
        failures.append("min_frames_with_pose")
    if stats["mean_reproj_err_px"] > config.max_mean_reproj_err_px:
        failures.append("max_mean_reproj_err_px")
    if stats["p95_reproj_err_px"] > config.max_p95_reproj_err_px:
        failures.append("max_p95_reproj_err_px")

    return QualityGateResult(passed=not failures, failure_reasons=failures, stats=stats)
