"""Phase 1 tests to ensure core LabOS objects instantiate cleanly."""

from __future__ import annotations

import unittest

from labos.core.audit import AuditEvent
from labos.core.datasets import DatasetRef
from labos.core.experiments import Experiment
from labos.core.jobs import Job
from labos.core.signature import Signature


class CoreObjectInstantiationTests(unittest.TestCase):
    def test_examples_round_trip_to_dict(self) -> None:
        experiment = Experiment.example(idx=1, mode="Learner")
        job = Job.example(idx=1, experiment_id=experiment.id)
        dataset = DatasetRef.example(idx=2)
        audit_event = AuditEvent.example(idx=3)
        signature = Signature(signer="qa.bot", intent="approve-phase1")

        for obj in (experiment, job, dataset, audit_event, signature):
            payload = obj.to_dict()
            self.assertIsInstance(payload, dict)
            self.assertGreater(len(payload), 0)

    def test_job_attach_signature_updates_dict(self) -> None:
        experiment = Experiment.example(idx=4)
        job = Job.example(idx=5, experiment_id=experiment.id)
        signature = Signature(signer="qa.bot", intent="review")
        job.apply_signature(signature)
        snapshot = job.to_dict()
        self.assertEqual(snapshot["signature"]["signer"], "qa.bot")
        self.assertEqual(job.last_audit_event_id, signature.stub_token)


if __name__ == "__main__":
    unittest.main()
