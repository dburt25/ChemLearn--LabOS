"""Command line interface for scanner utilities."""
"""CLI entry point for scanner pipelines."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from scanner.anchors import AnchorType
from scanner.board import BoardSpec, MarkerFamily, generate_board_png
from scanner.intrinsics import Intrinsics, load_intrinsics_json
from scanner.pipeline import PipelineConfig, run_pipeline
from scanner.quality_gates import QualityGateConfig


def _parse_float_list(value: Optional[str]) -> list[float]:
    if not value:
        return []
    return [float(part.strip()) for part in value.split(",") if part.strip()]


def _build_board_spec(args: argparse.Namespace) -> BoardSpec:
    board_spec_path = getattr(args, "board_spec", None)
    if board_spec_path:
        return BoardSpec.from_json(board_spec_path)
    return BoardSpec(
        family=MarkerFamily.from_string(getattr(args, "board_family", "")),
        rows=getattr(args, "board_rows", 0),
        cols=getattr(args, "board_cols", 0),
        marker_size_m=getattr(args, "board_marker_size_m", 0.0),
        marker_spacing_m=getattr(args, "board_marker_spacing_m", 0.0),
        board_id=getattr(args, "board_id", "") or "",
    )


def _load_intrinsics(args: argparse.Namespace) -> Intrinsics | None:
    if args.intrinsics_file:
        return load_intrinsics_json(args.intrinsics_file)
    if args.intrinsics:
        values = _parse_float_list(args.intrinsics)
        if len(values) != 4:
            raise ValueError("--intrinsics must have fx,fy,cx,cy")
        dist_values = _parse_float_list(args.dist)
        if dist_values and len(dist_values) not in (4, 5):
            raise ValueError("--dist must have 4 or 5 values")
        dist = dist_values if dist_values else [0.0, 0.0, 0.0, 0.0, 0.0]
        if len(dist) == 4:
            dist.append(0.0)
        return Intrinsics(
            fx=values[0],
            fy=values[1],
            cx=values[2],
            cy=values[3],
            dist=tuple(dist),
        )
    return None


def cmd_board_generate(args: argparse.Namespace) -> None:
    board_spec = _build_board_spec(args)
    generate_board_png(board_spec, args.out, dpi=args.dpi)
    print(f"Generated board {board_spec.board_id} at {args.out}")
    print("Print at 100% scale with no fit-to-page to preserve metric sizing.")


def cmd_pipeline(args: argparse.Namespace) -> None:
    board_spec = _build_board_spec(args)
    intrinsics = _load_intrinsics(args)
    quality_config = QualityGateConfig(
        min_frames_with_pose=args.min_poses,
        max_mean_reproj_err_px=args.max_mean_reproj_px,
        max_p95_reproj_err_px=args.max_p95_reproj_px,
    )
    config = PipelineConfig(
        anchor_type=AnchorType.MARKER_BOARD,
        board_spec=board_spec,
        intrinsics=intrinsics,
        quality_config=quality_config,
        anchor_frame_step=args.anchor_frame_step,
        frames_dir=Path(args.frames_dir),
        output_dir=Path(args.out_dir),
    )
    result = run_pipeline(config)
    print("Anchor applied" if result.applied else "Anchor not applied")
    if result.failure_reason:
        print(f"Failure reason: {result.failure_reason}")
    if result.anchor_summary_path:
        print(f"Summary: {result.anchor_summary_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scanner", description="Marker board scanning utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    board_cmd = sub.add_parser("board", help="Board utilities")
    board_sub = board_cmd.add_subparsers(dest="board_command", required=True)
    board_gen = board_sub.add_parser("generate", help="Generate an ArUco board image")
    board_gen.add_argument("--family", dest="board_family", required=True)
    board_gen.add_argument("--rows", dest="board_rows", type=int, required=True)
    board_gen.add_argument("--cols", dest="board_cols", type=int, required=True)
    board_gen.add_argument("--marker-size-m", dest="board_marker_size_m", type=float, required=True)
    board_gen.add_argument(
        "--marker-spacing-m", dest="board_marker_spacing_m", type=float, required=True
    )
    board_gen.add_argument("--board-id", dest="board_id")
    board_gen.add_argument("--out", required=True)
    board_gen.add_argument("--dpi", type=int, default=300)
    board_gen.set_defaults(func=cmd_board_generate)

    pipeline_cmd = sub.add_parser("pipeline", help="Run the scanner pipeline")
    pipeline_cmd.add_argument("--frames-dir", required=True)
    pipeline_cmd.add_argument("--out-dir", default="out")
    pipeline_cmd.add_argument("--anchor", choices=["marker_board"], default="marker_board")
    pipeline_cmd.add_argument("--board-spec")
    pipeline_cmd.add_argument("--board-family", default="aruco_4x4")
    pipeline_cmd.add_argument("--board-rows", type=int, default=4)
    pipeline_cmd.add_argument("--board-cols", type=int, default=6)
    pipeline_cmd.add_argument("--board-marker-size-m", type=float, default=0.02)
    pipeline_cmd.add_argument("--board-marker-spacing-m", type=float, default=0.005)
    pipeline_cmd.add_argument("--board-id")
    pipeline_cmd.add_argument("--intrinsics-file")
    pipeline_cmd.add_argument("--intrinsics")
    pipeline_cmd.add_argument("--dist")
    pipeline_cmd.add_argument("--min-poses", type=int, default=10)
    pipeline_cmd.add_argument("--max-mean-reproj-px", type=float, default=2.0)
    pipeline_cmd.add_argument("--max-p95-reproj-px", type=float, default=4.0)
    pipeline_cmd.add_argument("--anchor-frame-step", type=int, default=1)
    pipeline_cmd.set_defaults(func=cmd_pipeline)

    return parser
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
