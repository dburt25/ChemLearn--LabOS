import json
from pathlib import Path

import pytest

from labos.core.audit import AuditEvent
from labos.core.datasets import DatasetRef
from labos.core.experiments import Experiment
from labos.core.jobs import Job
from labos.storage import JSONFileStore


def test_jsonfilestore_round_trip_with_validation(tmp_path: Path):
    store = JSONFileStore(tmp_path)
    experiment = Experiment.example(1)

    store.save(experiment.id, experiment.to_dict())

    loaded = store.load_all(Experiment.from_dict)

    assert loaded == [experiment]


def test_jsonfilestore_skips_corrupted_and_partial(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    store = JSONFileStore(tmp_path)
    job = Job.example(1, experiment_id="EXP-001")

    store.save(job.id, job.to_dict())
    store._record_path("broken").write_text("{not-valid", encoding="utf-8")
    store._record_path("partial").write_text(
        json.dumps({"id": "JOB-999", "created_at": job.created_at.isoformat()}),
        encoding="utf-8",
    )

    caplog.set_level("WARNING")
    loaded = store.load_all(Job.from_dict)

    assert loaded == [job]
    assert any("corrupted" in record.message for record in caplog.records)
    assert any("validation" in record.message or "missing" in record.message for record in caplog.records)


def test_from_dict_validators_guard_against_missing_fields():
    assert Experiment.from_dict({}) is None
    assert Job.from_dict({}) is None
    assert DatasetRef.from_dict({}) is None
    assert AuditEvent.from_dict({}) is None
