"""Marker board specifications and rendering utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

try:
    import cv2
except ImportError:  # pragma: no cover - optional dependency
    cv2 = None

BoardFamily = Literal["aruco_4x4", "aruco_5x5"]


@dataclass(frozen=True)
class BoardSpec:
    """Defines a planar ArUco marker board for anchoring."""

    family: BoardFamily
    rows: int
    cols: int
    marker_size_m: float
    marker_spacing_m: float
    origin_definition: str = "board_center"

    def __post_init__(self) -> None:
        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("Board rows and cols must be positive")
        if self.marker_size_m <= 0 or self.marker_spacing_m < 0:
            raise ValueError("Marker size must be positive and spacing non-negative")
        if self.origin_definition != "board_center":
            raise ValueError("Only board_center origin_definition is supported")
        if self.family not in ("aruco_4x4", "aruco_5x5"):
            raise ValueError("Unsupported board family")


def _aruco_dictionary(family: BoardFamily):
    if cv2 is None:  # pragma: no cover - optional dependency
        raise RuntimeError("OpenCV is required to build ArUco boards")
    if not hasattr(cv2, "aruco"):
        raise RuntimeError("OpenCV ArUco module not available")
    if family == "aruco_4x4":
        return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_100)


def create_board(spec: BoardSpec):
    if cv2 is None:  # pragma: no cover - optional dependency
        raise RuntimeError("OpenCV is required to build ArUco boards")
    dictionary = _aruco_dictionary(spec.family)
    return cv2.aruco.GridBoard_create(
        spec.cols,
        spec.rows,
        spec.marker_size_m,
        spec.marker_spacing_m,
        dictionary,
    )


def generate_board_image(
    spec: BoardSpec,
    output_path: Path | str,
    *,
    pixels_per_meter: int = 1000,
) -> Path:
    """
    Generate a PNG image of the board for printing.

    The printed scale is determined by pixels_per_meter (e.g., 1000 px == 1 meter).
    """

    if cv2 is None:  # pragma: no cover - optional dependency
        raise RuntimeError("OpenCV is required to render ArUco boards")
    board = create_board(spec)

    board_width_m = spec.cols * spec.marker_size_m + (spec.cols - 1) * spec.marker_spacing_m
    board_height_m = spec.rows * spec.marker_size_m + (spec.rows - 1) * spec.marker_spacing_m
    width_px = max(1, int(round(board_width_m * pixels_per_meter)))
    height_px = max(1, int(round(board_height_m * pixels_per_meter)))

    image = board.draw((width_px, height_px))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), image):
        raise RuntimeError(f"Failed to write board image to {output}")
    return output
