from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.scanner.pipeline import apply_scale_to_ply, run_pipeline
from src.scanner.scale_constraints import (
    ScanRegime,
    ScaleConstraintError,
    build_scale_policy,
    determine_scale_estimate,
)


def _write_simple_ply(path: Path) -> None:
    contents = """ply
format ascii 1.0
element vertex 2
property float x
property float y
property float z
end_header
0 0 0
1 2 3
"""
    path.write_text(contents, encoding="utf-8")


def test_default_policy_small_object_requires_reference() -> None:
    policy = build_scale_policy(ScanRegime.SMALL_OBJECT)
    assert policy.require_user_reference is True
    assert policy.allow_autoscale is False


def test_bounds_violation_without_autoscale_raises() -> None:
    policy = build_scale_policy(ScanRegime.SMALL_OBJECT)
    with pytest.raises(ScaleConstraintError):
        determine_scale_estimate(policy=policy, extent_m=10.0)


def test_bounds_violation_autoscale_applies_low_confidence() -> None:
    policy = build_scale_policy(ScanRegime.ROOM_BUILDING)
    estimate = determine_scale_estimate(policy=policy, extent_m=500.0)
    assert estimate.scale_factor is not None
    assert "AUTOSCALE_APPLIED" in estimate.notes
    assert estimate.confidence == "LOW"


def test_apply_scale_to_point_cloud(tmp_path: Path) -> None:
    input_path = tmp_path / "scene_sparse.ply"
    output_path = tmp_path / "scene_sparse_scaled.ply"
    _write_simple_ply(input_path)

    apply_scale_to_ply(input_path, output_path, 2.0)
    scaled_lines = output_path.read_text(encoding="utf-8").splitlines()
    assert scaled_lines[-2].startswith("0.000000 0.000000 0.000000")
    assert scaled_lines[-1].startswith("2.000000 4.000000 6.000000")


def test_reports_include_policy_and_estimate(tmp_path: Path) -> None:
    run_pipeline(output_dir=tmp_path, regime=ScanRegime.ROOM_BUILDING)
    run_payload = json.loads((tmp_path / "run.json").read_text(encoding="utf-8"))
    metrics_payload = json.loads((tmp_path / "reconstruction_metrics.json").read_text(encoding="utf-8"))

    assert "scale_policy" in run_payload
    assert "scale_estimate" in run_payload
    assert "scale_policy" in metrics_payload
    assert "scale_estimate" in metrics_payload
