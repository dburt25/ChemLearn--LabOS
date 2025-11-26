"""Command line interface for ChemLearn LabOS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence

from labos.config import LabOSConfig
from labos.core.module_registry import get_default_registry
from labos.core.workflows import run_module_job
from labos.core.errors import LabOSError
from labos.core.types import DatasetType, ExperimentStatus
from labos.runtime import LabOSRuntime


def _load_config(root: Optional[str]) -> LabOSConfig:
    return LabOSConfig.load(Path(root) if root else None)


def _print_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    widths = [len(header) for header in headers]
    materialized_rows = []
    for row in rows:
        stringified = [str(value) for value in row]
        materialized_rows.append(stringified)
        widths = [max(current, len(value)) for current, value in zip(widths, stringified)]

    header_line = "  ".join(header.ljust(width) for header, width in zip(headers, widths))
    print(header_line)
    print("  ".join("-" * width for width in widths))
    for row in materialized_rows:
        print("  ".join(value.ljust(width) for value, width in zip(row, widths)))


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
    params = _load_params(args)
    result = run_module_job(
        module_key=args.module_key,
        operation=args.operation,
        params=params,
        actor=args.actor,
        experiment_name=args.experiment_name,
        experiment_owner=args.experiment_owner,
        module_registry=get_default_registry(),
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))


def cmd_list_modules(args: argparse.Namespace) -> None:
    registry = get_default_registry()
    modules = registry.list_metadata()
    if not modules:
        print("No modules registered")
        return
    _print_table(("key", "method"), ((meta.key, meta.method_name) for meta in modules))


def _load_experiments(args: argparse.Namespace):
    runtime = LabOSRuntime(_load_config(args.root))
    experiments = []
    for exp_id in runtime.components.experiments.list_ids():
        experiment = runtime.components.experiments.get(exp_id)
        experiments.append(experiment)
    return experiments


def cmd_list_experiments(args: argparse.Namespace) -> None:
    experiments = _load_experiments(args)
    if not experiments:
        print("No experiments found")
        return
    _print_table(
        ("id", "name", "created"),
        ((exp.record_id, exp.title, exp.created_at) for exp in experiments),
    )


def cmd_list_datasets(args: argparse.Namespace) -> None:
    runtime = LabOSRuntime(_load_config(args.root))
    dataset_registry = runtime.components.datasets
    rows = []
    for dataset_id in dataset_registry.list_ids():
        dataset = dataset_registry.get(dataset_id)
        experiment_id = dataset.metadata.get("experiment_id", "-")
        job_id = dataset.metadata.get("job_id", "-")
        rows.append((dataset.record_id, experiment_id, job_id))
    if not rows:
        print("No datasets found")
        return
    _print_table(("id", "experiment", "job"), rows)


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
    run_cmd.add_argument("module_key", help="Registered module key (e.g. pchem.calorimetry)")
    run_cmd.add_argument("--operation", default="compute", help="Operation name to invoke")
    run_cmd.add_argument("--actor", default="labos.cli", help="Actor recorded in audit trail")
    run_cmd.add_argument("--experiment-name", help="Optional experiment label when minting a new record")
    run_cmd.add_argument("--experiment-owner", default="cli-user", help="Owner recorded on the experiment")
    run_cmd.add_argument("--params-file")
    run_cmd.add_argument("--params-json")
    run_cmd.set_defaults(func=cmd_run_module)

    list_modules_cmd = sub.add_parser("list-modules", help="Show registered module metadata")
    list_modules_cmd.set_defaults(func=cmd_list_modules)

    list_experiments_cmd = sub.add_parser("list-experiments", help="List known experiments under the root")
    list_experiments_cmd.set_defaults(func=cmd_list_experiments)

    list_datasets_cmd = sub.add_parser("list-datasets", help="List datasets and provenance hints")
    list_datasets_cmd.set_defaults(func=cmd_list_datasets)

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
