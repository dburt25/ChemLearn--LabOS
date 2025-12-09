"""
Advanced Spectroscopy Module

Comprehensive tools for advanced spectroscopic techniques:
- Raman spectroscopy (vibrational modes, polarizability)
- Fluorescence spectroscopy (emission, quantum yield, quenching)
- Circular dichroism (secondary structure, ellipticity)
- 2D NMR spectroscopy (COSY, HSQC, HMBC correlations)
"""

from .raman import (
    RamanPeak,
    calculate_raman_shift,
    identify_functional_groups,
    calculate_polarizability_derivative,
    analyze_raman_spectrum,
)

from .fluorescence import (
    FluorescenceData,
    calculate_stokes_shift,
    calculate_quantum_yield,
    analyze_quenching,
    calculate_fluorescence_lifetime,
    analyze_fluorescence_spectrum,
)

from .circular_dichroism import (
    CDSpectrum,
    calculate_ellipticity,
    calculate_mean_residue_ellipticity,
    estimate_secondary_structure,
    analyze_protein_stability,
    analyze_cd_spectrum,
)

from .nmr_2d import (
    NMR2DPeak,
    COSYCorrelation,
    identify_cosy_correlations,
    identify_hsqc_correlations,
    identify_hmbc_correlations,
    analyze_2d_nmr,
)

__all__ = [
    # Raman
    "RamanPeak",
    "calculate_raman_shift",
    "identify_functional_groups",
    "calculate_polarizability_derivative",
    "analyze_raman_spectrum",
    
    # Fluorescence
    "FluorescenceData",
    "calculate_stokes_shift",
    "calculate_quantum_yield",
    "analyze_quenching",
    "calculate_fluorescence_lifetime",
    "analyze_fluorescence_spectrum",
    
    # Circular Dichroism
    "CDSpectrum",
    "calculate_ellipticity",
    "calculate_mean_residue_ellipticity",
    "estimate_secondary_structure",
    "analyze_protein_stability",
    "analyze_cd_spectrum",
    
    # 2D NMR
    "NMR2DPeak",
    "COSYCorrelation",
    "identify_cosy_correlations",
    "identify_hsqc_correlations",
    "identify_hmbc_correlations",
    "analyze_2d_nmr",
]
