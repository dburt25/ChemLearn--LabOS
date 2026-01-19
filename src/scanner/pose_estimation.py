"""Marker detection and board pose estimation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from scanner.board import BoardSpec, MarkerFamily, _aruco_dictionary, _build_board
from scanner.intrinsics import Intrinsics


@dataclass(frozen=True)
class MarkerDetections:
    ids: list[int]
    corners: list


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
    )
