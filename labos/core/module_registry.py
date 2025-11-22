# labos/core/module_registry.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


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

    key: str                 # e.g. "pchem.calorimetry"
    display_name: str        # e.g. "Calorimetry Calculator"
    method_name: str         # e.g. "Constant-pressure calorimetry"
    primary_citation: str    # free-form for now
    dataset_citations: List[str] = field(default_factory=list)
    limitations: str = "Phase 0 skeleton – not validated for clinical use."
    reference_url: str = ""
    version: str = "0.1.0"

    def to_dict(self) -> Dict[str, str | List[str]]:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "method_name": self.method_name,
            "primary_citation": self.primary_citation,
            "dataset_citations": list(self.dataset_citations),
            "limitations": self.limitations,
            "reference_url": self.reference_url,
            "version": self.version,
        }


class ModuleRegistry:
    """
    In-memory module registry for Phase 0.

    Later:
    - Could be backed by JSON, DB, or configuration files.
    - Tied into UI selectors and provenance indicators.
    """

    def __init__(self) -> None:
        self._modules: Dict[str, ModuleMetadata] = {}

    def register(self, meta: ModuleMetadata) -> None:
        self._modules[meta.key] = meta

    def get(self, key: str) -> Optional[ModuleMetadata]:
        return self._modules.get(key)

    def all(self) -> List[ModuleMetadata]:
        return list(self._modules.values())

    @classmethod
    def with_phase0_defaults(cls) -> "ModuleRegistry":
        registry = cls()
        registry.register(
            ModuleMetadata(
                key="pchem.calorimetry",
                display_name="P-Chem Calorimetry",
                method_name="Constant-pressure heat capacity estimation",
                primary_citation="Placeholder – replace with peer-reviewed thermodynamics reference.",
                dataset_citations=["Phase 0 example dataset only."],
                limitations="Educational and development only. Not validated for clinical decisions.",
                reference_url="https://doi.org/10.0000/placeholder-pchem",
                version="0.1.0",
            )
        )
        registry.register(
            ModuleMetadata(
                key="eims.fragmentation",
                display_name="EI-MS Fragmentation Engine",
                method_name="Rule-based + ML-augmented EI fragmentation",
                primary_citation="Placeholder – insert ACS-style EI-MS reference.",
                dataset_citations=["NIST-like spectral libraries (to be wired later)."],
                reference_url="https://doi.org/10.0000/placeholder-eims",
                version="0.1.0",
            )
        )
        registry.register(
            ModuleMetadata(
                key="import.wizard",
                display_name="Import Wizard",
                method_name="Schema-guided dataset onboarding",
                primary_citation="Placeholder – cite the data ingestion methodology reference.",
                dataset_citations=["Internal onboarding datasets (Phase 2 placeholders)."],
                limitations="Development-only import helper; no real files processed yet.",
                reference_url="https://doi.org/10.0000/placeholder-import",
                version="0.1.0",
            )
        )
        return registry
