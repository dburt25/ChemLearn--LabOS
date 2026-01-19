import json

import pytest

from scanner.intrinsics import load_intrinsics_json


def test_load_intrinsics_json(tmp_path):
    path = tmp_path / "intrinsics.json"
    path.write_text(
        json.dumps({"fx": 1000, "fy": 1001, "cx": 320, "cy": 240, "dist": [0.1, 0.2, 0.0, 0.0]}),
        encoding="utf-8",
    )
    intrinsics = load_intrinsics_json(path)
    assert intrinsics.fx == 1000
    assert intrinsics.fy == 1001
    assert intrinsics.cx == 320
    assert intrinsics.cy == 240
    assert intrinsics.dist == (0.1, 0.2, 0.0, 0.0, 0.0)


def test_load_intrinsics_requires_keys(tmp_path):
    path = tmp_path / "intrinsics.json"
    path.write_text(json.dumps({"fx": 1000}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_intrinsics_json(path)
