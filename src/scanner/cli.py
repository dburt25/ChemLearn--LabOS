"""Command-line interface for the scanner pipeline skeleton."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from scanner.anchors import ScanRegime, parse_anchor_spec
from scanner.pipeline import PipelineInputs, run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scanner", description="3D scanner pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    pipeline = sub.add_parser("pipeline", help="Run the scanner pipeline skeleton")
    pipeline.add_argument("--frames-dir", type=Path, required=True)
    pipeline.add_argument("--output-dir", type=Path, required=True)
    pipeline.add_argument(
        "--regime",
        choices=[regime.value for regime in ScanRegime],
        default=ScanRegime.SMALL_OBJECT.value,
    )
    pipeline.add_argument("--metadata-json", help="Metadata JSON string")
    pipeline.add_argument("--metadata-file", type=Path, help="Metadata JSON file")
    pipeline.add_argument("--scale-constraints", type=Path, help="Scale constraints JSON file")
    pipeline.add_argument("--reference-frame", type=Path, help="Reference frame JSON file")

    pipeline.add_argument("--anchor", choices=["marker", "geo", "time"], help="Anchor mode")
    pipeline.add_argument("--marker-family", choices=["aruco_4x4", "aruco_5x5", "apriltag"])
    pipeline.add_argument("--marker-size-m", type=float)
    pipeline.add_argument("--marker-ids")
    pipeline.add_argument("--marker-frames-max", type=int)

    pipeline.add_argument("--geo-anchor", help="lat,lon[,alt]")
    pipeline.add_argument("--time-anchor", help="ISO8601 timestamp")
    pipeline.set_defaults(func=cmd_pipeline)

    return parser


def _load_json_arg(value: Optional[str], file_path: Optional[Path]) -> dict:
    if value:
        return json.loads(value)
    if file_path:
        return json.loads(file_path.read_text(encoding="utf-8"))
    return {}


def cmd_pipeline(args: argparse.Namespace) -> None:
    metadata = _load_json_arg(args.metadata_json, args.metadata_file)
    if args.marker_frames_max is not None:
        metadata["marker_frames_max"] = args.marker_frames_max

    scale_constraints = _load_json_arg(None, args.scale_constraints)
    reference_frame = _load_json_arg(None, args.reference_frame)

    anchor_spec = parse_anchor_spec(
        anchor=args.anchor,
        regime=ScanRegime(args.regime),
        marker_family=args.marker_family,
        marker_size_m=args.marker_size_m,
        marker_ids=args.marker_ids,
        geo_anchor=args.geo_anchor,
        time_anchor=args.time_anchor,
    )

    inputs = PipelineInputs(
        frames_dir=args.frames_dir,
        metadata=metadata,
        scale_constraints=scale_constraints,
        reference_frame=reference_frame,
        anchor_spec=anchor_spec,
        output_dir=args.output_dir,
    )

    anchor_result = run_pipeline(inputs)
    print(json.dumps(anchor_result.to_dict(), indent=2, sort_keys=True))


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

