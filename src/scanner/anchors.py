"""Anchor subsystem for marker- and geo-based scan alignment."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple



class AnchorType(Enum):
    MARKER_BOARD = "marker_board"
    MARKER_PAIR = "marker_pair"
    GEO_POINT = "geo_point"
    TIME_ANCHOR = "time_anchor"


class MarkerFamily(Enum):
    ARUCO_4X4 = "aruco_4x4"
    ARUCO_5X5 = "aruco_5x5"
    APRILTAG = "apriltag"


class AnchorConfidence(Enum):
    HIGH = "HIGH"
    MED = "MED"
    LOW = "LOW"


class ScanRegime(Enum):
    SMALL_OBJECT = "small_object"
    AERIAL = "aerial"
    OTHER = "other"


@dataclass(slots=True)
class AnchorSpec:
    """User intent for anchor resolution."""

    anchor_type: AnchorType
    regime: ScanRegime
    marker_family: Optional[MarkerFamily] = None
    marker_ids: Optional[list[int]] = None
    marker_size_m: Optional[float] = None
    board_layout: Optional[dict] = None
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None
    geo_alt_m: Optional[float] = None
    time_iso8601: Optional[str] = None


@dataclass(slots=True)
class AnchorResult:
    """Outcome of anchor resolution and application."""

    resolved: bool
    applied: bool
    anchor_type: AnchorType
    scale_factor: Optional[float]
    origin_xyz: Optional[Tuple[float, float, float]]
    rotation_quat_wxyz: Optional[Tuple[float, float, float, float]]
    confidence: AnchorConfidence
    warnings: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)
    failure_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "resolved": self.resolved,
            "applied": self.applied,
            "anchor_type": self.anchor_type.value,
            "scale_factor": self.scale_factor,
            "origin_xyz": self.origin_xyz,
            "rotation_quat_wxyz": self.rotation_quat_wxyz,
            "confidence": self.confidence.value,
            "warnings": list(self.warnings),
            "evidence": dict(self.evidence),
            "failure_reason": self.failure_reason,
        }


def parse_marker_ids(value: Optional[str]) -> Optional[list[int]]:
    if not value:
        return None
    marker_ids: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        marker_ids.append(int(item))
    return marker_ids or None


def _parse_geo_anchor(value: Optional[str]) -> tuple[Optional[float], Optional[float], Optional[float]]:
    if not value:
        return None, None, None
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if len(parts) < 2:
        raise ValueError("geo anchor must include at least lat,lon")
    lat = float(parts[0])
    lon = float(parts[1])
    alt = float(parts[2]) if len(parts) > 2 else None
    return lat, lon, alt


def parse_anchor_spec(
    *,
    anchor: Optional[str],
    regime: ScanRegime,
    marker_family: Optional[str] = None,
    marker_size_m: Optional[float] = None,
    marker_ids: Optional[str] = None,
    board_layout: Optional[dict] = None,
    geo_anchor: Optional[str] = None,
    time_anchor: Optional[str] = None,
) -> Optional[AnchorSpec]:
    """Parse CLI-like options into an AnchorSpec."""

    resolved_anchor = anchor
    if not resolved_anchor and regime == ScanRegime.SMALL_OBJECT and (marker_family or marker_size_m):
        resolved_anchor = "marker"

    if not resolved_anchor:
        return None

    anchor_type = {
        "marker": AnchorType.MARKER_BOARD,
        "geo": AnchorType.GEO_POINT,
        "time": AnchorType.TIME_ANCHOR,
    }.get(resolved_anchor)
    if anchor_type is None:
        raise ValueError(f"Unknown anchor type '{resolved_anchor}'")

    family = None
    if marker_family:
        family = MarkerFamily(marker_family)

    parsed_marker_ids = parse_marker_ids(marker_ids)
    geo_lat, geo_lon, geo_alt = _parse_geo_anchor(geo_anchor)

    return AnchorSpec(
        anchor_type=anchor_type,
        regime=regime,
        marker_family=family,
        marker_ids=parsed_marker_ids,
        marker_size_m=marker_size_m,
        board_layout=board_layout,
        geo_lat=geo_lat,
        geo_lon=geo_lon,
        geo_alt_m=geo_alt,
        time_iso8601=time_anchor,
    )


def resolve_anchors(anchor_spec: AnchorSpec, frames_dir: Path, metadata: dict) -> AnchorResult:
    """Resolve anchors for a scan, returning the outcome."""

    if anchor_spec.anchor_type in {AnchorType.GEO_POINT, AnchorType.TIME_ANCHOR}:
        warnings = ["Geo/time anchors are captured but not applied in v1."]
        evidence = {
            "geo_lat": anchor_spec.geo_lat,
            "geo_lon": anchor_spec.geo_lon,
            "geo_alt_m": anchor_spec.geo_alt_m,
            "time_iso8601": anchor_spec.time_iso8601,
        }
        return AnchorResult(
            resolved=True,
            applied=False,
            anchor_type=anchor_spec.anchor_type,
            scale_factor=None,
            origin_xyz=None,
            rotation_quat_wxyz=None,
            confidence=AnchorConfidence.LOW,
            warnings=warnings,
            evidence=evidence,
            failure_reason=None,
        )

    if anchor_spec.anchor_type not in {AnchorType.MARKER_BOARD, AnchorType.MARKER_PAIR}:
        return AnchorResult(
            resolved=False,
            applied=False,
            anchor_type=anchor_spec.anchor_type,
            scale_factor=None,
            origin_xyz=None,
            rotation_quat_wxyz=None,
            confidence=AnchorConfidence.LOW,
            warnings=["Unsupported anchor type."],
            evidence={},
            failure_reason="unsupported_anchor",
        )

    from scanner.markers import detect_markers

    detection = detect_markers(
        frames_dir=frames_dir,
        marker_family=anchor_spec.marker_family or MarkerFamily.ARUCO_4X4,
        marker_ids=anchor_spec.marker_ids,
        marker_size_m=anchor_spec.marker_size_m,
        metadata=metadata,
        frames_max=metadata.get("marker_frames_max"),
    )
    if not detection.available:
        return AnchorResult(
            resolved=False,
            applied=False,
            anchor_type=anchor_spec.anchor_type,
            scale_factor=None,
            origin_xyz=None,
            rotation_quat_wxyz=None,
            confidence=AnchorConfidence.LOW,
            warnings=detection.warnings,
            evidence=detection.evidence,
            failure_reason=detection.failure_reason or "marker_capability_missing",
        )

    if not detection.detected_ids:
        warnings = list(detection.warnings)
        warnings.append("No markers detected in frames.")
        return AnchorResult(
            resolved=False,
            applied=False,
            anchor_type=anchor_spec.anchor_type,
            scale_factor=None,
            origin_xyz=None,
            rotation_quat_wxyz=None,
            confidence=AnchorConfidence.LOW,
            warnings=warnings,
            evidence=detection.evidence,
            failure_reason="no_markers_detected",
        )

    scale_factor = _infer_scale_factor(detection, metadata)
    warnings = list(detection.warnings)
    confidence = AnchorConfidence.MED
    resolved = scale_factor is not None
    applied = False
    failure_reason = None

    if not scale_factor:
        warnings.append("Marker detections captured but intrinsics/pose data missing for scaling.")
        confidence = AnchorConfidence.LOW
        resolved = False
        failure_reason = "insufficient_intrinsics"

    return AnchorResult(
        resolved=resolved,
        applied=applied,
        anchor_type=anchor_spec.anchor_type,
        scale_factor=scale_factor,
        origin_xyz=None,
        rotation_quat_wxyz=None,
        confidence=confidence,
        warnings=warnings,
        evidence=detection.evidence,
        failure_reason=failure_reason,
    )


def apply_anchor_overrides(
    scale_constraints: dict,
    reference_frame: dict,
    anchor_result: AnchorResult,
) -> tuple[dict, dict]:
    """Apply anchor overrides to scale and reference frame configs."""

    acceptable = anchor_result.confidence in {AnchorConfidence.HIGH, AnchorConfidence.MED}
    if not acceptable or not anchor_result.resolved:
        return scale_constraints, reference_frame

    updated_scale = dict(scale_constraints)
    updated_reference = dict(reference_frame)

    if anchor_result.scale_factor is not None:
        updated_scale["scale_factor"] = anchor_result.scale_factor
        updated_scale["source"] = "anchor"

    if anchor_result.origin_xyz is not None:
        updated_reference["origin_xyz"] = anchor_result.origin_xyz
        updated_reference["source"] = "anchor"

    return updated_scale, updated_reference


def _infer_scale_factor(detection: Any, metadata: dict) -> Optional[float]:
    intrinsics = metadata.get("camera_intrinsics")
    if not intrinsics:
        return None
    if not detection.pose_tvecs_m:
        return None
    reconstruction_distances = metadata.get("reconstruction_camera_distance_units")
    if not reconstruction_distances:
        return None

    ratios: list[float] = []
    for entry in detection.pose_tvecs_m:
        frame_id = entry["frame"]
        distance_m = entry["distance_m"]
        distance_units = reconstruction_distances.get(frame_id)
        if distance_units:
            ratios.append(distance_m / distance_units)

    if not ratios:
        return None
    return sum(ratios) / len(ratios)
