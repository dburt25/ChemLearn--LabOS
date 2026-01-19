"""Scanner pipeline skeleton with reference frame anchoring."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Sequence

from scanner.point_cloud_io import read_ply_points, write_ply_points
from scanner.reference_frame import (
    NO_ORIGIN_ERROR,
    AnchorInputs,
    ReferenceFrame,
    ReferenceFrameSource,
    select_reference_frame,
    translate_points,
)
from scanner.scale_constraints import ScanRegime, default_allow_heuristics


def resolve_regime(value: str) -> ScanRegime:
    try:
        return ScanRegime(value)
    except ValueError as exc:
        raise ValueError(f"Unsupported regime: {value}") from exc


def parse_xyz(value: str) -> tuple[float, float, float]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 3:
        raise ValueError("Expected three comma-separated values for origin.")
    return tuple(float(part) for part in parts)  # type: ignore[return-value]


def parse_geo_anchor(value: str) -> tuple[float, float, float | None]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) not in (2, 3):
        raise ValueError("Expected lat,lon[,alt] for geo anchor.")
    lat = float(parts[0])
    lon = float(parts[1])
    alt = float(parts[2]) if len(parts) == 3 else None
    return (lat, lon, alt)


def find_scaled_point_cloud(output_dir: Path) -> tuple[Path | None, str | None]:
    dense_path = output_dir / "dense_scaled.ply"
    if dense_path.exists():
        return dense_path, "dense"
    sparse_path = output_dir / "scene_sparse_scaled.ply"
    if sparse_path.exists():
        return sparse_path, "sparse"
    return None, None


def center_point_cloud_file(
    input_path: Path,
    output_path: Path,
    origin_xyz: tuple[float, float, float],
) -> int:
    points = read_ply_points(input_path)
    centered = translate_points(points, origin_xyz)
    write_ply_points(output_path, centered)
    return len(points)


def apply_anchor_mode(
    anchor_mode: str,
    inputs: AnchorInputs,
    notes: list[str],
) -> AnchorInputs:
    allow_heuristics = inputs.allow_heuristics

    if anchor_mode == "user":
        allow_heuristics = False
    elif anchor_mode == "bbox":
        allow_heuristics = True
    elif anchor_mode == "marker":
        notes.append("Marker anchoring not implemented; falling back to heuristics.")
    elif anchor_mode == "geo":
        notes.append("Geospatial anchor not implemented; falling back to heuristics.")
    elif anchor_mode != "auto":
        raise ValueError(f"Unsupported anchor mode: {anchor_mode}")

    return AnchorInputs(
        regime=inputs.regime,
        user_origin_xyz=inputs.user_origin_xyz,
        user_geo_anchor=inputs.user_geo_anchor,
        user_timestamp_anchor=inputs.user_timestamp_anchor,
        allow_heuristics=allow_heuristics,
    )


def build_reference_frame(
    points: Sequence[tuple[float, float, float]] | None,
    inputs: AnchorInputs,
    anchor_mode: str,
) -> ReferenceFrame:
    notes: list[str] = []
    adjusted_inputs = apply_anchor_mode(anchor_mode, inputs, notes)
    reference_frame = select_reference_frame(points, adjusted_inputs)
    reference_frame.notes.extend(notes)

    if anchor_mode == "marker" and reference_frame.source != ReferenceFrameSource.MARKER_FRAME:
        reference_frame.notes.append("Marker frame not available; using fallback origin.")
    if anchor_mode == "geo" and reference_frame.source != ReferenceFrameSource.GEO_ANCHOR:
        reference_frame.notes.append("Geo anchor not applied; using fallback origin.")

    return reference_frame


def write_reference_frame(output_dir: Path, reference_frame: ReferenceFrame) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "reference_frame.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(reference_frame.to_dict(), handle, indent=2)
    return path


def write_run_record(output_dir: Path, record: dict[str, object]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "run.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)
    return path


def run_pipeline(
    output_dir: Path,
    anchor_inputs: AnchorInputs,
    anchor_mode: str = "auto",
    point_cloud_path: Path | None = None,
    colmap_available: bool | None = None,
) -> dict[str, object]:
    output_dir = output_dir.resolve()

    if colmap_available is None:
        colmap_available = shutil.which("colmap") is not None

    point_cloud_points: Sequence[tuple[float, float, float]] | None = None
    if point_cloud_path and point_cloud_path.exists():
        point_cloud_points = read_ply_points(point_cloud_path)

    reference_frame = build_reference_frame(point_cloud_points, anchor_inputs, anchor_mode)

    run_record: dict[str, object] = {
        "reference_frame": reference_frame.to_dict(),
        "anchor_inputs": anchor_inputs.to_dict(),
        "anchor_mode": anchor_mode,
        "warnings": [],
        "status": "ok",
    }

    if not colmap_available:
        run_record["warnings"].append("COLMAP not available; reconstruction skipped.")
        run_record["status"] = "skipped"

    if reference_frame.origin_xyz is None:
        run_record["status"] = "failed"
        run_record["error"] = NO_ORIGIN_ERROR

    centered_output: Path | None = None
    if reference_frame.origin_xyz is not None:
        cloud_path = point_cloud_path
        cloud_kind = None
        if cloud_path is None:
            cloud_path, cloud_kind = find_scaled_point_cloud(output_dir)
        elif cloud_kind is None:
            cloud_kind = "dense" if "dense" in cloud_path.name else "sparse"

        if cloud_path and cloud_path.exists():
            if cloud_kind == "dense":
                centered_output = output_dir / "dense_scaled_centered.ply"
            else:
                centered_output = output_dir / "scene_sparse_scaled_centered.ply"
            center_point_cloud_file(cloud_path, centered_output, reference_frame.origin_xyz)

    run_record["centered_point_cloud"] = str(centered_output) if centered_output else None

    write_reference_frame(output_dir, reference_frame)
    write_run_record(output_dir, run_record)

    return run_record


def default_anchor_inputs(
    regime: ScanRegime,
    user_origin_xyz: tuple[float, float, float] | None = None,
    user_geo_anchor: tuple[float, float, float | None] | None = None,
    user_timestamp_anchor: str | None = None,
    allow_heuristics: bool | None = None,
) -> AnchorInputs:
    if allow_heuristics is None:
        allow_heuristics = default_allow_heuristics(regime)
    return AnchorInputs(
        regime=regime,
        user_origin_xyz=user_origin_xyz,
        user_geo_anchor=user_geo_anchor,
        user_timestamp_anchor=user_timestamp_anchor,
        allow_heuristics=allow_heuristics,
    )
