# labos/core/module_registry.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional

from labos.modules import ModuleRegistry as OperationRegistry
from labos.modules import get_registry as get_operation_registry

from .errors import NotFoundError


@dataclass
class ModuleMetadata:
    """
    Metadata a scientific module must expose.

    This aligns with the long-term plan:
    - Every method/tool has a name, description, citations, and limitations.
    - The UI can show "ⓘ Method & Data" based on this.

    Phase 2:
    - Still an in-memory registry, but enriched with citations/limitations for the UI.
    """

    key: str  # e.g. "pchem.calorimetry"
    display_name: str  # e.g. "Calorimetry Calculator"
    method_name: str  # e.g. "Constant-pressure calorimetry"
    primary_citation: str  # free-form for now
    dataset_citations: List[str] = field(default_factory=list)
    limitations: str = "Educational and development only. Not validated for clinical use."
    reference_url: str = ""
    version: str = "0.1.0"
    category: str = "general"

    def to_dict(self) -> Dict[str, str | List[str]]:
        """Return a shallow copy of the metadata fields as a dictionary."""

        return {
            "key": self.key,
            "display_name": self.display_name,
            "method_name": self.method_name,
            "primary_citation": self.primary_citation,
            "dataset_citations": list(self.dataset_citations),
            "limitations": self.limitations,
            "reference_url": self.reference_url,
            "version": self.version,
            "category": self.category,
        }


class ModuleRegistry:
    """Metadata-aware wrapper around the runtime module registry.

    The runtime registry (``labos.modules``) already knows how to run operations
    and auto-discovers installed packages. This wrapper enriches those entries
    with method metadata and simple search helpers so the rest of the runtime
    can rely on a single abstraction.
    """

    def __init__(self, *, operation_registry: OperationRegistry | None = None) -> None:
        self._modules: Dict[str, ModuleMetadata] = {}
        self._operation_registry = operation_registry or get_operation_registry()

    # ---- Metadata management -------------------------------------------------
    def register(self, meta: ModuleMetadata) -> None:
        """Register a single module's metadata by its key."""

        if not meta.key:
            raise ValueError("module metadata requires a non-empty key")
        self._modules[meta.key] = meta

    def register_many(self, entries: Iterable[ModuleMetadata]) -> None:
        """Register multiple metadata entries in sequence."""

        for meta in entries:
            self.register(meta)

    def get_metadata(self, key: str) -> ModuleMetadata:
        """Return metadata for ``key`` or raise ``NotFoundError`` if missing."""

        try:
            return self._modules[key]
        except KeyError as exc:
            available_keys = ", ".join(sorted(self._modules)) or "<none>"
            raise NotFoundError(
                f"Module metadata not found for key {key!r}. Available keys: {available_keys}"
            ) from exc

    def get_metadata_optional(self, key: str) -> Optional[ModuleMetadata]:
        """Return metadata for ``key`` when present, otherwise ``None``."""

        return self._modules.get(key)

    # Compatibility aliases used by early-phase tests/clients
    def get(self, key: str) -> Optional[ModuleMetadata]:
        """Compatibility alias for :meth:`get_metadata_optional`."""

        return self.get_metadata_optional(key)

    def list_metadata(self) -> List[ModuleMetadata]:
        """Return all registered metadata entries in insertion order."""

        return list(self._modules.values())

    def all(self) -> List[ModuleMetadata]:
        """Compatibility alias for :meth:`list_metadata`."""

        return self.list_metadata()

    def list_keys(self) -> List[str]:
        """Return the keys of all registered metadata entries."""

        return [meta.key for meta in self.list_metadata()]

    def search(self, *, category: Optional[str] = None, name_contains: Optional[str] = None) -> List[ModuleMetadata]:
        """Search metadata entries by category and/or substring match."""

        results: List[ModuleMetadata] = []
        for meta in self._modules.values():
            if category and meta.category.lower() != category.lower():
                continue
            if name_contains and name_contains.lower() not in meta.display_name.lower():
                continue
            results.append(meta)
        return results

    # ---- Operation helpers ---------------------------------------------------
    def get_callable(self, key: str, operation: str = "compute") -> Callable[[dict], dict]:
        """Return the callable registered for ``operation`` on ``key``."""

        operation_record = self._get_operation_record(key, operation)
        return operation_record.handler

    def run(self, key: str, operation: str, params: dict[str, object] | None = None) -> dict[str, object]:
        """Execute ``operation`` for ``key`` using the runtime registry."""

        if params is not None and not isinstance(params, dict):
            raise ValueError(
                "params must be a dictionary of arguments or None; "
                f"received {type(params).__name__}"
            )
        self._get_operation_record(key, operation)
        return dict(self._operation_registry.run(key, operation, params or {}))

    def _get_operation_record(self, key: str, operation: str):
        """Retrieve an operation record and surface missing modules clearly."""

        try:
            return self._operation_registry.get_operation(key, operation)
        except (KeyError, NotFoundError) as exc:
            available_keys = ", ".join(sorted(self._operation_registry._modules)) or "<none>"
            raise NotFoundError(
                f"Module operation not found for key {key!r} and operation {operation!r}. "
                f"Registered module keys: {available_keys}"
            ) from exc

    # ---- Factory helpers -----------------------------------------------------
    @classmethod
    def with_phase0_defaults(
        cls, *, operation_registry: OperationRegistry | None = None
    ) -> "ModuleRegistry":
        registry = cls(operation_registry=operation_registry)
        registry.register_many(
            [
                ModuleMetadata(
                    key="pchem.calorimetry",
                    display_name="P-Chem Calorimetry",
                    method_name="Constant-pressure heat capacity estimation",
                    primary_citation="See CITATIONS.md (P-Chem / Calorimetry / Thermodynamics placeholder).",
                    dataset_citations=["Phase 0 example dataset only."],
                    limitations="Educational and development only. Not validated for clinical use.",
                    reference_url="https://doi.org/10.0000/placeholder-pchem",
                    version="0.1.0",
                    category="pchem",
                ),
                ModuleMetadata(
                    key="eims.fragmentation",
                    display_name="EI-MS Fragmentation Engine",
                    method_name="Rule-based + ML-augmented EI fragmentation",
                    primary_citation="See CITATIONS.md (EI-MS / Mass Spectrometry placeholder).",
                    dataset_citations=["NIST-like spectral libraries (to be wired later)."],
                    limitations="Educational and development only. Not validated for clinical use.",
                    reference_url="https://doi.org/10.0000/placeholder-eims",
                    version="0.1.0",
                    category="mass-spectrometry",
                ),
                ModuleMetadata(
                    key="import.wizard",
                    display_name="Import Wizard",
                    method_name="Schema-guided dataset onboarding",
                    primary_citation="See CITATIONS.md (Data Import / General Data Handling placeholder).",
                    dataset_citations=["Internal onboarding datasets (Phase 2 placeholders)."],
                    limitations=(
                        "Educational and development only. Not validated for clinical use. "
                        "Provenance is stubbed but wired for dataset/audit linkage."
                    ),
                    reference_url="https://doi.org/10.0000/placeholder-import",
                    version="0.1.0",
                    category="data-import",
                ),
            ]
        )
        return registry


# Global metadata-aware registry shared across the runtime.
_DEFAULT_REGISTRY: ModuleRegistry | None = None


def get_default_registry() -> ModuleRegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = ModuleRegistry.with_phase0_defaults()
    return _DEFAULT_REGISTRY
