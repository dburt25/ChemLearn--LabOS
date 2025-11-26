"""Heuristic EI-MS analysis stub for ChemLearn LabOS."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor

MODULE_KEY = "ei_ms.basic_analysis"
MODULE_VERSION = "0.2.0"
METHOD_METADATA = {
    "method_name": "EI-MS basic heuristic analysis",
    "description": (
        "Rule-based EI-MS helper that tags base peaks, minor peaks, and simple "
        "neutral losses without performing physics-based simulations."
    ),
    "version": MODULE_VERSION,
    "limitations": (
        "Heuristic only; deterministic labels without validated predictive power. "
        "Does not model ionization physics, instrument response, or intensity scaling."
    ),
    "citations": [],
}

_COMMON_LOSSES = {
    15.0: "Methyl loss (CH3)",
    18.0: "Water loss (H2O)",
    28.0: "Carbon monoxide loss (CO)",
    31.0: "Methoxy loss (OCH3)",
    43.0: "Acetyl loss (C2H3O)",
    44.0: "Carbon dioxide loss (CO2)",
}
_LOSS_TOLERANCE = 0.5


def _normalize_fragment_masses(fragments: Sequence[Any] | None) -> list[float]:
    if fragments is None:
        return []
    normalized: list[float] = []
    for value in fragments:
        if value is None:
            continue
        try:
            normalized.append(float(value))
        except (TypeError, ValueError):
            continue
    return normalized


def _normalize_intensities(
    intensities: Sequence[Any] | None, count: int, precursor_mass: float, fragment_masses: Sequence[float]
) -> list[float]:
    if intensities is None:
        # Heuristic intensity: scale by mass ratio for deterministic output
        return [round((frag / precursor_mass) * 100, 2) if precursor_mass > 0 else 0.0 for frag in fragment_masses]

    normalized: list[float] = []
    for value in intensities:
        try:
            normalized.append(float(value))
        except (TypeError, ValueError):
            normalized.append(0.0)
    while len(normalized) < count:
        normalized.append(0.0)
    return normalized[:count]


def _detect_neutral_losses(precursor_mass: float, fragment_mass: float) -> list[dict[str, float | str]]:
    if precursor_mass <= 0 or fragment_mass <= 0:
        return []

    loss = precursor_mass - fragment_mass
    if loss <= 0:
        return []

    matches: list[dict[str, float | str]] = []
    for expected_loss, label in _COMMON_LOSSES.items():
        if abs(loss - expected_loss) <= _LOSS_TOLERANCE:
            matches.append({"mass_difference": round(loss, 3), "label": label})
    if not matches:
        matches.append({"mass_difference": round(loss, 3), "label": "Unassigned neutral loss"})
    return matches


def _apply_annotations(fragment_mass: float, annotations: Mapping[Any, Any]) -> str | None:
    for key, note in annotations.items():
        try:
            key_mass = float(key)
        except (TypeError, ValueError):
            continue
        if abs(key_mass - fragment_mass) <= 0.1:
            return str(note)
    return None


def run_ei_ms_analysis(params: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Perform deterministic EI-MS heuristics for quick inspection.

    Parameters
    ----------
    params:
        Input values including ``precursor_mass`` (float), ``fragment_masses`` (list of floats),
        optional ``fragment_intensities`` (list of floats), and ``annotations`` (mapping).

    Returns
    -------
    dict
        Structured analysis with fragment labels, neutral loss suggestions, and metadata.
    """

    payload = dict(params or {})
    precursor_mass = float(payload.get("precursor_mass", 0.0))
    fragment_masses = _normalize_fragment_masses(payload.get("fragment_masses"))
    intensities = _normalize_intensities(
        payload.get("fragment_intensities"), len(fragment_masses), precursor_mass, fragment_masses
    )
    annotations = payload.get("annotations") or {}

    fragments: list[dict[str, Any]] = []
    base_peak_index = 0 if fragment_masses else None
    if intensities and fragment_masses:
        base_peak_index = max(range(len(fragment_masses)), key=intensities.__getitem__)

    base_intensity = intensities[base_peak_index] if base_peak_index is not None else 0.0
    major_threshold = base_intensity * 0.5 if base_intensity > 0 else float("inf")

    for idx, mass in enumerate(fragment_masses):
        rel_intensity = intensities[idx] if idx < len(intensities) else 0.0
        tags: list[str] = ["candidate_fragment"]
        classification = "minor_peak"
        if base_peak_index is not None and idx == base_peak_index and rel_intensity > 0:
            tags.append("base_peak")
            classification = "base_peak"
        elif rel_intensity >= major_threshold and rel_intensity > 0:
            tags.append("major_fragment")
            classification = "major_fragment"
        fragment_annotations = _apply_annotations(mass, annotations)
        neutral_losses = _detect_neutral_losses(precursor_mass, mass)

        fragment_entry: dict[str, Any] = {
            "mass": round(mass, 4),
            "relative_intensity": rel_intensity,
            "classification": classification,
            "labels": tags,
            "neutral_losses": neutral_losses,
        }
        if fragment_annotations:
            fragment_entry["annotation"] = fragment_annotations
        fragments.append(fragment_entry)

    summary_losses: list[dict[str, Any]] = []
    seen_losses: set[float] = set()
    for fragment in fragments:
        for loss in fragment.get("neutral_losses", []):
            loss_mass = float(loss["mass_difference"])
            if loss_mass in seen_losses:
                continue
            seen_losses.add(loss_mass)
            summary_losses.append(loss)

    base_peak_mass = (
        round(fragment_masses[base_peak_index], 4) if base_peak_index is not None else None
    )
    major_fragment_masses = [frag["mass"] for frag in fragments if "major_fragment" in frag["labels"]]

    result = {
        "module_key": MODULE_KEY,
        "status": "ok",
        "method": METHOD_METADATA,
        "inputs": {
            "precursor_mass": precursor_mass,
            "fragment_masses": fragment_masses,
            "fragment_intensities": intensities,
            "annotations": annotations,
        },
        "fragments": fragments,
        "summary": {
            "base_peak_mass": base_peak_mass,
            "major_fragment_masses": major_fragment_masses,
            "neutral_losses": summary_losses,
        },
        "message": "Heuristic-only EI-MS tagging; not validated for experimental planning.",
    }
    return result


def _register() -> None:
    descriptor = ModuleDescriptor(
        module_id=MODULE_KEY,
        version=MODULE_VERSION,
        description=METHOD_METADATA["description"],
    )
    descriptor.register_operation(
        ModuleOperation(
            name="analyze",
            description="Run heuristic EI-MS fragmentation tagging.",
            handler=run_ei_ms_analysis,
        )
    )
    descriptor.register_operation(
        ModuleOperation(
            name="compute",
            description="Alias of analyze for LabOS runtimes expecting 'compute'.",
            handler=run_ei_ms_analysis,
        )
    )
    register_descriptor(descriptor)


_register()

