import pytest

from scanner.anchors import FrameData, resolve_marker_board_anchor
from scanner.board import BoardSpec, MarkerFamily, generate_board_png
from scanner.intrinsics import Intrinsics
from scanner.pose_estimation import detect_markers_in_frame
from scanner.quality_gates import QualityGateConfig


def _has_aruco() -> bool:
    try:
        import cv2  # type: ignore
    except ModuleNotFoundError:
        return False
    return hasattr(cv2, "aruco")


def test_aruco_capability(tmp_path):
    board_spec = BoardSpec(
        family=MarkerFamily.ARUCO_4X4,
        rows=2,
        cols=2,
        marker_size_m=0.02,
        marker_spacing_m=0.005,
        origin_definition="board_center",
        board_id="capability-test",
    )

    if _has_aruco():
        import cv2  # type: ignore

        out_path = tmp_path / "board.png"
        generate_board_png(board_spec, out_path, dpi=300)
        image = cv2.imread(str(out_path))
        detections = detect_markers_in_frame(image, board_spec.family)

        assert detections.ids
    else:
        intrinsics = Intrinsics(fx=500.0, fy=500.0, cx=320.0, cy=240.0)
        frames = [FrameData(index=0, image=None, timestamp=None)]
        result, poses = resolve_marker_board_anchor(
            frames,
            board_spec,
            intrinsics,
            QualityGateConfig(min_frames_with_pose=1),
            frame_step=1,
        )

        assert poses == []
        assert result.capability_missing is True
        assert result.failure_reason == "aruco_unavailable"
