"""CLI for scanner pipeline reference frame support."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Tuple

from scanner.pipeline import run_pipeline
from scanner.reference_frame import AnchorInputs, default_allow_heuristics
from scanner.scale_constraints import ScanRegime


def _parse_xyz(value: str) -> Tuple[float, float, float]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("Origin must be formatted as x,y,z")
    return tuple(float(part) for part in parts)  # type: ignore[return-value]


def _parse_geo_anchor(value: str) -> Tuple[float, float, Optional[float]]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if len(parts) not in {2, 3}:
        raise argparse.ArgumentTypeError("Geo anchor must be formatted as lat,lon[,alt]")
    lat = float(parts[0])
    lon = float(parts[1])
    alt = float(parts[2]) if len(parts) == 3 else None
    return lat, lon, alt


def _resolve_allow_heuristics(regime: ScanRegime, override: Optional[bool]) -> bool:
    if override is not None:
        return override
    return default_allow_heuristics(regime)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scanner", description="3D scanner pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    pipeline_cmd = sub.add_parser("pipeline", help="Run the scanner pipeline")
    pipeline_cmd.add_argument("--output-dir", default="scanner_run", help="Output directory")
    pipeline_cmd.add_argument(
        "--regime",
        default=ScanRegime.ROOM_BUILDING.value,
        choices=[regime.value for regime in ScanRegime],
        help="Scan regime for default anchoring behavior",
    )
    pipeline_cmd.add_argument("--origin", type=_parse_xyz, help="Model-space origin as x,y,z")
    pipeline_cmd.add_argument(
        "--anchor-mode",
        default="auto",
        choices=["auto", "user", "bbox", "marker", "geo"],
        help="Anchor selection mode",
    )
    pipeline_cmd.add_argument("--geo-anchor", type=_parse_geo_anchor, help="Geo anchor lat,lon[,alt]")
    pipeline_cmd.add_argument("--time-anchor", help="Timestamp anchor ISO8601")
    pipeline_cmd.add_argument(
        "--allow-heuristic-origin",
        dest="allow_heuristics",
        action="store_true",
        default=None,
        help="Allow heuristic origin selection",
    )
    pipeline_cmd.add_argument(
        "--no-allow-heuristic-origin",
        dest="allow_heuristics",
        action="store_false",
        help="Disable heuristic origin selection",
    )
    pipeline_cmd.add_argument(
        "--point-cloud",
        help="Optional path to a simple XYZ text file for centering",
    )
    pipeline_cmd.set_defaults(func=cmd_pipeline)
    return parser


def _load_point_cloud(path: Optional[str]) -> Optional[list[Tuple[float, float, float]]]:
    if not path:
        return None
    data = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        data.append((float(parts[0]), float(parts[1]), float(parts[2])))
    return data


def cmd_pipeline(args: argparse.Namespace) -> None:
    regime = ScanRegime.from_string(args.regime)
    allow_heuristics = _resolve_allow_heuristics(regime, args.allow_heuristics)
    if args.anchor_mode == "user" and args.origin is None:
        raise ValueError("Anchor mode 'user' requires --origin x,y,z.")
    if args.anchor_mode == "bbox":
        allow_heuristics = True
    anchors = AnchorInputs(
        regime=regime,
        user_origin_xyz=args.origin,
        user_geo_anchor=args.geo_anchor,
        user_timestamp_anchor=args.time_anchor,
        allow_heuristics=allow_heuristics,
    )
    point_cloud = _load_point_cloud(args.point_cloud)
    run_pipeline(
        Path(args.output_dir),
        anchors,
        point_cloud=point_cloud,
        anchor_mode=args.anchor_mode,
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except Exception as exc:
        parser.error(str(exc))
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
