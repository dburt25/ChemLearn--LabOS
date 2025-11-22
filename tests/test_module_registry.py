"""Tests covering ModuleRegistry behavior and UI smoke checks."""

from __future__ import annotations

import contextlib
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Mapping, cast
from unittest import mock

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from labos.core.module_registry import ModuleRegistry as MetadataRegistry
from labos.modules import ModuleDescriptor, ModuleOperation, ModuleRegistry, get_registry

if "streamlit" not in sys.modules:  # Provide a stub so control_panel imports without dependency.
    sys.modules["streamlit"] = types.ModuleType("streamlit")

from labos.ui import control_panel


class ModuleRegistryTests(unittest.TestCase):
    def test_descriptor_registration_and_run(self) -> None:
        registry = ModuleRegistry()
        descriptor = ModuleDescriptor(
            module_id="demo.echo",
            version="0.0.1",
            description="Echo stub for testing",
        )

        def _echo(params: Mapping[str, object]) -> dict[str, object]:
            return {"echo": dict(params)}

        descriptor.register_operation(
            ModuleOperation(name="compute", description="Returns params", handler=_echo)
        )
        registry.register(descriptor)
        result: Dict[str, object] = dict(registry.run("demo.echo", "compute", {"value": 42}))
        echo = cast(Mapping[str, object], result["echo"])
        self.assertEqual(echo["value"], 42)

    def test_builtin_stubs_are_loaded(self) -> None:
        registry = get_registry()
        descriptor = registry.ensure_module_loaded("eims.fragmentation")
        self.assertIn("compute", descriptor.operations)


class ModuleMetadataTests(unittest.TestCase):
    def test_phase2_metadata_entries_present(self) -> None:
        registry = MetadataRegistry.with_phase0_defaults()
        required_keys = ["eims.fragmentation", "pchem.calorimetry", "import.wizard"]
        for key in required_keys:
            meta = registry.get(key)
            self.assertIsNotNone(meta, f"missing metadata for {key}")
            assert meta is not None  # for mypy
            self.assertTrue(meta.method_name)
            self.assertTrue(meta.limitations)

    def test_phase2_metadata_fields_are_populated(self) -> None:
        registry = MetadataRegistry.with_phase0_defaults()
        for key in ("eims.fragmentation", "pchem.calorimetry", "import.wizard"):
            meta = registry.get(key)
            self.assertIsNotNone(meta)
            assert meta is not None
            self.assertTrue(meta.display_name.strip())
            self.assertTrue(meta.method_name.strip())
            self.assertTrue(meta.primary_citation.strip())
            self.assertTrue(meta.limitations.strip())
            self.assertTrue(meta.version)


class ControlPanelSmokeTest(unittest.TestCase):
    def test_render_control_panel_smoke(self) -> None:
        dummy_runtime = SimpleNamespace(config=SimpleNamespace(), components=SimpleNamespace())
        class _SessionState(dict):
            def __getattr__(self, name: str) -> Any:
                try:
                    return self[name]
                except KeyError as exc:  # pragma: no cover - mimic streamlit behavior
                    raise AttributeError(name) from exc

            def __setattr__(self, name: str, value: Any) -> None:
                self[name] = value

            def get(self, key: str, default: Any | None = None) -> Any:
                return super().get(key, default)

        session_state = _SessionState(
            runtime=dummy_runtime,
            module_registry=ModuleRegistry(),
            method_metadata_registry=MetadataRegistry.with_phase0_defaults(),
            current_section="Overview",
            mode="Learner",
        )

        class _StreamlitHarness:
            def __init__(self) -> None:
                self.session_state = session_state

            def set_page_config(self, **kwargs: object) -> None:  # pragma: no cover - configuration only
                self.config = kwargs

        dummy_st = _StreamlitHarness()
        mock_overview = mock.Mock()

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(control_panel, "st", dummy_st))
            stack.enter_context(mock.patch.object(control_panel, "_init_session_state", return_value=None))
            stack.enter_context(mock.patch.object(control_panel, "_render_header", return_value=None))
            stack.enter_context(mock.patch.object(control_panel, "_render_sidebar", return_value=None))
            stack.enter_context(mock.patch.object(control_panel, "_render_mode_banner", return_value=None))
            stack.enter_context(mock.patch.object(control_panel, "_render_overview", mock_overview))
            stack.enter_context(mock.patch.object(control_panel, "_render_method_and_data_footer", return_value=None))
            stack.enter_context(mock.patch.object(control_panel, "_load_experiments", return_value=[]))
            stack.enter_context(mock.patch.object(control_panel, "_load_datasets", return_value=[]))
            stack.enter_context(mock.patch.object(control_panel, "_load_jobs", return_value=[]))
            stack.enter_context(mock.patch.object(control_panel, "_load_audit_events", return_value=[]))
            control_panel.render_control_panel()

        mock_overview.assert_called_once()


if __name__ == "__main__":
    unittest.main()
