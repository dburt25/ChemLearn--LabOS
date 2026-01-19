"""Reference frame selection utilities for 3D scans."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Optional, Sequence, Tuple

from scanner.scale_constraints import ScanRegime


class ReferenceFrameSource(str, Enum):
    USER_ANCHOR_POINT = "user_anchor_point"
    BBOX_CENTER = "bbox_center"
    MARKER_FRAME = "marker_frame"
    GEO_ANCHOR = "geo_anchor"
    NONE = "none"


@dataclass(frozen=True)
class ReferenceFrame:
    source: ReferenceFrameSource
    origin_xyz: Optional[Tuple[float, float, float]]
    rotation_quat_wxyz: Optional[Tuple[float, float, float, float]]
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


@dataclass(frozen=True)
class AnchorInputs:
    regime: ScanRegime
    user_origin_xyz: Optional[Tuple[float, float, float]] = None
    user_geo_anchor: Optional[Tuple[float, float, Optional[float]]] = None
    user_timestamp_anchor: Optional[str] = None
    allow_heuristics: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "regime": self.regime.value,
            "user_origin_xyz": self.user_origin_xyz,
            "user_geo_anchor": self.user_geo_anchor,
            "user_timestamp_anchor": self.user_timestamp_anchor,
            "allow_heuristics": self.allow_heuristics,
        }


def default_allow_heuristics(regime: ScanRegime) -> bool:
    if regime is ScanRegime.SMALL_OBJECT:
        return False
    if regime is ScanRegime.AERIAL:
        return True
    return True


def compute_bbox_center(points: Sequence[Sequence[float]]) -> Tuple[float, float, float]:
    if not points:
        raise ValueError("Point cloud is empty; cannot compute bbox center.")
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    for point in points:
        for idx, coord in enumerate(point[:3]):
            mins[idx] = min(mins[idx], coord)
            maxs[idx] = max(maxs[idx], coord)
    return tuple((mins[i] + maxs[i]) / 2.0 for i in range(3))


def translate_points(
    points: Iterable[Sequence[float]],
    origin_xyz: Tuple[float, float, float],
) -> list[Tuple[float, float, float]]:
    translated = []
    ox, oy, oz = origin_xyz
    for point in points:
        translated.append((point[0] - ox, point[1] - oy, point[2] - oz))
    return translated


def select_reference_frame(
    points: Optional[Sequence[Sequence[float]]],
    anchors: AnchorInputs,
    *,
    anchor_mode: str = "auto",
) -> ReferenceFrame:
    notes: list[str] = []
    required_inputs_missing: list[str] = []

    if anchors.user_geo_anchor:
        notes.append("Geospatial anchor recorded; not applied to geometry in v1.")
    if anchors.user_timestamp_anchor:
        notes.append("Timestamp anchor recorded; not applied to geometry in v1.")

    if anchor_mode in {"marker", "geo"}:
        notes.append(f"{anchor_mode} anchoring not implemented; using available fallbacks.")

    if anchors.user_origin_xyz is not None:
        return ReferenceFrame(
            source=ReferenceFrameSource.USER_ANCHOR_POINT,
            origin_xyz=anchors.user_origin_xyz,
            rotation_quat_wxyz=None,
            notes=notes,
            confidence="HIGH",
            required_inputs_missing=required_inputs_missing,
        )

    if anchors.allow_heuristics:
        if points:
            origin_xyz = compute_bbox_center(points)
            if anchors.regime is ScanRegime.AERIAL:
                notes.append("Geospatial anchor not implemented; using heuristic.")
            return ReferenceFrame(
                source=ReferenceFrameSource.BBOX_CENTER,
                origin_xyz=origin_xyz,
                rotation_quat_wxyz=None,
                notes=notes,
                confidence="MED",
                required_inputs_missing=required_inputs_missing,
            )
        required_inputs_missing.append("point_cloud")
        notes.append("Point cloud unavailable for heuristic origin.")
        return ReferenceFrame(
            source=ReferenceFrameSource.NONE,
            origin_xyz=None,
            rotation_quat_wxyz=None,
            notes=notes,
            confidence="LOW",
            required_inputs_missing=required_inputs_missing,
        )

    raise ValueError("No origin anchor available; provide --origin or enable heuristics.")
