"""Reusable experiment template registry for LabOS."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from .errors import NotFoundError


@dataclass(slots=True)
class Template:
    """A lightweight experiment template linked to a scientific module."""

    name: str
    description: str
    module_key: str
    default_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return the template metadata as a dictionary."""

        return {
            "name": self.name,
            "description": self.description,
            "module_key": self.module_key,
            "default_params": dict(self.default_params),
        }


class TemplateRegistry:
    """In-memory registry for experiment templates."""

    def __init__(self) -> None:
        self._templates: Dict[str, Template] = {}

    def register(self, template: Template) -> None:
        """Register a single template by its unique name."""

        if not template.name:
            raise ValueError("template requires a non-empty name")
        self._templates[template.name] = template

    def register_many(self, templates: Iterable[Template]) -> None:
        """Register multiple templates in order."""

        for template in templates:
            self.register(template)

    def get(self, name: str) -> Template:
        """Return a template by name or raise ``NotFoundError`` if missing."""

        try:
            return self._templates[name]
        except KeyError as exc:
            raise NotFoundError(f"Experiment template not found for name {name!r}") from exc

    def get_optional(self, name: str) -> Template | None:
        """Return a template by name when present, otherwise ``None``."""

        return self._templates.get(name)

    def list(self) -> List[Template]:
        """Return all registered templates in insertion order."""

        return list(self._templates.values())

    def list_names(self) -> List[str]:
        """Return the names of all registered templates."""

        return [template.name for template in self.list()]

    @classmethod
    def with_defaults(cls) -> "TemplateRegistry":
        """Return a registry populated with Phase 0 starter templates."""

        registry = cls()
        registry.register_many(
            [
                Template(
                    name="pchem.calorimetry.basic",
                    description=(
                        "Baseline constant-pressure calorimetry setup for"
                        " heat capacity estimation with mass and ΔT inputs."
                    ),
                    module_key="pchem.calorimetry",
                    default_params={
                        "sample_mass_g": 1.0,
                        "specific_heat_capacity_j_per_g_c": 4.18,
                        "delta_temp_c": 1.0,
                        "pressure_atm": 1.0,
                    },
                ),
                Template(
                    name="eims.analysis.basic",
                    description=(
                        "Starter electron ionization mass spectrometry analysis"
                        " for fragment prediction and spectral matching."
                    ),
                    module_key="eims.fragmentation",
                    default_params={
                        "precursor_mz": 200.0,
                        "ionization_energy_ev": 70,
                        "resolution": "unit",
                        "match_threshold": 0.6,
                    },
                ),
            ]
        )
        return registry


_DEFAULT_TEMPLATE_REGISTRY: TemplateRegistry | None = None


def get_default_template_registry() -> TemplateRegistry:
    """Return the singleton template registry populated with defaults."""

    global _DEFAULT_TEMPLATE_REGISTRY
    if _DEFAULT_TEMPLATE_REGISTRY is None:
        _DEFAULT_TEMPLATE_REGISTRY = TemplateRegistry.with_defaults()
    return _DEFAULT_TEMPLATE_REGISTRY


def list_templates() -> List[Template]:
    """List all templates from the default registry."""

    return get_default_template_registry().list()


def get_template(name: str) -> Template:
    """Retrieve a template by name from the default registry."""

    return get_default_template_registry().get(name)
