"""Job registry and execution helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Mapping, Optional

from .audit import AuditLogger
from .config import LabOSConfig
from .core.errors import ModuleExecutionError, ValidationError
from .core.types import BaseRecord, JobStatus
from .core.utils import utc_now
from .modules import ModuleRegistry, get_registry
from .storage import JSONFileStore


@dataclass(slots=True)
class Job(BaseRecord):
    experiment_id: str
    module_id: str
    operation: str
    status: JobStatus
    parameters: Mapping[str, object]
    actor: str
    logs: list[str] = field(default_factory=list)
    result_path: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    @classmethod
    def create(
        cls,
        experiment_id: str,
        module_id: str,
        operation: str,
        actor: str,
        parameters: Mapping[str, object],
    ) -> "Job":
        now = utc_now()
        return cls(
            record_id=BaseRecord.new_id(),
            created_at=now,
            updated_at=now,
            experiment_id=experiment_id,
            module_id=module_id,
            operation=operation,
            status=JobStatus.PENDING,
            parameters=dict(parameters),
            actor=actor,
        )


class JobRegistry:
    def __init__(self, config: LabOSConfig, audit: AuditLogger) -> None:
        self.store = JSONFileStore(config.jobs_dir)
        self.audit = audit
        self.config = config

    def add(self, job: Job) -> Job:
        self.store.save(job.record_id, job.to_dict())
        event = self.audit.record(
            event_type="job.created",
            actor=job.actor,
            payload={"job_id": job.record_id, "experiment_id": job.experiment_id},
        )
        job.attach_audit_event(event)
        return job

    def save(self, job: Job, event_type: str) -> Job:
        job.touch()
        self.store.save(job.record_id, job.to_dict())
        event = self.audit.record(
            event_type=event_type,
            actor=job.actor,
            payload={
                "job_id": job.record_id,
                "experiment_id": job.experiment_id,
                "status": job.status.value,
            },
        )
        job.attach_audit_event(event)
        return job

    def get(self, job_id: str) -> Job:
        return Job(**self.store.load(job_id))


class JobRunner:
    """Executes registered module operations while maintaining audit trails."""

    def __init__(self, config: LabOSConfig, audit: AuditLogger, modules: ModuleRegistry | None = None) -> None:
        self.config = config
        self.audit = audit
        self.registry = JobRegistry(config, audit)
        self.modules = modules or get_registry()

    def run(self, *, experiment_id: str, module_id: str, operation: str, actor: str, parameters: Mapping[str, object]) -> Job:
        if not experiment_id:
            raise ValidationError("Experiment ID is required for running a job")
        job = Job.create(experiment_id, module_id, operation, actor, parameters)
        self.registry.add(job)
        job.status = JobStatus.RUNNING
        job.started_at = utc_now()
        self.registry.save(job, "job.running")
        try:
            result = self.modules.run(module_id, operation, parameters)
        except ModuleExecutionError as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
            self.registry.save(job, "job.failed")
            raise
        result_path = self.config.timestamped_path(self.config.jobs_dir, f"job-{job.record_id}")
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        job.status = JobStatus.SUCCEEDED
        job.completed_at = utc_now()
        job.result_path = str(result_path)
        self.registry.save(job, "job.succeeded")
        return job
