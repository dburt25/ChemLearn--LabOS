"""CLI wrapper for the scanner pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Tuple

from .pipeline import run_pipeline
from .reference_frame import ReferenceFrameUserInputs, ScanRegime


def _parse_origin(value: str) -> Tuple[float, float, float]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("Origin must be formatted as x,y,z")
    return (float(parts[0]), float(parts[1]), float(parts[2]))


def _parse_geo_anchor(value: str) -> Tuple[float, float, Optional[float]]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if len(parts) not in {2, 3}:
        raise argparse.ArgumentTypeError("Geo anchor must be formatted as lat,lon[,alt]")
    lat = float(parts[0])
    lon = float(parts[1])
    alt = float(parts[2]) if len(parts) == 3 else None
    return (lat, lon, alt)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scanner")
    sub = parser.add_subparsers(dest="command", required=True)

    pipeline_cmd = sub.add_parser("pipeline", help="Run scanner pipeline")
    pipeline_cmd.add_argument("--output", type=Path, required=True)
    pipeline_cmd.add_argument(
        "--regime",
        choices=[regime.value for regime in ScanRegime],
        default=ScanRegime.ROOM_BUILDING.value,
    )
    pipeline_cmd.add_argument("--origin", type=_parse_origin)
    pipeline_cmd.add_argument(
        "--center-mode",
        choices=["auto", "user", "bbox", "marker", "geo"],
        default="auto",
    )
    pipeline_cmd.add_argument("--geo-anchor", type=_parse_geo_anchor)
    pipeline_cmd.add_argument("--time-anchor")
    pipeline_cmd.add_argument("--marker-anchor")
    pipeline_cmd.add_argument(
        "--allow-heuristic-center",
        dest="allow_heuristic_center",
        action="store_true",
    )
    pipeline_cmd.add_argument(
        "--no-allow-heuristic-center",
        dest="allow_heuristic_center",
        action="store_false",
    )
    pipeline_cmd.set_defaults(allow_heuristic_center=None)
    pipeline_cmd.set_defaults(func=_run_pipeline)

    return parser


def _run_pipeline(args: argparse.Namespace) -> None:
    user_inputs = ReferenceFrameUserInputs(
        origin=args.origin,
        center_mode=args.center_mode,
        marker_anchor=args.marker_anchor,
        geo_anchor=args.geo_anchor,
        time_anchor=args.time_anchor,
    )
    run_pipeline(
        args.output,
        regime=ScanRegime(args.regime),
        user_inputs=user_inputs,
        allow_heuristic_center=args.allow_heuristic_center,
    )


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
