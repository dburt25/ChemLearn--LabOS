from __future__ import annotations

from labos.ui.control_panel import _run_module_from_ui


def test_run_module_from_ui_calls_workflow_with_parameters(monkeypatch):
    captured: dict[str, object] = {}

    def fake_run_module_job(**kwargs):
        captured.update(kwargs)
        return "workflow-result"

    monkeypatch.setattr("labos.ui.control_panel.run_module_job", fake_run_module_job)

    params = {"delta_t": 1.2, "heat_capacity": 4.18}
    result = _run_module_from_ui(
        "pchem.calorimetry",
        params,
        operation="compute",
        experiment_name="exp-123",
        actor="tester",
    )

    assert result == "workflow-result"
    assert captured["module_key"] == "pchem.calorimetry"
    assert captured["params"] == params
    assert captured["operation"] == "compute"
    assert captured["experiment_name"] == "exp-123"
    assert captured["actor"] == "tester"


def test_run_module_from_ui_defaults_operation_and_actor(monkeypatch):
    captured: dict[str, object] = {}

    def fake_run_module_job(**kwargs):
        captured.update(kwargs)
        return "workflow-result"

    monkeypatch.setattr("labos.ui.control_panel.run_module_job", fake_run_module_job)

    _run_module_from_ui("ei_ms.basic_analysis", {"fragment_masses": [15.0, 43.0]})

    assert captured["module_key"] == "ei_ms.basic_analysis"
    assert captured["operation"] == "compute"
    assert captured["actor"] == "labos.ui"
