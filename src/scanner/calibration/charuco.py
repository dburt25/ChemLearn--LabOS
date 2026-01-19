"""Charuco calibration pipeline."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from typing import List, Sequence

import numpy as np

from scanner.calibration.models import CalibrationResult
from scanner.calibration.quality import assess_quality, reject_outliers
from scanner.intrinsics import Intrinsics


@dataclass
class CalibrationDetails:
    rejected_indices: List[int]
    p95_error_px: float | None
    labels_used: List[str]


def aruco_capability() -> tuple[bool, str]:
    if importlib.util.find_spec("cv2") is None:
        return False, "OpenCV is not installed. Install opencv-contrib-python for Charuco support."
    import cv2  # type: ignore

    if not hasattr(cv2, "aruco"):
        return False, (
            "OpenCV aruco module missing. Install opencv-contrib-python to enable Charuco."
        )

    required = ["CharucoBoard", "DetectorParameters", "calibrateCameraCharuco"]
    missing = [name for name in required if not hasattr(cv2.aruco, name)]
    if missing:
        return False, (
            "OpenCV aruco module lacks Charuco support. Install opencv-contrib-python >= 4.7."
        )

    return True, ""


def _aruco_dictionary(family: str):
    import cv2  # type: ignore

    if family == "aruco_4x4":
        return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    if family == "aruco_5x5":
        return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_50)
    raise ValueError(f"Unsupported aruco family: {family}")


def _compute_reprojection_errors(
    board,
    charuco_corners: Sequence[np.ndarray],
    charuco_ids: Sequence[np.ndarray],
    rvecs: Sequence[np.ndarray],
    tvecs: Sequence[np.ndarray],
    camera_matrix: np.ndarray,
    dist_coeffs: np.ndarray,
) -> list[float]:
    import cv2  # type: ignore

    errors: list[float] = []
    for corners, ids, rvec, tvec in zip(charuco_corners, charuco_ids, rvecs, tvecs):
        if corners is None or ids is None:
            continue
        ids_flat = ids.flatten()
        obj_points = board.chessboardCorners[ids_flat]
        projected, _ = cv2.projectPoints(obj_points, rvec, tvec, camera_matrix, dist_coeffs)
        projected = projected.reshape(-1, 2)
        imgp = corners.reshape(-1, 2)
        error = np.sqrt(np.mean(np.sum((imgp - projected) ** 2, axis=1)))
        errors.append(float(error))
    return errors


def calibrate_charuco(
    *,
    images: Sequence[np.ndarray],
    labels: Sequence[str],
    squares_x: int,
    squares_y: int,
    square_length_mm: float,
    marker_length_mm: float,
    aruco_family: str,
    min_views: int,
    rms_threshold_px: float,
) -> tuple[CalibrationResult, CalibrationDetails, list[tuple[np.ndarray, np.ndarray]], list[np.ndarray]]:
    ready, message = aruco_capability()
    if not ready:
        result = CalibrationResult(
            intrinsics=None,
            rms_reproj_err_px=None,
            per_view_errors=[],
            num_images_used=0,
            warnings=[message],
            passed_quality_gates=False,
        )
        details = CalibrationDetails(rejected_indices=[], p95_error_px=None, labels_used=[])
        return result, details, [], []

    import cv2  # type: ignore

    if not images:
        result = CalibrationResult(
            intrinsics=None,
            rms_reproj_err_px=None,
            per_view_errors=[],
            num_images_used=0,
            warnings=["No images supplied for calibration."],
            passed_quality_gates=False,
        )
        details = CalibrationDetails(rejected_indices=[], p95_error_px=None, labels_used=[])
        return result, details, [], []

    dictionary = _aruco_dictionary(aruco_family)
    board = cv2.aruco.CharucoBoard((squares_x, squares_y), square_length_mm, marker_length_mm, dictionary)
    params = cv2.aruco.DetectorParameters()

    charuco_corners: list[np.ndarray] = []
    charuco_ids: list[np.ndarray] = []
    used_labels: list[str] = []
    preview_corners: list[tuple[np.ndarray, np.ndarray]] = []
    preview_images: list[np.ndarray] = []

    for image, label in zip(images, labels):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=params)
        if ids is None or len(ids) == 0:
            continue
        retval, ch_corners, ch_ids = cv2.aruco.interpolateCornersCharuco(
            markerCorners=corners,
            markerIds=ids,
            image=gray,
            board=board,
        )
        if retval is None or retval < 4:
            continue
        if ch_corners is None or ch_ids is None:
            continue
        charuco_corners.append(ch_corners)
        charuco_ids.append(ch_ids)
        used_labels.append(label)
        preview_corners.append((ch_corners, ch_ids))
        preview_images.append(image)

    if not charuco_corners:
        result = CalibrationResult(
            intrinsics=None,
            rms_reproj_err_px=None,
            per_view_errors=[],
            num_images_used=0,
            warnings=["No Charuco corners detected."],
            passed_quality_gates=False,
        )
        details = CalibrationDetails(rejected_indices=[], p95_error_px=None, labels_used=[])
        return result, details, [], []

    image_size = (images[0].shape[1], images[0].shape[0])

    rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(
        charuco_corners,
        charuco_ids,
        board,
        image_size,
        None,
        None,
    )

    per_view_errors = _compute_reprojection_errors(
        board, charuco_corners, charuco_ids, rvecs, tvecs, camera_matrix, dist_coeffs
    )
    rejected_indices, p95 = reject_outliers(per_view_errors)
    if rejected_indices:
        charuco_corners = [
            corners for idx, corners in enumerate(charuco_corners) if idx not in rejected_indices
        ]
        charuco_ids = [ids for idx, ids in enumerate(charuco_ids) if idx not in rejected_indices]
        used_labels = [
            label for idx, label in enumerate(used_labels) if idx not in rejected_indices
        ]
        rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(
            charuco_corners,
            charuco_ids,
            board,
            image_size,
            None,
            None,
        )
        per_view_errors = _compute_reprojection_errors(
            board, charuco_corners, charuco_ids, rvecs, tvecs, camera_matrix, dist_coeffs
        )

    intrinsics = Intrinsics(
        fx=float(camera_matrix[0, 0]),
        fy=float(camera_matrix[1, 1]),
        cx=float(camera_matrix[0, 2]),
        cy=float(camera_matrix[1, 2]),
        distortion_coeffs=[float(x) for x in dist_coeffs.flatten().tolist()],
        image_width=int(image_size[0]),
        image_height=int(image_size[1]),
    )

    quality = assess_quality(
        num_views=len(charuco_corners),
        rms_error=float(rms) if rms is not None else None,
        per_view_errors=per_view_errors,
        min_views=min_views,
        rms_threshold_px=rms_threshold_px,
    )

    result = CalibrationResult(
        intrinsics=intrinsics,
        rms_reproj_err_px=float(rms) if rms is not None else None,
        per_view_errors=per_view_errors,
        num_images_used=len(charuco_corners),
        warnings=quality.warnings,
        passed_quality_gates=quality.passed,
    )
    details = CalibrationDetails(
        rejected_indices=rejected_indices,
        p95_error_px=p95,
        labels_used=used_labels,
    )
    return result, details, preview_corners, preview_images


def draw_charuco_previews(
    images: Sequence[np.ndarray],
    detections: Sequence[tuple[np.ndarray, np.ndarray]],
    board,
) -> list[np.ndarray]:
    import cv2  # type: ignore

    previews: list[np.ndarray] = []
    for image, (corner_set, id_set) in zip(images, detections):
        preview = image.copy()
        cv2.aruco.drawDetectedCornersCharuco(preview, corner_set, id_set, (0, 255, 0))
        previews.append(preview)
    return previews
