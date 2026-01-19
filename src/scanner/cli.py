"""CLI entry point for scanner pipelines."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional

from src.scanner.pipeline import parse_ref_pair, run_pipeline
from src.scanner.scale_constraints import ScanRegime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scanner", description="3D scanner pipeline CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    pipeline_cmd = sub.add_parser("pipeline", help="Run the reconstruction pipeline")
    pipeline_cmd.add_argument("--output-dir", default=".", help="Output directory for run artifacts")
    pipeline_cmd.add_argument(
        "--regime",
        choices=[regime.value for regime in ScanRegime],
        default=ScanRegime.ROOM_BUILDING.value,
        help="Scan regime to constrain scale",
    )
    pipeline_cmd.add_argument("--expected-size-min-m", type=float)
    pipeline_cmd.add_argument("--expected-size-max-m", type=float)
    pipeline_cmd.add_argument("--hard-bounds-min-m", type=float)
    pipeline_cmd.add_argument("--hard-bounds-max-m", type=float)
    pipeline_cmd.add_argument("--ref-distance-m", type=float)
    pipeline_cmd.add_argument("--ref-pair", type=str)
    pipeline_cmd.add_argument("--ref-scale-factor", type=float)
    pipeline_cmd.add_argument(
        "--allow-weak-scale",
        action="store_true",
        help="Allow SMALL_OBJECT scans to proceed without a user reference",
    )
    pipeline_cmd.add_argument(
        "--allow-autoscale",
        action="store_true",
        help="Enable autoscale when hard bounds are violated",
    )
    pipeline_cmd.set_defaults(func=_run_pipeline)

    return parser


def _run_pipeline(args: argparse.Namespace) -> None:
    expected_size = _range_from_args(args.expected_size_min_m, args.expected_size_max_m)
    hard_bounds = _range_from_args(args.hard_bounds_min_m, args.hard_bounds_max_m)
    ref_pair = parse_ref_pair(args.ref_pair) if args.ref_pair else None
    if args.ref_scale_factor is not None:
        logging.warning("User-provided scale factor override in use; verify metrology separately.")

    run_pipeline(
        output_dir=Path(args.output_dir),
        regime=ScanRegime(args.regime),
        expected_size_m=expected_size,
        hard_bounds_m=hard_bounds,
        allow_autoscale=args.allow_autoscale or None,
        allow_weak_scale=args.allow_weak_scale,
        ref_distance_m=args.ref_distance_m,
        ref_pair=ref_pair,
        ref_scale_factor=args.ref_scale_factor,
    )


def _range_from_args(
    min_value: Optional[float], max_value: Optional[float]
) -> Optional[tuple[Optional[float], Optional[float]]]:
    if min_value is None and max_value is None:
        return None
    return (min_value, max_value)


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
