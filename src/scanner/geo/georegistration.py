"""Georegistration pipeline for scanner runs."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import numpy as np

from .gcp import GCPSet, load_gcps
from .helmert import HelmertTransform, compute_residuals, solve_helmert
from ..validation.aerial_abs import evaluate_aerial_abs

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeoregConfig:
    georeg_mode: str = "off"
    georeg_space: str = "anchored"
    georeg_max_rmse_m: float = 0.05
    gcp_file: Optional[str] = None
    rel_eligible: bool = False


@dataclass(frozen=True)
class GeoregResult:
    solved: bool
    report: dict
    transform: Optional[HelmertTransform] = None


SPACE_CHOICES = ("raw", "scaled", "centered", "anchored")


def _load_transforms(path: Path) -> dict:
    if not path.exists():
        return {"spaces": {"raw": np.eye(4).tolist()}, "entries": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_space_matrix(data: dict, space: str) -> np.ndarray:
    if "spaces" in data and space in data["spaces"]:
        return np.array(data["spaces"][space], dtype=float)

    entries = data.get("entries", [])
    if not entries:
        return np.eye(4)

    matrix = np.eye(4)
    for entry in entries:
        entry_matrix = np.array(entry.get("matrix"), dtype=float)
        matrix = entry_matrix @ matrix
        if entry.get("to_space") == space:
            break
    return matrix


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _apply_matrix(points: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    ones = np.ones((points.shape[0], 1))
    homogeneous = np.hstack([points, ones])
    transformed = (matrix @ homogeneous.T).T
    return transformed[:, :3]


def _load_ply(path: Path) -> tuple[list[str], list[list[str]], int, int, int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("ply"):
        raise ValueError("PLY file must start with a ply header.")
    if "format ascii" not in lines[1]:
        raise ValueError("Only ASCII PLY files are supported.")

    header_lines = []
    vertex_count = None
    properties = []
    in_vertex = False
    header_end = 0
    for idx, line in enumerate(lines):
        header_lines.append(line)
        if line.startswith("element vertex"):
            vertex_count = int(line.split()[2])
            in_vertex = True
        elif line.startswith("element") and not line.startswith("element vertex"):
            in_vertex = False
        elif line.startswith("property") and in_vertex:
            properties.append(line.split()[-1])
        elif line.strip() == "end_header":
            header_end = idx + 1
            break

    if vertex_count is None:
        raise ValueError("PLY header missing vertex count.")

    try:
        x_idx = properties.index("x")
        y_idx = properties.index("y")
        z_idx = properties.index("z")
    except ValueError as exc:
        raise ValueError("PLY vertex properties must include x, y, z.") from exc

    vertex_lines = [lines[header_end + i].split() for i in range(vertex_count)]
    return header_lines, vertex_lines, x_idx, y_idx, z_idx


def _write_ply(path: Path, header: list[str], vertices: list[list[str]]) -> None:
    content = "\n".join(header + [" ".join(row) for row in vertices]) + "\n"
    path.write_text(content, encoding="utf-8")


def _transform_ply(src: Path, dest: Path, matrix: np.ndarray) -> None:
    header, vertices, x_idx, y_idx, z_idx = _load_ply(src)
    points = np.array(
        [[float(row[x_idx]), float(row[y_idx]), float(row[z_idx])] for row in vertices],
        dtype=float,
    )
    transformed = _apply_matrix(points, matrix)
    for row, (x, y, z) in zip(vertices, transformed):
        row[x_idx] = f"{x:.6f}"
        row[y_idx] = f"{y:.6f}"
        row[z_idx] = f"{z:.6f}"
    _write_ply(dest, header, vertices)


def _transform_obj(src: Path, dest: Path, matrix: np.ndarray) -> None:
    lines = src.read_text(encoding="utf-8").splitlines()
    new_lines = []
    for line in lines:
        if line.startswith("v "):
            parts = line.split()
            coords = np.array([float(parts[1]), float(parts[2]), float(parts[3])])
            transformed = _apply_matrix(coords.reshape(1, 3), matrix)[0]
            parts[1:4] = [f"{value:.6f}" for value in transformed]
            new_lines.append(" ".join(parts))
        else:
            new_lines.append(line)
    dest.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _build_report(
    gcp_set: GCPSet,
    transform: HelmertTransform,
    residuals: dict,
    config: GeoregConfig,
) -> dict:
    abs_eval = evaluate_aerial_abs(
        rel_eligible=config.rel_eligible,
        georeg_solved=True,
        rmse_m=residuals["summary"]["rmse_m"],
        max_rmse_m=config.georeg_max_rmse_m,
    )
    return {
        "status": "solved",
        "gcp_count": len(gcp_set.records),
        "world_frame": gcp_set.world_frame,
        "enu_origin": gcp_set.enu_origin,
        "georeg_space": config.georeg_space,
        "transform": {
            "scale": transform.scale,
            "rotation": transform.rotation.tolist(),
            "translation": transform.translation.tolist(),
        },
        "residuals": residuals,
        "validation": abs_eval,
    }


def run_georegistration(run_dir: str | Path, config: GeoregConfig) -> GeoregResult:
    run_path = Path(run_dir)
    stage_report = run_path / "stage_reports" / "georeg.json"

    if config.georeg_mode == "off":
        report = {"status": "skipped", "reason": "georeg disabled"}
        _write_json(stage_report, report)
        return GeoregResult(solved=False, report=report)

    if not config.gcp_file:
        message = "GCP file is required when georegistration is enabled."
        if config.georeg_mode == "require":
            raise ValueError(message)
        LOGGER.warning(message)
        report = {"status": "skipped", "reason": message}
        _write_json(stage_report, report)
        return GeoregResult(solved=False, report=report)

    gcp_set = load_gcps(config.gcp_file)
    try:
        transform = solve_helmert(gcp_set.model_points, gcp_set.world_points)
    except ValueError as exc:
        if config.georeg_mode == "require":
            raise
        LOGGER.warning("Skipping georegistration: %s", exc)
        report = {"status": "skipped", "reason": str(exc)}
        _write_json(stage_report, report)
        return GeoregResult(solved=False, report=report)

    residuals = compute_residuals(transform, gcp_set.model_points, gcp_set.world_points)
    residuals_payload = {
        "per_point_m": {
            record.gcp_id: error for record, error in zip(gcp_set.records, residuals.per_point_m)
        },
        "summary": {
            "rmse_m": residuals.rmse_m,
            "mean_m": residuals.mean_m,
            "p95_m": residuals.p95_m,
        },
    }

    geo_dir = run_path / "out" / "geo"
    _write_json(
        geo_dir / "geo_transform.json",
        {
            "scale": transform.scale,
            "rotation": transform.rotation.tolist(),
            "translation": transform.translation.tolist(),
            "georeg_space": config.georeg_space,
            "world_frame": gcp_set.world_frame,
            "enu_origin": gcp_set.enu_origin,
        },
    )
    _write_json(geo_dir / "gcp_residuals.json", residuals_payload)

    transforms_path = run_path / "out" / "transforms.json"
    transforms = _load_transforms(transforms_path)
    space_matrix = _extract_space_matrix(transforms, config.georeg_space)
    georeg_matrix = transform.as_matrix()
    append_entry = {
        "name": "T_georeg",
        "matrix": georeg_matrix.tolist(),
        "to_space": "world",
    }
    transforms.setdefault("entries", []).append(append_entry)
    _write_json(transforms_path, transforms)

    combined_matrix = georeg_matrix @ space_matrix

    recon_dir = run_path / "out" / "reconstruction"
    if recon_dir.exists():
        sparse = recon_dir / "sparse.ply"
        if sparse.exists():
            _transform_ply(sparse, recon_dir / "sparse_georeg.ply", combined_matrix)
        dense = recon_dir / "dense.ply"
        if dense.exists():
            _transform_ply(dense, recon_dir / "dense_georeg.ply", combined_matrix)
        mesh = recon_dir / "mesh.obj"
        if mesh.exists():
            _transform_obj(mesh, recon_dir / "mesh_georeg.obj", combined_matrix)

    report = _build_report(gcp_set, transform, residuals_payload, config)
    _write_json(stage_report, report)
    return GeoregResult(solved=True, report=report, transform=transform)
