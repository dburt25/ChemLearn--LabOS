"""Anchor resolution using marker board world frames."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import numpy as np

from .board import BoardSpec
from .intrinsics import Intrinsics
from .pose import AnchorPose, PoseQualityGates, estimate_board_poses, evaluate_pose_quality, reject_outlier_poses

try:
    import cv2
except ImportError:  # pragma: no cover - optional dependency
    cv2 = None


@dataclass(frozen=True)
class ReferenceFrame:
    origin_m: list[float]
    axes: list[list[float]]


@dataclass(frozen=True)
class ScaleConstraints:
    confidence: str


@dataclass(frozen=True)
class AnchorResult:
    resolved: bool
    applied: bool
    failure_reason: Optional[str]
    scale_constraints: ScaleConstraints
    reference_frame: Optional[ReferenceFrame]
    poses: list[AnchorPose]
    summary: dict


def _default_reference_frame() -> ReferenceFrame:
    return ReferenceFrame(origin_m=[0.0, 0.0, 0.0], axes=np.eye(3).tolist())


def resolve_board_anchor(
    frames: Iterable[np.ndarray],
    spec: BoardSpec,
    intrinsics: Intrinsics | None,
    *,
    gates: PoseQualityGates | None = None,
    output_dir: Path | str | None = None,
) -> AnchorResult:
    if intrinsics is None:
        return AnchorResult(
            resolved=False,
            applied=False,
            failure_reason="missing_intrinsics",
            scale_constraints=ScaleConstraints(confidence="LOW"),
            reference_frame=None,
            poses=[],
            summary={},
        )
    if cv2 is None or not hasattr(cv2, "aruco"):
        return AnchorResult(
            resolved=False,
            applied=False,
            failure_reason="aruco_unavailable",
            scale_constraints=ScaleConstraints(confidence="LOW"),
            reference_frame=None,
            poses=[],
            summary={},
        )
    gates = gates or PoseQualityGates()

    poses = estimate_board_poses(frames, spec, intrinsics)
    ok, summary = evaluate_pose_quality(poses, gates)

    filtered = reject_outlier_poses(poses, gates.outlier_sigma)
    summary["rejected_frames"] = [
        pose.frame_index for pose in poses if pose.frame_index not in {p.frame_index for p in filtered}
    ]

    if not ok:
        return AnchorResult(
            resolved=False,
            applied=False,
            failure_reason="pose_quality_gate_failed",
            scale_constraints=ScaleConstraints(confidence="LOW"),
            reference_frame=None,
            poses=filtered,
            summary=summary,
        )

    reference_frame = _default_reference_frame()
    result = AnchorResult(
        resolved=True,
        applied=True,
        failure_reason=None,
        scale_constraints=ScaleConstraints(confidence="HIGH"),
        reference_frame=reference_frame,
        poses=filtered,
        summary=summary,
    )

    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        _write_anchor_artifacts(output_path, result, spec)

    return result


def _write_anchor_artifacts(output_dir: Path, result: AnchorResult, spec: BoardSpec) -> None:
    poses_path = output_dir / "anchor_poses.json"
    summary_path = output_dir / "anchor_summary.json"

    poses_payload = [
        {
            "frame_index": pose.frame_index,
            "rvec": pose.rvec,
            "tvec": pose.tvec,
            "reproj_err_px": pose.reproj_err_px,
            "camera_position_m": pose.camera_position_m,
            "camera_rotation_matrix": pose.camera_rotation_matrix,
        }
        for pose in result.poses
    ]
    summary_payload = {
        "resolved": result.resolved,
        "applied": result.applied,
        "failure_reason": result.failure_reason,
        "scale_confidence": result.scale_constraints.confidence,
        "reference_frame": result.reference_frame.__dict__ if result.reference_frame else None,
        "board_spec": {
            "family": spec.family,
            "rows": spec.rows,
            "cols": spec.cols,
            "marker_size_m": spec.marker_size_m,
            "marker_spacing_m": spec.marker_spacing_m,
            "origin_definition": spec.origin_definition,
        },
        "stats": result.summary,
    }

    poses_path.write_text(json.dumps(poses_payload, indent=2))
    summary_path.write_text(json.dumps(summary_payload, indent=2))
