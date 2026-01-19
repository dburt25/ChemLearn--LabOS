"""Marker detection and pose estimation helpers."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Iterable

import numpy as np

from scanner.board import BoardSpec, MarkerFamily
from scanner.intrinsics import Intrinsics

_cv2_spec = importlib.util.find_spec("cv2")
if _cv2_spec:
    import cv2


@dataclass(frozen=True)
class MarkerDetections:
    ids: list[int]
    corners: list[np.ndarray]


@dataclass(frozen=True)
class PoseEstimate:
    rvec: np.ndarray
    tvec: np.ndarray
    reproj_error_px: float
    used_markers: int


def aruco_available() -> bool:
    return bool(_cv2_spec) and hasattr(cv2, "aruco")


def _get_dictionary(family: MarkerFamily):
    if family == MarkerFamily.ARUCO_4X4:
        return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_50)


def _create_board(board_spec: BoardSpec):
    dictionary = _get_dictionary(board_spec.family)
    if hasattr(cv2.aruco, "GridBoard_create"):
        return cv2.aruco.GridBoard_create(
            board_spec.cols,
            board_spec.rows,
            board_spec.marker_size_m,
            board_spec.marker_spacing_m,
            dictionary,
        )
    return cv2.aruco.GridBoard.create(
        board_spec.cols,
        board_spec.rows,
        board_spec.marker_size_m,
        board_spec.marker_spacing_m,
        dictionary,
    )


def _ensure_gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def detect_markers_in_frame(
    image: np.ndarray,
    family: MarkerFamily = MarkerFamily.ARUCO_4X4,
) -> MarkerDetections:
    if not aruco_available():
        raise RuntimeError("cv2.aruco is unavailable")
    dictionary = _get_dictionary(family)
    if hasattr(cv2.aruco, "DetectorParameters_create"):
        params = cv2.aruco.DetectorParameters_create()
    else:
        params = cv2.aruco.DetectorParameters()

    gray = _ensure_gray(image)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=params)
    if ids is None or len(ids) == 0:
        return MarkerDetections(ids=[], corners=[])
    return MarkerDetections(ids=[int(x) for x in ids.flatten().tolist()], corners=corners)


def _build_point_correspondences(
    board: object,
    ids: Iterable[int],
    corners: Iterable[np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    board_ids = board.ids.flatten().tolist()
    mapping = {int(board_id): obj for board_id, obj in zip(board_ids, board.objPoints)}
    object_points = []
    image_points = []
    for marker_id, marker_corners in zip(ids, corners):
        if marker_id not in mapping:
            continue
        obj = np.asarray(mapping[marker_id]).reshape(-1, 3)
        img = np.asarray(marker_corners).reshape(-1, 2)
        object_points.append(obj)
        image_points.append(img)
    if not object_points:
        return np.zeros((0, 3), dtype=np.float32), np.zeros((0, 2), dtype=np.float32)
    return (
        np.concatenate(object_points, axis=0).astype(np.float32),
        np.concatenate(image_points, axis=0).astype(np.float32),
    )


def estimate_board_pose_per_frame(
    board_spec: BoardSpec,
    intrinsics: Intrinsics,
    detections: MarkerDetections,
) -> PoseEstimate | None:
    if not detections.ids:
        return None
    board = _create_board(board_spec)
    camera_matrix = np.array(
        [[intrinsics.fx, 0.0, intrinsics.cx], [0.0, intrinsics.fy, intrinsics.cy], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )
    dist_coeffs = np.array(intrinsics.dist, dtype=np.float64).reshape(1, 5)

    result = cv2.aruco.estimatePoseBoard(
        detections.corners,
        np.array(detections.ids, dtype=np.int32),
        board,
        camera_matrix,
        dist_coeffs,
    )
    if len(result) != 3:
        return None
    retval, rvec, tvec = result
    if retval is None or float(retval) <= 0.0:
        return None

    object_points, image_points = _build_point_correspondences(
        board, detections.ids, detections.corners
    )
    if object_points.size == 0:
        return None
    projected_points, _ = cv2.projectPoints(object_points, rvec, tvec, camera_matrix, dist_coeffs)
    projected_points = projected_points.reshape(-1, 2)
    errors = np.linalg.norm(projected_points - image_points, axis=1)
    reproj_error_px = float(np.mean(errors)) if errors.size else 0.0

    return PoseEstimate(
        rvec=np.array(rvec, dtype=np.float64).reshape(3, 1),
        tvec=np.array(tvec, dtype=np.float64).reshape(3, 1),
        reproj_error_px=reproj_error_px,
        used_markers=len(detections.ids),
    )
