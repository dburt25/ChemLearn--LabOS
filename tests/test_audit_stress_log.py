import json
from pathlib import Path

from labos.audit import AuditLogger
from labos.config import LabOSConfig
from labos.ui.control_panel import _load_audit_events


def _make_config(tmp_path: Path) -> LabOSConfig:
    return LabOSConfig.load(root=tmp_path)


def test_audit_log_loads_many_entries(tmp_path) -> None:
    config = _make_config(tmp_path)
    logger = AuditLogger(config)
    event_count = 200

    for idx in range(event_count):
        logger.record(
            event_type="test.event",
            actor="tester",
            payload={"index": idx},
        )

    events = _load_audit_events(config, limit=event_count + 10)
    assert len(events) == event_count
    assert all(event.get("event_type") == "test.event" for event in events)


def test_audit_log_skips_corrupted_line(tmp_path) -> None:
    config = _make_config(tmp_path)
    logger = AuditLogger(config)
    event_count = 120

    for idx in range(event_count):
        logger.record(
            event_type="test.event",
            actor="tester",
            payload={"index": idx},
        )

    log_path = next(config.audit_dir.glob("*.jsonl"))
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("not-a-json-line\n")

    events = _load_audit_events(config, limit=event_count + 10)
    assert len(events) == event_count
    assert any(event.get("payload", {}).get("index") == 0 for event in events)
