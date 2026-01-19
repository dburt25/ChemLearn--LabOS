"""Integration coverage for scanner pipeline reference frame defaults."""

from __future__ import annotations

import json
import shutil

from scanner.pipeline import default_anchor_inputs, run_pipeline
from scanner.point_cloud_io import write_ply_points
from scanner.scale_constraints import ScanRegime


def test_pipeline_writes_run_json_when_colmap_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda _: None)

    points = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
    point_cloud_path = tmp_path / "scene_sparse_scaled.ply"
    write_ply_points(point_cloud_path, points)

    anchor_inputs = default_anchor_inputs(ScanRegime.ROOM_BUILDING)
    run_record = run_pipeline(
        output_dir=tmp_path,
        anchor_inputs=anchor_inputs,
        anchor_mode="auto",
        point_cloud_path=point_cloud_path,
    )

    run_path = tmp_path / "run.json"
    assert run_path.exists()

    data = json.loads(run_path.read_text())
    assert data["anchor_inputs"]["allow_heuristics"] is True
    assert data["status"] == "skipped"
    assert "COLMAP not available" in data["warnings"][0]
    assert run_record["status"] == "skipped"
