"""Performance and stability stubs for future benchmarking.

These tests intentionally keep the payloads small and time-boxed while
exercising repeated workflows and moderate inline imports to catch obvious
regressions (exceptions, runaway state accumulation) before heavier suites
exist.
"""

from __future__ import annotations

from typing import List
import time

from labos.core.jobs import JobStatus
from labos.core.workflows import create_experiment, run_import_workflow, run_module_job
from labos.modules.eims.fragmentation_stub import MODULE_KEY as EIMS_KEY


def test_repeated_workflow_job_runs_complete_without_errors() -> None:
    """Run a module job several times to surface basic stability issues."""

    start = time.monotonic()
    experiment = create_experiment(name="Perf Repeat", owner="perf-tests")
    dataset_ids: List[str] = []

    for idx in range(5):
        result = run_module_job(
            module_key=EIMS_KEY,
            params={"precursor_mz": 100 + idx, "collision_energy": 10 + idx},
            actor="perf-stubs",
            experiment=experiment,
        )

        assert result.error is None, result.error
        assert result.job.status is JobStatus.COMPLETED
        assert result.dataset is not None
        assert result.dataset.id not in dataset_ids
        dataset_ids.append(result.dataset.id)

    assert len(experiment.jobs) == 5
    assert len(dataset_ids) == 5
    assert time.monotonic() - start < 10


def test_import_workflow_handles_moderate_inline_dataset() -> None:
    """Feed a moderately sized in-memory dataset through the import stub."""

    start = time.monotonic()
    rows = [
        {
            "sample": f"S-{i:03d}",
            "analyte": "demo",
            "value": float(i) / 3.0,
            "units": "a.u.",
            "replicate": i % 5,
        }
        for i in range(250)
    ]

    result = run_import_workflow({"data": rows, "source": "perf://inline", "actor": "perf-stubs"})

    dataset_payload = result.get("dataset", {})
    audit_events = result.get("audit_events", [])
    module_output = result.get("module_output", {})
    schema = module_output.get("schema", {})

    assert dataset_payload
    assert dataset_payload.get("id")
    assert module_output.get("status") == "imported"
    assert schema.get("row_count") == len(rows)
    assert audit_events, "Expected provenance records for import runs"

    preview = module_output.get("preview", {})
    assert preview.get("row_count") == min(5, len(rows))
    assert isinstance(preview.get("rows"), list)
    assert time.monotonic() - start < 10
