"""Calorimetry import wizard provenance tests."""

from __future__ import annotations

import pytest

from labos.core import storage
from labos.modules.import_wizard import stub


@pytest.fixture(autouse=True)
def _reset_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LABOS_USE_STORE", "1")
    monkeypatch.setattr(storage, "_ACTIVE_STORES", None)


def test_calorimetry_import_summary_includes_provenance() -> None:
    records = [
        {"Time (s)": 0, "Temp C": 21.5, "heatflow": 0.8},
    ]

    summary = stub.build_calorimetry_import_summary(records, source="labos://wizard-demo")

    dataset = summary["dataset"]
    assert dataset["id"].startswith("DS-CAL-")
    stores = storage.get_active_stores()
    assert stores is not None
    assert dataset["id"] in stores.datasets.list_datasets()

    audit_events = summary["audit_events"]
    assert audit_events, "Expected at least one audit event for calorimetry import"
    assert audit_events[0]["details"].get("module_key") == "import.calorimetry"
