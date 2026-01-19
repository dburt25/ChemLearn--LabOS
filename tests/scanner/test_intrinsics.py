import json
from pathlib import Path

import pytest

from scanner.intrinsics import Intrinsics, load_intrinsics_json, parse_intrinsics_string


def test_load_intrinsics_json(tmp_path: Path):
    payload = {"fx": 500.0, "fy": 510.0, "cx": 320.0, "cy": 240.0, "dist": [0.1, -0.2, 0.0, 0.0, 0.01]}
    path = tmp_path / "intrinsics.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    intrinsics = load_intrinsics_json(path)

    assert intrinsics == Intrinsics(
        fx=500.0,
        fy=510.0,
        cx=320.0,
        cy=240.0,
        dist=(0.1, -0.2, 0.0, 0.0, 0.01),
    )


def test_load_intrinsics_missing_fields(tmp_path: Path):
    path = tmp_path / "intrinsics.json"
    path.write_text(json.dumps({"fx": 500.0}), encoding="utf-8")

    with pytest.raises(ValueError, match="Missing intrinsics fields"):
        load_intrinsics_json(path)


def test_parse_intrinsics_string_with_dist():
    intrinsics = parse_intrinsics_string("500,510,320,240", dist="0.1,-0.2,0.0,0.0,0.01")

    assert intrinsics.dist == (0.1, -0.2, 0.0, 0.0, 0.01)
