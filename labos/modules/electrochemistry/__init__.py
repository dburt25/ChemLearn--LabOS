"""
Electrochemistry Module

Voltammetry, impedance spectroscopy, electrode kinetics.
"""

from .voltammetry import (
    VoltammogramData,
    calculate_peak_current,
    calculate_diffusion_coefficient,
    analyze_cyclic_voltammetry,
    identify_reversibility,
)

from .impedance import (
    ImpedanceData,
    calculate_impedance_magnitude,
    calculate_phase_angle,
    fit_randles_circuit,
    analyze_nyquist_plot,
)

from .electrode_kinetics import (
    ElectrodeReaction,
    calculate_nernst_potential,
    calculate_butler_volmer_current,
    calculate_exchange_current,
    analyze_tafel_plot,
)

__all__ = [
    # Voltammetry
    "VoltammogramData",
    "calculate_peak_current",
    "calculate_diffusion_coefficient",
    "analyze_cyclic_voltammetry",
    "identify_reversibility",
    
    # Impedance
    "ImpedanceData",
    "calculate_impedance_magnitude",
    "calculate_phase_angle",
    "fit_randles_circuit",
    "analyze_nyquist_plot",
    
    # Electrode Kinetics
    "ElectrodeReaction",
    "calculate_nernst_potential",
    "calculate_butler_volmer_current",
    "calculate_exchange_current",
    "analyze_tafel_plot",
]
