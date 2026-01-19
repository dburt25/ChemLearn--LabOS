"""Pose estimation and quality gates for marker boards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .board import BoardSpec, create_board
from .intrinsics import Intrinsics

try:
    import cv2
except ImportError:  # pragma: no cover - optional dependency
    cv2 = None


@dataclass(frozen=True)
class PoseQualityGates:
    min_frames_with_pose: int = 10
    max_mean_reproj_err_px: float = 2.0
    outlier_sigma: float = 3.5


@dataclass(frozen=True)
class AnchorPose:
    frame_index: int
    rvec: list[float]
    tvec: list[float]
    reproj_err_px: float
    camera_position_m: list[float]
    camera_rotation_matrix: list[list[float]]


def _camera_matrix(intrinsics: Intrinsics) -> np.ndarray:
    return np.array(
        [[intrinsics.fx, 0.0, intrinsics.cx], [0.0, intrinsics.fy, intrinsics.cy], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )


def _estimate_reprojection_error(
    board,
    corners,
    ids,
    rvec,
    tvec,
    intrinsics: Intrinsics,
) -> float:
    if cv2 is None:  # pragma: no cover - optional dependency
        raise RuntimeError("OpenCV is required for reprojection error")
    obj_points, img_points = board.matchImagePoints(corners, ids)
    if obj_points is None or img_points is None or len(obj_points) == 0:
        return float("inf")
    projected, _ = cv2.projectPoints(
        obj_points,
        rvec,
        tvec,
        _camera_matrix(intrinsics),
        np.array(intrinsics.dist, dtype=np.float64),
    )
    projected = projected.reshape(-1, 2)
    img_points = img_points.reshape(-1, 2)
    errors = np.linalg.norm(projected - img_points, axis=1)
    return float(np.mean(errors))


def estimate_board_poses(
    frames: Iterable[np.ndarray],
    spec: BoardSpec,
    intrinsics: Intrinsics,
) -> list[AnchorPose]:
    if cv2 is None:  # pragma: no cover - optional dependency
        raise RuntimeError("OpenCV is required for pose estimation")
    if not hasattr(cv2, "aruco"):
        raise RuntimeError("OpenCV ArUco module not available")

    board = create_board(spec)
    dictionary = board.dictionary
    camera_matrix = _camera_matrix(intrinsics)
    dist = np.array(intrinsics.dist, dtype=np.float64)

    poses: list[AnchorPose] = []
    for index, frame in enumerate(frames):
        corners, ids, _ = cv2.aruco.detectMarkers(frame, dictionary)
        if ids is None or len(ids) == 0:
            continue
        retval, rvec, tvec = cv2.aruco.estimatePoseBoard(
            corners,
            ids,
            board,
            camera_matrix,
            dist,
        )
        if retval <= 0:
            continue
        reproj_err = _estimate_reprojection_error(board, corners, ids, rvec, tvec, intrinsics)
        rotation_matrix, _ = cv2.Rodrigues(rvec)
        camera_rotation = rotation_matrix.T
        camera_position = (-camera_rotation @ tvec).reshape(3)
        poses.append(
            AnchorPose(
                frame_index=index,
                rvec=[float(v) for v in rvec.reshape(-1)],
                tvec=[float(v) for v in tvec.reshape(-1)],
                reproj_err_px=float(reproj_err),
                camera_position_m=[float(v) for v in camera_position],
                camera_rotation_matrix=camera_rotation.tolist(),
            )
        )
    return poses


def reject_outlier_poses(poses: Iterable[AnchorPose], sigma: float) -> list[AnchorPose]:
    poses = list(poses)
    if not poses:
        return []
    errors = np.array([pose.reproj_err_px for pose in poses], dtype=np.float64)
    median = np.median(errors)
    mad = np.median(np.abs(errors - median))
    if mad == 0:
        return poses
    threshold = median + sigma * 1.4826 * mad
    return [pose for pose, err in zip(poses, errors) if err <= threshold]


def evaluate_pose_quality(
    poses: Iterable[AnchorPose],
    gates: PoseQualityGates,
) -> tuple[bool, dict]:
    poses = list(poses)
    filtered = reject_outlier_poses(poses, gates.outlier_sigma)
    mean_error = float(np.mean([pose.reproj_err_px for pose in filtered])) if filtered else float("inf")
    meets_frames = len(filtered) >= gates.min_frames_with_pose
    meets_error = mean_error <= gates.max_mean_reproj_err_px

    return (
        meets_frames and meets_error,
        {
            "frames_with_pose": len(poses),
            "frames_after_rejection": len(filtered),
            "mean_reproj_err_px": mean_error,
            "thresholds": {
                "min_frames_with_pose": gates.min_frames_with_pose,
                "max_mean_reproj_err_px": gates.max_mean_reproj_err_px,
                "outlier_sigma": gates.outlier_sigma,
            },
        },
    )
