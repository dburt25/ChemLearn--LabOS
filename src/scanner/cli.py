"""Command line interface for scanner calibration."""

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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:  # pragma: no cover - guardrail
        print(f"Calibration failed: {exc}")
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
