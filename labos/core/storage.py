"""Storage abstractions for LabOS data assets.

The goal of this module is to define **interfaces** for persisting
experiments, jobs, and datasets. Implementations can stay in-memory for
now, but the interfaces should make it obvious how to plug in a future
database or object store backend without rewriting call sites.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Protocol, runtime_checkable

from .datasets import DatasetRef
from .experiments import Experiment
from .jobs import Job


@runtime_checkable
class DatasetStore(Protocol):
    """Interface for persisting datasets.

    Only minimal CRUD operations are defined here; schemas, blobs, and
    validation live elsewhere. This protocol mirrors the previous
    ``StorageBackend`` name for backwards compatibility.

    Example:
        >>> class PostgresDatasetStore:
        ...     def save_dataset(self, dataset_ref, content):
        ...         ...  # insert into a table and return the dataset id
        ...     def load_dataset(self, dataset_id):
        ...         ...  # fetch and deserialize payload
        ...     def list_datasets(self):
        ...         ...  # return known identifiers
    """

    def save_dataset(self, dataset_ref: DatasetRef, content: object) -> str:
        """Persist a dataset and return a dataset identifier."""

    def load_dataset(self, dataset_id: str) -> object:
        """Retrieve a dataset by identifier."""

    def list_datasets(self) -> List[str]:
        """Return known dataset identifiers."""


@runtime_checkable
class ExperimentStore(Protocol):
    """Interface for recording experiment metadata.

    Implementations may choose to handle optimistic locking, audit
    trails, or versioning. The in-memory implementation is intentionally
    lightweight and does not copy objects.

    Example:
        >>> class DynamoExperimentStore:
        ...     def create_experiment(self, experiment):
        ...         ...  # put_item in DynamoDB
        ...     def update_experiment(self, experiment):
        ...         ...  # update_item or conditional write
        ...     def get_experiment(self, experiment_id):
        ...         ...  # get_item
        ...     def list_experiments(self):
        ...         ...  # scan or query
    """

    def create_experiment(self, experiment: Experiment) -> Experiment:
        """Persist a new experiment record and return it."""

    def update_experiment(self, experiment: Experiment) -> Experiment:
        """Update an existing experiment and return the stored record."""

    def get_experiment(self, experiment_id: str) -> Experiment:
        """Fetch a single experiment by identifier."""

    def list_experiments(self) -> List[Experiment]:
        """Return all known experiments."""


@runtime_checkable
class JobStore(Protocol):
    """Interface for storing jobs and their lifecycle state.

    Example:
        >>> class MongoJobStore:
        ...     def register_job(self, job):
        ...         ...  # insert_one into a collection
        ...     def update_job(self, job):
        ...         ...  # replace_one by _id
        ...     def get_job(self, job_id):
        ...         ...  # find_one
        ...     def list_jobs(self, experiment_id=None):
        ...         ...  # query by experiment
    """

    def register_job(self, job: Job) -> Job:
        """Persist a new job definition."""

    def update_job(self, job: Job) -> Job:
        """Update the stored representation of a job."""

    def get_job(self, job_id: str) -> Job:
        """Retrieve a single job."""

    def list_jobs(self, experiment_id: str | None = None) -> List[Job]:
        """List jobs, optionally filtering by experiment identifier."""


# Backwards compatibility: previous code referenced ``StorageBackend`` for
# datasets. Keep the alias while nudging new code toward DatasetStore.
StorageBackend = DatasetStore


class NullDatasetStore:
    """Placeholder backend that refuses all dataset storage operations."""

    def save_dataset(self, dataset_ref: DatasetRef, content: object) -> str:  # pragma: no cover - placeholder
        raise NotImplementedError("No dataset storage backend configured")

    def load_dataset(self, dataset_id: str) -> object:  # pragma: no cover - placeholder
        raise NotImplementedError("No dataset storage backend configured")

    def list_datasets(self) -> List[str]:  # pragma: no cover - placeholder
        raise NotImplementedError("No dataset storage backend configured")


class InMemoryDatasetStore:
    """Ephemeral, in-memory storage for datasets.

    This is suitable for unit tests or notebook exploration where
    durability is not required.
    """

    def __init__(self) -> None:
        self._store: Dict[str, object] = {}

    def save_dataset(self, dataset_ref: DatasetRef, content: object) -> str:
        self._store[dataset_ref.id] = content
        return dataset_ref.id

    def load_dataset(self, dataset_id: str) -> object:
        try:
            return self._store[dataset_id]
        except KeyError as exc:  # pragma: no cover - guardrail
            raise KeyError(f"Dataset '{dataset_id}' not found in memory") from exc

    def list_datasets(self) -> List[str]:
        return list(self._store.keys())


class NullExperimentStore:
    """Placeholder backend for experiments."""

    def create_experiment(self, experiment: Experiment) -> Experiment:  # pragma: no cover - placeholder
        raise NotImplementedError("No experiment storage backend configured")

    def update_experiment(self, experiment: Experiment) -> Experiment:  # pragma: no cover - placeholder
        raise NotImplementedError("No experiment storage backend configured")

    def get_experiment(self, experiment_id: str) -> Experiment:  # pragma: no cover - placeholder
        raise NotImplementedError("No experiment storage backend configured")

    def list_experiments(self) -> List[Experiment]:  # pragma: no cover - placeholder
        raise NotImplementedError("No experiment storage backend configured")


class InMemoryExperimentStore:
    """Simple dictionary-backed experiment storage."""

    def __init__(self) -> None:
        self._experiments: Dict[str, Experiment] = {}

    def create_experiment(self, experiment: Experiment) -> Experiment:
        if experiment.id in self._experiments:  # pragma: no cover - guardrail
            raise ValueError(f"Experiment '{experiment.id}' already exists")
        self._experiments[experiment.id] = experiment
        return experiment

    def update_experiment(self, experiment: Experiment) -> Experiment:
        if experiment.id not in self._experiments:  # pragma: no cover - guardrail
            raise KeyError(f"Experiment '{experiment.id}' not found")
        self._experiments[experiment.id] = experiment
        return experiment

    def get_experiment(self, experiment_id: str) -> Experiment:
        try:
            return self._experiments[experiment_id]
        except KeyError as exc:  # pragma: no cover - guardrail
            raise KeyError(f"Experiment '{experiment_id}' not found in memory") from exc

    def list_experiments(self) -> List[Experiment]:
        return list(self._experiments.values())


class NullJobStore:
    """Placeholder backend for jobs."""

    def register_job(self, job: Job) -> Job:  # pragma: no cover - placeholder
        raise NotImplementedError("No job storage backend configured")

    def update_job(self, job: Job) -> Job:  # pragma: no cover - placeholder
        raise NotImplementedError("No job storage backend configured")

    def get_job(self, job_id: str) -> Job:  # pragma: no cover - placeholder
        raise NotImplementedError("No job storage backend configured")

    def list_jobs(self, experiment_id: str | None = None) -> List[Job]:  # pragma: no cover - placeholder
        raise NotImplementedError("No job storage backend configured")


class InMemoryJobStore:
    """Dictionary-backed job store that mirrors current in-memory usage."""

    def __init__(self, *, experiments: ExperimentStore | None = None) -> None:
        self._jobs: Dict[str, Job] = {}
        self._experiments = experiments

    def register_job(self, job: Job) -> Job:
        if job.id in self._jobs:  # pragma: no cover - guardrail
            raise ValueError(f"Job '{job.id}' already exists")
        self._jobs[job.id] = job
        if self._experiments is not None:
            try:
                experiment = self._experiments.get_experiment(job.experiment_id)
                experiment.add_job(job.id)
                self._experiments.update_experiment(experiment)
            except Exception:  # pragma: no cover - optional hook
                # Storage backends can choose to handle linkage differently;
                # in-memory version keeps it best-effort.
                pass
        return job

    def update_job(self, job: Job) -> Job:
        if job.id not in self._jobs:  # pragma: no cover - guardrail
            raise KeyError(f"Job '{job.id}' not found")
        self._jobs[job.id] = job
        return job

    def get_job(self, job_id: str) -> Job:
        try:
            return self._jobs[job_id]
        except KeyError as exc:  # pragma: no cover - guardrail
            raise KeyError(f"Job '{job_id}' not found in memory") from exc

    def list_jobs(self, experiment_id: str | None = None) -> List[Job]:
        jobs: Iterable[Job] = self._jobs.values()
        if experiment_id is not None:
            jobs = (job for job in jobs if job.experiment_id == experiment_id)
        return list(jobs)


# Backwards compatibility: expose prior names so imports continue to work
# during the transition to the new store interfaces.
NullStorageBackend = NullDatasetStore
InMemoryStorageBackend = InMemoryDatasetStore
