"""Thermodynamics calculators for physical chemistry.

Implements Gibbs free energy, equilibrium constants, and
van't Hoff equation for temperature-dependent equilibria.
"""

from __future__ import annotations

import math
from typing import Dict


# Constants
R_GAS = 8.314  # J/(mol·K) - Universal gas constant
R_KCAL = 1.987e-3  # kcal/(mol·K) - Gas constant in kcal/mol


def calculate_gibbs_free_energy(
    delta_h: float,
    delta_s: float,
    temperature: float = 298.15,
) -> float:
    """Calculate Gibbs free energy from enthalpy and entropy.
    
    ΔG = ΔH - TΔS
    
    Args:
        delta_h: Enthalpy change in J/mol
        delta_s: Entropy change in J/(mol·K)
        temperature: Temperature in K (default: 298.15 K = 25°C)
        
    Returns:
        Gibbs free energy in J/mol
        
    Example:
        >>> calculate_gibbs_free_energy(100000, 50, 298.15)
        85100  # ΔG = 100000 - 298.15 * 50
    """
    if temperature <= 0:
        raise ValueError("Temperature must be positive (Kelvin scale)")
    
    # All units in J/mol
    delta_g = delta_h - (temperature * delta_s)
    return delta_g


def calculate_equilibrium_constant(
    delta_g: float,
    temperature: float = 298.15,
) -> float:
    """Calculate equilibrium constant from Gibbs free energy.
    
    ΔG° = -RT ln(K)
    K = exp(-ΔG° / RT)
    
    Args:
        delta_g: Standard Gibbs free energy in kJ/mol
        temperature: Temperature in K
        
    Returns:
        Equilibrium constant K (dimensionless)
        
    Example:
        >>> calculate_equilibrium_constant(-5.7, 298.15)
        10.0  # ΔG° = -5.7 kJ/mol gives K = 10
    """
    if temperature <= 0:
        raise ValueError("Temperature must be positive")
    
    # K = exp(-ΔG / RT)
    exponent = -delta_g / (R_GAS * temperature)
    
    # Protect against overflow
    if exponent > 700:
        return float('inf')
    if exponent < -700:
        return 0.0
    
    return math.exp(exponent)


def calculate_delta_g_from_k(
    k_eq: float,
    temperature: float = 298.15,
) -> float:
    """Calculate Gibbs free energy from equilibrium constant.
    
    ΔG° = -RT ln(K)
    
    Args:
        k_eq: Equilibrium constant
        temperature: Temperature in K
        
    Returns:
        Standard Gibbs free energy in J/mol
        
    Example:
        >>> calculate_delta_g_from_k(10.0, 298.15)
        -5704.8  # K = 10 corresponds to ΔG° = -5704.8 J/mol
    """
    if k_eq <= 0:
        raise ValueError("Equilibrium constant must be positive")
    if temperature <= 0:
        raise ValueError("Temperature must be positive")
    
    # ΔG° = -RT ln(K)
    return -R_GAS * temperature * math.log(k_eq)


def vant_hoff_equation(
    k1: float,
    delta_h: float,
    t1: float,
    t2: float,
) -> float:
    """Calculate equilibrium constant at T2 from K at T1 using van't Hoff equation.
    
    ln(K2/K1) = -ΔH°/R * (1/T2 - 1/T1)
    
    Args:
        k1: Equilibrium constant at T1
        delta_h: Standard enthalpy change in J/mol
        t1: First temperature in K
        t2: Second temperature in K
        
    Returns:
        Equilibrium constant K2 at temperature T2
        
    Example:
        >>> vant_hoff_equation(1.0, 298.15, 323.15, 50000)
        # K increases with temperature for endothermic reaction
    """
    if k1 <= 0:
        raise ValueError("K1 must be positive")
    if t1 <= 0 or t2 <= 0:
        raise ValueError("Temperatures must be positive")
    
    # ln(K2/K1) = -ΔH/R * (1/T2 - 1/T1)
    ln_k_ratio = -(delta_h / R_GAS) * (1/t2 - 1/t1)
    
    # Handle overflow/underflow
    if ln_k_ratio > 700:
        return float('inf') if k1 > 0 else 0.0
    elif ln_k_ratio < -700:
        return 0.0
    
    # K2 = K1 * exp(ln_k_ratio)
    k2 = k1 * math.exp(ln_k_ratio)
    
    return k2


def predict_spontaneity(
    delta_g: float | None = None,
    delta_h: float | None = None,
    delta_s: float | None = None,
    temperature: float = 298.15,
) -> Dict[str, object]:
    """Predict reaction spontaneity from thermodynamic quantities.
    
    Args:
        delta_g: Optional Gibbs free energy in J/mol (if not provided, calculated from delta_h and delta_s)
        delta_h: Optional enthalpy in J/mol (for calculation and interpretation)
        delta_s: Optional entropy in J/(mol·K) (for calculation and interpretation)
        temperature: Temperature in K (used for calculation and interpretation)
        
    Returns:
        Dictionary with spontaneity prediction and interpretation
    """
    # Calculate delta_g if not provided
    if delta_g is None:
        if delta_h is not None and delta_s is not None:
            delta_g = calculate_gibbs_free_energy(delta_h, delta_s, temperature)
        else:
            raise ValueError("Must provide either delta_g or both delta_h and delta_s")
    
    is_spontaneous = delta_g < 0
    
    # Generate interpretation
    interpretation = ""
    if delta_h is not None and delta_s is not None:
        if delta_h < 0 and delta_s > 0:
            interpretation = "Spontaneous at all temperatures (ΔH < 0, ΔS > 0)"
        elif delta_h > 0 and delta_s < 0:
            interpretation = "Not spontaneous at any temperature (ΔH > 0, ΔS < 0)"
        elif delta_h < 0 and delta_s < 0:
            interpretation = "Spontaneous at low temperatures (ΔH < 0, ΔS < 0)"
        elif delta_h > 0 and delta_s > 0:
            interpretation = "Spontaneous at high temperatures (ΔH > 0, ΔS > 0)"
    else:
        interpretation = "Spontaneous" if is_spontaneous else "Not spontaneous"
    
    return {
        "delta_g": delta_g,
        "is_spontaneous": is_spontaneous,
        "interpretation": interpretation,
    }


