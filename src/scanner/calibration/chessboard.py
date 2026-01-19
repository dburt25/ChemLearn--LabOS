"""Chessboard calibration pipeline."""

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


def _object_points(board_size: tuple[int, int], square_size_mm: float) -> np.ndarray:
    cols, rows = board_size
    objp = np.zeros((rows * cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
    objp *= float(square_size_mm)
    return objp


def _compute_reprojection_errors(
    objpoints: Sequence[np.ndarray],
    imgpoints: Sequence[np.ndarray],
    rvecs: Sequence[np.ndarray],
    tvecs: Sequence[np.ndarray],
    camera_matrix: np.ndarray,
    dist_coeffs: np.ndarray,
) -> list[float]:
    import cv2  # type: ignore

    errors: list[float] = []
    for objp, imgp, rvec, tvec in zip(objpoints, imgpoints, rvecs, tvecs):
        projected, _ = cv2.projectPoints(objp, rvec, tvec, camera_matrix, dist_coeffs)
        projected = projected.reshape(-1, 2)
        imgp = imgp.reshape(-1, 2)
        error = np.sqrt(np.mean(np.sum((imgp - projected) ** 2, axis=1)))
        errors.append(float(error))
    return errors


def _detect_corners(
    images: Sequence[np.ndarray],
    labels: Sequence[str],
    board_size: tuple[int, int],
) -> tuple[list[np.ndarray], list[np.ndarray], list[str], list[np.ndarray], list[np.ndarray]]:
    import cv2  # type: ignore

    objpoints: list[np.ndarray] = []
    imgpoints: list[np.ndarray] = []
    used_labels: list[str] = []
    corners_for_preview: list[np.ndarray] = []
    images_for_preview: list[np.ndarray] = []

    objp = _object_points(board_size, 1.0)

    for image, label in zip(images, labels):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        found, corners = cv2.findChessboardCorners(gray, board_size)
        if not found or corners is None:
            continue
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        objpoints.append(objp)
        imgpoints.append(refined)
        used_labels.append(label)
        corners_for_preview.append(refined)
        images_for_preview.append(image)

    return objpoints, imgpoints, used_labels, corners_for_preview, images_for_preview


def calibrate_chessboard(
    *,
    images: Sequence[np.ndarray],
    labels: Sequence[str],
    board_size: tuple[int, int],
    square_size_mm: float,
    min_views: int,
    rms_threshold_px: float,
) -> tuple[CalibrationResult, CalibrationDetails, list[np.ndarray], list[np.ndarray]]:
    if importlib.util.find_spec("cv2") is None:  # pragma: no cover
        raise RuntimeError(
            "OpenCV is required for chessboard calibration. Install opencv-python."
        )
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

    objpoints, imgpoints, used_labels, preview_corners, preview_images = _detect_corners(
        images, labels, board_size
    )

    if not objpoints:
        result = CalibrationResult(
            intrinsics=None,
            rms_reproj_err_px=None,
            per_view_errors=[],
            num_images_used=0,
            warnings=["No chessboard corners detected."],
            passed_quality_gates=False,
        )
        details = CalibrationDetails(rejected_indices=[], p95_error_px=None, labels_used=[])
        return result, details, [], []

    image_size = (images[0].shape[1], images[0].shape[0])
    objpoints_scaled = [obj * square_size_mm for obj in objpoints]

    rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        objpoints_scaled,
        imgpoints,
        image_size,
        None,
        None,
    )
    per_view_errors = _compute_reprojection_errors(
        objpoints_scaled, imgpoints, rvecs, tvecs, camera_matrix, dist_coeffs
    )

    rejected_indices, p95 = reject_outliers(per_view_errors)
    if rejected_indices:
        objpoints_scaled = [
            obj for idx, obj in enumerate(objpoints_scaled) if idx not in rejected_indices
        ]
        imgpoints = [
            img for idx, img in enumerate(imgpoints) if idx not in rejected_indices
        ]
        used_labels = [
            label for idx, label in enumerate(used_labels) if idx not in rejected_indices
        ]
        rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            objpoints_scaled,
            imgpoints,
            image_size,
            None,
            None,
        )
        per_view_errors = _compute_reprojection_errors(
            objpoints_scaled, imgpoints, rvecs, tvecs, camera_matrix, dist_coeffs
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
        num_views=len(objpoints_scaled),
        rms_error=float(rms) if rms is not None else None,
        per_view_errors=per_view_errors,
        min_views=min_views,
        rms_threshold_px=rms_threshold_px,
    )

    warnings = quality.warnings
    passed = quality.passed

    result = CalibrationResult(
        intrinsics=intrinsics,
        rms_reproj_err_px=float(rms) if rms is not None else None,
        per_view_errors=per_view_errors,
        num_images_used=len(objpoints_scaled),
        warnings=warnings,
        passed_quality_gates=passed,
    )
    details = CalibrationDetails(
        rejected_indices=rejected_indices,
        p95_error_px=p95,
        labels_used=used_labels,
    )
    return result, details, preview_corners, preview_images


def draw_chessboard_previews(
    images: Sequence[np.ndarray],
    corners: Sequence[np.ndarray],
    board_size: tuple[int, int],
) -> list[np.ndarray]:
    import cv2  # type: ignore

    previews: list[np.ndarray] = []
    for image, corner_set in zip(images, corners):
        preview = image.copy()
        cv2.drawChessboardCorners(preview, board_size, corner_set, True)
        previews.append(preview)
    return previews
