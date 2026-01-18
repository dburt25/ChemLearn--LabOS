import argparse
import sys
from pathlib import Path

from scanner.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Multiview 3D scanner pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pipeline_parser = subparsers.add_parser("pipeline", help="Run the multiview pipeline")
    pipeline_parser.add_argument("--input", required=True, type=Path, help="Path to input video")
    pipeline_parser.add_argument("--out", required=True, type=Path, help="Output directory")
    pipeline_parser.add_argument("--backend", default="colmap", help="Backend name (default: colmap)")
    pipeline_parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Optional cap on frames extracted",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "pipeline":
        return run_pipeline(
            input_path=args.input,
            output_dir=args.out,
            backend_name=args.backend,
            max_frames=args.max_frames,
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
