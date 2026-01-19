"""Reference frame selection and centering utilities."""

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
    )
