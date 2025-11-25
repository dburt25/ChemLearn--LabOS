"""Workflow lineage regression tests for experiments, jobs, datasets, and audits."""

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
from labos.core.jobs import JobStatus
from labos.core.workflows import WorkflowResult, create_experiment, run_module_job
from labos.modules import get_registry
from labos.modules.eims.fragmentation_stub import MODULE_KEY as EIMS_KEY
from labos.modules.import_wizard.stub import MODULE_KEY as IMPORT_WIZARD_KEY
from labos.modules.pchem.calorimetry_stub import MODULE_KEY as CALORIMETRY_KEY


class WorkflowExperimentLineageTests(unittest.TestCase):
    def test_calorimetry_workflow_emits_dataset_and_audit_metadata(self) -> None:
        experiment = create_experiment(name="Calorimetry lineage", owner="core-workflows")
        params = {"sample_id": "CAL-WF-LINEAGE", "delta_t": 8.2, "heat_capacity": 3.14}

        result = run_module_job(
            module_key=CALORIMETRY_KEY,
            params=params,
            actor="workflow-tests",
            experiment=experiment,
        )

        self.assertIsInstance(result, WorkflowResult)
        self.assertEqual(result.experiment.id, experiment.id)
        self.assertIn(result.job.id, result.experiment.jobs)
        self.assertEqual(result.job.status, JobStatus.COMPLETED)

        dataset = result.dataset
        self.assertIsNotNone(dataset)
        assert dataset is not None
        self.assertIsInstance(dataset, DatasetRef)
        self.assertTrue(dataset.id)
        self.assertNotIn(" ", dataset.id)
        self.assertIn(dataset.id, result.job.datasets_out)
        self.assertEqual(dataset.metadata.get("module_key"), CALORIMETRY_KEY)

        audit_events = result.audit_events
        self.assertGreater(len(audit_events), 0)
        self.assertTrue(all(isinstance(event, AuditEvent) for event in audit_events))
        self.assertTrue(
            any(event.details.get("module_key") == CALORIMETRY_KEY for event in audit_events)
        )
        self.assertTrue(all(isinstance(event.created_at, datetime) for event in audit_events))
        self.assertTrue(all(event.created_at.tzinfo is not None for event in audit_events))

    def test_module_registry_reports_expected_builtin_keys(self) -> None:
        registry = get_registry()
        expected_keys = {CALORIMETRY_KEY, EIMS_KEY, IMPORT_WIZARD_KEY}

        registered_keys = set(registry._modules.keys())
        self.assertTrue(expected_keys.issubset(registered_keys))

        for key in expected_keys:
            with self.subTest(module_key=key):
                descriptor = registry.ensure_module_loaded(key)
                self.assertEqual(descriptor.module_id, key)
                self.assertIn("compute", descriptor.operations)
                operation = registry.get_operation(key, "compute")
                self.assertTrue(callable(operation.handler))


if __name__ == "__main__":
    unittest.main()
