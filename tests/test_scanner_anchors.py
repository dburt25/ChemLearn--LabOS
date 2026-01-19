"""Tests for scanner anchors and marker detection."""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import pytest

from scanner.anchors import AnchorType, MarkerFamily, ScanRegime, parse_anchor_spec
from scanner.markers import detect_markers


def test_parse_anchor_spec_marker_auto():
    spec = parse_anchor_spec(
        anchor=None,
        regime=ScanRegime.SMALL_OBJECT,
        marker_family="aruco_4x4",
        marker_size_m=0.02,
    )
    assert spec is not None
    assert spec.anchor_type is AnchorType.MARKER_BOARD


def test_parse_anchor_spec_geo_anchor():
    spec = parse_anchor_spec(
        anchor="geo",
        regime=ScanRegime.AERIAL,
        geo_anchor="37.1,-122.2,15",
    )
    assert spec is not None
    assert spec.anchor_type is AnchorType.GEO_POINT
    assert spec.geo_lat == pytest.approx(37.1)
    assert spec.geo_lon == pytest.approx(-122.2)
    assert spec.geo_alt_m == pytest.approx(15.0)


def test_marker_detection_capability_missing(tmp_path: Path):
    result = detect_markers(
        frames_dir=tmp_path,
        marker_family=MarkerFamily.ARUCO_4X4,
        marker_ids=None,
        marker_size_m=None,
        metadata={},
    )
    if not result.available:
        assert result.failure_reason in {"opencv_missing", "aruco_missing"}
        assert any("opencv-contrib-python" in warning for warning in result.warnings)
    else:
        assert result.evidence["frames_scanned"] == 0


def test_marker_detection_synthetic(tmp_path: Path):
    cv2 = _load_cv2()
    if cv2 is None or not hasattr(cv2, "aruco"):
        result = detect_markers(
            frames_dir=tmp_path,
            marker_family=MarkerFamily.ARUCO_4X4,
            marker_ids=None,
            marker_size_m=None,
            metadata={},
        )
        assert not result.available
        return

    marker_image = _generate_marker(cv2)
    image_path = tmp_path / "marker.png"
    cv2.imwrite(str(image_path), marker_image)

    result = detect_markers(
        frames_dir=tmp_path,
        marker_family=_marker_family("aruco_4x4"),
        marker_ids=None,
        marker_size_m=None,
        metadata={},
    )

    assert result.available
    assert 0 in result.detected_ids


def _load_cv2():
    if importlib.util.find_spec("cv2") is None:
        return None
    return importlib.import_module("cv2")


def _marker_family(name: str):
    from scanner.anchors import MarkerFamily

    return MarkerFamily(name)


def _generate_marker(cv2):
    import numpy as np

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    side = 200
    if hasattr(cv2.aruco, "generateImageMarker"):
        marker = cv2.aruco.generateImageMarker(dictionary, 0, side)
        return marker
    marker = np.zeros((side, side), dtype="uint8")
    cv2.aruco.drawMarker(dictionary, 0, side, marker, 1)
    return marker
