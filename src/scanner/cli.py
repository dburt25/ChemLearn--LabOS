"""Command-line interface for the scanner pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from scanner.anchor_types import ScanRegime
from scanner.anchors import parse_anchor_spec
from scanner.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scanner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pipeline_parser = subparsers.add_parser("pipeline", help="Run scanner pipeline")
    pipeline_parser.add_argument("--frames-dir", required=True)
    pipeline_parser.add_argument("--metadata", dest="metadata_path")
    pipeline_parser.add_argument("--output-dir", required=True)
    pipeline_parser.add_argument(
        "--regime",
        choices=[regime.value for regime in ScanRegime],
        default=ScanRegime.SMALL_OBJECT.value,
    )

    pipeline_parser.add_argument("--anchor", choices=["marker", "geo", "time"])  # noqa: B008
    pipeline_parser.add_argument(
        "--marker-family",
        choices=["aruco_4x4", "aruco_5x5"],
    )
    pipeline_parser.add_argument("--marker-size-m", type=float)
    pipeline_parser.add_argument("--marker-ids")
    pipeline_parser.add_argument("--marker-frames-max", type=int)

    pipeline_parser.add_argument("--geo-anchor")
    pipeline_parser.add_argument("--time-anchor")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "pipeline":
        regime = ScanRegime(args.regime)
        anchor_spec = parse_anchor_spec(
            anchor=args.anchor,
            regime=regime,
            marker_family=args.marker_family,
            marker_ids=args.marker_ids,
            marker_size_m=args.marker_size_m,
            geo_anchor=args.geo_anchor,
            time_anchor=args.time_anchor,
        )
        run_pipeline(
            frames_dir=Path(args.frames_dir),
            output_dir=Path(args.output_dir),
            metadata_path=Path(args.metadata_path) if args.metadata_path else None,
            anchor_spec=anchor_spec,
            regime=regime,
            marker_frames_max=args.marker_frames_max,
        )
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
