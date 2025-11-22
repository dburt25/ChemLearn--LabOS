"""Tests covering ModuleRegistry behavior and UI smoke checks."""

from __future__ import annotations

import contextlib
import unittest
from types import SimpleNamespace
from typing import Any, Dict, Mapping, cast
from unittest import mock

from labos.modules import ModuleDescriptor, ModuleOperation, ModuleRegistry, get_registry
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
        descriptor = registry.ensure_module_loaded("eims.fragmentation.stub")
        self.assertIn("compute", descriptor.operations)


class ControlPanelSmokeTest(unittest.TestCase):
    def test_render_control_panel_smoke(self) -> None:
        dummy_runtime = SimpleNamespace(config=SimpleNamespace(), components=SimpleNamespace())
        session_state: Dict[str, Any] = {
            "runtime": dummy_runtime,
            "module_registry": ModuleRegistry(),
            "current_section": "Overview",
            "mode": "Learner",
        }

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
