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
"""Marker board specification and generation helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Literal

import importlib.util

_cv2_spec = importlib.util.find_spec("cv2")
if _cv2_spec:
    import cv2


class MarkerFamily(Enum):
    ARUCO_4X4 = "aruco_4x4"
    ARUCO_5X5 = "aruco_5x5"

    @classmethod
    def from_string(cls, value: str) -> "MarkerFamily":
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized or member.name.lower() == normalized:
                return member
        raise ValueError(f"Unsupported marker family: {value}")


@dataclass(frozen=True)
class BoardSpec:
    """Defines a planar ArUco marker board for anchoring."""

    family: BoardFamily
    family: MarkerFamily
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
    origin_definition: Literal["board_center"] = "board_center"
    board_id: str = ""

    def __post_init__(self) -> None:
        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("rows and cols must be positive")
        if self.marker_size_m <= 0:
            raise ValueError("marker_size_m must be positive")
        if self.marker_spacing_m < 0:
            raise ValueError("marker_spacing_m cannot be negative")
        if self.origin_definition != "board_center":
            raise ValueError("origin_definition must be 'board_center'")
        if not self.board_id:
            object.__setattr__(self, "board_id", _generate_board_id(self))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family": self.family.value,
            "rows": self.rows,
            "cols": self.cols,
            "marker_size_m": self.marker_size_m,
            "marker_spacing_m": self.marker_spacing_m,
            "origin_definition": self.origin_definition,
            "board_id": self.board_id,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "BoardSpec":
        return cls(
            family=MarkerFamily.from_string(str(payload["family"])),
            rows=int(payload["rows"]),
            cols=int(payload["cols"]),
            marker_size_m=float(payload["marker_size_m"]),
            marker_spacing_m=float(payload["marker_spacing_m"]),
            origin_definition=str(payload.get("origin_definition", "board_center")),
            board_id=str(payload.get("board_id", "")),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "BoardSpec":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _generate_board_id(spec: BoardSpec) -> str:
    identity = (
        f"{spec.family.value}|{spec.rows}|{spec.cols}|"
        f"{spec.marker_size_m:.6f}|{spec.marker_spacing_m:.6f}|{spec.origin_definition}"
    )
    digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:12]
    return f"board-{digest}"


def _get_aruco_dictionary(family: MarkerFamily):
    if not _cv2_spec:
        return None
    if not hasattr(cv2, "aruco"):
        return None
    if family == MarkerFamily.ARUCO_4X4:
        return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_50)


def _create_grid_board(board_spec: BoardSpec):
    if not _cv2_spec or not hasattr(cv2, "aruco"):
        return None
    dictionary = _get_aruco_dictionary(board_spec.family)
    if dictionary is None:
        return None
    if hasattr(cv2.aruco, "GridBoard_create"):
        return cv2.aruco.GridBoard_create(
            board_spec.cols,
            board_spec.rows,
            board_spec.marker_size_m,
            board_spec.marker_spacing_m,
            dictionary,
        )
    return cv2.aruco.GridBoard.create(
        board_spec.cols,
        board_spec.rows,
        board_spec.marker_size_m,
        board_spec.marker_spacing_m,
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
def generate_board_png(board_spec: BoardSpec, out_path: str | Path, dpi: int = 300) -> None:
    if not _cv2_spec or not hasattr(cv2, "aruco"):
        raise RuntimeError(
            "cv2.aruco is required to generate board images. Install opencv-contrib-python."
        )
    board = _create_grid_board(board_spec)
    if board is None:
        raise RuntimeError("Unable to create aruco board for requested specification.")

    board_width_m = board_spec.cols * board_spec.marker_size_m + (
        board_spec.cols - 1
    ) * board_spec.marker_spacing_m
    board_height_m = board_spec.rows * board_spec.marker_size_m + (
        board_spec.rows - 1
    ) * board_spec.marker_spacing_m
    pixels_per_meter = dpi / 0.0254
    width_px = max(1, int(round(board_width_m * pixels_per_meter)))
    height_px = max(1, int(round(board_height_m * pixels_per_meter)))

    image = cv2.aruco.drawPlanarBoard(board, (width_px, height_px), marginSize=0, borderBits=1)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(out_path), image):
        raise RuntimeError(f"Failed to write board image to {out_path}")
