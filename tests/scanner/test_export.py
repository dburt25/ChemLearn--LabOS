from pathlib import Path

import pytest

from scanner.export import export_sparse_ply


@pytest.mark.scanner
def test_export_requires_colmap(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(RuntimeError, match="COLMAP is required"):
        export_sparse_ply(tmp_path, tmp_path, logger=_null_logger())


def _null_logger():
    import logging

    logger = logging.getLogger("test-export")
    logger.addHandler(logging.NullHandler())
    return logger
