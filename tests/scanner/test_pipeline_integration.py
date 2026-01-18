from pathlib import Path

import pytest

from scanner.pipeline import run_pipeline


@pytest.mark.scanner
def test_pipeline_fallback_without_colmap(
    sample_video: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("shutil.which", lambda _: None)
    output_dir = tmp_path / "run"
    exit_code = run_pipeline(
        input_path=sample_video,
        output_dir=output_dir,
        backend_name="colmap",
        max_frames=3,
    )
    assert exit_code == 2
    run_report = output_dir / "run.json"
    metrics_report = output_dir / "reconstruction_metrics.json"
    assert run_report.exists()
    assert metrics_report.exists()
    assert "COLMAP" in run_report.read_text(encoding="utf-8")
