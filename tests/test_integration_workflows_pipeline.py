"""Integration coverage for Experiment -> Job -> DatasetRef -> AuditEvent pipelines."""

from __future__ import annotations

from labos.core.audit import AuditEvent
from labos.core.datasets import DatasetRef
from labos.core.jobs import JobStatus
from labos.core.workflows import WorkflowResult, create_experiment, run_module_job
from labos.modules.eims.fragmentation_stub import MODULE_KEY as EIMS_MODULE_KEY
from labos.modules.pchem.calorimetry_stub import MODULE_KEY as PCHEM_MODULE_KEY


def _assert_basic_lineage(result: WorkflowResult, *, module_key: str) -> None:
    experiment = result.experiment
    job = result.job
    dataset = result.dataset
    audit_events = result.audit_events

    assert isinstance(experiment, type(result.experiment))
    assert job.kind.startswith(module_key)
    assert job.experiment_id == experiment.id
    assert job.status is JobStatus.COMPLETED

    assert dataset is not None
    assert isinstance(dataset, DatasetRef)
    assert dataset.id in job.datasets_out
    assert dataset.metadata.get("module_key") == module_key

    assert audit_events, "Expected at least one audit event"
    assert all(isinstance(event, AuditEvent) for event in audit_events)
    assert any(event.details.get("module_key") == module_key for event in audit_events)
    assert any(event.details.get("job_id") == job.id for event in audit_events)


def test_integration_pchem_calorimetry_workflow() -> None:
    experiment = create_experiment(name="PChem calorimetry integration", owner="integration-tests")
    params = {"sample_id": "PCHEM-INT", "delta_t": 2.75, "heat_capacity": 4.12}

    result = run_module_job(
        module_key=PCHEM_MODULE_KEY,
        params=params,
        actor="integration-runner",
        experiment=experiment,
    )

    assert isinstance(result, WorkflowResult)
    assert result.experiment.id == experiment.id
    assert result.job.id in result.experiment.jobs

    _assert_basic_lineage(result, module_key=PCHEM_MODULE_KEY)

    assert result.module_output is not None
    assert result.module_output.get("dataset", {}).get("metadata", {}).get("sample_id") == "PCHEM-INT"
    assert result.module_output.get("audit", {}).get("action") == "simulate-calorimetry"


def test_integration_eims_fragmentation_workflow() -> None:
    experiment = create_experiment(name="EI-MS integration", owner="integration-tests")
    params = {"precursor_mz": 250.5, "collision_energy": 55.0}

    result = run_module_job(
        module_key=EIMS_MODULE_KEY,
        params=params,
        actor="integration-runner",
        experiment=experiment,
    )

    assert isinstance(result, WorkflowResult)
    assert result.experiment.id == experiment.id
    assert result.job.id in result.experiment.jobs

    _assert_basic_lineage(result, module_key=EIMS_MODULE_KEY)

    assert result.module_output is not None
    assert result.module_output.get("dataset", {}).get("kind") == "spectrum"
    assert result.module_output.get("audit", {}).get("action") == "simulate-fragmentation"
