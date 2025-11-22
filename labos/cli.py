"""Command line interface for ChemLearn LabOS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from .config import LabOSConfig
from .core.errors import LabOSError
from .core.types import DatasetType, ExperimentStatus
from .runtime import LabOSRuntime


def _load_config(root: Optional[str]) -> LabOSConfig:
    return LabOSConfig.load(Path(root) if root else None)


def _prompt(message: str) -> str:
    try:
        return input(message)
    except EOFError:  # pragma: no cover - non-interactive shells
        return ""


def _parse_tags(value: Optional[str]) -> tuple[str, ...]:
    if not value:
        return tuple()
    return tuple(tag.strip() for tag in value.split(",") if tag.strip())


def _load_params(args: argparse.Namespace) -> Dict[str, Any]:
    if args.params_file:
        return json.loads(Path(args.params_file).read_text(encoding="utf-8"))
    if args.params_json:
        return json.loads(args.params_json)
    return {}


def cmd_init(args: argparse.Namespace) -> None:
    config = _load_config(args.root)
    runtime = LabOSRuntime(config)
    runtime.ensure_initialized()
    print(f"Initialized LabOS directories under {runtime.config.root_dir}")


def cmd_new_experiment(args: argparse.Namespace) -> None:
    config = _load_config(args.root)
    runtime = LabOSRuntime(config)
    user_id = args.user or _prompt("User ID: ").strip()
    title = args.title or _prompt("Experiment title: ").strip()
    purpose = args.purpose or _prompt("Purpose: ").strip()
    tags = args.tags or _prompt("Comma-separated tags (optional): ")
    experiment = runtime.create_experiment(
        user_id=user_id,
        title=title,
        purpose=purpose,
        status=ExperimentStatus(args.status),
        inputs=None,
        tags=_parse_tags(tags),
    )
    print(f"Created experiment {experiment.record_id}")


def cmd_register_dataset(args: argparse.Namespace) -> None:
    config = _load_config(args.root)
    runtime = LabOSRuntime(config)
    dataset = runtime.register_dataset(
        owner=args.owner or _prompt("Owner: ").strip(),
        dataset_type=DatasetType(args.dataset_type),
        uri=args.uri,
        tags=_parse_tags(args.tags),
    )
    print(f"Registered dataset {dataset.record_id}")


def cmd_run_module(args: argparse.Namespace) -> None:
    config = _load_config(args.root)
    runtime = LabOSRuntime(config)
    params = _load_params(args)
    job = runtime.run_module_operation(
        experiment_id=args.experiment_id,
        module_id=args.module_id,
        operation=args.operation,
        actor=args.actor,
        parameters=params,
    )
    print(f"Job {job.record_id} finished with status {job.status.value}")
    if job.result_path:
        print(f"Result stored at {job.result_path}")
    if job.error:
        print(f"Error: {job.error}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="labos", description="ChemLearn LabOS CLI")
    parser.add_argument("--root", help="Override LABOS_ROOT path", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Create required directories")
    init_cmd.set_defaults(func=cmd_init)

    exp_cmd = sub.add_parser("new-experiment", help="Create a new experiment record")
    exp_cmd.add_argument("--user", help="Experiment owner identifier")
    exp_cmd.add_argument("--title", help="Experiment title")
    exp_cmd.add_argument("--purpose", help="Experiment purpose")
    exp_cmd.add_argument("--tags", help="Comma-separated tags")
    exp_cmd.add_argument(
        "--status",
        choices=[status.value for status in ExperimentStatus],
        default=ExperimentStatus.DRAFT.value,
        help="Initial experiment status",
    )
    exp_cmd.set_defaults(func=cmd_new_experiment)

    ds_cmd = sub.add_parser("register-dataset", help="Register a dataset placeholder")
    ds_cmd.add_argument("--owner")
    ds_cmd.add_argument("--dataset-type", dest="dataset_type", choices=[t.value for t in DatasetType])
    ds_cmd.add_argument("--uri", required=True)
    ds_cmd.add_argument("--tags")
    ds_cmd.set_defaults(func=cmd_register_dataset)

    run_cmd = sub.add_parser("run-module", help="Execute a registered module operation")
    run_cmd.add_argument("--experiment-id", required=True)
    run_cmd.add_argument("--module-id", required=True)
    run_cmd.add_argument("--operation", required=True)
    run_cmd.add_argument("--actor", required=True)
    run_cmd.add_argument("--params-file")
    run_cmd.add_argument("--params-json")
    run_cmd.set_defaults(func=cmd_run_module)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except LabOSError as exc:
        parser.error(str(exc))
    except Exception as exc:  # pragma: no cover - defensive catch
        parser.error(f"Unexpected failure: {exc}")
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
