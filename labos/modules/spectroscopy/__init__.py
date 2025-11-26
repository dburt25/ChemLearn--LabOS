"""Spectroscopy module providing lightweight NMR and IR analysis helpers.

The functions defined here are intentionally simple and schema-focused. They are
meant to illustrate expected inputs/outputs and provide a stable contract for
future, more capable implementations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Mapping, MutableMapping, Sequence

from .. import ModuleDescriptor, ModuleOperation, register_descriptor


MODULE_ID = "spectroscopy"
VERSION = "0.2.0"
DESCRIPTION = (
    "Spectroscopy utilities exposing NMR and IR analysis entrypoints with "
    "schema-focused outputs."
)

SpectrumPairs = Iterable[Sequence[float]]


@dataclass
class NMRResult:
    """Result container for :func:`analyze_nmr_spectrum`.

    Attributes
    ----------
    peaks:
        List of detected peaks represented as dictionaries with
        ``shift_ppm``, ``intensity``, and ``annotation`` keys.
    integration_suggestions:
        Human-readable notes about how the detected peaks could be integrated.
    notes:
        Additional stub notes to communicate the simplified nature of the
        analysis.
    """

    peaks: List[Mapping[str, object]] = field(default_factory=list)
    integration_suggestions: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class IRResult:
    """Result container for :func:`analyze_ir_spectrum`.

    Attributes
    ----------
    peaks:
        List of detected IR bands represented as dictionaries with
        ``wavenumber_cm_1``, ``intensity``, and ``annotation`` keys.
    functional_group_hints:
        Human-readable notes suggesting potential functional groups.
    notes:
        Additional stub notes to communicate the simplified nature of the
        analysis.
    """

    peaks: List[Mapping[str, object]] = field(default_factory=list)
    functional_group_hints: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def _normalize_spectrum(
    spectrum: object, x_key: str, y_key: str
) -> List[tuple[float, float]]:
    """Normalize incoming spectral data to a list of ``(x, y)`` pairs.

    The primary representation for spectra in this module is a list of
    ``(x, y)`` pairs, where *x* is the axis value (ppm for NMR, cm⁻¹ for IR)
    and *y* is the corresponding intensity/absorbance. For convenience, a
    mapping with parallel arrays under ``x_key`` and ``y_key`` is also
    accepted.
    """

    if isinstance(spectrum, Mapping):
        xs = spectrum.get(x_key) or []
        ys = spectrum.get(y_key) or []
        return [(float(x), float(y)) for x, y in zip(xs, ys)]

    if spectrum is None:
        return []

    return [(float(pair[0]), float(pair[1])) for pair in spectrum]  # type: ignore[index]


def analyze_nmr_spectrum(
    spectrum: SpectrumPairs | Mapping[str, object], params: Mapping[str, object] | None = None
) -> NMRResult:
    """Analyze a simple NMR spectrum and return peak annotations.

    Parameters
    ----------
    spectrum:
        Preferred representation is a list of ``(ppm, intensity)`` pairs. A
        mapping with ``{"ppm": [...], "intensity": [...]}`` is also accepted
        and will be normalized to pairs internally.
    params:
        Optional mapping of analysis settings. Recognized keys:
        - ``threshold`` (float): minimum intensity required to report a peak.
          Defaults to ``0.2``.
        - ``aromatic_window`` (tuple[float, float]): ppm window that should be
          annotated as potentially aromatic. Defaults to ``(6.0, 8.5)``.

    Returns
    -------
    NMRResult
        Dataclass containing detected peaks, integration suggestions, and
        notes. The analysis is intentionally educational and deterministic
        rather than physically rigorous.
    """

    params = dict(params or {})
    threshold = float(params.get("threshold", 0.2))
    aromatic_window = params.get("aromatic_window", (6.0, 8.5))
    try:
        aromatic_min, aromatic_max = (float(aromatic_window[0]), float(aromatic_window[1]))
    except Exception:  # pragma: no cover - defensive fallback
        aromatic_min, aromatic_max = 6.0, 8.5

    normalized = _normalize_spectrum(spectrum, "ppm", "intensity")

    peaks: List[Mapping[str, object]] = []
    for shift_ppm, intensity in normalized:
        if intensity < threshold:
            continue

        annotation = "above threshold"
        if aromatic_min <= shift_ppm <= aromatic_max:
            annotation = "within aromatic window"

        peaks.append(
            {
                "shift_ppm": shift_ppm,
                "intensity": intensity,
                "annotation": annotation,
            }
        )

    integration_suggestions: List[str] = []
    if peaks:
        integration_suggestions.append(
            f"Detected {len(peaks)} candidate peaks above threshold {threshold:.2f}."
        )
    else:
        integration_suggestions.append("No peaks exceeded the reporting threshold.")

    notes = [
        "This NMR analysis is intentionally lightweight and deterministic.",
        "Use the annotated peaks as guidance for more advanced pipelines.",
    ]

    return NMRResult(peaks=peaks, integration_suggestions=integration_suggestions, notes=notes)


def analyze_ir_spectrum(
    spectrum: SpectrumPairs | Mapping[str, object], params: Mapping[str, object] | None = None
) -> IRResult:
    """Analyze a simple IR spectrum and return band annotations.

    Parameters
    ----------
    spectrum:
        Preferred representation is a list of ``(wavenumber_cm_1, intensity)``
        pairs. A mapping with ``{"wavenumber": [...], "absorbance": [...]}``
        is also accepted and will be normalized to pairs internally.
    params:
        Optional mapping of analysis settings. Recognized keys:
        - ``threshold`` (float): minimum intensity required to report a band.
          Defaults to ``0.3``.
        - ``carbonyl_window`` (tuple[float, float]): wavenumber window flagged
          as potentially carbonyl. Defaults to ``(1650.0, 1750.0)`` cm⁻¹.

    Returns
    -------
    IRResult
        Dataclass containing detected peaks, functional group hints, and notes.
        The analysis is intentionally educational and deterministic rather than
        a full spectral interpretation.
    """

    params = dict(params or {})
    threshold = float(params.get("threshold", 0.3))
    carbonyl_window = params.get("carbonyl_window", (1650.0, 1750.0))
    try:
        carbonyl_min, carbonyl_max = (float(carbonyl_window[0]), float(carbonyl_window[1]))
    except Exception:  # pragma: no cover - defensive fallback
        carbonyl_min, carbonyl_max = 1650.0, 1750.0

    normalized = _normalize_spectrum(spectrum, "wavenumber", "absorbance")

    peaks: List[Mapping[str, object]] = []
    functional_group_hints: List[str] = []

    for wavenumber_cm_1, intensity in normalized:
        if intensity < threshold:
            continue

        annotation = "above threshold"
        if carbonyl_min <= wavenumber_cm_1 <= carbonyl_max:
            annotation = "within carbonyl window"
            functional_group_hints.append("Possible carbonyl stretch detected.")

        peaks.append(
            {
                "wavenumber_cm_1": wavenumber_cm_1,
                "intensity": intensity,
                "annotation": annotation,
            }
        )

    if not functional_group_hints:
        functional_group_hints.append("No functional group hints generated.")

    notes = [
        "This IR analysis is intentionally lightweight and deterministic.",
        "Use the annotated bands as guidance for more advanced pipelines.",
    ]

    return IRResult(peaks=peaks, functional_group_hints=functional_group_hints, notes=notes)


def run_nmr_stub(params: Mapping[str, object]) -> MutableMapping[str, object]:
    """Backward-compatible stub that delegates to :func:`analyze_nmr_spectrum`.

    The legacy stub accepted a mapping with ``peak_list`` entries. Each entry
    may contain ``shift_ppm`` and ``intensity`` fields. These are normalized and
    passed through the new analysis routine while preserving echoed inputs and
    metadata that downstream consumers may rely on.
    """

    peak_pairs = []
    for peak in params.get("peak_list", []) or []:
        shift = peak.get("shift_ppm") if isinstance(peak, Mapping) else None
        intensity = peak.get("intensity") if isinstance(peak, Mapping) else None
        if shift is None or intensity is None:
            continue
        peak_pairs.append((shift, intensity))

    result = analyze_nmr_spectrum(peak_pairs, params)

    return {
        "method_name": "spectroscopy.nmr_stub",
        "description": "NMR spectroscopy analysis stub with schema guidance.",
        "stub": True,
        "annotated_peaks": result.peaks,
        "notes": result.notes,
        "metadata": {
            "module_id": MODULE_ID,
            "version": VERSION,
            "nucleus": params.get("nucleus"),
        },
        "received_params": dict(params),
        "integration_suggestions": result.integration_suggestions,
    }


def run_ir_stub(params: Mapping[str, object]) -> MutableMapping[str, object]:
    """Backward-compatible stub that delegates to :func:`analyze_ir_spectrum`.

    The legacy stub accepted a mapping with ``peak_list`` entries. Each entry
    may contain ``wavenumber_cm_1`` and ``intensity`` fields. These are
    normalized and passed through the new analysis routine while preserving
    echoed inputs and metadata that downstream consumers may rely on.
    """

    peak_pairs = []
    for peak in params.get("peak_list", []) or []:
        wavenumber = peak.get("wavenumber_cm_1") if isinstance(peak, Mapping) else None
        intensity = peak.get("intensity") if isinstance(peak, Mapping) else None
        if wavenumber is None or intensity is None:
            continue
        peak_pairs.append((wavenumber, intensity))

    result = analyze_ir_spectrum(peak_pairs, params)

    return {
        "method_name": "spectroscopy.ir_stub",
        "description": "IR spectroscopy analysis stub with schema guidance.",
        "stub": True,
        "annotated_peaks": result.peaks,
        "notes": result.notes,
        "metadata": {
            "module_id": MODULE_ID,
            "version": VERSION,
            "chemical_formula": params.get("chemical_formula"),
        },
        "received_params": dict(params),
        "functional_group_hints": result.functional_group_hints,
    }


descriptor = ModuleDescriptor(
    module_id=MODULE_ID,
    version=VERSION,
    description=DESCRIPTION,
)

descriptor.register_operation(
    ModuleOperation(
        name="analyze_nmr_spectrum",
        description="Entrypoint for lightweight NMR spectrum analysis.",
        handler=analyze_nmr_spectrum,
    )
)


descriptor.register_operation(
    ModuleOperation(
        name="analyze_ir_spectrum",
        description="Entrypoint for lightweight IR spectrum analysis.",
        handler=analyze_ir_spectrum,
    )
)


descriptor.register_operation(
    ModuleOperation(
        name="nmr_stub",
        description="Legacy stub entrypoint for NMR spectroscopy analysis.",
        handler=run_nmr_stub,
    )
)

descriptor.register_operation(
    ModuleOperation(
        name="ir_stub",
        description="Legacy stub entrypoint for IR spectroscopy analysis.",
        handler=run_ir_stub,
    )
)

register_descriptor(descriptor)

__all__ = [
    "NMRResult",
    "IRResult",
    "analyze_nmr_spectrum",
    "analyze_ir_spectrum",
    "run_nmr_stub",
    "run_ir_stub",
]
