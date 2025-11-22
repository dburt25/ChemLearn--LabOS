"""Unified CLI entrypoint for LabOS (Phase 2 demo commands).

This module intentionally keeps operations in-memory and focuses on
educational output that mirrors the core data structures without
persisting any state.
"""

from __future__ import annotations

import argparse
import json
import textwrap
from datetime import datetime
from enum import Enum
from typing import Any, Dict

from labos.core import ModuleRegistry, Experiment, create_experiment_with_job


def _serialize_value(value: Any) -> Any:
    """Convert enums and datetimes to JSON-friendly representations."""

    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_value(val) for key, val in value.items()}
    return value


def _normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    return {key: _serialize_value(val) for key, val in record.items()}


def _handle_modules(_: argparse.Namespace) -> int:
    registry = ModuleRegistry.with_phase0_defaults()
    modules = registry.all()

    if not modules:
        print("No modules registered yet. This demo is safe to rerun.")
        return 0

    print("Registered modules (demo view):")
    for meta in sorted(modules, key=lambda m: m.key):
        print(f"- {meta.key}")
        print(f"  Display: {meta.display_name}")
        print(
            "  Method: "
            + textwrap.shorten(meta.method_name, width=60, placeholder="…")
        )
        print(
            "  Limitations: "
            + textwrap.shorten(meta.limitations, width=80, placeholder="…")
        )
        print()
    return 0


def _handle_experiments(_: argparse.Namespace) -> int:
    print("Demo experiments only – no persistence yet.")
    demos = [
        Experiment.example(1, mode="Learner"),
        Experiment.example(2, mode="Lab"),
        Experiment.example(3, mode="Builder"),
    ]
    for exp in demos:
        payload = _normalize_record(exp.to_dict())
        print(json.dumps(payload, indent=2))
    return 0


def _handle_demo_job(_: argparse.Namespace) -> int:
    print("Running in-memory demo: creating an Experiment and Job without persistence.")
    experiment, job = create_experiment_with_job(
        experiment_id="EXP-DEM-001",
        experiment_name="Demo Experiment",
        job_id="JOB-DEM-001",
        job_kind="demo.module:noop",
        owner="demo-user",
        mode="Learner",
        experiment_metadata={"note": "Phase 2 demo only"},
        job_params={"demo": True, "purpose": "show workflow wiring"},
        job_datasets_in=["DS-DEMO-INPUT"],
    )

    job.start()
    job.finish(success=True, outputs=["DS-DEMO-OUTPUT"], error=None)
    experiment.mark_completed()

    print("Experiment record:")
    print(json.dumps(_normalize_record(experiment.to_dict()), indent=2))
    print("\nJob record:")
    print(json.dumps(_normalize_record(job.to_dict()), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Unified LabOS CLI (Phase 2 demo). Commands are educational only and do not "
            "persist state."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    modules_parser = subparsers.add_parser(
        "modules",
        help="List registered module metadata from the in-memory registry.",
    )
    modules_parser.set_defaults(func=_handle_modules)

    experiments_parser = subparsers.add_parser(
        "experiments",
        help="Show demo experiments (non-persistent examples).",
    )
    experiments_parser.set_defaults(func=_handle_experiments)

    demo_job_parser = subparsers.add_parser(
        "demo-job",
        help="Create an in-memory experiment+job pair and display their fields.",
    )
    demo_job_parser.set_defaults(func=_handle_demo_job)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # pragma: no cover - CLI friendly error handling
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
