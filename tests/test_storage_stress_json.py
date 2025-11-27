import json
from pathlib import Path

from labos.config import LabOSConfig
from labos.core.types import DatasetType, ExperimentStatus
from labos.datasets import DatasetRegistry, Dataset
from labos.experiments import ExperimentRegistry, Experiment
from labos.jobs import Job, JobRegistry
from labos.runtime import LabOSRuntime
from labos.ui.control_panel import _load_datasets, _load_experiments, _load_jobs


def _setup_runtime(tmp_path: Path) -> LabOSRuntime:
    config = LabOSConfig.load(root=tmp_path)
    return LabOSRuntime(config)


def _make_job(experiment_id: str, idx: int) -> Job:
    job = Job.create(
        experiment_id=experiment_id,
        module_id="mod",
        operation="op",
        actor="runner",
        parameters={"idx": idx},
    )
    return job


def test_storage_loaders_skip_corrupted_files(tmp_path) -> None:
    runtime = _setup_runtime(tmp_path)
    audit = runtime.components.audit

    exp_registry = ExperimentRegistry(runtime.config, audit)
    dataset_registry = DatasetRegistry(runtime.config, audit)
    job_registry = JobRegistry(runtime.config, audit)

    experiments: list[Experiment] = []
    datasets: list[Dataset] = []

    for idx in range(3):
        exp = Experiment.create(
            user_id="user",
            title=f"exp-{idx}",
            purpose="stress",
            status=ExperimentStatus.DRAFT,
        )
        experiments.append(exp_registry.add(exp))

        dataset = Dataset.create(
            owner="owner",
            dataset_type=DatasetType.EXPERIMENTAL,
            uri=f"s3://bucket/{idx}",
            metadata={"idx": idx},
        )
        datasets.append(dataset_registry.add(dataset))

        job_registry.add(_make_job(exp.record_id, idx))

    corrupted_experiment = runtime.config.experiments_dir / f"{experiments[-1].record_id}.json"
    corrupted_experiment.write_text("{not-json}", encoding="utf-8")

    corrupted_dataset = runtime.config.datasets_dir / f"{datasets[-1].record_id}.json"
    corrupted_dataset.write_text("{not-json}", encoding="utf-8")

    corrupted_job = next(runtime.config.jobs_dir.glob("*.json"))
    corrupted_job.write_text("{not-json}", encoding="utf-8")

    experiments_loaded = _load_experiments(runtime)
    datasets_loaded = _load_datasets(runtime)
    jobs_loaded = _load_jobs(runtime.config)

    assert len(experiments_loaded) == len(experiments) - 1
    assert len(datasets_loaded) == len(datasets) - 1
    assert len(jobs_loaded) == 2

    loaded_titles = {exp.title for exp in experiments_loaded}
    loaded_uris = {ds.uri for ds in datasets_loaded}

    assert experiments[0].title in loaded_titles
    assert datasets[0].uri in loaded_uris

    assert all(isinstance(job, Job) for job in jobs_loaded)
