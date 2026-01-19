"""Integration tests for reference frame pipeline outputs."""

from __future__ import annotations

import json

from scanner.pipeline import run_pipeline
from scanner.reference_frame import AnchorInputs
from scanner.scale_constraints import ScanRegime


def test_pipeline_writes_run_json_without_point_cloud(tmp_path) -> None:
    anchors = AnchorInputs(regime=ScanRegime.ROOM_BUILDING, allow_heuristics=True)
    payload = run_pipeline(tmp_path, anchors, point_cloud=None)

    run_path = tmp_path / "run.json"
    assert run_path.exists()
    data = json.loads(run_path.read_text(encoding="utf-8"))
    assert "reference_frame" in data
    assert data["reference_frame"]["anchors"]["allow_heuristics"] is True
    assert data["reference_frame"]["anchors"]["regime"] == ScanRegime.ROOM_BUILDING.value
    assert payload["reference_frame"]["anchors"]["regime"] == ScanRegime.ROOM_BUILDING.value
