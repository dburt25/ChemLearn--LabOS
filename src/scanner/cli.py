"""Command line interface for scanner calibration."""
"""Command line interface for marker-board anchoring."""
"""Command line interface for scanner utilities."""
"""CLI entry point for scanner pipelines."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from scanner.calibration.charuco import aruco_capability, calibrate_charuco, draw_charuco_previews
from scanner.calibration.chessboard import calibrate_chessboard, draw_chessboard_previews
from scanner.calibration.io import load_images_from_input, report_payload, save_calibration_report, save_camera_json


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", required=True, help="Path to a video file or directory of images")
    parser.add_argument("--out", required=True, help="Output camera.json path")
    parser.add_argument("--frame-step", type=int, default=1, help="Use every Kth frame")
    parser.add_argument("--max-frames", type=int, default=None, help="Limit number of frames/images")
    parser.add_argument("--min-views", type=int, default=15, help="Minimum valid views")
    parser.add_argument(
        "--rms-threshold-px",
        type=float,
        default=0.8,
        help="Maximum RMS reprojection error in pixels",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Write camera.json even if quality gates fail",
    )
    parser.add_argument(
        "--preview-count",
        type=int,
        default=0,
        help="Write annotated corner previews (0 disables)",
    )


def _report_path(out_path: Path) -> Path:
    return out_path.parent / "calibration_report.json"


def _preview_dir(out_path: Path) -> Path:
    return out_path.parent / "detected_corners_preview"


def _write_previews(preview_dir: Path, previews: Sequence, labels: Sequence[str]) -> None:
    import cv2  # type: ignore

    preview_dir.mkdir(parents=True, exist_ok=True)
    for preview, label in zip(previews, labels):
        filename = f"{label}.png"
        cv2.imwrite(str(preview_dir / filename), preview)


def _validate_image_sizes(images: Sequence) -> None:
    if not images:
        return
    height, width = images[0].shape[:2]
    for idx, image in enumerate(images[1:], start=1):
        if image.shape[:2] != (height, width):
            raise ValueError(
                f"Image size mismatch at index {idx}: expected {width}x{height}, "
                f"got {image.shape[1]}x{image.shape[0]}."
            )


def _build_suggestions(result_warnings: Sequence[str]) -> list[str]:
    suggestions: list[str] = []
    for warning in result_warnings:
        lowered = warning.lower()
        if "views" in lowered:
            suggestions.append("Capture more views spanning varied angles and distances.")
        if "reprojection" in lowered:
            suggestions.append("Improve focus, lock exposure, and avoid motion blur.")
        if "corners" in lowered:
            suggestions.append("Ensure the board fills the frame and is evenly lit.")
    if not suggestions:
        suggestions.append("Re-capture with sharper focus and wider angle coverage.")
    return suggestions


def cmd_calibrate_chessboard(args: argparse.Namespace) -> int:
    images, labels = load_images_from_input(
        Path(args.input), frame_step=args.frame_step, max_frames=args.max_frames
    )
    _validate_image_sizes(images)
    result, details, preview_corners, preview_images = calibrate_chessboard(
        images=images,
        labels=labels,
        board_size=(args.squares_x, args.squares_y),
        square_size_mm=args.square_size_mm,
        min_views=args.min_views,
        rms_threshold_px=args.rms_threshold_px,
    )

    report = report_payload(
        num_images_used=result.num_images_used,
        min_views_required=args.min_views,
        rms_reproj_err_px=result.rms_reproj_err_px,
        rms_threshold_px=args.rms_threshold_px,
        per_view_errors=result.per_view_errors,
        passed_quality_gates=result.passed_quality_gates,
        warnings=result.warnings,
        rejected_views=details.rejected_indices,
        p95_error_px=details.p95_error_px,
        suggestions=_build_suggestions(result.warnings),
    )
    report_path = _report_path(Path(args.out))
    save_calibration_report(report_path, report)

    if result.passed_quality_gates or args.force:
        if result.intrinsics is None:
            print("Calibration failed; no intrinsics were computed.")
            return 1
        save_camera_json(Path(args.out), result.intrinsics)
        if args.preview_count > 0 and preview_corners:
            previews = draw_chessboard_previews(
                preview_images[: args.preview_count],
                preview_corners[: args.preview_count],
                (args.squares_x, args.squares_y),
            )
            _write_previews(
                _preview_dir(Path(args.out)),
                previews,
                details.labels_used[: args.preview_count],
            )
        return 0

    print("Calibration quality gates failed; see calibration_report.json for details.")
    return 2


def cmd_calibrate_charuco(args: argparse.Namespace) -> int:
    ready, message = aruco_capability()
    if not ready:
        report = report_payload(
            num_images_used=0,
            min_views_required=args.min_views,
            rms_reproj_err_px=None,
            rms_threshold_px=args.rms_threshold_px,
            per_view_errors=[],
            passed_quality_gates=False,
            warnings=[message],
            suggestions=[
                "Install opencv-contrib-python to enable Charuco calibration.",
                "Re-run scanner calibrate charuco after installation.",
            ],
        )
        save_calibration_report(_report_path(Path(args.out)), report)
        print(message)
        return 2

    images, labels = load_images_from_input(
        Path(args.input), frame_step=args.frame_step, max_frames=args.max_frames
    )
    _validate_image_sizes(images)
    result, details, preview_detections, preview_images = calibrate_charuco(
        images=images,
        labels=labels,
        squares_x=args.squares_x,
        squares_y=args.squares_y,
        square_length_mm=args.square_length_mm,
        marker_length_mm=args.marker_length_mm,
        aruco_family=args.aruco_family,
        min_views=args.min_views,
        rms_threshold_px=args.rms_threshold_px,
    )

    report = report_payload(
        num_images_used=result.num_images_used,
        min_views_required=args.min_views,
        rms_reproj_err_px=result.rms_reproj_err_px,
        rms_threshold_px=args.rms_threshold_px,
        per_view_errors=result.per_view_errors,
        passed_quality_gates=result.passed_quality_gates,
        warnings=result.warnings,
        rejected_views=details.rejected_indices,
        p95_error_px=details.p95_error_px,
        suggestions=_build_suggestions(result.warnings),
    )
    save_calibration_report(_report_path(Path(args.out)), report)

    if result.passed_quality_gates or args.force:
        if result.intrinsics is None:
            print("Calibration failed; no intrinsics were computed.")
            return 1
        save_camera_json(Path(args.out), result.intrinsics)
        if args.preview_count > 0 and preview_detections:
            import cv2  # type: ignore

            dictionary = cv2.aruco.getPredefinedDictionary(
                cv2.aruco.DICT_4X4_50 if args.aruco_family == "aruco_4x4" else cv2.aruco.DICT_5X5_50
            )
            board = cv2.aruco.CharucoBoard(
                (args.squares_x, args.squares_y),
                args.square_length_mm,
                args.marker_length_mm,
                dictionary,
            )
            previews = draw_charuco_previews(
                preview_images[: args.preview_count],
                preview_detections[: args.preview_count],
                board,
            )
            _write_previews(
                _preview_dir(Path(args.out)),
                previews,
                details.labels_used[: args.preview_count],
            )
        return 0

    print("Calibration quality gates failed; see calibration_report.json for details.")
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scanner", description="3D scanner calibration")
    sub = parser.add_subparsers(dest="command", required=True)

    calibrate = sub.add_parser("calibrate", help="Calibrate camera intrinsics")
    cal_sub = calibrate.add_subparsers(dest="board", required=True)

    chessboard = cal_sub.add_parser("chessboard", help="Calibrate using a chessboard")
    _add_common_args(chessboard)
    chessboard.add_argument("--squares-x", type=int, required=True, help="Inner corners along X")
    chessboard.add_argument("--squares-y", type=int, required=True, help="Inner corners along Y")
    chessboard.add_argument(
        "--square-size-mm",
        "-m",
        type=float,
        required=True,
        help="Chessboard square size in millimeters",
    )
    chessboard.set_defaults(func=cmd_calibrate_chessboard)

    charuco = cal_sub.add_parser("charuco", help="Calibrate using a Charuco board")
    _add_common_args(charuco)
    charuco.add_argument(
        "--aruco-family",
        choices=["aruco_4x4", "aruco_5x5"],
        default="aruco_4x4",
    )
    charuco.add_argument("--squares-x", type=int, required=True, help="Squares along X")
    charuco.add_argument("--squares-y", type=int, required=True, help="Squares along Y")
    charuco.add_argument(
        "--square-length-mm",
        type=float,
        required=True,
        help="Charuco square length in millimeters",
    )
    charuco.add_argument(
        "--marker-length-mm",
        type=float,
        required=True,
        help="ArUco marker length in millimeters",
    )
    charuco.set_defaults(func=cmd_calibrate_charuco)

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


def main(argv: list[str] | None = None) -> int:
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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:  # pragma: no cover - guardrail
        print(f"Calibration failed: {exc}")
        return 1
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
