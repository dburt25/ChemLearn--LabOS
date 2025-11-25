"""Spectroscopy stub module providing placeholder NMR and IR analysis entrypoints.

The functions defined here deliberately avoid heavy computation while exposing
rich schemas and metadata. They act as a contract for future implementations.
"""
from __future__ import annotations

from typing import Mapping, MutableMapping

from .. import ModuleDescriptor, ModuleOperation, register_descriptor


MODULE_ID = "spectroscopy"
VERSION = "0.1.0"
DESCRIPTION = (
    "Stub spectroscopy module exposing NMR and IR analysis entrypoints with "
    "schema-focused outputs."
)


def run_nmr_stub(params: Mapping[str, object]) -> MutableMapping[str, object]:
    """Stub NMR analysis returning schemas and echoed inputs.

    Expected input structure (not validated in depth):
    - sample_id: Optional identifier string for traceability.
    - chemical_formula: Molecular formula string (e.g., "C8H10N4O2").
    - nucleus: Observed nucleus label (e.g., "1H", "13C").
    - solvent: Acquisition solvent (e.g., "CDCl3").
    - peak_list: List of peaks with chemical shift and optional metadata.
        Example entry:
        {
            "shift_ppm": 7.12,
            "intensity": 0.8,
            "multiplicity": "d",
            "coupling_constants": [8.4],
            "integration": 1.0,
            "notes": "aromatic proton"
        }
    - acquisition: Optional mapping of acquisition parameters such as frequency,
      temperature, pulse program, or number of scans.
    """

    peak_schema = {
        "shift_ppm": "Chemical shift in ppm (float)",
        "intensity": "Relative intensity or arbitrary units (float)",
        "multiplicity": "Signal multiplicity string (s, d, t, q, m, br, etc.)",
        "coupling_constants": "List of J values in Hz (list[float])",
        "integration": "Relative integration value (float)",
        "notes": "Optional free-form annotation for the peak",
    }

    output_schema = {
        "method_name": "Identifier for the stub method (string)",
        "stub": "Boolean flag indicating placeholder behavior",
        "received_params": "Echo of provided inputs for traceability",
        "annotated_peaks": "List of peaks enriched with placeholder annotations",
        "notes": "High-level notes about stub limitations",
        "metadata": "Additional metadata such as version and nucleus",
    }

    annotated_peaks = []
    for idx, peak in enumerate(params.get("peak_list", []) or []):
        annotated_peaks.append(
            {
                "index": idx,
                "original": peak,
                "annotation": "Stub peak annotation — replace with real logic later.",
            }
        )

    return {
        "method_name": "spectroscopy.nmr_stub",
        "description": "NMR spectroscopy analysis stub with schema guidance.",
        "stub": True,
        "input_schema": {
            "sample_id": "Optional unique sample identifier (string)",
            "chemical_formula": "Molecular formula for the analyte (string)",
            "nucleus": "Observed nucleus label such as '1H' or '13C' (string)",
            "solvent": "Acquisition solvent (string)",
            "peak_list": peak_schema,
            "acquisition": "Optional acquisition parameters mapping",
        },
        "output_schema": output_schema,
        "annotated_peaks": annotated_peaks,
        "notes": [
            "This is a stub with no spectral interpretation or validation.",
            "Use the schemas to shape real implementations and data contracts.",
        ],
        "metadata": {
            "module_id": MODULE_ID,
            "version": VERSION,
            "nucleus": params.get("nucleus"),
        },
        "received_params": dict(params),
    }


def run_ir_stub(params: Mapping[str, object]) -> MutableMapping[str, object]:
    """Stub IR analysis returning schemas and echoed inputs.

    Expected input structure (not validated in depth):
    - sample_id: Optional identifier string for traceability.
    - chemical_formula: Molecular formula string.
    - peak_list: List of IR bands with position and optional metadata.
        Example entry:
        {
            "wavenumber_cm_1": 1710,
            "intensity": "strong",
            "assignment": "C=O stretch",
            "confidence": 0.6,
            "notes": "placeholder assignment"
        }
    - instrument: Optional mapping of instrument settings (resolution, source,
      detector, beam splitter, number of scans, atmosphere, etc.).
    - processing: Optional mapping of processing flags (baseline_correction,
      smoothing, ATR correction details, etc.).
    """

    peak_schema = {
        "wavenumber_cm_1": "Band position in cm^-1 (number)",
        "intensity": "Qualitative or quantitative intensity (string|float)",
        "assignment": "Tentative functional group assignment (string)",
        "confidence": "Confidence score for assignment between 0-1 (float)",
        "notes": "Optional free-form annotation",
    }

    output_schema = {
        "method_name": "Identifier for the stub method (string)",
        "stub": "Boolean flag indicating placeholder behavior",
        "received_params": "Echo of provided inputs for traceability",
        "annotated_peaks": "List of bands enriched with placeholder annotations",
        "notes": "High-level notes about stub limitations",
        "metadata": "Additional metadata such as version and formula",
    }

    annotated_peaks = []
    for idx, peak in enumerate(params.get("peak_list", []) or []):
        annotated_peaks.append(
            {
                "index": idx,
                "original": peak,
                "annotation": "Stub IR annotation — add interpretation later.",
            }
        )

    return {
        "method_name": "spectroscopy.ir_stub",
        "description": "IR spectroscopy analysis stub with schema guidance.",
        "stub": True,
        "input_schema": {
            "sample_id": "Optional unique sample identifier (string)",
            "chemical_formula": "Molecular formula for the analyte (string)",
            "peak_list": peak_schema,
            "instrument": "Optional instrument settings mapping",
            "processing": "Optional processing metadata mapping",
        },
        "output_schema": output_schema,
        "annotated_peaks": annotated_peaks,
        "notes": [
            "This is a stub with no vibrational mode identification.",
            "Use the schemas as contracts for future IR pipelines.",
        ],
        "metadata": {
            "module_id": MODULE_ID,
            "version": VERSION,
            "chemical_formula": params.get("chemical_formula"),
        },
        "received_params": dict(params),
    }


descriptor = ModuleDescriptor(
    module_id=MODULE_ID,
    version=VERSION,
    description=DESCRIPTION,
)

descriptor.register_operation(
    ModuleOperation(
        name="nmr_stub",
        description="Stub entrypoint for NMR spectroscopy analysis contracts.",
        handler=run_nmr_stub,
    )
)

descriptor.register_operation(
    ModuleOperation(
        name="ir_stub",
        description="Stub entrypoint for IR spectroscopy analysis contracts.",
        handler=run_ir_stub,
    )
)

register_descriptor(descriptor)
