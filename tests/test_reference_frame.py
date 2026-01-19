"""Unit tests for reference frame selection."""

from __future__ import annotations

from scanner.cli import build_parser
from scanner.reference_frame import compute_bbox_center, translate_points
from scanner.scale_constraints import ScanRegime
from scanner.reference_frame import default_allow_heuristics


def test_bbox_center_computed_correctly() -> None:
    points = [(0.0, 0.0, 0.0), (2.0, 4.0, 6.0)]
    assert compute_bbox_center(points) == (1.0, 2.0, 3.0)


def test_translation_applied_correctly() -> None:
    points = [(1.0, 2.0, 3.0), (4.0, 5.0, 6.0)]
    translated = translate_points(points, (1.0, 1.0, 1.0))
    assert translated == [(0.0, 1.0, 2.0), (3.0, 4.0, 5.0)]


def test_regime_defaults_enforce_heuristics_off_for_small_objects() -> None:
    assert default_allow_heuristics(ScanRegime.SMALL_OBJECT) is False
    assert default_allow_heuristics(ScanRegime.ROOM_BUILDING) is True
    assert default_allow_heuristics(ScanRegime.AERIAL) is True


def test_cli_parses_origin_and_geo_anchor() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "pipeline",
            "--origin",
            "1,2,3",
            "--geo-anchor",
            "10,20,30",
        ]
    )
    assert args.origin == (1.0, 2.0, 3.0)
    assert args.geo_anchor == (10.0, 20.0, 30.0)
