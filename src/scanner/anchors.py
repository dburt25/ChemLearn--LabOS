"""Anchor resolution for marker-board world frames."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional

import json

from scanner.board import BoardSpec
from scanner.intrinsics import Intrinsics
from scanner.pose_estimation import (
    ArucoUnavailableError,
    MarkerDetections,
    PoseEstimate,
    detect_markers_in_frame,
    estimate_board_pose_per_frame,
)
from scanner.quality_gates import QualityGateConfig, evaluate_quality_gates


class AnchorType(str, Enum):
    MARKER_BOARD = "marker_board"


@dataclass(frozen=True)
class FramePose:
    frame_index: int
    timestamp: Optional[float]
    translation_xyz: list[float]
    rotation_quat_wxyz: list[float]
    reproj_err_px: float
    detected_markers: int


@dataclass
class AnchorResult:
    anchor_type: AnchorType
    resolved: bool
    applied: bool
    origin_xyz: Optional[list[float]] = None
    rotation_quat_wxyz: Optional[list[float]] = None
    scale_factor: Optional[float] = None
    failure_reason: Optional[str] = None
    evidence: dict = field(default_factory=dict)
    capability_missing: bool = False
    guidance: Optional[str] = None


@dataclass(frozen=True)
class FrameData:
    index: int
    image: object
    timestamp: Optional[float] = None


def _rotation_matrix_to_quaternion_wxyz(rotation) -> list[float]:
    import numpy as np

    r = np.array(rotation, dtype=float)
    trace = np.trace(r)
    if trace > 0:
        s = 0.5 / (trace + 1.0) ** 0.5
        w = 0.25 / s
        x = (r[2, 1] - r[1, 2]) * s
        y = (r[0, 2] - r[2, 0]) * s
        z = (r[1, 0] - r[0, 1]) * s
    else:
        if r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
            s = 2.0 * (1.0 + r[0, 0] - r[1, 1] - r[2, 2]) ** 0.5
            w = (r[2, 1] - r[1, 2]) / s
            x = 0.25 * s
            y = (r[0, 1] + r[1, 0]) / s
            z = (r[0, 2] + r[2, 0]) / s
        elif r[1, 1] > r[2, 2]:
            s = 2.0 * (1.0 + r[1, 1] - r[0, 0] - r[2, 2]) ** 0.5
            w = (r[0, 2] - r[2, 0]) / s
            x = (r[0, 1] + r[1, 0]) / s
            y = 0.25 * s
            z = (r[1, 2] + r[2, 1]) / s
        else:
            s = 2.0 * (1.0 + r[2, 2] - r[0, 0] - r[1, 1]) ** 0.5
            w = (r[1, 0] - r[0, 1]) / s
            x = (r[0, 2] + r[2, 0]) / s
            y = (r[1, 2] + r[2, 1]) / s
            z = 0.25 * s
    return [float(w), float(x), float(y), float(z)]


def _pose_to_world_from_cam(pose: PoseEstimate, board_spec: BoardSpec):
    import numpy as np
    import cv2  # type: ignore

    rvec = np.array(pose.rvec, dtype=float).reshape(3, 1)
    tvec = np.array(pose.tvec, dtype=float).reshape(3, 1)
    rotation, _ = cv2.Rodrigues(rvec)
    center = np.array(board_spec.board_center_m, dtype=float).reshape(3, 1)
    tvec_center = tvec + rotation @ center
    world_from_cam_rotation = rotation.T
    world_from_cam_translation = -(rotation.T @ tvec_center)
    quat = _rotation_matrix_to_quaternion_wxyz(world_from_cam_rotation)
    return quat, world_from_cam_translation.flatten().tolist()


def resolve_marker_board_anchor(
    frames: Iterable[FrameData],
    board_spec: Optional[BoardSpec],
    intrinsics: Optional[Intrinsics],
    gate_config: QualityGateConfig,
    frame_step: int = 1,
) -> tuple[AnchorResult, list[FramePose]]:
    frame_list = list(frames)
    if board_spec is None:
        return (
            AnchorResult(
                anchor_type=AnchorType.MARKER_BOARD,
                resolved=False,
                applied=False,
                failure_reason="missing_board_spec",
            ),
            [],
        )
    if intrinsics is None:
        return (
            AnchorResult(
                anchor_type=AnchorType.MARKER_BOARD,
                resolved=False,
                applied=False,
                failure_reason="missing_intrinsics",
            ),
            [],
        )

    poses: list[FramePose] = []
    reproj_errors: list[float] = []
    detected_ids: set[int] = set()

    try:
        for frame in frame_list:
            if frame.index % frame_step != 0:
                continue
            detections = detect_markers_in_frame(frame.image, board_spec.family)
            detected_ids.update(detections.ids)
            pose = estimate_board_pose_per_frame(board_spec, intrinsics, detections)
            if pose is None:
                continue
            quat, translation = _pose_to_world_from_cam(pose, board_spec)
            reproj_errors.append(pose.reproj_err_px)
            poses.append(
                FramePose(
                    frame_index=frame.index,
                    timestamp=frame.timestamp,
                    translation_xyz=translation,
                    rotation_quat_wxyz=quat,
                    reproj_err_px=pose.reproj_err_px,
                    detected_markers=pose.detected_markers,
                )
            )
    except ArucoUnavailableError as exc:
        return (
            AnchorResult(
                anchor_type=AnchorType.MARKER_BOARD,
                resolved=False,
                applied=False,
                failure_reason="aruco_unavailable",
                capability_missing=True,
                guidance=str(exc),
            ),
            [],
        )

    passed, reason, stats = evaluate_quality_gates(reproj_errors, gate_config)
    evidence = {
        "detected_marker_ids": sorted(detected_ids),
        "frame_count": len(frame_list),
        "poses_with_valid_board": len(poses),
        "reproj_error_stats": {
            "frame_count": stats.frame_count,
            "accepted_frame_count": stats.accepted_frame_count,
            "mean_reproj_err_px": stats.mean_reproj_err_px,
            "p95_reproj_err_px": stats.p95_reproj_err_px,
            "rejected_count": stats.rejected_count,
        },
        "frame_step": frame_step,
    }

    if not passed:
        return (
            AnchorResult(
                anchor_type=AnchorType.MARKER_BOARD,
                resolved=False,
                applied=False,
                failure_reason=reason,
                evidence=evidence,
            ),
            poses,
        )

    return (
        AnchorResult(
            anchor_type=AnchorType.MARKER_BOARD,
            resolved=True,
            applied=True,
            origin_xyz=list(board_spec.board_center_m),
            rotation_quat_wxyz=[1.0, 0.0, 0.0, 0.0],
            scale_factor=1.0,
            evidence={
                **evidence,
                "origin_definition": board_spec.origin_definition,
                "scale_confidence": "high",
            },
        ),
        poses,
    )


def write_anchor_artifacts(
    output_dir: str | Path,
    anchor_result: AnchorResult,
    poses: Iterable[FramePose],
) -> None:
    output_dir = Path(output_dir)
    anchor_dir = output_dir / "anchor"
    anchor_dir.mkdir(parents=True, exist_ok=True)

    poses_payload = [
        {
            "frame_index": pose.frame_index,
            "timestamp": pose.timestamp,
            "translation_xyz": pose.translation_xyz,
            "rotation_quat_wxyz": pose.rotation_quat_wxyz,
            "reproj_err_px": pose.reproj_err_px,
            "detected_markers": pose.detected_markers,
        }
        for pose in poses
    ]
    (anchor_dir / "anchor_poses.json").write_text(
        json.dumps(poses_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    summary_payload = {
        "anchor_type": anchor_result.anchor_type.value,
        "resolved": anchor_result.resolved,
        "applied": anchor_result.applied,
        "origin_xyz": anchor_result.origin_xyz,
        "rotation_quat_wxyz": anchor_result.rotation_quat_wxyz,
        "scale_factor": anchor_result.scale_factor,
        "failure_reason": anchor_result.failure_reason,
        "capability_missing": anchor_result.capability_missing,
        "guidance": anchor_result.guidance,
        "evidence": anchor_result.evidence,
    }
    (anchor_dir / "anchor_summary.json").write_text(
        json.dumps(summary_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
