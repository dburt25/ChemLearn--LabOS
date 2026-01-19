"""Scanner pipeline hooks for reference frame handling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

from .io import write_ply
from .reference_frame import (
    ReferenceFramePolicy,
    ReferenceFrameResult,
    ReferenceFrameUserInputs,
    ScanRegime,
    resolve_reference_frame,
    translate_points,
)


def _serialize_reference_frame(
    result: ReferenceFrameResult,
    user_inputs: ReferenceFrameUserInputs,
) -> dict:
    return {
        "source": result.source.value,
        "origin_xyz": result.origin_xyz,
        "confidence": result.confidence.value,
        "warnings": list(result.warnings),
        "missing_requirements": list(result.missing_requirements),
        "provided_anchors": {
            "marker_anchor": user_inputs.marker_anchor,
            "geo_anchor": user_inputs.geo_anchor,
            "time_anchor": user_inputs.time_anchor,
        },
    }


def _scaled_points(
    points: Sequence[Tuple[float, float, float]], scale: float
) -> list[Tuple[float, float, float]]:
    return [(x * scale, y * scale, z * scale) for x, y, z in points]


def run_pipeline(
    output_dir: Path,
    *,
    regime: ScanRegime,
    points: Optional[Sequence[Tuple[float, float, float]]] = None,
    scale: float = 1.0,
    user_inputs: Optional[ReferenceFrameUserInputs] = None,
    allow_heuristic_center: Optional[bool] = None,
    require_explicit_origin: Optional[bool] = None,
    write_artifacts: bool = True,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    user_inputs = user_inputs or ReferenceFrameUserInputs()
    policy = ReferenceFramePolicy.for_regime(
        regime,
        allow_heuristic_center=allow_heuristic_center,
        require_explicit_origin=require_explicit_origin,
    )

    scaled_points = _scaled_points(points, scale) if points else None
    result = resolve_reference_frame(scaled_points, policy, user_inputs)

    centered_points: Optional[Iterable[Tuple[float, float, float]]] = None
    if scaled_points is not None and result.origin_xyz is not None:
        centered_points = translate_points(scaled_points, result.origin_xyz)

    if write_artifacts and centered_points is not None:
        write_ply(output_dir / "cloud_scaled_centered.ply", centered_points)

    reference_frame_payload = _serialize_reference_frame(result, user_inputs)

    run_payload = {
        "regime": regime.value,
        "reference_frame": reference_frame_payload,
    }
    run_path = output_dir / "run.json"
    run_path.write_text(json.dumps(run_payload, indent=2, sort_keys=True), encoding="utf-8")

    metrics_payload = {
        "reference_frame": reference_frame_payload,
        "point_count": len(points) if points else 0,
        "output": {
            "centered_point_cloud": "cloud_scaled_centered.ply"
            if centered_points is not None
            else None,
        },
    }
    metrics_path = output_dir / "reconstruction_metrics.json"
    metrics_path.write_text(
        json.dumps(metrics_payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    return {
        "run": run_payload,
        "metrics": metrics_payload,
        "reference_frame": reference_frame_payload,
    }
