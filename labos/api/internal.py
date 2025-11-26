"""Internal workflow helpers intended for external Python callers."""

from __future__ import annotations

from typing import Mapping

from labos.core.workflows import WorkflowResult, run_module_job
from labos.modules import get_registry as get_operation_registry


def run_pchem_calorimetry(params: Mapping[str, object] | None = None) -> WorkflowResult:
    """Run the placeholder P-Chem calorimetry workflow via the default registry."""

    return run_module_job(
        module_key="pchem.calorimetry",
        operation="compute",
        params=params,
        module_registry=get_operation_registry(),
    )


def run_ei_ms_analysis(params: Mapping[str, object] | None = None) -> WorkflowResult:
    """Execute the EI-MS basic analysis workflow using the registered operation."""

    return run_module_job(
        module_key="ei_ms.basic_analysis",
        operation="analyze",
        params=params,
        module_registry=get_operation_registry(),
    )
