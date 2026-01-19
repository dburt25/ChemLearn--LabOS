"""CLI parsing tests for scanner pipeline."""

from __future__ import annotations

from scanner.cli import build_parser
from scanner.pipeline import parse_geo_anchor, parse_xyz


def test_cli_parses_origin_and_geo_anchor() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "pipeline",
            "--origin",
            "1.0,2.0,3.0",
            "--geo-anchor",
            "40.1,-70.2,5.5",
        ]
    )

    assert parse_xyz(args.origin) == (1.0, 2.0, 3.0)
    assert parse_geo_anchor(args.geo_anchor) == (40.1, -70.2, 5.5)
