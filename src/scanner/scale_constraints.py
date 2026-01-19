"""Scale constraint policies and estimation helpers for scanner reconstructions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import sqrt
from typing import Iterable, Optional, Tuple


class ScanRegime(Enum):
    SMALL_OBJECT = "small_object"
    ROOM_BUILDING = "room"
    AERIAL = "aerial"


class ScaleSource(Enum):
    USER_DISTANCE_PAIR = "user_distance_pair"
    USER_OBJECT_SIZE = "user_object_size"
    USER_MARKER = "user_marker"
    DEVICE_METADATA_PRIOR = "device_metadata_prior"
    NONE = "none"


@dataclass
class ScalePolicy:
    regime: ScanRegime
    expected_size_m: Tuple[float, float]
    hard_bounds_m: Tuple[float, float]
    allow_autoscale: bool
    require_user_reference: bool

    def to_dict(self) -> dict:
        return {
            "regime": self.regime.value,
            "expected_size_m": list(self.expected_size_m),
            "hard_bounds_m": list(self.hard_bounds_m),
            "allow_autoscale": self.allow_autoscale,
            "require_user_reference": self.require_user_reference,
        }


@dataclass
class ScaleEstimate:
    source: ScaleSource
    scale_factor: Optional[float]
    confidence: str
    notes: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source": self.source.value,
            "scale_factor": self.scale_factor,
            "confidence": self.confidence,
            "notes": list(self.notes),
            "violations": list(self.violations),
        }


class ScaleConstraintError(RuntimeError):
    """Raised when scale constraints are violated and autoscale is not allowed."""


DEFAULT_POLICIES = {
    ScanRegime.SMALL_OBJECT: {
        "expected_size_m": (0.05, 1.0),
        "hard_bounds_m": (0.005, 2.0),
        "allow_autoscale": False,
        "require_user_reference": True,
    },
    ScanRegime.ROOM_BUILDING: {
        "expected_size_m": (1.0, 30.0),
        "hard_bounds_m": (0.25, 100.0),
        "allow_autoscale": True,
        "require_user_reference": False,
    },
    ScanRegime.AERIAL: {
        "expected_size_m": (30.0, 5000.0),
        "hard_bounds_m": (10.0, 20000.0),
        "allow_autoscale": True,
        "require_user_reference": False,
    },
}


def build_scale_policy(
    regime: ScanRegime,
    expected_size_m: Optional[Tuple[Optional[float], Optional[float]]] = None,
    hard_bounds_m: Optional[Tuple[Optional[float], Optional[float]]] = None,
    allow_autoscale: Optional[bool] = None,
    allow_weak_scale: bool = False,
) -> ScalePolicy:
    defaults = DEFAULT_POLICIES[regime]
    expected_min, expected_max = _resolve_range("expected_size_m", expected_size_m, defaults)
    hard_min, hard_max = _resolve_range("hard_bounds_m", hard_bounds_m, defaults)

    resolved_autoscale = defaults["allow_autoscale"] if allow_autoscale is None else allow_autoscale
    require_reference = defaults["require_user_reference"]
    if regime == ScanRegime.SMALL_OBJECT and allow_weak_scale:
        require_reference = False

    return ScalePolicy(
        regime=regime,
        expected_size_m=(expected_min, expected_max),
        hard_bounds_m=(hard_min, hard_max),
        allow_autoscale=resolved_autoscale,
        require_user_reference=require_reference,
    )


def _resolve_range(
    label: str,
    override: Optional[Tuple[Optional[float], Optional[float]]],
    defaults: dict,
) -> Tuple[float, float]:
    if override is None:
        return defaults[label]
    if override[0] is None or override[1] is None:
        raise ValueError(f"{label} requires both min and max values when overridden")
    min_value, max_value = float(override[0]), float(override[1])
    if min_value <= 0 or max_value <= 0:
        raise ValueError(f"{label} values must be positive")
    if min_value >= max_value:
        raise ValueError(f"{label} min must be < max")
    return min_value, max_value


def validate_scene_extent(points: Iterable[Tuple[float, float, float]]) -> float:
    points_list = list(points)
    if not points_list:
        return 0.0
    min_x = min(point[0] for point in points_list)
    min_y = min(point[1] for point in points_list)
    min_z = min(point[2] for point in points_list)
    max_x = max(point[0] for point in points_list)
    max_y = max(point[1] for point in points_list)
    max_z = max(point[2] for point in points_list)
    dx = max_x - min_x
    dy = max_y - min_y
    dz = max_z - min_z
    return sqrt(dx * dx + dy * dy + dz * dz)


def determine_scale_estimate(
    policy: ScalePolicy,
    ref_distance_m: Optional[float] = None,
    ref_pair: Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = None,
    ref_scale_factor: Optional[float] = None,
    extent_m: Optional[float] = None,
) -> ScaleEstimate:
    notes: list[str] = []
    violations: list[str] = []
    scale_factor: Optional[float] = None
    source = ScaleSource.NONE
    confidence = "LOW"

    if ref_pair and ref_distance_m is None:
        violations.append("REF_DISTANCE_REQUIRED_FOR_PAIR")
    if ref_distance_m is not None and not ref_pair:
        violations.append("REF_PAIR_REQUIRED_FOR_DISTANCE")

    if ref_pair and ref_distance_m is not None:
        model_distance = _distance_between(ref_pair[0], ref_pair[1])
        if model_distance <= 0:
            violations.append("REF_PAIR_DISTANCE_INVALID")
        elif ref_distance_m <= 0:
            violations.append("REF_DISTANCE_INVALID")
        else:
            scale_factor = ref_distance_m / model_distance
            source = ScaleSource.USER_DISTANCE_PAIR
            confidence = "HIGH"
            notes.append("USER_DISTANCE_REFERENCE")

    if ref_scale_factor is not None:
        if scale_factor is not None:
            notes.append("REF_SCALE_FACTOR_IGNORED_DUE_TO_DISTANCE_PAIR")
        elif ref_scale_factor <= 0:
            violations.append("REF_SCALE_FACTOR_INVALID")
        else:
            scale_factor = ref_scale_factor
            source = ScaleSource.USER_OBJECT_SIZE
            confidence = "MED"
            notes.append("WARNING: USER_SCALE_FACTOR_OVERRIDE")

    if scale_factor is None:
        notes.append("NO_USER_REFERENCE")

    if policy.require_user_reference and scale_factor is None:
        violations.append("USER_REFERENCE_REQUIRED")

    if extent_m is not None and extent_m > 0:
        scaled_extent = extent_m * (scale_factor or 1.0)
        if scaled_extent < policy.hard_bounds_m[0] or scaled_extent > policy.hard_bounds_m[1]:
            if policy.allow_autoscale:
                autoscale_factor = _autoscale_factor(scaled_extent, policy.expected_size_m)
                if autoscale_factor != 1.0:
                    scale_factor = (scale_factor or 1.0) * autoscale_factor
                    if source == ScaleSource.NONE:
                        source = ScaleSource.DEVICE_METADATA_PRIOR
                    notes.append("AUTOSCALE_APPLIED")
                    confidence = "LOW"
                violations.append("HARD_BOUNDS_VIOLATION_AUTOSCALED")
            else:
                raise ScaleConstraintError(
                    "Scale is implausible for the selected regime; provide a user reference or "
                    "select a more appropriate scan regime."
                )

    return ScaleEstimate(
        source=source,
        scale_factor=scale_factor,
        confidence=confidence,
        notes=notes,
        violations=violations,
    )


def _distance_between(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _autoscale_factor(extent_m: float, expected_size_m: Tuple[float, float]) -> float:
    if extent_m <= 0:
        return 1.0
    if extent_m < expected_size_m[0]:
        return expected_size_m[0] / extent_m
    if extent_m > expected_size_m[1]:
        return expected_size_m[1] / extent_m
    return 1.0
