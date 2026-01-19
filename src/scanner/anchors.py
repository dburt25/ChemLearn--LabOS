"""Anchor resolution for marker-board world frames."""

from __future__ import annotations

import json
import importlib.util
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional

import numpy as np

from scanner.board import BoardSpec
from scanner.intrinsics import Intrinsics
from scanner.pose_estimation import aruco_available, detect_markers_in_frame, estimate_board_pose_per_frame
from scanner.quality_gates import QualityGateConfig, evaluate_quality_gates

_cv2_spec = importlib.util.find_spec("cv2")
if _cv2_spec:
    import cv2


class AnchorType(Enum):
    MARKER_BOARD = "marker_board"


@dataclass
class AnchorPose:
    frame_index: int
    translation_m: list[float]
    rotation_quat_wxyz: list[float]
    reproj_error_px: float
    timestamp: Optional[float] = None


@dataclass
class AnchorResult:
    anchor_type: AnchorType
    resolved: bool
    applied: bool
    failure_reason: Optional[str] = None
    origin_xyz: Optional[list[float]] = None
    rotation_quat_wxyz: Optional[list[float]] = None
    scale_factor: Optional[float] = None
    evidence: dict = field(default_factory=dict)
    anchor_poses_path: Optional[str] = None
    anchor_summary_path: Optional[str] = None


