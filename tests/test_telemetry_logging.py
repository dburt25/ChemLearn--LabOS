"""Telemetry logging behavior and persistence tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from unittest.mock import mock_open
from uuid import UUID

import pytest

from labos.core.telemetry import TelemetryRecorder


@pytest.fixture
def fixed_datetime() -> datetime:
    """Consistent timestamp to make serialized telemetry deterministic."""

    return datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


@pytest.fixture
def stub_datetime_class(fixed_datetime: datetime):
    """Shim datetime replacement that always returns the fixed timestamp."""

    class _StubDateTime(datetime):  # type: ignore[misc]
        @classmethod
        def now(cls, tz=None):  # noqa: D401
            return fixed_datetime

    return _StubDateTime


@pytest.fixture
def patched_uuid(monkeypatch: pytest.MonkeyPatch):
    """Yield a helper to patch uuid4 with deterministic UUIDs."""

    def _apply(uuid_value: UUID | Iterable[UUID]):
        if isinstance(uuid_value, Iterable):
            sequence = iter(uuid_value)
            monkeypatch.setattr("labos.core.telemetry.uuid4", lambda: next(sequence))
        else:
            monkeypatch.setattr("labos.core.telemetry.uuid4", lambda: uuid_value)

    return _apply


@pytest.fixture
def patched_datetime(monkeypatch: pytest.MonkeyPatch, stub_datetime_class: type[datetime]):
    """Replace telemetry.datetime with a controllable stub for tests."""

    monkeypatch.setattr("labos.core.telemetry.datetime", stub_datetime_class)


def test_log_event_persists_jsonl_without_writing_files(
    monkeypatch: pytest.MonkeyPatch,
    patched_datetime: None,
    patched_uuid,
    fixed_datetime: datetime,
):
    uuid_value = UUID("12345678-1234-5678-1234-567812345678")
    patched_uuid(uuid_value)

    mock_file = mock_open()

    def _fake_open(self, *args, **kwargs):
        return mock_file(*args, **kwargs)

    monkeypatch.setattr(Path, "open", _fake_open)

    recorder = TelemetryRecorder(storage_path=Path("telemetry-test.jsonl"), persist=True)

    event = recorder.log_event("demo_event", {"flag": True})

    assert event.event_id == "TEL-12345678-1234-5678-1234-567812345678"
    assert event.payload == {"flag": True}
    assert event.created_at == fixed_datetime
    assert recorder.events == (event,)

    mock_file.assert_called_once_with("a", encoding="utf-8")
    handle = mock_file()
    expected_payload = {
        "event_id": event.event_id,
        "name": "demo_event",
        "payload": {"flag": True},
        "created_at": fixed_datetime.isoformat(),
    }
    handle.write.assert_called_once_with(json.dumps(expected_payload, sort_keys=True) + "\n")


def test_log_event_accumulates_multiple_calls_without_persisting(
    monkeypatch: pytest.MonkeyPatch, patched_uuid
):
    uuid_values = (
        UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    )
    patched_uuid(uuid_values)

    def _fail_open(*args, **kwargs):
        raise AssertionError("log_event should not attempt file IO when persist is False")

    monkeypatch.setattr(Path, "open", _fail_open)

    recorder = TelemetryRecorder(storage_path=Path("in-memory.jsonl"), persist=False)

    first = recorder.log_event("first", {"idx": 1})
    second = recorder.log_event("second", {"idx": 2})

    assert first.event_id != second.event_id
    assert recorder.events == (first, second)
    assert [event.name for event in recorder.events] == ["first", "second"]

    with pytest.raises(AssertionError):
        Path("should-not-open").open()
