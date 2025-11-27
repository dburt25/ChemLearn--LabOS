"""Lightweight orchestration helpers for experiments, jobs, and datasets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
from uuid import uuid4

from . import storage
from .audit import AuditEvent
from .datasets import DatasetRef
from .errors import ModuleExecutionError
from .experiments import Experiment, ExperimentMode, ExperimentStatus
from .jobs import Job
from .module_registry import (
    ModuleRegistry,
    OperationRegistryProtocol,
    get_default_registry,
)
from .provenance import link_job_to_dataset, register_import_result


def _utc_now() -> datetime:
    """Return timezone-aware UTC now to align with other core models."""

    return datetime.now(timezone.utc)


def _prefixed_id(prefix: str) -> str:
    """Generate a simple, timestamp-based identifier with ``prefix``."""

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}-{timestamp}"


def _validate_module_key(module_key: str) -> str:
    if not isinstance(module_key, str) or not module_key.strip():
        raise ValueError("module_key must be a non-empty string")
    return module_key


def _coerce_registry(
    registry: ModuleRegistry | OperationRegistryProtocol | None,
) -> ModuleRegistry:
    """Normalize registry inputs to a metadata-aware ``ModuleRegistry``."""

    if isinstance(registry, ModuleRegistry):
        return registry
    if registry is None:
        return get_default_registry()
    if not isinstance(registry, OperationRegistryProtocol):
        raise TypeError(
            "module_registry must be a ModuleRegistry, OperationRegistry, or None"
        )
    return ModuleRegistry.with_phase0_defaults(operation_registry=registry)


@dataclass(slots=True)
class WorkflowResult:
    """Outcome of a workflow run, including lineage and error context."""

    experiment: Experiment
    job: Job
    dataset: DatasetRef | None
    audit_events: List[AuditEvent]
    module_output: Dict[str, object] | None = None
    error: str | None = None

    def succeeded(self) -> bool:
        """Return ``True`` when the module completed without error."""

        return self.error is None

    def to_dict(self) -> Dict[str, object]:
        """Serialize the workflow result for logging or API responses."""

        return {
            "experiment": self.experiment.to_dict(),
            "job": self.job.to_dict(),
            "dataset": self.dataset.to_dict() if self.dataset else None,
            "audit_events": [event.to_dict() for event in self.audit_events],
            "module_output": self.module_output,
            "error": self.error,
            "succeeded": self.succeeded(),
        }


def _normalize_params(params: Mapping[str, object] | None) -> Dict[str, object]:
    """Ensure parameters are dict-like with stringified keys."""

    if params is None:
        return {}
    if not isinstance(params, Mapping):
        raise TypeError("params must be a mapping of argument names to values")
    return {str(key): value for key, value in params.items()}


def _extract_input_dataset_ids(params: Mapping[str, object]) -> List[str]:
    """Extract dataset identifiers from known parameter keys."""

    dataset_ids: List[str] = []
    maybe_single = params.get("dataset_id")
    if maybe_single:
        dataset_ids.append(str(maybe_single))
    maybe_many = params.get("dataset_ids")
    if isinstance(maybe_many, Sequence) and not isinstance(maybe_many, (str, bytes, bytearray)):
        dataset_ids.extend(str(item) for item in maybe_many)
    return list(dict.fromkeys(dataset_ids))


def _build_placeholder_dataset(module_key: str, label: str = "Module output") -> DatasetRef:
    """Create a placeholder dataset reference for modules that omit one."""

    return DatasetRef(
        id=_prefixed_id("DS"),
        label=label,
        kind="table",
        metadata={"module_key": module_key, "placeholder": True},
    )


def create_experiment(
    *,
    name: str,
    owner: str = "local-user",
    mode: ExperimentMode | str = ExperimentMode.LAB,
    status: ExperimentStatus | str = ExperimentStatus.DRAFT,
    metadata: Optional[Dict[str, Any]] = None,
    experiment_id: Optional[str] = None,
) -> Experiment:
    """Create a standalone ``Experiment`` record with generated identifiers."""

    resolved_mode = ExperimentMode(mode) if isinstance(mode, str) else mode
    resolved_status = ExperimentStatus(status) if isinstance(status, str) else status
    experiment = Experiment(
        id=experiment_id or _prefixed_id("EXP"),
        name=name,
        owner=owner,
        mode=resolved_mode,
        status=resolved_status,
        metadata=dict(metadata or {}),
    )
    return storage.upsert_experiment(experiment)


def _create_job_record(
    experiment: Experiment,
    *,
    module_key: str,
    operation: str,
    params: Mapping[str, object],
    datasets_in: Optional[Sequence[str]] = None,
    job_id: Optional[str] = None,
) -> Job:
    if not module_key:
        raise ValueError("module_key is required to create a job record")

    storage.upsert_experiment(experiment)
    job = Job(
        id=job_id or _prefixed_id("JOB"),
        experiment_id=experiment.id,
        kind=f"{module_key}:{operation}",
        params=dict(params),
        datasets_in=list(dict.fromkeys(list(datasets_in or []))),
    )
    experiment.add_job(job.id)
    storage.upsert_experiment(experiment)
    return storage.upsert_job(job)


def _audit_from_dict(
    payload: Mapping[str, object],
    *,
    module_key: str,
    job: Job,
    actor: str,
) -> AuditEvent:
    created_at = payload.get("created_at")
    if isinstance(created_at, str):
        try:
            parsed = datetime.fromisoformat(created_at)
        except ValueError:
            parsed = _utc_now()
    else:
        parsed = _utc_now()

    details = payload.get("details")
    detail_dict = dict(details) if isinstance(details, Mapping) else {}
    detail_dict.setdefault("module_key", module_key)
    detail_dict.setdefault("job_id", job.id)
    detail_dict.setdefault("experiment_id", job.experiment_id)
    detail_dict.setdefault("status", payload.get("status", "success"))

    return AuditEvent(
        id=str(payload.get("id") or _prefixed_id("AUD")),
        actor=str(payload.get("actor") or actor),
        action=str(payload.get("action") or "module-run"),
        target=str(payload.get("target") or job.id),
        created_at=parsed,
        details=detail_dict,
    )


def run_module_job(
    module_key: str,
    params: Mapping[str, object] | None = None,
    *,
    experiment_id: str | None = None,
    experiment: Experiment | None = None,
    operation: str = "compute",
    actor: str = "labos.workflow",
    experiment_name: Optional[str] = None,
    experiment_owner: str = "local-user",
    experiment_mode: ExperimentMode | str = ExperimentMode.LAB,
    datasets_in: Optional[Sequence[str]] = None,
    job_id: Optional[str] = None,
    module_registry: ModuleRegistry | OperationRegistry | None = None,
) -> WorkflowResult:
    """Run a module operation and wire Experiment → Job → Dataset → Audit.

    Args:
        module_key: Registry key for the module to execute.
        params: Parameters forwarded to the module operation.
        experiment_id: Optional existing experiment identifier to attach to.
        experiment: Optional experiment object. When omitted, a new experiment is created.
        operation: Operation name registered for the module (defaults to ``"compute"``).
        actor: Identifier for the actor performing the run (used in audit events).
        experiment_name: Friendly name used when creating a new experiment.
        experiment_owner: Owner field for new experiments.
        experiment_mode: Mode value for new experiments.
        datasets_in: Optional dataset identifiers to associate as inputs.
        job_id: Optional explicit job identifier.
        module_registry: Optional registry override (metadata-aware or runtime registry).

    Returns:
        WorkflowResult containing the created Experiment, Job, DatasetRef, and AuditEvent list.

    Side Effects:
        - Creates an Experiment when none is supplied.
        - Registers a Job linked to the experiment.
        - Persists a DatasetRef for module outputs (placeholder when absent).
        - Emits AuditEvents describing success or failure lineage.
    """

    _validate_module_key(module_key)
    registry = _coerce_registry(module_registry)
    resolved_params = _normalize_params(params)
    inferred_inputs = _extract_input_dataset_ids(resolved_params)
    all_inputs = list(dict.fromkeys(list(datasets_in or []) + inferred_inputs))

    if experiment and experiment_id and experiment.id != experiment_id:
        raise ValueError(
            "experiment_id does not match the provided experiment object"
        )

    experiment_obj = experiment or create_experiment(
        name=experiment_name or f"{module_key} workflow",
        owner=experiment_owner,
        mode=experiment_mode,
        experiment_id=experiment_id,
    )

    job = _create_job_record(
        experiment_obj,
        module_key=module_key,
        operation=operation,
        params=resolved_params,
        datasets_in=all_inputs,
        job_id=job_id,
    )
    job.params.setdefault("module_key", module_key)
    job.params.setdefault("operation", operation)
    module_meta = registry.get_metadata_optional(module_key)
    if module_meta:
        job.params.setdefault("module_version", module_meta.version)
        job.params.setdefault("module_method_name", module_meta.method_name)

    experiment_obj.mark_running()
    job.start()
    storage.upsert_experiment(experiment_obj)
    storage.upsert_job(job)

    def _finalize_failure(error_message: str) -> WorkflowResult:
        placeholder = _build_placeholder_dataset(
            module_key,
            label="Module output unavailable",
        )
        placeholder.metadata.update(
            {
                "placeholder_reason": "module_failed",
                "error": error_message,
            }
        )
        storage.save_dataset_record(placeholder, None)
        job.finish(success=False, outputs=[placeholder.id], error=error_message)
        experiment_obj.mark_failed()
        storage.upsert_job(job)
        storage.upsert_experiment(experiment_obj)
        failure_event = log_event_for_job(
            job,
            action="module-run-failed",
            details={
                "module_key": module_key,
                "operation": operation,
                "status": "failed",
                "error": error_message,
                "experiment_id": experiment_obj.id,
                "dataset_id": placeholder.id,
            },
            actor=actor,
        )
        link_event = link_job_to_dataset(job.id, placeholder.id, direction="out")
        return WorkflowResult(
            experiment=experiment_obj,
            job=job,
            dataset=placeholder,
            audit_events=[failure_event, link_event],
            module_output=None,
            error=error_message,
        )

    try:
        raw_output = registry.run(module_key, operation, resolved_params)
    except ModuleExecutionError as exc:
        return _finalize_failure(str(exc))

    if isinstance(raw_output, Mapping):
        module_output: Dict[str, object] = dict(raw_output)
    else:
        module_output = {"result": raw_output}

    dataset_payload = module_output.get("dataset")
    dataset_ref: DatasetRef
    if isinstance(dataset_payload, Mapping):
        dataset_ref = _dataset_from_dict(dataset_payload, module_key=module_key)
    else:
        dataset_ref = _build_placeholder_dataset(module_key)
        dataset_ref.metadata.setdefault("placeholder_reason", "no_dataset_payload")
    storage.save_dataset_record(dataset_ref, dataset_payload)

    job.finish(success=True, outputs=[dataset_ref.id])
    experiment_obj.mark_completed()
    storage.upsert_job(job)
    storage.upsert_experiment(experiment_obj)

    audit_events: List[AuditEvent] = []
    audit_payload = module_output.get("audit")
    if isinstance(audit_payload, Mapping):
        audit_events.append(_audit_from_dict(audit_payload, module_key=module_key, job=job, actor=actor))
    else:
        audit_events.append(
            log_event_for_job(
                job,
                action="module-run",
                details={
                    "module_key": module_key,
                    "operation": operation,
                    "status": "success",
                    "experiment_id": experiment_obj.id,
                    "dataset_id": dataset_ref.id,
                },
                actor=actor,
            )
        )

    audit_events.append(link_job_to_dataset(job.id, dataset_ref.id, direction="out"))
    audit_events.append(
        AuditEvent(
            id=_prefixed_id("AUD-EXP"),
            actor=actor,
            action="attach-job",
            target=experiment_obj.id,
            details={
                "job_id": job.id,
                "dataset_id": dataset_ref.id,
                "module_key": module_key,
                "experiment_id": experiment_obj.id,
            },
        )
    )

    return WorkflowResult(
        experiment=experiment_obj,
        job=job,
        dataset=dataset_ref,
        audit_events=audit_events,
        module_output=module_output,
        error=None,
    )


def create_experiment_with_job(
    *,
    experiment_id: str,
    experiment_name: str,
    job_id: str,
    job_kind: str,
    owner: str = "local-user",
    mode: str = "Lab",
    experiment_metadata: Optional[Dict[str, object]] = None,
    job_params: Optional[Dict[str, object]] = None,
    job_datasets_in: Optional[List[str]] = None,
) -> Tuple[Experiment, Job]:
    """Create a paired ``Experiment`` and ``Job`` with consistent IDs.

    This helper keeps setup code concise for quick prototyping or UI wiring.
    It mirrors the default field choices of the underlying dataclasses while
    allowing overrides for owner/mode/params.
    """

    experiment = Experiment(
        id=experiment_id,
        name=experiment_name,
        owner=owner,
        mode=mode,
        metadata=dict(experiment_metadata or {}),
    )
    storage.upsert_experiment(experiment)

    job = Job(
        id=job_id,
        experiment_id=experiment.id,
        kind=job_kind,
        params=dict(job_params or {}),
        datasets_in=list(job_datasets_in or []),
    )

    experiment.add_job(job.id)
    experiment = storage.upsert_experiment(experiment)
    job = storage.upsert_job(job)
    return experiment, job


def attach_dataset_to_job(job: Job, dataset_id: str, direction: str = "out") -> None:
    """Attach a dataset reference to a job input or output list.

    Args:
        job: Job to be updated.
        dataset_id: Dataset identifier (e.g., ``"DS-001"``).
        direction: "in" or "out" to target ``datasets_in`` or ``datasets_out``.
    """

    if direction not in {"in", "out"}:
        raise ValueError("direction must be either 'in' or 'out'")

    target = job.datasets_in if direction == "in" else job.datasets_out
    if dataset_id not in target:
        target.append(dataset_id)


def log_event_for_job(
    job: Job,
    action: str,
    details: Optional[Dict[str, object]] = None,
    *,
    actor: str = "local-system",
    event_id: Optional[str] = None,
    dataset: Optional[DatasetRef] = None,
) -> AuditEvent:
    """Create an ``AuditEvent`` describing an action against a job.

    If ``event_id`` is not supplied, a timestamp-based identifier is
    generated with the ``AUD-`` prefix to maintain a consistent shape
    with other audit helpers.
    """

    timestamp_ms = int(_utc_now().timestamp() * 1000)
    resolved_event_id = event_id or f"AUD-{timestamp_ms}"

    payload: Dict[str, object] = {"job_id": job.id, "experiment_id": job.experiment_id}
    payload.update(details or {})
    if dataset:
        payload["dataset_id"] = dataset.id

    return AuditEvent(
        id=resolved_event_id,
        actor=actor,
        action=action,
        target=job.id,
        created_at=_utc_now(),
        details=payload,
    )


def _dataset_from_dict(payload: Mapping[str, object], module_key: str | None = None) -> DatasetRef:
    created_at = payload.get("created_at")
    if isinstance(created_at, str):
        try:
            parsed = datetime.fromisoformat(created_at)
        except ValueError:
            parsed = _utc_now()
    else:
        parsed = _utc_now()

    payload_id = payload.get("id")
    if payload_id:
        dataset_id = str(payload_id)
    else:
        dataset_id = f"DS-{uuid4()}"
    return DatasetRef(
        id=dataset_id,
        label=str(payload.get("label", dataset_id)),
        kind=str(payload.get("kind", "table")),
        created_at=parsed,
        path_hint=payload.get("path_hint"),
        metadata=_dataset_metadata_with_module(payload.get("metadata"), module_key),
    )


def _dataset_metadata_with_module(metadata: object, module_key: str | None) -> Dict[str, Any]:
    payload_metadata = dict(metadata or {}) if isinstance(metadata, Mapping) else {}
    if module_key and "module_key" not in payload_metadata:
        payload_metadata["module_key"] = module_key
    return payload_metadata


def _run_import_stub(params: Dict[str, object]) -> Dict[str, object]:
    from importlib import import_module

    stub = import_module("labos.modules.import_wizard.stub")
    return stub.run_import_stub(params)


def run_import_workflow(params: Dict[str, object]) -> Dict[str, object]:
    """Run the import stub and return provenance-aware payloads."""

    module_output = _run_import_stub(params)
    dataset_payload = module_output.get("dataset") or {}
    dataset_ref = _dataset_from_dict(dataset_payload)

    experiment_id = params.get("experiment_id")
    job_id = params.get("job_id")
    provenance = register_import_result(
        str(experiment_id) if experiment_id is not None else None,
        str(job_id) if job_id is not None else None,
        dataset_ref,
    )

    extra_events: List[Dict[str, object]] = provenance.get("audit_events", [])
    audit_records: List[Dict[str, object]] = []
    audit_from_module = module_output.get("audit")
    if isinstance(audit_from_module, dict):
        audit_records.append(audit_from_module)
    audit_records.extend(extra_events)

    return {
        "module_output": module_output,
        "dataset": provenance["dataset"],
        "audit_events": audit_records,
        "links": provenance.get("links", {}),
    }
