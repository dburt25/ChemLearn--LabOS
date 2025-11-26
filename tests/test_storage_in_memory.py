from labos.core.datasets import DatasetRef
from labos.core.experiments import Experiment
from labos.core.jobs import Job
from labos.core.storage import (
    InMemoryDatasetStore,
    InMemoryExperimentStore,
    InMemoryJobStore,
)


def test_in_memory_dataset_store_round_trip():
    store = InMemoryDatasetStore()
    dataset_ref = DatasetRef.example(1)
    payload = {"rows": [1, 2, 3]}

    saved_id = store.save_dataset(dataset_ref, payload)

    assert saved_id == dataset_ref.id
    assert store.load_dataset(dataset_ref.id) == payload
    assert store.list_datasets() == [dataset_ref.id]


def test_in_memory_experiment_store_round_trip():
    store = InMemoryExperimentStore()
    experiment = Experiment.example(1)

    stored = store.create_experiment(experiment)

    assert stored is experiment
    assert store.get_experiment(experiment.id) is experiment
    assert store.list_experiments() == [experiment]

    experiment.metadata["note"] = "updated"
    assert store.update_experiment(experiment).metadata["note"] == "updated"


def test_in_memory_job_store_register_and_filter():
    experiment_store = InMemoryExperimentStore()
    experiment = Experiment.example(1)
    experiment_store.create_experiment(experiment)
    job_store = InMemoryJobStore(experiments=experiment_store)
    job = Job.example(1, experiment_id=experiment.id)

    stored = job_store.register_job(job)

    assert stored is job
    assert job_store.get_job(job.id) is job
    assert job_store.list_jobs() == [job]
    assert job_store.list_jobs(experiment_id=experiment.id) == [job]
    assert experiment_store.get_experiment(experiment.id).jobs == [job.id]


def test_job_registration_without_experiment_linking():
    experiment = Experiment.example(2)
    job_store = InMemoryJobStore()  # experiment linkage disabled
    job = Job.example(2, experiment_id=experiment.id)

    job_store.register_job(job)

    assert experiment.jobs == []
    assert job_store.list_jobs(experiment_id=experiment.id) == [job]
