"""CLI for scanner georegistration."""

from __future__ import annotations

import argparse

from .geo.georegistration import GeoregConfig, run_georegistration, SPACE_CHOICES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scanner georegistration tools")
    parser.add_argument("--run-dir", required=True, help="Run directory containing out/ and stage_reports/")
    parser.add_argument("--georeg", choices=["off", "on", "require"], default="off")
    parser.add_argument("--gcp-file", help="Path to GCP CSV file")
    parser.add_argument("--georeg-space", choices=SPACE_CHOICES, default="anchored")
    parser.add_argument("--georeg-max-rmse-m", type=float, default=0.05)
    parser.add_argument(
        "--rel-eligible",
        action="store_true",
        help="Flag that REL eligibility has been met prior to georeg gating",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = GeoregConfig(
        georeg_mode=args.georeg,
        georeg_space=args.georeg_space,
        georeg_max_rmse_m=args.georeg_max_rmse_m,
        gcp_file=args.gcp_file,
        rel_eligible=args.rel_eligible,
    )
    run_georegistration(args.run_dir, config)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