def analyze_temperature_dependence(
    delta_h: float,
    delta_s: float,
    t_start: float = 273,
    t_end: float = 373,
    t_step: float = 10,
) -> Dict[str, object]:
    """Analyze how ΔG changes with temperature.
    
    Args:
        delta_h: Enthalpy change in J/mol
        delta_s: Entropy change in J/(mol·K)
        t_start: Starting temperature in K
        t_end: Ending temperature in K
        t_step: Temperature step in K
        
    Returns:
        Dictionary with temperature series and ΔG values
    """
    temperature_series = []
    temperature = t_start
    
    while temperature <= t_end:
        delta_g = calculate_gibbs_free_energy(delta_h, delta_s, temperature)
        k_eq = calculate_equilibrium_constant(delta_g, temperature)
        is_spontaneous = delta_g < 0
        
        temperature_series.append({
            "temperature": temperature,
            "delta_g": delta_g,
            "k_eq": k_eq,
            "is_spontaneous": is_spontaneous,
        })
        
        temperature += t_step
    
    return {
        "delta_h": delta_h,
        "delta_s": delta_s,
        "temperature_series": temperature_series,
    }


# Module registration
MODULE_KEY = "pchem.thermodynamics"
MODULE_VERSION = "1.0.0"


def compute_thermodynamics(
    delta_h: float | None = None,
    delta_s: float | None = None,
    delta_g: float | None = None,
    k_eq: float | None = None,
    temperature: float = 298.15,
    analyze_temp_dependence: bool = False,
) -> Dict[str, object]:
    """Comprehensive thermodynamics calculator.
    
    Main entry point for module operation. Calculates missing values
    from provided thermodynamic parameters.
    
    Args:
        delta_h: Enthalpy change in kJ/mol
        delta_s: Entropy change in J/(mol·K)
        delta_g: Gibbs free energy in kJ/mol
        k_eq: Equilibrium constant
        temperature: Temperature in K
        analyze_temp_dependence: Whether to analyze temperature dependence
        
    Returns:
        Dictionary with calculated thermodynamic quantities
        
    Example:
        >>> compute_thermodynamics(delta_h=-50.0, delta_s=100.0, temperature=298.15)
        # Calculates ΔG and K from ΔH and ΔS
    """
    result = {"temperature": temperature}
    
    # Calculate ΔG from ΔH and ΔS if available
    if delta_h is not None and delta_s is not None:
        delta_g_calc = calculate_gibbs_free_energy(delta_h, delta_s, temperature)
        result["delta_g"] = delta_g_calc
        result["delta_h"] = delta_h
        result["delta_s"] = delta_s
        
        # Calculate K from ΔG
        k_eq_calc = calculate_equilibrium_constant(delta_g_calc, temperature)
        result["k_eq"] = k_eq_calc
        
        # Spontaneity prediction
        spontaneity_info = predict_spontaneity(delta_g_calc)
        result["is_spontaneous"] = spontaneity_info["is_spontaneous"]
        
        # Temperature dependence analysis
        if analyze_temp_dependence:
            result["temperature_analysis"] = analyze_temperature_dependence(delta_h, delta_s)
    
    # Calculate ΔG from K if provided
    elif k_eq is not None:
        delta_g_calc = calculate_delta_g_from_k(k_eq, temperature)
        result["delta_g"] = delta_g_calc
        result["k_eq"] = k_eq
        spontaneity_info = predict_spontaneity(delta_g_calc)
        result["is_spontaneous"] = spontaneity_info["is_spontaneous"]
    
    # Calculate K from ΔG if provided
    elif delta_g is not None:
        k_eq_calc = calculate_equilibrium_constant(delta_g, temperature)
        result["delta_g"] = delta_g
        result["k_eq"] = k_eq_calc
        spontaneity_info = predict_spontaneity(delta_g)
        result["is_spontaneous"] = spontaneity_info["is_spontaneous"]
    
    else:
        raise ValueError("Must provide either (delta_h, delta_s), k_eq, or delta_g")
    
    return result


def _register() -> None:
    """Register thermodynamics calculations with module system."""
    from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor
    
    descriptor = ModuleDescriptor(
        module_id=MODULE_KEY,
        version=MODULE_VERSION,
        description="Calculate thermodynamic quantities and equilibria",
    )
    
    descriptor.register_operation(
        ModuleOperation(
            name="compute",
            description="Calculate ΔG, K, and temperature dependencies",
            handler=lambda params: compute_thermodynamics(**params),
        )
    )
    
    register_descriptor(descriptor)


# Auto-register on import
_register()
