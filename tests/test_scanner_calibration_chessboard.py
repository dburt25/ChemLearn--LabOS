"""Tests for chessboard calibration pipeline."""

from __future__ import annotations

import numpy as np
import pytest

from scanner.calibration.chessboard import calibrate_chessboard


pytest.importorskip("cv2")
import cv2  # noqa: E402


def _generate_chessboard(inner_corners_x: int, inner_corners_y: int, square_px: int = 40) -> np.ndarray:
    squares_x = inner_corners_x + 1
    squares_y = inner_corners_y + 1
    board = np.zeros((squares_y * square_px, squares_x * square_px), dtype=np.uint8)
    for y in range(squares_y):
        for x in range(squares_x):
            if (x + y) % 2 == 0:
                board[
                    y * square_px : (y + 1) * square_px,
                    x * square_px : (x + 1) * square_px,
                ] = 255
    return cv2.cvtColor(board, cv2.COLOR_GRAY2BGR)


def test_chessboard_calibration_insufficient_views() -> None:
    board_size = (7, 6)
    base = _generate_chessboard(*board_size)
    images = []
    labels = []
    for idx, angle in enumerate([-5, 0, 5]):
        center = (base.shape[1] // 2, base.shape[0] // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            base,
            matrix,
            (base.shape[1], base.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderValue=(127, 127, 127),
        )
        images.append(rotated)
        labels.append(f"synthetic_{idx}")

    result, _, _, _ = calibrate_chessboard(
        images=images,
        labels=labels,
        board_size=board_size,
        square_size_mm=10.0,
        min_views=15,
        rms_threshold_px=0.8,
    )

    assert result.passed_quality_gates is False
    assert result.num_images_used < 15
    assert any("views" in warning.lower() for warning in result.warnings)
