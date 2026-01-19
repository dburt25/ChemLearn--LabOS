"""Quality gate evaluation for anchor estimation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class QualityGateConfig:
    min_frames_with_pose: int = 10
    max_mean_reproj_err_px: float = 2.0
    max_p95_reproj_err_px: float = 4.0


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
