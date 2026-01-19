"""Anchor data models and enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ScanRegime(str, Enum):
    SMALL_OBJECT = "small_object"
    AERIAL = "aerial"


class AnchorType(str, Enum):
    MARKER_BOARD = "marker_board"
    MARKER_PAIR = "marker_pair"
    GEO_POINT = "geo_point"
    TIME_ANCHOR = "time_anchor"


class MarkerFamily(str, Enum):
    ARUCO_4X4 = "aruco_4x4"
    ARUCO_5X5 = "aruco_5x5"
    APRILTAG = "apriltag"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MED = "MED"
    LOW = "LOW"


@dataclass(frozen=True)
class AnchorSpec:
    anchor_type: AnchorType
    regime: ScanRegime
    marker_family: MarkerFamily | None = None
    marker_ids: list[int] | None = None
    marker_size_m: float | None = None
    board_layout: dict | None = None
    geo_lat: float | None = None
    geo_lon: float | None = None
    geo_alt_m: float | None = None
    time_iso8601: str | None = None


@dataclass
class AnchorResult:
    resolved: bool
    applied: bool
    anchor_type: AnchorType
    scale_factor: float | None = None
    origin_xyz: tuple[float, float, float] | None = None
    rotation_quat_wxyz: tuple[float, float, float, float] | None = None
    confidence: Confidence = Confidence.LOW
    warnings: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)
    failure_reason: str | None = None
