"""Command line interface for marker-board anchoring."""

from __future__ import annotations

import argparse
from pathlib import Path

from scanner.board import BoardSpec, MarkerFamily, generate_board_png
from scanner.pipeline import run_pipeline
from scanner.quality_gates import QualityGateConfig


def _build_board_spec_from_args(args: argparse.Namespace) -> dict:
    if not (args.board_family and args.board_rows and args.board_cols):
        return {}
    return {
        "family": args.board_family,
        "rows": args.board_rows,
        "cols": args.board_cols,
        "marker_size_m": args.board_marker_size_m,
        "marker_spacing_m": args.board_marker_spacing_m,
        "origin_definition": "board_center",
        "board_id": args.board_id or "board-v1",
    }


def cmd_board_generate(args: argparse.Namespace) -> None:
    spec = BoardSpec(
        family=MarkerFamily(args.family),
        rows=args.rows,
        cols=args.cols,
        marker_size_m=args.marker_size_m,
        marker_spacing_m=args.marker_spacing_m,
        origin_definition="board_center",
        board_id=args.board_id,
    )
    generate_board_png(spec, args.out, dpi=args.dpi)
    print(f"Board saved to {args.out}")
    print("Print at 100% scale (no fit-to-page) for metric accuracy.")


def cmd_pipeline(args: argparse.Namespace) -> None:
    board_overrides = _build_board_spec_from_args(args)
    gate_config = QualityGateConfig(
        min_frames_with_pose=args.min_poses,
        max_mean_reproj_err_px=args.max_mean_reproj_px,
        max_p95_reproj_err_px=args.max_p95_reproj_px,
    )
    run_pipeline(
        frames_dir=args.frames_dir,
        output_dir=args.output_dir,
        anchor_type=args.anchor,
        board_spec_path=args.board_spec,
        board_overrides=board_overrides,
        intrinsics_path=args.intrinsics_file,
        intrinsics_value=args.intrinsics,
        dist_value=args.dist,
        gate_config=gate_config,
        frame_step=args.anchor_frame_step,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scanner", description="Marker-board anchoring tools")
    sub = parser.add_subparsers(dest="command", required=True)

    board_cmd = sub.add_parser("board", help="Marker-board utilities")
    board_sub = board_cmd.add_subparsers(dest="board_command", required=True)

    board_generate = board_sub.add_parser("generate", help="Generate a printable marker board")
    board_generate.add_argument("--family", required=True, choices=[f.value for f in MarkerFamily])
    board_generate.add_argument("--rows", required=True, type=int)
    board_generate.add_argument("--cols", required=True, type=int)
    board_generate.add_argument("--marker-size-m", required=True, type=float)
    board_generate.add_argument("--marker-spacing-m", required=True, type=float)
    board_generate.add_argument("--board-id", default="board-v1")
    board_generate.add_argument("--out", required=True)
    board_generate.add_argument("--dpi", type=int, default=300)
    board_generate.set_defaults(func=cmd_board_generate)

    pipeline_cmd = sub.add_parser("pipeline", help="Run the scanner pipeline")
    pipeline_cmd.add_argument("--frames-dir", required=True)
    pipeline_cmd.add_argument("--output-dir", default=str(Path("out")))
    pipeline_cmd.add_argument("--anchor", choices=["marker_board"], default="marker_board")

    pipeline_cmd.add_argument("--board-spec", help="Board JSON specification")
    pipeline_cmd.add_argument("--board-family", choices=[f.value for f in MarkerFamily])
    pipeline_cmd.add_argument("--board-rows", type=int)
    pipeline_cmd.add_argument("--board-cols", type=int)
    pipeline_cmd.add_argument("--board-marker-size-m", type=float)
    pipeline_cmd.add_argument("--board-marker-spacing-m", type=float)
    pipeline_cmd.add_argument("--board-id")

    pipeline_cmd.add_argument("--intrinsics-file")
    pipeline_cmd.add_argument("--intrinsics", help="fx,fy,cx,cy")
    pipeline_cmd.add_argument("--dist", help="k1,k2,p1,p2,k3")

    pipeline_cmd.add_argument("--min-poses", type=int, default=10)
    pipeline_cmd.add_argument("--max-mean-reproj-px", type=float, default=2.0)
    pipeline_cmd.add_argument("--max-p95-reproj-px", type=float, default=4.0)
    pipeline_cmd.add_argument("--anchor-frame-step", type=int, default=1)
    pipeline_cmd.set_defaults(func=cmd_pipeline)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
