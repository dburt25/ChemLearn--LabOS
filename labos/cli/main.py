"""Minimal LabOS CLI for creating experiments and running jobs.

This entry point is intentionally small and only surfaces the most
common workflow helpers. It bridges to the workflow layer so that
experiments and module jobs share the same identifiers and lineage
as other LabOS integrations.

Examples
--------
Create a new experiment record (identifiers are auto-generated)::

    labos experiment create --name "Kinetic sweep"

Run a module operation and capture its workflow result::

    labos job run --module demo.calorimetry --params '{"temp": 298}'

Both commands print JSON payloads that mirror the workflow models for
quick scripting or debugging.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from labos.core import create_experiment, run_module_job
from labos.core.experiments import ExperimentMode, ExperimentStatus


def _json_dumps(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def _parse_metadata(value: str | None) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:  # pragma: no cover - CLI validation
        raise argparse.ArgumentTypeError(f"Invalid JSON for metadata: {exc}")
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("Metadata JSON must decode to an object")
    return parsed


def _parse_params(value: str | None) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:  # pragma: no cover - CLI validation
        raise argparse.ArgumentTypeError(f"Invalid JSON for params: {exc}")
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("Params JSON must decode to an object")
    return parsed


def _handle_experiment_create(args: argparse.Namespace) -> int:
    experiment = create_experiment(
        name=args.name,
        owner=args.owner,
        mode=args.mode,
        status=args.status,
        metadata=_parse_metadata(args.metadata),
    )
    print(_json_dumps(experiment.to_dict()))
    return 0


def _handle_job_run(args: argparse.Namespace) -> int:
    params = _parse_params(args.params)
    result = run_module_job(
        module_key=args.module,
        operation=args.operation,
        params=params,
        actor=args.actor,
        experiment_name=args.experiment_name,
        experiment_owner=args.experiment_owner,
        experiment_mode=args.experiment_mode,
    )
    print(_json_dumps(result.to_dict()))
    return 0 if result.succeeded() else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LabOS CLI for experiments and jobs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    exp_parser = subparsers.add_parser("experiment", help="Experiment related commands")
    exp_sub = exp_parser.add_subparsers(dest="experiment_command", required=True)

    exp_create = exp_sub.add_parser("create", help="Create a new experiment record")
    exp_create.add_argument("--name", required=True, help="Human-friendly experiment name")
    exp_create.add_argument(
        "--owner",
        default="cli-user",
        help="Owner identifier for the experiment",
    )
    exp_create.add_argument(
        "--mode",
        choices=[mode.value for mode in ExperimentMode],
        default=ExperimentMode.LAB.value,
        help="Experiment mode",
    )
    exp_create.add_argument(
        "--status",
        choices=[status.value for status in ExperimentStatus],
        default=ExperimentStatus.DRAFT.value,
        help="Initial experiment status",
    )
    exp_create.add_argument(
        "--metadata",
        help="Optional JSON object to attach to experiment metadata",
    )
    exp_create.set_defaults(func=_handle_experiment_create)

    job_parser = subparsers.add_parser("job", help="Job and module execution commands")
    job_sub = job_parser.add_subparsers(dest="job_command", required=True)

    job_run = job_sub.add_parser("run", help="Run a module operation as a job")
    job_run.add_argument("--module", required=True, help="Registered module key")
    job_run.add_argument(
        "--operation",
        default="compute",
        help="Operation name exposed by the module",
    )
    job_run.add_argument(
        "--params",
        help="JSON object with parameters passed to the module operation",
    )
    job_run.add_argument(
        "--actor",
        default="labos.cli",
        help="Actor string recorded on audit events",
    )
    job_run.add_argument(
        "--experiment-name",
        help="Override the auto-generated experiment name for the run",
    )
    job_run.add_argument(
        "--experiment-owner",
        default="cli-user",
        help="Owner assigned to the experiment if created implicitly",
    )
    job_run.add_argument(
        "--experiment-mode",
        choices=[mode.value for mode in ExperimentMode],
        default=ExperimentMode.LAB.value,
        help="Mode applied when creating the experiment",
    )
    job_run.set_defaults(func=_handle_job_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # pragma: no cover - CLI friendly errors
        parser.error(str(exc))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
