from pathlib import Path

import pytest

from scanner.frames import FrameExtractionResult
from scanner.metadata import MetadataResult
from scanner.report import build_metrics_report


@pytest.mark.scanner
def test_metrics_report_failure_has_low_confidence(tmp_path: Path) -> None:
    metadata = MetadataResult(
        container={},
        streams=[],
        extracted_fields=[],
        missing_fields=[],
        source="missing",
    )
    frames = FrameExtractionResult(frames_dir=tmp_path, frame_count=0, fps=0.0)
    report = build_metrics_report(
        reconstruction=None,
        metadata=metadata,
        frame_result=frames,
        failure_reason="no backend",
    )
    assert report["status"] == "failed"
    assert report["scale_confidence"] == "low"
    assert report["accuracy_tiers"]["phase0_disclaimer"]
