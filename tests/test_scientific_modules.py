"""Phase 2 tests for scientific module stubs."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from labos.modules.eims.fragmentation_stub import MODULE_KEY as EIMS_KEY, run_eims_stub
from labos.modules.import_wizard.stub import MODULE_KEY as IMPORT_KEY, run_import_stub
from labos.modules.pchem.calorimetry_stub import MODULE_KEY as PCHEM_KEY, run_calorimetry_stub


def _assert_stub_payload(payload: dict[str, object], expected_key: str) -> None:
    assert payload["module_key"] == expected_key
    assert "dataset" in payload and "audit" in payload

    dataset = payload["dataset"]
    audit = payload["audit"]

    assert isinstance(dataset, dict) and dataset["id"]
    assert dataset.get("metadata", {}).get("module_key") == expected_key
    assert isinstance(audit, dict) and audit["id"] and audit["actor"]


def test_run_eims_stub_returns_dataset_and_audit() -> None:
    payload = run_eims_stub()
    _assert_stub_payload(payload, EIMS_KEY)


def test_run_calorimetry_stub_returns_dataset_and_audit() -> None:
    payload = run_calorimetry_stub()
    _assert_stub_payload(payload, PCHEM_KEY)


def test_run_import_stub_returns_dataset_and_audit() -> None:
    payload = run_import_stub()
    _assert_stub_payload(payload, IMPORT_KEY)

