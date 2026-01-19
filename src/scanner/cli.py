"""Command-line interface for scanner pipeline skeleton."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scanner.pipeline import (
    default_anchor_inputs,
    parse_geo_anchor,
    parse_xyz,
    resolve_regime,
    run_pipeline,
)
from scanner.scale_constraints import ScanRegime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scanner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pipeline_parser = subparsers.add_parser("pipeline", help="Run scanner pipeline")
    pipeline_parser.add_argument(
        "--regime",
        choices=[regime.value for regime in ScanRegime],
        default="room_building",
        help="Scan regime for defaults.",
    )
    pipeline_parser.add_argument("--origin", help="Explicit origin x,y,z in model coordinates.")
    pipeline_parser.add_argument(
        "--anchor-mode",
        choices=["auto", "user", "bbox", "marker", "geo"],
        default="auto",
    )
    pipeline_parser.add_argument("--geo-anchor", help="Geospatial anchor lat,lon[,alt].")
    pipeline_parser.add_argument("--time-anchor", help="Timestamp anchor ISO8601 string.")
    pipeline_parser.add_argument(
        "--allow-heuristic-origin",
        dest="allow_heuristic_origin",
        action="store_true",
        help="Allow heuristic origin selection.",
    )
    pipeline_parser.add_argument(
        "--no-allow-heuristic-origin",
        dest="allow_heuristic_origin",
        action="store_false",
        help="Disallow heuristic origin selection.",
    )
    pipeline_parser.set_defaults(allow_heuristic_origin=None)
    pipeline_parser.add_argument(
        "--output-dir",
        default="scanner_output",
        help="Output directory for run.json and reference_frame.json.",
    )
    pipeline_parser.add_argument(
        "--point-cloud",
        help="Optional input point cloud (.ply) for centering.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "pipeline":
        parser.error("Unsupported command")

    regime = resolve_regime(args.regime)
    user_origin = parse_xyz(args.origin) if args.origin else None
    user_geo_anchor = parse_geo_anchor(args.geo_anchor) if args.geo_anchor else None
    allow_heuristics = args.allow_heuristic_origin

    anchor_inputs = default_anchor_inputs(
        regime=regime,
        user_origin_xyz=user_origin,
        user_geo_anchor=user_geo_anchor,
        user_timestamp_anchor=args.time_anchor,
        allow_heuristics=allow_heuristics,
    )

    output_dir = Path(args.output_dir)
    point_cloud_path = Path(args.point_cloud) if args.point_cloud else None

    run_record = run_pipeline(
        output_dir=output_dir,
        anchor_inputs=anchor_inputs,
        anchor_mode=args.anchor_mode,
        point_cloud_path=point_cloud_path,
    )

    if run_record.get("status") == "failed":
        error = run_record.get("error", "Pipeline failed")
        print(error, file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
