"""Ensure demo calorimetry fixtures load through JSON-backed registries."""

from __future__ import annotations

import json
from pathlib import Path

from labos.audit import AuditLogger
from labos.config import LabOSConfig
from labos.datasets import DatasetRegistry
from labos.experiments import ExperimentRegistry
from labos.jobs import JobRegistry
from labos.core.types import DatasetType, ExperimentStatus, JobStatus


_REPO_ROOT = Path(__file__).resolve().parents[1]


def _config() -> LabOSConfig:
    return LabOSConfig.load(root=_REPO_ROOT)


def _enum_or_str_value(value: object) -> object:
    return value.value if hasattr(value, "value") else value


def test_demo_experiment_fixture_loads() -> None:
    config = _config()
    registry = ExperimentRegistry(config, AuditLogger(config))

    experiment = registry.get("demo-exp-calorimetry")

    assert experiment.record_id == "demo-exp-calorimetry"
    assert _enum_or_str_value(experiment.status) == ExperimentStatus.ACTIVE.value
    assert experiment.inputs.get("sample_id") == "CAL-DEM-001"
    assert "calorimetry" in experiment.tags


def test_demo_job_fixture_loads_and_links() -> None:
    config = _config()
    registry = JobRegistry(config, AuditLogger(config))

    job = registry.get("demo-job-calorimetry")

    assert job.experiment_id == "demo-exp-calorimetry"
    assert _enum_or_str_value(job.status) == JobStatus.SUCCEEDED.value
    assert job.parameters.get("sample_id") == "CAL-DEM-001"
    assert "demo-dataset-calorimetry" in (job.result_path or "")


def test_demo_dataset_fixture_loads() -> None:
    config = _config()
    registry = DatasetRegistry(config, AuditLogger(config))

    dataset = registry.get("demo-dataset-calorimetry")

    assert dataset.record_id == "demo-dataset-calorimetry"
    assert _enum_or_str_value(dataset.dataset_type) == DatasetType.EXPERIMENTAL.value
    assert dataset.metadata.get("module_key") == "pchem.calorimetry"
    assert "calorimetry" in dataset.tags


def test_demo_audit_log_is_parseable() -> None:
    config = _config()
    audit_path = config.audit_dir / "demo_audit_calorimetry.jsonl"

    assert audit_path.exists()

    events = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(events) >= 2
    assert events[0]["payload"].get("experiment_id") == "demo-exp-calorimetry"
    assert events[-1]["payload"].get("dataset_id") == "demo-dataset-calorimetry"
    assert all(len(event["checksum"]) == 64 for event in events)
