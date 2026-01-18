from pathlib import Path

import pytest

from scanner.metadata import extract_metadata


@pytest.mark.scanner
def test_metadata_fallback_to_opencv(sample_video: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _: None)
    metadata = extract_metadata(sample_video, logger=_null_logger())
    assert metadata.source == "opencv"
    assert "streams.width" in metadata.extracted_fields


def _null_logger():
    import logging

    logger = logging.getLogger("test-metadata")
    logger.addHandler(logging.NullHandler())
    return logger
