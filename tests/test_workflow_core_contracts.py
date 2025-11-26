"""Workflow contract tests for Experiment → Job → Dataset → Audit wiring."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from labos.core.experiments import ExperimentStatus
from labos.core.jobs import JobStatus
from labos.core.module_registry import ModuleMetadata, ModuleRegistry
from labos.core.workflows import WorkflowResult, run_module_job
from labos.modules import ModuleDescriptor, ModuleOperation, ModuleRegistry as OperationRegistry
from labos.modules.pchem.calorimetry_stub import MODULE_KEY as CALORIMETRY_KEY


def test_run_module_job_creates_experiment_when_missing() -> None:
    params = {"sample_id": "AUTO-EXP", "delta_t": 3.2, "heat_capacity": 4.0}

    result = run_module_job(module_key=CALORIMETRY_KEY, params=params, actor="workflow-test")

    assert isinstance(result, WorkflowResult)
    assert result.experiment.id.startswith("EXP-")
    assert result.job.experiment_id == result.experiment.id
    assert result.job.status is JobStatus.COMPLETED
    assert result.dataset is not None
    assert result.dataset.id in result.job.datasets_out
    assert any(event.details.get("module_key") == CALORIMETRY_KEY for event in result.audit_events)
    assert any(event.details.get("status") == "success" for event in result.audit_events)


def _build_failing_registry() -> ModuleRegistry:
    def _raise_error(params: dict[str, object]) -> dict[str, object]:  # noqa: ARG001
        raise RuntimeError("boom")

    descriptor = ModuleDescriptor(
        module_id="workflow.failure",
        version="0.0.0",
        description="Always fails",
    )
    descriptor.register_operation(
        ModuleOperation(name="compute", description="fail", handler=_raise_error)
    )
    op_registry = OperationRegistry()
    op_registry.register(descriptor)

    registry = ModuleRegistry(operation_registry=op_registry)
    registry.register(
        ModuleMetadata(
            key="workflow.failure",
            display_name="Failing Module",
            method_name="Always fails",
            primary_citation="n/a",
            category="test",
        )
    )
    return registry


def test_run_module_job_records_failure_and_placeholder_dataset() -> None:
    registry = _build_failing_registry()

    result = run_module_job(
        "workflow.failure",
        params={"value": 1},
        actor="workflow-test",
        module_registry=registry,
    )

    assert not result.succeeded()
    assert result.error is not None and "boom" in result.error
    assert result.job.status is JobStatus.FAILED
    assert result.experiment.status is ExperimentStatus.FAILED
    assert result.dataset is not None
    assert result.dataset.metadata.get("placeholder") is True
    assert result.dataset.metadata.get("placeholder_reason") == "module_failed"
    assert result.dataset.id in result.job.datasets_out
    assert any(event.details.get("status") == "failed" for event in result.audit_events)

