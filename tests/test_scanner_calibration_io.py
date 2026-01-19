"""Tests for calibration IO schemas."""

from __future__ import annotations

from scanner.calibration.io import report_payload, validate_camera_json, validate_report_json
from scanner.intrinsics import Intrinsics


def test_camera_json_validation_roundtrip() -> None:
    intrinsics = Intrinsics(
        fx=1000.0,
        fy=1001.0,
        cx=512.0,
        cy=384.0,
        distortion_coeffs=[0.1, -0.02, 0.001, 0.0, 0.0],
        image_width=1024,
        image_height=768,
    )
    payload = intrinsics.to_dict()
    assert validate_camera_json(payload) == []

    payload.pop("fx")
    errors = validate_camera_json(payload)
    assert any("fx" in error for error in errors)


def test_report_json_validation() -> None:
    payload = report_payload(
        num_images_used=10,
        min_views_required=15,
        rms_reproj_err_px=0.9,
        rms_threshold_px=0.8,
        per_view_errors=[0.5, 0.6],
        passed_quality_gates=False,
        warnings=["Only 10 views"],
        rejected_views=[1],
        p95_error_px=0.7,
        suggestions=["Capture more views"],
    )
    assert validate_report_json(payload) == []

    payload.pop("warnings")
    errors = validate_report_json(payload)
    assert any("warnings" in error for error in errors)
