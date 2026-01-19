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
"""Scanner pipeline helpers."""

from __future__ import annotations

from pathlib import Path


def ensure_intrinsics_for_small_object(
    *,
    regime: str,
    anchor: str,
    intrinsics_path: str | None,
) -> None:
    """Ensure intrinsics exist for SMALL_OBJECT + marker_board workflows."""

    if regime != "SMALL_OBJECT" or anchor != "marker_board":
        return

    if not intrinsics_path or not Path(intrinsics_path).exists():
        raise ValueError(
            "Run scanner calibrate chessboard/charuco --input <video_or_dir> --out camera.json to generate camera.json"
        )
"""Simple scanning pipeline with marker-board anchoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from scanner.anchors import FrameData, resolve_marker_board_anchor, write_anchor_artifacts
from scanner.board import BoardSpec
from scanner.intrinsics import Intrinsics, load_intrinsics_json, parse_intrinsics_string
from scanner.quality_gates import QualityGateConfig


SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}


def _load_cv2():
    try:
        import cv2  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - env dependent
        raise RuntimeError("OpenCV is required to load frames.") from exc
    return cv2


def load_frames_from_dir(frames_dir: str | Path) -> list[FrameData]:
    frames_path = Path(frames_dir)
    if not frames_path.exists():
        raise FileNotFoundError(f"Frames directory not found: {frames_path}")
    cv2 = _load_cv2()
    frames: list[FrameData] = []
    for index, path in enumerate(sorted(frames_path.iterdir())):
        if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            continue
        image = cv2.imread(str(path))
        frames.append(FrameData(index=index, image=image, timestamp=None))
    return frames


def load_board_spec(path: Optional[str], overrides: dict) -> Optional[BoardSpec]:
    if path:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return BoardSpec.from_dict(payload)
    if overrides:
        return BoardSpec.from_dict(overrides)
    return None


def load_intrinsics(path: Optional[str], intrinsics_value: Optional[str], dist_value: Optional[str]) -> Optional[Intrinsics]:
    if path:
        return load_intrinsics_json(path)
    if intrinsics_value:
        return parse_intrinsics_string(intrinsics_value, dist_value)
    return None


def run_pipeline(
    frames_dir: str,
    output_dir: str,
    anchor_type: str,
    board_spec_path: Optional[str],
    board_overrides: dict,
    intrinsics_path: Optional[str],
    intrinsics_value: Optional[str],
    dist_value: Optional[str],
    gate_config: QualityGateConfig,
    frame_step: int,
) -> None:
    frames = load_frames_from_dir(frames_dir)
    board_spec = load_board_spec(board_spec_path, board_overrides)
    intrinsics = load_intrinsics(intrinsics_path, intrinsics_value, dist_value)

    if anchor_type == "marker_board":
        anchor_result, poses = resolve_marker_board_anchor(
            frames,
            board_spec,
            intrinsics,
            gate_config,
            frame_step=frame_step,
        )
    else:
        raise ValueError(f"Unsupported anchor type: {anchor_type}")

    write_anchor_artifacts(output_dir, anchor_result, poses)
"""Scanner pipeline entrypoints."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from scanner.anchors import AnchorResult, AnchorType, resolve_marker_board_anchor
from scanner.board import BoardSpec
from scanner.intrinsics import Intrinsics
from scanner.quality_gates import QualityGateConfig

_cv2_spec = importlib.util.find_spec("cv2")
if _cv2_spec:
    import cv2


@dataclass(frozen=True)
class PipelineConfig:
    anchor_type: AnchorType
    board_spec: BoardSpec
    intrinsics: Optional[Intrinsics]
    quality_config: QualityGateConfig
    anchor_frame_step: int = 1
    frames_dir: Optional[Path] = None
    output_dir: Path = Path("out")


def _load_frames(frames_dir: Path) -> list[np.ndarray]:
    if not _cv2_spec:
        raise RuntimeError("cv2 is required to load frames from disk")
    frames = []
    for image_path in sorted(frames_dir.glob("*")):
        if image_path.is_dir():
            continue
        image = cv2.imread(str(image_path))
        if image is None:
            continue
        frames.append(image)
    return frames


def run_pipeline(config: PipelineConfig) -> AnchorResult:
    if config.frames_dir is None:
        raise ValueError("frames_dir is required")
    frames = _load_frames(config.frames_dir)

    if config.anchor_type == AnchorType.MARKER_BOARD:
        return resolve_marker_board_anchor(
            frames=frames,
            board_spec=config.board_spec,
            intrinsics=config.intrinsics,
            quality_config=config.quality_config,
            frame_step=config.anchor_frame_step,
            output_dir=config.output_dir,
        )

    return AnchorResult(
        anchor_type=config.anchor_type,
        resolved=False,
        applied=False,
        failure_reason="unsupported_anchor_type",
    )
