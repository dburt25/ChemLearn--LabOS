"""Marker board specification and generation utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Literal


class MarkerFamily(str, Enum):
    ARUCO_4X4 = "aruco_4x4"
    ARUCO_5X5 = "aruco_5x5"


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
    if not cv2.imwrite(str(out_path), image):
        raise RuntimeError(f"Failed to write board image to {out_path}")
