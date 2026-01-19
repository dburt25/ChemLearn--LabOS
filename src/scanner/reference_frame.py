"""Reference frame selection and centering utilities."""
"""Reference frame selection and origin anchoring helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Optional, Sequence, Tuple


class ScanRegime(str, Enum):
    SMALL_OBJECT = "small_object"
    ROOM_BUILDING = "room_building"
    AERIAL = "aerial"


class ReferenceFrameSource(str, Enum):
    USER_DEFINED_ORIGIN = "user_defined_origin"
    BBOX_CENTER = "bbox_center"
    MARKER_ANCHOR = "marker_anchor"
from typing import Iterable, Sequence

from scanner.scale_constraints import ScanRegime, default_allow_heuristics

NO_ORIGIN_ERROR = "No origin anchor available; provide --origin or enable heuristics."


class ReferenceFrameSource(str, Enum):
    USER_ANCHOR_POINT = "user_anchor_point"
    BBOX_CENTER = "bbox_center"
    MARKER_FRAME = "marker_frame"
    GEO_ANCHOR = "geo_anchor"
    NONE = "none"


class ReferenceFrameConfidence(str, Enum):
    HIGH = "high"
    MED = "med"
    LOW = "low"


@dataclass(frozen=True)
class ReferenceFramePolicy:
    regime: ScanRegime
    allow_heuristic_center: bool
    require_explicit_origin: bool

    @classmethod
    def for_regime(
        cls,
        regime: ScanRegime,
        *,
        allow_heuristic_center: Optional[bool] = None,
        require_explicit_origin: Optional[bool] = None,
    ) -> "ReferenceFramePolicy":
        if regime == ScanRegime.SMALL_OBJECT:
            default_require = True
            default_allow = False
        else:
            default_require = False
            default_allow = True
        return cls(
            regime=regime,
            allow_heuristic_center=default_allow if allow_heuristic_center is None else allow_heuristic_center,
            require_explicit_origin=default_require
            if require_explicit_origin is None
            else require_explicit_origin,
        )


@dataclass(frozen=True)
class ReferenceFrameResult:
    source: ReferenceFrameSource
    origin_xyz: Optional[Tuple[float, float, float]]
    confidence: ReferenceFrameConfidence
    warnings: list[str] = field(default_factory=list)
    missing_requirements: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReferenceFrameUserInputs:
    origin: Optional[Tuple[float, float, float]] = None
    center_mode: str = "auto"
    marker_anchor: Optional[str] = None
    geo_anchor: Optional[Tuple[float, float, Optional[float]]] = None
    time_anchor: Optional[str] = None


def compute_bbox_center(points: Sequence[Tuple[float, float, float]]) -> Tuple[float, float, float]:
    if not points:
        raise ValueError("Cannot compute bbox center without points.")
    xs, ys, zs = zip(*points)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    return ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0, (min_z + max_z) / 2.0)


def translate_points(
    points: Iterable[Tuple[float, float, float]],
    origin: Tuple[float, float, float],
) -> list[Tuple[float, float, float]]:
    ox, oy, oz = origin
    return [(x - ox, y - oy, z - oz) for x, y, z in points]


def resolve_reference_frame(
    points: Optional[Sequence[Tuple[float, float, float]]],
    policy: ReferenceFramePolicy,
    user_inputs: ReferenceFrameUserInputs,
) -> ReferenceFrameResult:
    warnings: list[str] = []
    missing_requirements: list[str] = []

    center_mode = user_inputs.center_mode
    if center_mode not in {"auto", "user", "bbox", "marker", "geo"}:
        raise ValueError(f"Unsupported center mode: {center_mode}")

    if center_mode == "marker":
        warnings.append("anchor type not implemented; not applied")
        return ReferenceFrameResult(
            source=ReferenceFrameSource.MARKER_ANCHOR,
            origin_xyz=None,
            confidence=ReferenceFrameConfidence.LOW,
            warnings=warnings,
            missing_requirements=missing_requirements,
        )

    if center_mode == "geo":
        warnings.append("anchor type not implemented; not applied")
        return ReferenceFrameResult(
            source=ReferenceFrameSource.GEO_ANCHOR,
            origin_xyz=None,
            confidence=ReferenceFrameConfidence.LOW,
            warnings=warnings,
            missing_requirements=missing_requirements,
        )

    if user_inputs.marker_anchor or user_inputs.geo_anchor or user_inputs.time_anchor:
        warnings.append("anchor type not implemented; not applied")

    if user_inputs.origin is not None and center_mode in {"auto", "user"}:
        return ReferenceFrameResult(
            source=ReferenceFrameSource.USER_DEFINED_ORIGIN,
            origin_xyz=user_inputs.origin,
            confidence=ReferenceFrameConfidence.HIGH,
            warnings=warnings,
            missing_requirements=missing_requirements,
        )

    if center_mode == "user" and user_inputs.origin is None:
        missing_requirements.append("origin required for user center mode")
        raise ValueError("Center mode 'user' requires an explicit --origin x,y,z value.")

    if center_mode in {"auto", "bbox"} and policy.allow_heuristic_center:
        if points:
            origin = compute_bbox_center(points)
            confidence = (
                ReferenceFrameConfidence.MED
                if policy.regime == ScanRegime.ROOM_BUILDING
                else ReferenceFrameConfidence.LOW
            )
            if policy.regime == ScanRegime.AERIAL:
                warnings.append("heuristic center used for aerial regime; anchor support is future work")
            return ReferenceFrameResult(
                source=ReferenceFrameSource.BBOX_CENTER,
                origin_xyz=origin,
                confidence=confidence,
                warnings=warnings,
                missing_requirements=missing_requirements,
            )

    missing_requirements.append(
        "explicit origin required; provide --origin x,y,z or enable heuristic center"
    )
    if policy.require_explicit_origin:
        raise ValueError(
            "Origin is required for this scan regime. "
            "Provide --origin x,y,z or use --center-mode bbox with --allow-heuristic-center."
        )

    return ReferenceFrameResult(
        source=ReferenceFrameSource.NONE,
        origin_xyz=None,
        confidence=ReferenceFrameConfidence.LOW,
        warnings=warnings,
        missing_requirements=missing_requirements,
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
