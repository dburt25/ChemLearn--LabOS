import json
from pathlib import Path

import numpy as np

from src.scanner.geo.georegistration import GeoregConfig, run_georegistration


def _write_simple_ply(path: Path, points: np.ndarray) -> None:
    header = [
        "ply",
        "format ascii 1.0",
        f"element vertex {len(points)}",
        "property float x",
        "property float y",
        "property float z",
        "end_header",
    ]
    lines = [" ".join(map(str, point)) for point in points]
    path.write_text("\n".join(header + lines) + "\n", encoding="utf-8")


def test_georegistration_writes_outputs(tmp_path) -> None:
    run_dir = tmp_path / "run"
    (run_dir / "out" / "reconstruction").mkdir(parents=True)
    (run_dir / "stage_reports").mkdir(parents=True)

    gcp_content = """id,model_x,model_y,model_z,world_x,world_y,world_z
p1,0,0,0,10,0,0
p2,1,0,0,11,0,0
p3,0,1,0,10,1,0
"""
    gcp_path = run_dir / "gcps.csv"
    gcp_path.write_text(gcp_content)

    points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    _write_simple_ply(run_dir / "out" / "reconstruction" / "sparse.ply", points)

    config = GeoregConfig(
        georeg_mode="require",
        georeg_space="raw",
        georeg_max_rmse_m=0.05,
        gcp_file=str(gcp_path),
        rel_eligible=True,
    )
    result = run_georegistration(run_dir, config)

    assert result.solved
    geo_transform = run_dir / "out" / "geo" / "geo_transform.json"
    residuals = run_dir / "out" / "geo" / "gcp_residuals.json"
    stage_report = run_dir / "stage_reports" / "georeg.json"
    georeg_sparse = run_dir / "out" / "reconstruction" / "sparse_georeg.ply"

    assert geo_transform.exists()
    assert residuals.exists()
    assert stage_report.exists()
    assert georeg_sparse.exists()

    payload = json.loads(stage_report.read_text())
    assert payload["status"] == "solved"
