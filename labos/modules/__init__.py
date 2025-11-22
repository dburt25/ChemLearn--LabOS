"""Module registration system for scientific plugins."""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field
from typing import Callable, Dict, Mapping

from ..core.errors import ModuleExecutionError, NotFoundError

OperationFunc = Callable[[Mapping[str, object]], Mapping[str, object]]


@dataclass(slots=True)
class ModuleOperation:
    name: str
    description: str
    handler: OperationFunc


@dataclass(slots=True)
class ModuleDescriptor:
    module_id: str
    version: str
    description: str
    operations: Dict[str, ModuleOperation] = field(default_factory=dict)

    def register_operation(self, operation: ModuleOperation) -> None:
        self.operations[operation.name] = operation


class ModuleRegistry:
    """Keeps track of installed modules and their operations."""

    def __init__(self) -> None:
        self._modules: Dict[str, ModuleDescriptor] = {}

    def register(self, descriptor: ModuleDescriptor) -> None:
        self._modules[descriptor.module_id] = descriptor

    def ensure_module_loaded(self, module_id: str) -> ModuleDescriptor:
        try:
            return self._modules[module_id]
        except KeyError as exc:
            raise NotFoundError(f"Module {module_id} is not registered") from exc

    def get_operation(self, module_id: str, operation: str) -> ModuleOperation:
        descriptor = self.ensure_module_loaded(module_id)
        try:
            return descriptor.operations[operation]
        except KeyError as exc:
            raise NotFoundError(f"Operation {operation} missing in module {module_id}") from exc

    def run(self, module_id: str, operation: str, params: Mapping[str, object]) -> Mapping[str, object]:
        op = self.get_operation(module_id, operation)
        try:
            return op.handler(params)
        except Exception as exc:  # pragma: no cover - actual modules provide coverage
            raise ModuleExecutionError(str(exc)) from exc

    def auto_discover(self) -> None:
        """Import modules listed under the LABOS_MODULES env variable."""

        paths = os.getenv("LABOS_MODULES")
        if not paths:
            return
        for path in paths.split(","):
            importlib.import_module(path.strip())


_global_registry: ModuleRegistry | None = None


def get_registry() -> ModuleRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = ModuleRegistry()
        _global_registry.auto_discover()
    return _global_registry


def register_descriptor(descriptor: ModuleDescriptor) -> None:
    get_registry().register(descriptor)


_BUILTIN_STUBS = [
    "labos.modules.eims.fragmentation_stub",
    "labos.modules.pchem.calorimetry_stub",
    "labos.modules.import_wizard.stub",
]

for _stub_path in _BUILTIN_STUBS:
    try:
        importlib.import_module(_stub_path)
    except Exception:
        # We intentionally swallow errors here to avoid breaking bootstrap if a stub
        # module has unmet dependencies; such failures will surface when accessed.
        continue
