"""Marker detection and board pose estimation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from scanner.board import BoardSpec, MarkerFamily, _aruco_dictionary, _build_board
from scanner.intrinsics import Intrinsics

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
    corners: list
    corners: list[np.ndarray]


@dataclass(frozen=True)
class PoseEstimate:
    rvec: list[float]
    tvec: list[float]
    reproj_err_px: float
    detected_markers: int


class ArucoUnavailableError(RuntimeError):
    """Raised when OpenCV aruco support is unavailable."""


def _require_aruco():
    try:
        import cv2  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on env
        raise ArucoUnavailableError(
            "OpenCV is required for marker detection. Install opencv-contrib-python."
        ) from exc

    if not hasattr(cv2, "aruco"):
        raise ArucoUnavailableError(
            "OpenCV aruco module is unavailable. Install opencv-contrib-python."
        )
    return cv2


def detect_markers_in_frame(image, family: MarkerFamily = MarkerFamily.ARUCO_4X4) -> MarkerDetections:
    cv2 = _require_aruco()
    if image is None:
        return MarkerDetections(ids=[], corners=[])

    gray = image
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    dictionary = _aruco_dictionary(cv2, family)
    if hasattr(cv2.aruco, "ArucoDetector"):
        detector = cv2.aruco.ArucoDetector(dictionary)
        corners, ids, _ = detector.detectMarkers(gray)
    else:  # pragma: no cover - legacy OpenCV fallback
        corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary)
    if ids is None:
        return MarkerDetections(ids=[], corners=[])
    return MarkerDetections(ids=[int(val) for val in ids.flatten()], corners=corners)


def _compute_reproj_error(cv2, object_points, image_points, rvec, tvec, intrinsics: Intrinsics) -> float:
    projected, _ = cv2.projectPoints(object_points, rvec, tvec, intrinsics.camera_matrix(), intrinsics.dist_coeffs())
    projected = projected.reshape(-1, 2)
    image_points = image_points.reshape(-1, 2)
    if len(projected) == 0:
        return 0.0
    errors = ((projected - image_points) ** 2).sum(axis=1) ** 0.5
    return float(errors.mean())
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
) -> Optional[PoseEstimate]:
    if not detections.ids:
        return None

    cv2 = _require_aruco()
    board = _build_board(cv2, board_spec)

    object_points, image_points = cv2.aruco.getBoardObjectAndImagePoints(
        detections.corners,
        detections.ids,
        board,
    )
    if len(object_points) == 0:
        return None

    retval, rvec, tvec = cv2.aruco.estimatePoseBoard(
        detections.corners,
        detections.ids,
        board,
        intrinsics.camera_matrix(),
        intrinsics.dist_coeffs(),
        None,
        None,
    )
    if retval <= 0:
        return None

    reproj_err = _compute_reproj_error(
        cv2,
        object_points,
        image_points,
        rvec,
        tvec,
        intrinsics,
    )
    return PoseEstimate(
        rvec=[float(val) for val in rvec.flatten()],
        tvec=[float(val) for val in tvec.flatten()],
        reproj_err_px=reproj_err,
        detected_markers=int(retval),
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
