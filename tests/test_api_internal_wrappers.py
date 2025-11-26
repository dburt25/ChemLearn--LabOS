from types import SimpleNamespace

from labos import api
from labos.audit import AuditLogger
from labos.config import LabOSConfig
from labos.core.types import DatasetType
from labos.datasets import DatasetRegistry, Dataset
from labos.experiments import ExperimentRegistry, Experiment


def test_run_module_job_api_delegates(monkeypatch):
    captured = {}

    def fake_run_module_job(**kwargs):
        captured.update(kwargs)
        return "ok"

    monkeypatch.setattr(api.internal, "run_module_job", fake_run_module_job)
    monkeypatch.setattr(api.internal, "get_default_registry", lambda: "registry")

    result = api.internal.run_module_job_api("pchem.calorimetry", {"delta_t": 1.5})

    assert result == "ok"
    assert captured["module_key"] == "pchem.calorimetry"
    assert captured["params"] == {"delta_t": 1.5}
    assert captured["module_registry"] == "registry"


def test_list_modules_api_uses_default_registry(monkeypatch):
    registry = SimpleNamespace(list_metadata=lambda: ["meta1", "meta2"])
    monkeypatch.setattr(api.internal, "get_default_registry", lambda: registry)

    result = api.internal.list_modules_api()

    assert result == ["meta1", "meta2"]


def test_list_experiments_and_datasets_api(tmp_path):
    config = LabOSConfig.load(tmp_path)
    audit = AuditLogger(config)

    exp_registry = ExperimentRegistry(config, audit)
    exp = exp_registry.add(Experiment.create(user_id="user", title="Demo", purpose="Testing"))

    dataset_registry = DatasetRegistry(config, audit)
    dataset = dataset_registry.add(
        Dataset.create(owner="owner", dataset_type=DatasetType.EXPERIMENTAL, uri="file://dataset")
    )

    experiments = list(api.internal.list_experiments_api(config))
    datasets = list(api.internal.list_datasets_api(config))

    assert any(entry.record_id == exp.record_id for entry in experiments)
    assert any(entry.record_id == dataset.record_id for entry in datasets)
