from labos.api import internal
from labos.core.workflows import WorkflowResult
from labos.modules import get_registry


def test_run_module_job_api_calorimetry():
    result = internal.run_pchem_calorimetry({"delta_t": 2.5, "sample_id": "API-STUB"})
    assert isinstance(result, WorkflowResult)
    assert result.succeeded()
    assert result.module_output
    assert result.module_output.get("module_key") == "pchem.calorimetry"
    assert result.dataset is not None


def test_list_modules_api_returns_expected_keys():
    registry = get_registry()
    module_keys = list(registry._modules.keys())
    assert "pchem.calorimetry" in module_keys
    assert "ei_ms.basic_analysis" in module_keys
