import importlib.util

import pytest

from scanner.anchors import resolve_marker_board_anchor
from scanner.board import BoardSpec, MarkerFamily, generate_board_png
from scanner.intrinsics import Intrinsics
from scanner.pose_estimation import detect_markers_in_frame
from scanner.quality_gates import QualityGateConfig


def _aruco_available() -> bool:
    spec = importlib.util.find_spec("cv2")
    if not spec:
        return False
    import cv2

    return hasattr(cv2, "aruco")


@pytest.mark.skipif(not _aruco_available(), reason="cv2.aruco not available")
def test_marker_detection_on_generated_board(tmp_path):
    import cv2

    spec = BoardSpec(
        family=MarkerFamily.ARUCO_4X4,
        rows=4,
        cols=6,
        marker_size_m=0.02,
        marker_spacing_m=0.005,
    )
    image_path = tmp_path / "board.png"
    generate_board_png(spec, image_path)
    image = cv2.imread(str(image_path))
    detections = detect_markers_in_frame(image, spec.family)
    assert detections.ids


@pytest.mark.skipif(_aruco_available(), reason="cv2.aruco available")
def test_anchor_reports_capability_missing(tmp_path):
    spec = BoardSpec(
        family=MarkerFamily.ARUCO_4X4,
        rows=4,
        cols=6,
        marker_size_m=0.02,
        marker_spacing_m=0.005,
    )
    intrinsics = Intrinsics(fx=1000, fy=1000, cx=320, cy=240)
    result = resolve_marker_board_anchor(
        frames=[],
        board_spec=spec,
        intrinsics=intrinsics,
        quality_config=QualityGateConfig(),
        frame_step=1,
        output_dir=tmp_path,
    )
    assert not result.applied
    assert result.failure_reason == "capability_missing"
    assert "opencv-contrib-python" in result.evidence.get("guidance", "")