"""Minimal scanner pipeline hooks with scale constraint enforcement."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

from src.scanner.scale_constraints import (
    ScanRegime,
    ScaleConstraintError,
    ScaleEstimate,
    ScalePolicy,
    build_scale_policy,
    determine_scale_estimate,
    validate_scene_extent,
)

LOGGER = logging.getLogger(__name__)


def parse_ref_pair(ref_pair: str) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    try:
        left, right = ref_pair.split(":", maxsplit=1)
        return _parse_point(left), _parse_point(right)
    except ValueError as exc:
        raise ValueError("ref_pair must be formatted as x1,y1,z1:x2,y2,z2") from exc


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
    regime: ScanRegime,
    expected_size_m: Optional[Tuple[Optional[float], Optional[float]]] = None,
    hard_bounds_m: Optional[Tuple[Optional[float], Optional[float]]] = None,
    allow_autoscale: Optional[bool] = None,
    allow_weak_scale: bool = False,
    ref_distance_m: Optional[float] = None,
    ref_pair: Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = None,
    ref_scale_factor: Optional[float] = None,
) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    policy = build_scale_policy(
        regime=regime,
        expected_size_m=expected_size_m,
        hard_bounds_m=hard_bounds_m,
        allow_autoscale=allow_autoscale,
        allow_weak_scale=allow_weak_scale,
    )

    point_cloud_path = output_dir / "scene_sparse.ply"
    points: list[Tuple[float, float, float]] = []
    vertex_rows: list[list[str]] = []
    header_lines: list[str] = []
    extent_m = None

    if point_cloud_path.exists():
        header_lines, vertex_rows = _load_ply_vertices(point_cloud_path)
        points = _extract_points(vertex_rows)
        extent_m = validate_scene_extent(points)
    else:
        LOGGER.info("Point cloud not found; scale will not be applied.")

    estimate = determine_scale_estimate(
        policy=policy,
        ref_distance_m=ref_distance_m,
        ref_pair=ref_pair,
        ref_scale_factor=ref_scale_factor,
        extent_m=extent_m,
    )

    scale_applied = False
    scaled_point_cloud = None
    if points and estimate.scale_factor is not None:
        scaled_point_cloud = output_dir / "scene_sparse_scaled.ply"
        _write_scaled_ply(header_lines, vertex_rows, scaled_point_cloud, estimate.scale_factor)
        scale_applied = True
    elif not points:
        estimate.notes.append("RECONSTRUCTION_NOT_RUN")
        estimate.notes.append("SCALE_NOT_APPLIED")
    else:
        estimate.notes.append("SCALE_NOT_APPLIED")

    run_record = {
        "scale_policy": policy.to_dict(),
        "scale_estimate": estimate.to_dict(),
        "scale_applied": scale_applied,
        "scaled_point_cloud": str(scaled_point_cloud) if scaled_point_cloud else None,
    }
    metrics_record = {
        "scale_policy": policy.to_dict(),
        "scale_estimate": estimate.to_dict(),
        "estimated_extent_m": extent_m,
        "scaled_extent_m": extent_m * estimate.scale_factor
        if extent_m is not None and estimate.scale_factor is not None
        else None,
        "scale_applied": scale_applied,
    }

    _write_json(output_dir / "run.json", run_record)
    _write_json(output_dir / "reconstruction_metrics.json", metrics_record)

    return {
        "policy": policy,
        "estimate": estimate,
        "scale_applied": scale_applied,
        "scaled_point_cloud": scaled_point_cloud,
    }


def apply_scale_to_ply(input_path: Path, output_path: Path, scale_factor: float) -> int:
    header_lines, vertex_rows = _load_ply_vertices(input_path)
    _write_scaled_ply(header_lines, vertex_rows, output_path, scale_factor)
    return len(vertex_rows)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _parse_point(value: str) -> Tuple[float, float, float]:
    parts = [float(part) for part in value.split(",")]
    if len(parts) != 3:
        raise ValueError("point must include x,y,z")
    return parts[0], parts[1], parts[2]


def _load_ply_vertices(path: Path) -> Tuple[list[str], list[list[str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header_end_index = None
    vertex_count = None
    for idx, line in enumerate(lines):
        if line.startswith("element vertex"):
            try:
                vertex_count = int(line.split()[2])
            except (IndexError, ValueError) as exc:
                raise ValueError("Invalid PLY vertex count line") from exc
        if line.strip() == "end_header":
            header_end_index = idx
            break
    if header_end_index is None:
        raise ValueError("PLY header missing end_header")
    header_lines = lines[: header_end_index + 1]
    vertex_lines = lines[header_end_index + 1 :]
    if vertex_count is not None:
        vertex_lines = vertex_lines[:vertex_count]
    vertex_rows = [line.split() for line in vertex_lines if line.strip()]
    return header_lines, vertex_rows


def _extract_points(vertex_rows: Sequence[Sequence[str]]) -> list[Tuple[float, float, float]]:
    points: list[Tuple[float, float, float]] = []
    for row in vertex_rows:
        if len(row) < 3:
            raise ValueError("PLY vertex row must have at least 3 columns")
        points.append((float(row[0]), float(row[1]), float(row[2])))
    return points


def _write_scaled_ply(
    header_lines: Iterable[str],
    vertex_rows: Sequence[Sequence[str]],
    output_path: Path,
    scale_factor: float,
) -> None:
    scaled_lines = list(header_lines)
    for row in vertex_rows:
        x, y, z = float(row[0]) * scale_factor, float(row[1]) * scale_factor, float(row[2]) * scale_factor
        scaled_coords = [f"{x:.6f}", f"{y:.6f}", f"{z:.6f}"]
        scaled_lines.append(" ".join([*scaled_coords, *row[3:]]))
    output_path.write_text("\n".join(scaled_lines) + "\n", encoding="utf-8")


__all__ = [
    "ScaleConstraintError",
    "ScaleEstimate",
    "ScalePolicy",
    "apply_scale_to_ply",
    "parse_ref_pair",
    "run_pipeline",
]
