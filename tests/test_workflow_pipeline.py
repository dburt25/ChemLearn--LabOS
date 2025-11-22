"""End-to-end workflow coverage for run_module_job outputs and lineage."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from labos.core.experiments import Experiment
from labos.core.jobs import JobStatus
from labos.core.module_registry import ModuleRegistry
from labos.core.workflows import WorkflowResult, create_experiment, run_module_job
from labos.modules.pchem.calorimetry_stub import MODULE_KEY


class WorkflowPipelineTests(unittest.TestCase):
    def _run_calorimetry_workflow(self) -> tuple[WorkflowResult, Experiment, dict[str, object]]:
        experiment = create_experiment(name="Workflow Calorimetry QA", owner="qa.bot")
        params: dict[str, object] = {"sample_id": "CAL-PIPE", "delta_t": 4.2, "heat_capacity": 4.0}
        result = run_module_job(
            module_key=MODULE_KEY,
            params=params,
            actor="workflow-tester",
            experiment=experiment,
        )
        return result, experiment, params

    def test_workflow_lineage_and_metadata(self) -> None:
        result, experiment, params = self._run_calorimetry_workflow()

        self.assertTrue(result.succeeded())
        self.assertEqual(result.job.status, JobStatus.COMPLETED)
        self.assertEqual(result.experiment.id, experiment.id)
        self.assertIn(result.job.id, result.experiment.jobs)
        self.assertEqual(result.job.experiment_id, result.experiment.id)

        dataset = result.dataset
        self.assertIsNotNone(dataset)
        assert dataset is not None
        self.assertIn(dataset.id, result.job.datasets_out)
        self.assertTrue(dataset.label)

        audit_events = result.audit_events
        self.assertGreaterEqual(len(audit_events), 1)
        self.assertTrue(any(event.details.get("module_key") == MODULE_KEY for event in audit_events))
        self.assertTrue(all(hasattr(event, "created_at") for event in audit_events))
        inputs_events = [event for event in audit_events if isinstance(event.details.get("inputs"), dict)]
        if inputs_events:
            for event in inputs_events:
                for key, value in params.items():
                    self.assertEqual(event.details["inputs"].get(key), value)
        else:
            for key, value in params.items():
                self.assertEqual(result.job.params.get(key), value)

        identifiers = [result.experiment.id, result.job.id, dataset.id]
        identifiers.extend(event.id for event in audit_events)
        for identifier in identifiers:
            self.assertIsInstance(identifier, str)
            self.assertGreater(len(identifier), 0)

        experiment_payload = result.experiment.to_dict()
        job_payload = result.job.to_dict()
        dataset_payload = dataset.to_dict()
        audit_payload = audit_events[0].to_dict()

        self.assertTrue({"id", "name", "owner", "mode", "status", "jobs"}.issubset(experiment_payload))
        self.assertTrue({"id", "experiment_id", "kind", "status", "params", "datasets_out"}.issubset(job_payload))
        self.assertTrue({"id", "label", "kind", "metadata"}.issubset(dataset_payload))
        self.assertTrue({"id", "actor", "action", "target", "details"}.issubset(audit_payload))

        registry = ModuleRegistry.with_phase0_defaults()
        self.assertIsNotNone(registry.get(MODULE_KEY))

    def test_run_module_job_completion_smoke(self) -> None:
        result, _, _ = self._run_calorimetry_workflow()

        self.assertTrue(result.succeeded())
        self.assertIsNone(result.error)
        self.assertEqual(result.job.status, JobStatus.COMPLETED)
        self.assertIsNotNone(result.dataset)
        self.assertGreater(len(result.audit_events), 0)

    def test_workflow_result_to_dict_shape(self) -> None:
        result, _, _ = self._run_calorimetry_workflow()

        payload = result.to_dict()
        self.assertEqual(
            set(payload.keys()),
            {"experiment", "job", "dataset", "audit_events", "module_output", "error", "succeeded"},
        )
        self.assertIsInstance(payload["experiment"], dict)
        self.assertIsInstance(payload["job"], dict)
        if payload["dataset"] is not None:
            self.assertIsInstance(payload["dataset"], dict)
        self.assertIsInstance(payload["audit_events"], list)


if __name__ == "__main__":
    unittest.main()
