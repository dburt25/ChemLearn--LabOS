"""Reference frame selection and origin anchoring helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Sequence

from scanner.scale_constraints import ScanRegime, default_allow_heuristics

NO_ORIGIN_ERROR = "No origin anchor available; provide --origin or enable heuristics."


class ReferenceFrameSource(str, Enum):
    USER_ANCHOR_POINT = "user_anchor_point"
    BBOX_CENTER = "bbox_center"
    MARKER_FRAME = "marker_frame"
    GEO_ANCHOR = "geo_anchor"
    NONE = "none"


@dataclass
class ReferenceFrame:
    source: ReferenceFrameSource
    origin_xyz: tuple[float, float, float] | None
    rotation_quat_wxyz: tuple[float, float, float, float] | None
    notes: list[str] = field(default_factory=list)
    confidence: str = "LOW"
    required_inputs_missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source.value,
            "origin_xyz": self.origin_xyz,
            "rotation_quat_wxyz": self.rotation_quat_wxyz,
            "notes": list(self.notes),
            "confidence": self.confidence,
            "required_inputs_missing": list(self.required_inputs_missing),
        }


@dataclass
class AnchorInputs:
    regime: ScanRegime
    user_origin_xyz: tuple[float, float, float] | None = None
    user_geo_anchor: tuple[float, float, float | None] | None = None
    user_timestamp_anchor: str | None = None
    allow_heuristics: bool | None = None

    def resolved_allow_heuristics(self) -> bool:
        if self.allow_heuristics is None:
            return default_allow_heuristics(self.regime)
        return self.allow_heuristics

    def to_dict(self) -> dict[str, object]:
        return {
            "regime": self.regime.value,
            "user_origin_xyz": self.user_origin_xyz,
            "user_geo_anchor": self.user_geo_anchor,
            "user_timestamp_anchor": self.user_timestamp_anchor,
            "allow_heuristics": self.resolved_allow_heuristics(),
        }


def compute_bbox_center(points: Sequence[tuple[float, float, float]]) -> tuple[float, float, float]:
    if not points:
        raise ValueError("Point cloud is empty; cannot compute bbox center.")
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    return (
        (min(xs) + max(xs)) / 2.0,
        (min(ys) + max(ys)) / 2.0,
        (min(zs) + max(zs)) / 2.0,
    )


def translate_points(
    points: Iterable[tuple[float, float, float]],
    origin_xyz: tuple[float, float, float],
) -> list[tuple[float, float, float]]:
    ox, oy, oz = origin_xyz
    return [(x - ox, y - oy, z - oz) for x, y, z in points]


def select_reference_frame(
    points: Sequence[tuple[float, float, float]] | None,
    inputs: AnchorInputs,
) -> ReferenceFrame:
    notes: list[str] = []
    required_inputs_missing: list[str] = []
    origin_xyz: tuple[float, float, float] | None = None
    source = ReferenceFrameSource.NONE
    confidence = "LOW"

    if inputs.user_geo_anchor:
        notes.append("Geospatial anchor recorded but not applied to geometry in v1.")
    if inputs.user_timestamp_anchor:
        notes.append("Timestamp anchor recorded but not applied to geometry in v1.")

    if inputs.user_origin_xyz is not None:
        origin_xyz = inputs.user_origin_xyz
        source = ReferenceFrameSource.USER_ANCHOR_POINT
        confidence = "HIGH"
        return ReferenceFrame(
            source=source,
            origin_xyz=origin_xyz,
            rotation_quat_wxyz=None,
            notes=notes,
            confidence=confidence,
            required_inputs_missing=required_inputs_missing,
        )

    allow_heuristics = inputs.resolved_allow_heuristics()
    if allow_heuristics and points:
        origin_xyz = compute_bbox_center(points)
        source = ReferenceFrameSource.BBOX_CENTER
        if inputs.regime == ScanRegime.ROOM_BUILDING:
            confidence = "MED"
        else:
            confidence = "LOW"
        if inputs.regime == ScanRegime.AERIAL:
            notes.append("Geospatial anchor not implemented; using heuristic.")
    else:
        required_inputs_missing.append("origin")
        notes.append(NO_ORIGIN_ERROR)

    return ReferenceFrame(
        source=source,
        origin_xyz=origin_xyz,
        rotation_quat_wxyz=None,
        notes=notes,
        confidence=confidence,
        required_inputs_missing=required_inputs_missing,
    )
