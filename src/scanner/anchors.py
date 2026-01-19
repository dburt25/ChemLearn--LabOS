"""Anchor resolution for marker-board world frames."""

from __future__ import annotations

import json
import importlib.util
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
