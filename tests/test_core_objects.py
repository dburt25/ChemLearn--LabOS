"""Phase 2 tests validating core LabOS object lifecycles and registry defaults."""

from __future__ import annotations

import unittest

from labos.core.audit import AuditEvent
from labos.core.datasets import DatasetRef
from labos.core.experiments import Experiment
from labos.core.jobs import Job, JobStatus
from labos.core.module_registry import ModuleRegistry
from labos.core.signature import Signature


class CoreObjectInstantiationTests(unittest.TestCase):
    def test_examples_round_trip_to_dict(self) -> None:
        experiment = Experiment.example(idx=1, mode="Learner")
        job = Job.example(idx=1, experiment_id=experiment.id)
        dataset = DatasetRef.example(idx=2)
        audit_event = AuditEvent.example(idx=3)
        signature = Signature(signer="qa.bot", intent="approve-phase1")

        expectations = {
            Experiment: "EXP-",
            Job: "JOB-",
            DatasetRef: "DS-",
            AuditEvent: "AUD-",
        }

        for obj in (experiment, job, dataset, audit_event, signature):
            payload = obj.to_dict()
            self.assertIsInstance(payload, dict)
            self.assertGreater(len(payload), 0)
            if obj.__class__ in expectations:
                prefix = expectations[obj.__class__]
                self.assertIn("id", payload)
                self.assertTrue(str(payload["id"]).startswith(prefix))

    def test_job_lifecycle_updates_dict(self) -> None:
        experiment = Experiment.example(idx=4)
        job = Job.example(idx=6, experiment_id=experiment.id)
        self.assertEqual(job.status, JobStatus.QUEUED)
        job.start()
        self.assertEqual(job.status, JobStatus.RUNNING)
        job.finish(success=True, outputs=["DS-OUTPUT"])
        snapshot = job.to_dict()
        self.assertEqual(job.status, JobStatus.COMPLETED)
        self.assertIn("datasets_out", snapshot)
        self.assertIn("DS-OUTPUT", snapshot["datasets_out"])

    def test_module_registry_phase0_defaults_present(self) -> None:
        registry = ModuleRegistry.with_phase0_defaults()
        for key in ("eims.fragmentation", "pchem.calorimetry", "import.wizard"):
            meta = registry.get(key)
            self.assertIsNotNone(meta, f"metadata missing for {key}")
            assert meta is not None
            self.assertTrue(meta.display_name)
            self.assertTrue(meta.method_name)
            self.assertTrue(meta.primary_citation)
            self.assertTrue(meta.limitations)


if __name__ == "__main__":
    unittest.main()
