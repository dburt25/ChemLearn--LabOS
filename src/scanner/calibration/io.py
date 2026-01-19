"""IO helpers for calibration artifacts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Iterable, List, Sequence

import numpy as np

from scanner.intrinsics import Intrinsics

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def _sorted_image_paths(directory: Path) -> list[Path]:
    return sorted(
        [path for path in directory.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS]
    )


def load_images_from_input(
    input_path: Path,
    frame_step: int = 1,
    max_frames: int | None = None,
) -> tuple[list[np.ndarray], list[str]]:
    if importlib.util.find_spec("cv2") is None:  # pragma: no cover - tested via CLI capability checks
        raise RuntimeError(
            "OpenCV is required for calibration. Install opencv-python or opencv-contrib-python."
        )
    import cv2  # type: ignore

    images: list[np.ndarray] = []
    labels: list[str] = []

    if input_path.is_dir():
        for idx, img_path in enumerate(_sorted_image_paths(input_path)):
            if idx % frame_step != 0:
                continue
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            images.append(img)
            labels.append(img_path.name)
            if max_frames is not None and len(images) >= max_frames:
                break
        return images, labels

    if not input_path.exists():
        raise FileNotFoundError(f"Input path not found: {input_path}")

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {input_path}")

    frame_idx = 0
    grabbed = True
    while grabbed:
        grabbed, frame = cap.read()
        if not grabbed:
            break
        if frame_idx % frame_step != 0:
            frame_idx += 1
            continue
        images.append(frame)
        labels.append(f"frame_{frame_idx:06d}")
        frame_idx += 1
        if max_frames is not None and len(images) >= max_frames:
            break
    cap.release()
    return images, labels


def ensure_output_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_camera_json(path: Path, intrinsics: Intrinsics) -> None:
    ensure_output_dir(path)
    payload = intrinsics.to_dict()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def save_calibration_report(path: Path, report: dict) -> None:
    ensure_output_dir(path)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def validate_camera_json(payload: dict) -> list[str]:
    errors: list[str] = []
    required = [
        "model",
        "distortion_model",
        "image_width",
        "image_height",
        "fx",
        "fy",
        "cx",
        "cy",
        "distortion_coeffs",
    ]
    for key in required:
        if key not in payload:
            errors.append(f"Missing required field '{key}'.")

    if "distortion_coeffs" in payload and not isinstance(payload["distortion_coeffs"], list):
        errors.append("'distortion_coeffs' must be a list.")

    numeric_fields = ["image_width", "image_height", "fx", "fy", "cx", "cy"]
    for field in numeric_fields:
        if field in payload and not isinstance(payload[field], (int, float)):
            errors.append(f"'{field}' must be numeric.")

    return errors


def validate_report_json(payload: dict) -> list[str]:
    errors: list[str] = []
    required = [
        "num_images_used",
        "min_views_required",
        "rms_reproj_err_px",
        "rms_threshold_px",
        "per_view_errors",
        "passed_quality_gates",
        "warnings",
    ]
    for key in required:
        if key not in payload:
            errors.append(f"Missing required field '{key}'.")

    if "per_view_errors" in payload and not isinstance(payload["per_view_errors"], list):
        errors.append("'per_view_errors' must be a list.")

    if "warnings" in payload and not isinstance(payload["warnings"], list):
        errors.append("'warnings' must be a list.")

    return errors


def report_payload(
    *,
    num_images_used: int,
    min_views_required: int,
    rms_reproj_err_px: float | None,
    rms_threshold_px: float,
    per_view_errors: Sequence[float],
    passed_quality_gates: bool,
    warnings: Iterable[str],
    rejected_views: Iterable[int] | None = None,
    p95_error_px: float | None = None,
    suggestions: Iterable[str] | None = None,
) -> dict:
    return {
        "num_images_used": num_images_used,
        "min_views_required": min_views_required,
        "rms_reproj_err_px": rms_reproj_err_px,
        "rms_threshold_px": rms_threshold_px,
        "per_view_errors": list(per_view_errors),
        "passed_quality_gates": passed_quality_gates,
        "warnings": list(warnings),
        "rejected_views": list(rejected_views or []),
        "p95_error_px": p95_error_px,
        "suggestions": list(suggestions or []),
    }
