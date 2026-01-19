"""Anchor resolution for scanner workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from scanner import markers
from scanner.anchor_types import AnchorResult, AnchorSpec, AnchorType, Confidence, MarkerFamily, ScanRegime


def parse_marker_ids(value: str | None) -> list[int] | None:
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        return None
    return [int(item) for item in items]


def parse_geo_anchor(value: str | None) -> tuple[float, float, float | None] | None:
    if not value:
        return None
    parts = [item.strip() for item in value.split(",") if item.strip()]
    if len(parts) < 2:
        return None
    lat = float(parts[0])
    lon = float(parts[1])
    alt = float(parts[2]) if len(parts) > 2 else None
    return lat, lon, alt


def parse_anchor_spec(
    *,
    anchor: str | None,
    regime: ScanRegime,
    marker_family: str | None,
    marker_ids: str | None,
    marker_size_m: float | None,
    geo_anchor: str | None,
    time_anchor: str | None,
) -> AnchorSpec | None:
    if not anchor:
        return None
    anchor_key = anchor.lower()
    if anchor_key == "marker":
        family = MarkerFamily(marker_family) if marker_family else None
        return AnchorSpec(
            anchor_type=AnchorType.MARKER_BOARD,
            regime=regime,
            marker_family=family,
            marker_ids=parse_marker_ids(marker_ids),
            marker_size_m=marker_size_m,
        )
    if anchor_key == "geo":
        parsed = parse_geo_anchor(geo_anchor)
        if not parsed:
            return AnchorSpec(anchor_type=AnchorType.GEO_POINT, regime=regime)
        lat, lon, alt = parsed
        return AnchorSpec(
            anchor_type=AnchorType.GEO_POINT,
            regime=regime,
            geo_lat=lat,
            geo_lon=lon,
            geo_alt_m=alt,
            time_iso8601=time_anchor,
        )
    if anchor_key == "time":
        return AnchorSpec(
            anchor_type=AnchorType.TIME_ANCHOR,
            regime=regime,
            time_iso8601=time_anchor,
        )
    raise ValueError(f"Unsupported anchor type: {anchor}")


def _build_anchor_result(
    *,
    anchor_type: AnchorType,
    resolved: bool,
    applied: bool,
    confidence: Confidence,
    warnings: Iterable[str] = (),
    evidence: dict | None = None,
    failure_reason: str | None = None,
    scale_factor: float | None = None,
    origin_xyz: tuple[float, float, float] | None = None,
    rotation_quat_wxyz: tuple[float, float, float, float] | None = None,
) -> AnchorResult:
    return AnchorResult(
        resolved=resolved,
        applied=applied,
        anchor_type=anchor_type,
        confidence=confidence,
        warnings=list(warnings),
        evidence=evidence or {},
        failure_reason=failure_reason,
        scale_factor=scale_factor,
        origin_xyz=origin_xyz,
        rotation_quat_wxyz=rotation_quat_wxyz,
    )


def resolve_anchors(
    anchor_spec: AnchorSpec,
    frames_dir: str | Path,
    metadata: dict[str, Any] | None,
    *,
    marker_frames_max: int | None = None,
) -> AnchorResult:
    metadata = metadata or {}
    if anchor_spec.anchor_type in (AnchorType.MARKER_BOARD, AnchorType.MARKER_PAIR):
        result = markers.resolve_marker_anchor(
            anchor_spec=anchor_spec,
            frames_dir=Path(frames_dir),
            metadata=metadata,
            marker_frames_max=marker_frames_max,
        )
        return result

    if anchor_spec.anchor_type == AnchorType.GEO_POINT:
        warnings: list[str] = [
            "Geo anchors are recorded only; georegistration is not applied in v1.",
        ]
        if anchor_spec.geo_lat is None or anchor_spec.geo_lon is None:
            return _build_anchor_result(
                anchor_type=anchor_spec.anchor_type,
                resolved=False,
                applied=False,
                confidence=Confidence.LOW,
                warnings=warnings,
                failure_reason="geo_anchor_missing",
            )
        evidence = {
            "geo": {
                "lat": anchor_spec.geo_lat,
                "lon": anchor_spec.geo_lon,
                "alt_m": anchor_spec.geo_alt_m,
            },
            "time_iso8601": anchor_spec.time_iso8601,
        }
        return _build_anchor_result(
            anchor_type=anchor_spec.anchor_type,
            resolved=True,
            applied=False,
            confidence=Confidence.LOW,
            warnings=warnings,
            evidence=evidence,
        )

    if anchor_spec.anchor_type == AnchorType.TIME_ANCHOR:
        warnings = ["Time anchors are recorded only; no temporal alignment applied in v1."]
        if not anchor_spec.time_iso8601:
            return _build_anchor_result(
                anchor_type=anchor_spec.anchor_type,
                resolved=False,
                applied=False,
                confidence=Confidence.LOW,
                warnings=warnings,
                failure_reason="time_anchor_missing",
            )
        return _build_anchor_result(
            anchor_type=anchor_spec.anchor_type,
            resolved=True,
            applied=False,
            confidence=Confidence.LOW,
            warnings=warnings,
            evidence={"time_iso8601": anchor_spec.time_iso8601},
        )

    return _build_anchor_result(
        anchor_type=anchor_spec.anchor_type,
        resolved=False,
        applied=False,
        confidence=Confidence.LOW,
        warnings=["Anchor type not implemented."],
        failure_reason="anchor_type_not_implemented",
    )
