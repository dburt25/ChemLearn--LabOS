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
        delta_h: Enthalpy change in kJ/mol
        delta_s: Entropy change in J/(mol·K)
        temperature: Temperature in K (default: 298.15 K = 25°C)
        
    Returns:
        Gibbs free energy in kJ/mol
        
    Example:
        >>> calculate_gibbs_free_energy(-285.8, 163.2, 298.15)
        -334.4  # Combustion of hydrogen is spontaneous
    """
    if temperature <= 0:
        raise ValueError("Temperature must be positive (Kelvin scale)")
    
    # Convert entropy to kJ/(mol·K) for consistent units
    delta_s_kj = delta_s / 1000.0
    
    delta_g = delta_h - (temperature * delta_s_kj)
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
    
    # Convert ΔG from kJ/mol to J/mol
    delta_g_j = delta_g * 1000.0
    
    # K = exp(-ΔG / RT)
    exponent = -delta_g_j / (R_GAS * temperature)
    
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
        Standard Gibbs free energy in kJ/mol
        
    Example:
        >>> calculate_delta_g_from_k(10.0, 298.15)
        -5.7  # K = 10 corresponds to ΔG° = -5.7 kJ/mol
    """
    if k_eq <= 0:
        raise ValueError("Equilibrium constant must be positive")
    if temperature <= 0:
        raise ValueError("Temperature must be positive")
    
    # ΔG° = -RT ln(K)
    delta_g_j = -R_GAS * temperature * math.log(k_eq)
    
    # Convert to kJ/mol
    return delta_g_j / 1000.0


def vant_hoff_equation(
    k1: float,
    t1: float,
    t2: float,
    delta_h: float,
) -> float:
    """Calculate equilibrium constant at T2 from K at T1 using van't Hoff equation.
    
    ln(K2/K1) = -ΔH°/R * (1/T2 - 1/T1)
    
    Args:
        k1: Equilibrium constant at T1
        t1: First temperature in K
        t2: Second temperature in K
        delta_h: Standard enthalpy change in kJ/mol
        
    Returns:
        Equilibrium constant K2 at temperature T2
        
    Example:
        >>> vant_hoff_equation(1.0, 298.15, 323.15, 50.0)
        # K increases with temperature for endothermic reaction
    """
    if k1 <= 0:
        raise ValueError("K1 must be positive")
    if t1 <= 0 or t2 <= 0:
        raise ValueError("Temperatures must be positive")
    
    # Convert ΔH to J/mol
    delta_h_j = delta_h * 1000.0
    
    # ln(K2/K1) = -ΔH/R * (1/T2 - 1/T1)
    ln_k_ratio = -(delta_h_j / R_GAS) * (1/t2 - 1/t1)
    
    # K2 = K1 * exp(ln_k_ratio)
    k2 = k1 * math.exp(ln_k_ratio)
    
    return k2


def predict_spontaneity(delta_g: float) -> Dict[str, object]:
    """Predict reaction spontaneity from ΔG.
    
    Args:
        delta_g: Gibbs free energy in kJ/mol
        
    Returns:
        Dictionary with spontaneity prediction and interpretation
    """
    if delta_g < -10:
        spontaneity = "spontaneous"
        interpretation = "Reaction strongly favors products"
    elif delta_g < 0:
        spontaneity = "spontaneous"
        interpretation = "Reaction favors products"
    elif delta_g == 0:
        spontaneity = "equilibrium"
        interpretation = "Reaction at equilibrium"
    elif delta_g < 10:
        spontaneity = "non-spontaneous"
        interpretation = "Reaction slightly favors reactants"
    else:
        spontaneity = "non-spontaneous"
        interpretation = "Reaction strongly favors reactants"
    
    return {
        "delta_g": delta_g,
        "spontaneity": spontaneity,
        "interpretation": interpretation,
    }


def predict_spontaneity(
    delta_g: float,
    delta_h: float | None = None,
    delta_s: float | None = None,
) -> Dict[str, object]:
    """Predict reaction spontaneity from thermodynamic quantities.
    
    Args:
        delta_g: Gibbs free energy in J/mol
        delta_h: Optional enthalpy in J/mol (for interpretation)
        delta_s: Optional entropy in J/(mol·K) (for interpretation)
        
    Returns:
        Dictionary with spontaneity prediction and interpretation
    """
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
    temp_range: tuple[float, float] = (250, 400),
    num_points: int = 10,
) -> Dict[str, object]:
    """Analyze how ΔG and K vary with temperature.
    
    Args:
        delta_h: Enthalpy change in kJ/mol
        delta_s: Entropy change in J/(mol·K)
        temp_range: Temperature range (T_min, T_max) in K
        num_points: Number of temperature points to calculate
        
    Returns:
        Dictionary with temperature series and thermodynamic data
    """
    t_min, t_max = temp_range
    temperatures = [t_min + i * (t_max - t_min) / (num_points - 1) for i in range(num_points)]
    
    results = []
    for temp in temperatures:
        delta_g = calculate_gibbs_free_energy(delta_h, delta_s, temp)
        k_eq = calculate_equilibrium_constant(delta_g, temp)
        
        results.append({
            "temperature": temp,
            "delta_g": delta_g,
            "k_eq": k_eq,
            "spontaneous": delta_g < 0,
        })
    
    return {
        "delta_h": delta_h,
        "delta_s": delta_s,
        "temperature_series": results,
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
        result["spontaneity"] = predict_spontaneity(delta_g_calc)
        
        # Temperature dependence analysis
        if analyze_temp_dependence:
            result["temperature_analysis"] = analyze_temperature_dependence(delta_h, delta_s)
    
    # Calculate ΔG from K if provided
    elif k_eq is not None:
        delta_g_calc = calculate_delta_g_from_k(k_eq, temperature)
        result["delta_g"] = delta_g_calc
        result["k_eq"] = k_eq
        result["spontaneity"] = predict_spontaneity(delta_g_calc)
    
    # Calculate K from ΔG if provided
    elif delta_g is not None:
        k_eq_calc = calculate_equilibrium_constant(delta_g, temperature)
        result["delta_g"] = delta_g
        result["k_eq"] = k_eq_calc
        result["spontaneity"] = predict_spontaneity(delta_g)
    
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
