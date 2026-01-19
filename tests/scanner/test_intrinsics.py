import json

import pytest

from src.scanner.intrinsics import Intrinsics, require_intrinsics_for_mode


def test_intrinsics_from_json(tmp_path):
    payload = {
        "fx": 1000.0,
        "fy": 1001.0,
        "cx": 320.0,
        "cy": 240.0,
        "dist": [0.1, 0.01, 0.001, 0.002, 0.0],
    }
    path = tmp_path / "camera.json"
    path.write_text(json.dumps(payload))

    intrinsics = Intrinsics.from_json(path)

    assert intrinsics.fx == 1000.0
    assert intrinsics.fy == 1001.0
    assert intrinsics.dist == payload["dist"]


def test_intrinsics_required_for_small_object():
    with pytest.raises(ValueError):
        require_intrinsics_for_mode("SMALL_OBJECT", None, allow_fallback=False)

    require_intrinsics_for_mode("SMALL_OBJECT", None, allow_fallback=True)
