"""Integration-style tests covering workflow/job lineage and module registry coverage."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from labos.core.audit import AuditEvent
from labos.core.datasets import DatasetRef
from labos.core.experiments import Experiment
from labos.core.jobs import JobStatus
from labos.core.workflows import WorkflowResult, create_experiment, run_module_job
from labos.modules import get_registry
from labos.modules.eims.fragmentation_stub import MODULE_KEY as EIMS_KEY
from labos.modules.pchem.calorimetry_stub import MODULE_KEY as CALORIMETRY_KEY


class WorkflowJobIntegrationTests(unittest.TestCase):
    def test_calorimetry_workflow_attaches_job_and_dataset(self) -> None:
        experiment = create_experiment(name="Calorimetry Workflow", owner="core-tests")
        params = {"sample_id": "CAL-WF", "delta_t": 5.1, "heat_capacity": 4.25}

        result = run_module_job(
            module_key=CALORIMETRY_KEY,
            params=params,
            actor="core-workflows",
            experiment=experiment,
        )

        self.assertIsInstance(result, WorkflowResult)
        self.assertEqual(result.experiment.id, experiment.id)
        self.assertIn(result.job.id, experiment.jobs)
        self.assertEqual(result.job.experiment_id, experiment.id)
        self.assertEqual(result.job.status, JobStatus.COMPLETED)

        dataset = result.dataset
        self.assertIsNotNone(dataset)
        assert dataset is not None
        self.assertIsInstance(dataset, DatasetRef)
        self.assertIn(dataset.id, result.job.datasets_out)
        self.assertEqual(dataset.metadata.get("module_key"), CALORIMETRY_KEY)

        audit_events = result.audit_events
        self.assertGreater(len(audit_events), 0)
        self.assertTrue(all(isinstance(event, AuditEvent) for event in audit_events))
        self.assertTrue(any(event.details.get("module_key") == CALORIMETRY_KEY for event in audit_events))
        self.assertTrue(all(isinstance(event.created_at, datetime) for event in audit_events))

        payload = result.to_dict()
        self.assertTrue({"experiment", "job", "dataset", "audit_events", "module_output", "error", "succeeded"}.issubset(payload.keys()))
        self.assertTrue({"id", "name", "owner", "mode", "status", "jobs"}.issubset(payload["experiment"].keys()))
        self.assertTrue({"id", "experiment_id", "kind", "status", "params", "datasets_out"}.issubset(payload["job"].keys()))
        self.assertTrue({"id", "label", "kind", "metadata"}.issubset(payload["dataset"].keys()))
        first_audit = payload["audit_events"][0]
        self.assertTrue({"id", "actor", "action", "target", "details"}.issubset(first_audit.keys()))

    def test_eims_workflow_uses_module_registry_and_emits_lineage(self) -> None:
        registry = get_registry()
        descriptor = registry.ensure_module_loaded(EIMS_KEY)
        self.assertIn("compute", descriptor.operations)

        experiment = create_experiment(name="EI-MS Workflow", owner="core-tests")
        params = {"precursor_mz": 123.4, "collision_energy": 60.0}

        result = run_module_job(
            module_key=EIMS_KEY,
            params=params,
            actor="core-workflows",
            experiment=experiment,
        )

        self.assertIsInstance(result.experiment, Experiment)
        self.assertEqual(result.job.experiment_id, experiment.id)
        self.assertIn(result.job.id, result.experiment.jobs)
        self.assertEqual(result.job.status, JobStatus.COMPLETED)

        dataset = result.dataset
        self.assertIsNotNone(dataset)
        assert dataset is not None
        self.assertIsInstance(dataset, DatasetRef)
        self.assertIn(dataset.id, result.job.datasets_out)
        self.assertEqual(dataset.metadata.get("module_key"), EIMS_KEY)

        audit_events = result.audit_events
        self.assertGreater(len(audit_events), 0)
        self.assertTrue(any(event.details.get("module_key") == EIMS_KEY for event in audit_events))
        self.assertTrue(all(event.created_at is not None for event in audit_events))

        job_payload = result.job.to_dict()
        dataset_payload = dataset.to_dict()
        self.assertTrue({"id", "experiment_id", "kind", "status", "params", "datasets_out"}.issubset(job_payload.keys()))
        self.assertTrue({"id", "label", "kind", "metadata"}.issubset(dataset_payload.keys()))


if __name__ == "__main__":
    unittest.main()
