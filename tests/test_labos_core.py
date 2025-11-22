"""Basic smoke tests for LabOS core registries."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Mapping

from labos.audit import AuditLogger
from labos.config import LabOSConfig
from labos.core.types import DatasetType, ExperimentStatus, JobStatus
from labos.datasets import Dataset, DatasetRegistry
from labos.experiments import Experiment, ExperimentRegistry
from labos.jobs import JobRunner
from labos.modules import ModuleDescriptor, ModuleOperation, ModuleRegistry


class LabOSCoreTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config = LabOSConfig.load(self.root)
        self.audit = AuditLogger(self.config)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_dataset_registry_roundtrip(self) -> None:
        registry = DatasetRegistry(self.config, self.audit)
        dataset = Dataset.create(
            owner="owner",
            dataset_type=DatasetType.EXPERIMENTAL,
            uri="s3://demo",
            tags=("demo",),
        )
        registry.add(dataset)
        loaded = registry.get(dataset.record_id)
        self.assertEqual(loaded.owner, "owner")

    def test_experiment_registry(self) -> None:
        registry = ExperimentRegistry(self.config, self.audit)
        experiment = Experiment.create(
            user_id="user",
            title="Titration",
            purpose="demo",
            status=ExperimentStatus.DRAFT,
        )
        registry.add(experiment)
        fetched = registry.get(experiment.record_id)
        self.assertEqual(fetched.title, "Titration")

    def test_job_runner_with_mock_module(self) -> None:
        experiments = ExperimentRegistry(self.config, self.audit)
        experiment = experiments.add(
            Experiment.create(user_id="tester", title="job", purpose="demo")
        )
        modules = ModuleRegistry()
        descriptor = ModuleDescriptor(
            module_id="echo",
            version="0.0.1",
            description="Echo test module",
        )

        def _echo(params: Mapping[str, object]) -> dict[str, object]:
            materialized = {key: value for key, value in params.items()}
            return {"echo": materialized}

        descriptor.register_operation(ModuleOperation(name="echo", description="returns params", handler=_echo))
        modules.register(descriptor)
        runner = JobRunner(self.config, self.audit, modules=modules)
        job = runner.run(
            experiment_id=experiment.record_id,
            module_id="echo",
            operation="echo",
            actor="tester",
            parameters={"value": 1},
        )
        self.assertEqual(job.status, JobStatus.SUCCEEDED)
        self.assertIsNotNone(job.result_path)
        result_path = Path(job.result_path)  # type: ignore[arg-type]
        with result_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(data["echo"]["value"], 1)


if __name__ == "__main__":
    unittest.main()
