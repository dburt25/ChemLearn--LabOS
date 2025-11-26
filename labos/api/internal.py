"""Internal workflow helpers intended for external Python callers."""

from __future__ import annotations

from typing import Iterable, Mapping

from labos.audit import AuditLogger
from labos.config import LabOSConfig
from labos.core.module_registry import ModuleMetadata, get_default_registry
from labos.core.workflows import WorkflowResult, run_module_job
from labos.datasets import DatasetRegistry
from labos.experiments import ExperimentRegistry
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


def run_module_job_api(
    module_key: str,
    params: Mapping[str, object] | None = None,
    *,
    operation: str = "compute",
    actor: str = "labos.api",
) -> WorkflowResult:
    """Execute a module operation through the default workflow helper.

    This wrapper exists for callers who want a narrow surface area without
    importing the broader workflow module. It mirrors ``run_module_job`` while
    keeping the default registry choice stable.
    """

    return run_module_job(
        module_key=module_key,
        operation=operation,
        params=params,
        actor=actor,
        module_registry=get_default_registry(),
    )


def list_modules_api() -> list[ModuleMetadata]:
    """Return registered module metadata entries from the default registry."""

    return get_default_registry().list_metadata()


def list_experiments_api(config: LabOSConfig | None = None) -> Iterable[object]:
    """Yield experiments stored under ``config``'s experiment directory."""

    resolved_config = config or LabOSConfig.load()
    runtime_audit = AuditLogger(resolved_config)
    registry = ExperimentRegistry(resolved_config, runtime_audit)
    for exp_id in registry.list_ids():
        yield registry.get(exp_id)


def list_datasets_api(config: LabOSConfig | None = None) -> Iterable[object]:
    """Yield datasets stored under ``config``'s dataset directory."""

    resolved_config = config or LabOSConfig.load()
    runtime_audit = AuditLogger(resolved_config)
    registry = DatasetRegistry(resolved_config, runtime_audit)
    for dataset_id in registry.list_ids():
        yield registry.get(dataset_id)
