"""Lightweight tests for UI mode helpers and data assembly utilities."""

from __future__ import annotations

from labos.core.types import DatasetType
from labos.datasets import Dataset
from labos.jobs import Job
from labos.ui import control_panel


class DummySessionState(dict):
    """Minimal mapping that also exposes attribute access for session state."""

    def __getattr__(self, name: str):
        return self[name]

    def __setattr__(self, name: str, value):
        self[name] = value


class DummyStreamlit:
    def __init__(self, mode: str = "Learner") -> None:
        self.session_state = DummySessionState(mode=mode)


def test_mode_predicates_respect_session_state(monkeypatch):
    stub = DummyStreamlit(mode="Lab")
    monkeypatch.setattr(control_panel, "st", stub)

    assert control_panel.is_lab() is True
    stub.session_state.mode = "Builder"
    assert control_panel.is_builder() is True
    stub.session_state.mode = "Learner"
    assert control_panel.is_learner() is True


def test_internal_mode_flags_exact_match():
    assert control_panel._is_learner("Learner") is True
    assert control_panel._is_lab("Lab") is True
    assert control_panel._is_builder("Builder") is True
    assert control_panel._is_learner("lab") is False


def test_mode_tip_uses_profile_and_fallback(monkeypatch):
    stub = DummyStreamlit(mode="Builder")
    monkeypatch.setattr(control_panel, "st", stub)

    builder_tip = control_panel._mode_tip("overview")
    assert "metadata" in builder_tip.lower()

    stub.session_state.mode = "Unknown"
    learner_tip = control_panel._mode_tip("overview")
    assert learner_tip == control_panel.MODE_PROFILES["Learner"]["tips"]["overview"]


def test_dataset_helpers_extract_metadata():
    dataset = Dataset.create(
        owner="owner",
        dataset_type=DatasetType.EXPERIMENTAL,
        uri="s3://demo",
        metadata={"label": "  Demo dataset  ", "kind": "calorimetry", "schema": {"columns": [1, 2]}},
    )

    assert control_panel._dataset_label(dataset) == "Demo dataset"
    assert control_panel._dataset_kind(dataset) == "calorimetry"
    preview = control_panel._dataset_preview_text(dataset)
    assert "columns" in preview


def test_dataset_kind_falls_back_to_type():
    dataset = Dataset.create(
        owner="owner",
        dataset_type=DatasetType.INFERENCE,
        uri="s3://demo",
        metadata={},
    )

    assert control_panel._dataset_kind(dataset) == DatasetType.INFERENCE.value


def test_job_dataset_ids_handles_multiple_and_single():
    job = Job.create(
        experiment_id="exp-1",
        module_id="mod-1",
        operation="run",
        actor="tester",
        parameters={"dataset_ids": [1, "a"], "dataset_id": "a"},
    )

    assert control_panel._job_dataset_ids(job) == ["1", "a"]


def test_truncate_adds_ellipsis_when_needed():
    long_text = "abc" * 100
    truncated = control_panel._truncate(long_text, length=10)
    assert truncated.endswith("…")
    assert len(truncated) <= 10


def test_mode_tip_defaults_to_learner_when_section_missing(monkeypatch):
    stub = DummyStreamlit(mode="Lab")
    monkeypatch.setattr(control_panel, "st", stub)

    tip = control_panel._mode_tip("nonexistent-section")
    assert tip == ""

    stub.session_state.mode = "Unknown"
    fallback_tip = control_panel._mode_tip("experiments")
    assert "experiment" in fallback_tip.lower()
