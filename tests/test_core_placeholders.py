"""Smoke tests for placeholder core records exported via labos.core."""

from __future__ import annotations

import unittest

from labos.core import AuditEvent, DatasetRef, Experiment, Job, ModuleRegistry


class TestCorePlaceholders(unittest.TestCase):
    def test_examples_construct(self) -> None:
        experiment = Experiment.example()
        job = Job.example(experiment_id=experiment.id)
        dataset = DatasetRef.example()
        audit_event = AuditEvent.example()
        registry = ModuleRegistry.with_phase0_defaults()

        self.assertEqual(experiment.mode, "Lab")
        self.assertEqual(job.experiment_id, experiment.id)
        self.assertTrue(dataset.label.startswith("Example Dataset"))
        self.assertEqual(audit_event.target, "LabOS")
        self.assertGreaterEqual(len(registry.all()), 1)


if __name__ == "__main__":
    unittest.main()
