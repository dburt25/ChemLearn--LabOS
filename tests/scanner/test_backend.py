from pathlib import Path

import pytest

from scanner.backends.colmap_backend import ColmapBackend
from scanner.backends.backend_base import BackendUnavailableError
from scanner.metadata import MetadataResult


@pytest.mark.scanner
def test_colmap_backend_unavailable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("shutil.which", lambda _: None)
    backend = ColmapBackend()
    metadata = MetadataResult(container={}, streams=[], extracted_fields=[], missing_fields=[], source="test")
    with pytest.raises(BackendUnavailableError):
        backend.run(
            images_dir=tmp_path,
            workspace_dir=tmp_path / "colmap",
            metadata=metadata,
            logger=_null_logger(),
        )


def _null_logger():
    import logging

    logger = logging.getLogger("test-backend")
    logger.addHandler(logging.NullHandler())
    return logger
