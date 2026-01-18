from pathlib import Path

import pytest

from scanner.frames import extract_frames


@pytest.mark.scanner
def test_extract_frames_counts(sample_video: Path, tmp_path: Path) -> None:
    result = extract_frames(
        input_path=sample_video,
        output_dir=tmp_path / "frames",
        max_frames=None,
        logger=_null_logger(),
    )
    assert result.frame_count > 0
    assert (result.frames_dir / "frame_000000.png").exists()


def _null_logger():
    import logging

    logger = logging.getLogger("test-frames")
    logger.addHandler(logging.NullHandler())
    return logger
