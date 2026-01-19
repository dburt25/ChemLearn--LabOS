"""Tests for scanner anchor parsing and marker capability handling."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _PROJECT_ROOT / "src"
for path in (_PROJECT_ROOT, _SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from scanner import anchors
from scanner.anchor_types import AnchorSpec, AnchorType, MarkerFamily, ScanRegime
from scanner import markers


class AnchorParsingTests(unittest.TestCase):
    def test_parse_marker_anchor_spec(self) -> None:
        spec = anchors.parse_anchor_spec(
            anchor="marker",
            regime=ScanRegime.SMALL_OBJECT,
            marker_family="aruco_5x5",
            marker_ids="0,1,2",
            marker_size_m=0.04,
            geo_anchor=None,
            time_anchor=None,
        )
        self.assertIsInstance(spec, AnchorSpec)
        assert spec is not None
        self.assertEqual(spec.anchor_type, AnchorType.MARKER_BOARD)
        self.assertEqual(spec.marker_family, MarkerFamily.ARUCO_5X5)
        self.assertEqual(spec.marker_ids, [0, 1, 2])
        self.assertEqual(spec.marker_size_m, 0.04)

    def test_parse_geo_anchor_spec(self) -> None:
        spec = anchors.parse_anchor_spec(
            anchor="geo",
            regime=ScanRegime.AERIAL,
            marker_family=None,
            marker_ids=None,
            marker_size_m=None,
            geo_anchor="37.1,-122.5,15",
            time_anchor="2025-01-02T03:04:05Z",
        )
        self.assertIsInstance(spec, AnchorSpec)
        assert spec is not None
        self.assertEqual(spec.anchor_type, AnchorType.GEO_POINT)
        self.assertEqual(spec.geo_lat, 37.1)
        self.assertEqual(spec.geo_lon, -122.5)
        self.assertEqual(spec.geo_alt_m, 15.0)
        self.assertEqual(spec.time_iso8601, "2025-01-02T03:04:05Z")


class MarkerCapabilityTests(unittest.TestCase):
    def test_marker_capability_missing_returns_clean_result(self) -> None:
        has_capability, _ = markers.aruco_capability_status()
        if has_capability:
            self.skipTest("OpenCV aruco available; skipping missing capability assertion.")
        with tempfile.TemporaryDirectory() as temp_dir:
            spec = AnchorSpec(
                anchor_type=AnchorType.MARKER_BOARD,
                regime=ScanRegime.SMALL_OBJECT,
                marker_family=MarkerFamily.ARUCO_4X4,
                marker_size_m=0.04,
            )
            result = markers.resolve_marker_anchor(
                spec,
                Path(temp_dir),
                metadata={},
                marker_frames_max=1,
            )
        self.assertFalse(result.resolved)
        self.assertEqual(result.failure_reason, "marker_capability_missing")
        self.assertTrue(result.warnings)

    def test_marker_detection_when_capable(self) -> None:
        has_capability, _ = markers.aruco_capability_status()
        if not has_capability:
            self.skipTest("OpenCV aruco unavailable; skipping detection test.")
        image = markers.generate_marker_image(
            marker_id=7,
            marker_family=MarkerFamily.ARUCO_4X4,
            side_pixels=200,
        )
        self.assertIsNotNone(image)
        if image is None:
            return
        cv2_spec = __import__("importlib").util.find_spec("cv2")
        self.assertIsNotNone(cv2_spec)
        cv2 = __import__("importlib").import_module("cv2")

        with tempfile.TemporaryDirectory() as temp_dir:
            frame_path = Path(temp_dir) / "frame-000.png"
            cv2.imwrite(str(frame_path), image)
            spec = AnchorSpec(
                anchor_type=AnchorType.MARKER_BOARD,
                regime=ScanRegime.SMALL_OBJECT,
                marker_family=MarkerFamily.ARUCO_4X4,
                marker_size_m=0.05,
            )
            result = markers.resolve_marker_anchor(
                spec,
                Path(temp_dir),
                metadata={
                    "camera_intrinsics": {
                        "fx": 800.0,
                        "fy": 800.0,
                        "cx": 100.0,
                        "cy": 100.0,
                    }
                },
                marker_frames_max=1,
            )
        self.assertTrue(result.resolved)
        self.assertIn(7, result.evidence.get("detected_ids", []))
        self.assertIsNotNone(result.scale_factor)
