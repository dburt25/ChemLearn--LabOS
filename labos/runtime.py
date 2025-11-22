"""Convenience facade bundling config, audit logger, and registries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from .audit import AuditLogger
from .config import LabOSConfig
from .core.types import DatasetType, ExperimentStatus
from .datasets import Dataset, DatasetRegistry
from .experiments import Experiment, ExperimentRegistry
from .jobs import JobRunner
from .modules import get_registry


@dataclass(slots=True)
class RuntimeComponents:
    config: LabOSConfig
    audit: AuditLogger
    datasets: DatasetRegistry
    experiments: ExperimentRegistry
    jobs: JobRunner


class LabOSRuntime:
    def __init__(self, config: Optional[LabOSConfig] = None) -> None:
        config = config or LabOSConfig.load()
        audit = AuditLogger(config)
        datasets = DatasetRegistry(config, audit)
        experiments = ExperimentRegistry(config, audit)
        jobs = JobRunner(config, audit, modules=get_registry())
        self.components = RuntimeComponents(
            config=config,
            audit=audit,
            datasets=datasets,
            experiments=experiments,
            jobs=jobs,
        )

    @property
    def config(self) -> LabOSConfig:
        return self.components.config

    def ensure_initialized(self) -> None:
        self.config.ensure_directories()

    def create_experiment(
        self,
        *,
        user_id: str,
        title: str,
        purpose: str,
        status: ExperimentStatus = ExperimentStatus.DRAFT,
        inputs: Optional[Mapping[str, str]] = None,
        tags: Optional[Sequence[str]] = None,
    ) -> Experiment:
        experiment = Experiment.create(
            user_id=user_id,
            title=title,
            purpose=purpose,
            status=status,
            inputs=inputs,
            outputs=None,
            tags=tags,
        )
        return self.components.experiments.add(experiment)

    def register_dataset(
        self,
        *,
        owner: str,
        dataset_type: DatasetType,
        uri: str,
        tags: Optional[Sequence[str]] = None,
        metadata: Optional[Mapping[str, object]] = None,
    ) -> Dataset:
        dataset = Dataset.create(owner, dataset_type, uri, tags, metadata)
        return self.components.datasets.add(dataset)

    def run_module_operation(
        self,
        *,
        experiment_id: str,
        module_id: str,
        operation: str,
        actor: str,
        parameters: Mapping[str, object],
    ):
        return self.components.jobs.run(
            experiment_id=experiment_id,
            module_id=module_id,
            operation=operation,
            actor=actor,
            parameters=parameters,
        )
