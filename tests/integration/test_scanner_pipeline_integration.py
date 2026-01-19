from __future__ import annotations

import json
from pathlib import Path

from src.scanner.pipeline import run_pipeline
from src.scanner.scale_constraints import ScanRegime


def test_pipeline_emits_scale_fields_without_reconstruction(tmp_path: Path) -> None:
    run_pipeline(output_dir=tmp_path, regime=ScanRegime.ROOM_BUILDING)
    run_payload = json.loads((tmp_path / "run.json").read_text(encoding="utf-8"))
    metrics_payload = json.loads((tmp_path / "reconstruction_metrics.json").read_text(encoding="utf-8"))

    assert run_payload["scale_policy"]["regime"] == ScanRegime.ROOM_BUILDING.value
    assert "scale_estimate" in run_payload
    assert metrics_payload["scale_policy"]["regime"] == ScanRegime.ROOM_BUILDING.value
    assert "scale_estimate" in metrics_payload
