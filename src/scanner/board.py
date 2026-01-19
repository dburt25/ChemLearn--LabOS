"""Marker board specification and generation utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Literal


class MarkerFamily(str, Enum):
    ARUCO_4X4 = "aruco_4x4"
    ARUCO_5X5 = "aruco_5x5"

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
    family: MarkerFamily
    rows: int
    cols: int
    marker_size_m: float
    marker_spacing_m: float
    origin_definition: Literal["board_center"]
    board_id: str

    def to_dict(self) -> dict:
        data = asdict(self)
        data["family"] = self.family.value
        return data

    @classmethod
    def from_dict(cls, payload: dict) -> "BoardSpec":
        return cls(
            family=MarkerFamily(payload["family"]),
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
            origin_definition=payload.get("origin_definition", "board_center"),
            board_id=payload.get("board_id", "board-v1"),
        )

    @property
    def board_width_m(self) -> float:
        return self.cols * self.marker_size_m + (self.cols - 1) * self.marker_spacing_m

    @property
    def board_height_m(self) -> float:
        return self.rows * self.marker_size_m + (self.rows - 1) * self.marker_spacing_m

    @property
    def board_center_m(self) -> tuple[float, float, float]:
        return (self.board_width_m / 2.0, self.board_height_m / 2.0, 0.0)


def _require_aruco():
    try:
        import cv2  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "OpenCV is required for board generation. Install opencv-contrib-python."
        ) from exc

    if not hasattr(cv2, "aruco"):
        raise RuntimeError(
            "OpenCV aruco module is unavailable. Install opencv-contrib-python to generate boards."
        )
    return cv2


def _aruco_dictionary(cv2, family: MarkerFamily):
    if family == MarkerFamily.ARUCO_4X4:
        return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    if family == MarkerFamily.ARUCO_5X5:
        return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_50)
    raise ValueError(f"Unsupported marker family: {family}")


def _build_board(cv2, spec: BoardSpec):
    dictionary = _aruco_dictionary(cv2, spec.family)
    return cv2.aruco.GridBoard_create(
        spec.cols,
        spec.rows,
        spec.marker_size_m,
        spec.marker_spacing_m,
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


def generate_board_png(board_spec: BoardSpec, out_path: str | Path, dpi: int = 300) -> None:
    """Generate a printable PNG for the requested board specification."""

    cv2 = _require_aruco()
    board = _build_board(cv2, board_spec)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    inches_per_meter = 39.3701
    width_px = int(round(board_spec.board_width_m * inches_per_meter * dpi))
    height_px = int(round(board_spec.board_height_m * inches_per_meter * dpi))
    if width_px <= 0 or height_px <= 0:
        raise ValueError("Board dimensions must be positive.")

    image = board.draw((width_px, height_px))
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