def _rotation_matrix_to_quaternion_wxyz(rotation: np.ndarray) -> list[float]:
    trace = np.trace(rotation)
    if trace > 0.0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (rotation[2, 1] - rotation[1, 2]) * s
        y = (rotation[0, 2] - rotation[2, 0]) * s
        z = (rotation[1, 0] - rotation[0, 1]) * s
    else:
        if rotation[0, 0] > rotation[1, 1] and rotation[0, 0] > rotation[2, 2]:
            s = 2.0 * np.sqrt(1.0 + rotation[0, 0] - rotation[1, 1] - rotation[2, 2])
            w = (rotation[2, 1] - rotation[1, 2]) / s
            x = 0.25 * s
            y = (rotation[0, 1] + rotation[1, 0]) / s
            z = (rotation[0, 2] + rotation[2, 0]) / s
        elif rotation[1, 1] > rotation[2, 2]:
            s = 2.0 * np.sqrt(1.0 + rotation[1, 1] - rotation[0, 0] - rotation[2, 2])
            w = (rotation[0, 2] - rotation[2, 0]) / s
            x = (rotation[0, 1] + rotation[1, 0]) / s
            y = 0.25 * s
            z = (rotation[1, 2] + rotation[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + rotation[2, 2] - rotation[0, 0] - rotation[1, 1])
            w = (rotation[1, 0] - rotation[0, 1]) / s
            x = (rotation[0, 2] + rotation[2, 0]) / s
            y = (rotation[1, 2] + rotation[2, 1]) / s
            z = 0.25 * s
    return [float(w), float(x), float(y), float(z)]


def _board_center_offset(board_spec: BoardSpec) -> np.ndarray:
    width = board_spec.cols * board_spec.marker_size_m + (
        board_spec.cols - 1
    ) * board_spec.marker_spacing_m
    height = board_spec.rows * board_spec.marker_size_m + (
        board_spec.rows - 1
    ) * board_spec.marker_spacing_m
    return np.array([width / 2.0, height / 2.0, 0.0], dtype=np.float64).reshape(3, 1)


def _write_anchor_artifacts(
    output_dir: Path,
    poses: Iterable[AnchorPose],
    summary: dict,
) -> tuple[str, str]:
    anchor_dir = output_dir / "anchor"
    anchor_dir.mkdir(parents=True, exist_ok=True)
    poses_path = anchor_dir / "anchor_poses.json"
    summary_path = anchor_dir / "anchor_summary.json"
    poses_payload = [
        {
            "frame_index": pose.frame_index,
            "timestamp": pose.timestamp,
            "translation_m": pose.translation_m,
            "rotation_quat_wxyz": pose.rotation_quat_wxyz,
            "reproj_error_px": pose.reproj_error_px,
        }
        for pose in poses
    ]
    poses_path.write_text(json.dumps(poses_payload, indent=2, sort_keys=True), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return str(poses_path), str(summary_path)


def resolve_marker_board_anchor(
    frames: list[np.ndarray],
    board_spec: BoardSpec,
    intrinsics: Intrinsics | None,
    quality_config: QualityGateConfig,
    frame_step: int,
    output_dir: str | Path,
    timestamps: Optional[list[float]] = None,
) -> AnchorResult:
    if intrinsics is None:
        return AnchorResult(
            anchor_type=AnchorType.MARKER_BOARD,
            resolved=False,
            applied=False,
            failure_reason="missing_intrinsics",
            evidence={"required": "intrinsics"},
        )
    if not aruco_available():
        return AnchorResult(
            anchor_type=AnchorType.MARKER_BOARD,
            resolved=False,
            applied=False,
            failure_reason="capability_missing",
            evidence={"guidance": "Install opencv-contrib-python to enable cv2.aruco"},
        )

    poses: list[AnchorPose] = []
    reproj_errors: list[float] = []
    marker_ids: set[int] = set()
    center_offset = _board_center_offset(board_spec)

    for index in range(0, len(frames), max(1, frame_step)):
        detections = detect_markers_in_frame(frames[index], board_spec.family)
        marker_ids.update(detections.ids)
        pose = estimate_board_pose_per_frame(board_spec, intrinsics, detections)
        if pose is None:
            continue
        rotation, _ = cv2.Rodrigues(pose.rvec)
        tvec_center = pose.tvec + rotation @ center_offset
        rotation_world_from_cam = rotation.T
        translation_world_from_cam = -rotation_world_from_cam @ tvec_center
        quaternion = _rotation_matrix_to_quaternion_wxyz(rotation_world_from_cam)
        timestamp = None
        if timestamps and index < len(timestamps):
            timestamp = timestamps[index]
        poses.append(
            AnchorPose(
                frame_index=index,
                translation_m=translation_world_from_cam.flatten().tolist(),
                rotation_quat_wxyz=quaternion,
                reproj_error_px=pose.reproj_error_px,
                timestamp=timestamp,
            )
        )
        reproj_errors.append(pose.reproj_error_px)

    gate_result = evaluate_quality_gates(reproj_errors, quality_config)
    evidence = {
        "board_id": board_spec.board_id,
        "marker_ids": sorted(marker_ids),
        "frame_count": len(frames),
        "frames_with_pose": len(poses),
        "reproj_error_stats": gate_result.stats,
        "quality_gates": {
            "min_frames_with_pose": quality_config.min_frames_with_pose,
            "max_mean_reproj_err_px": quality_config.max_mean_reproj_err_px,
            "max_p95_reproj_err_px": quality_config.max_p95_reproj_err_px,
        },
    }

    if not gate_result.passed:
        return AnchorResult(
            anchor_type=AnchorType.MARKER_BOARD,
            resolved=False,
            applied=False,
            failure_reason=",".join(gate_result.failure_reasons),
            evidence=evidence,
        )

    output_dir = Path(output_dir)
    summary = {
        "board_spec": board_spec.to_dict(),
        "intrinsics": intrinsics.to_dict(),
        "frames_with_pose": len(poses),
        "reproj_error_stats": gate_result.stats,
    }
    poses_path, summary_path = _write_anchor_artifacts(output_dir, poses, summary)

    return AnchorResult(
        anchor_type=AnchorType.MARKER_BOARD,
        resolved=True,
        applied=True,
        origin_xyz=[0.0, 0.0, 0.0],
        rotation_quat_wxyz=[1.0, 0.0, 0.0, 0.0],
        scale_factor=1.0,
        evidence=evidence,
        anchor_poses_path=poses_path,
        anchor_summary_path=summary_path,
    )
