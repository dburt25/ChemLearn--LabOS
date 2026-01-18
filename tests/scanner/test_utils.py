from pathlib import Path

import pytest

from scanner.utils import hash_file


@pytest.mark.scanner
def test_hash_file(tmp_path: Path) -> None:
    sample = tmp_path / "data.txt"
    sample.write_text("hello", encoding="utf-8")
    digest = hash_file(sample)
    assert isinstance(digest, str)
    assert len(digest) == 64
