"""Kinetics calculators for reaction rate analysis.

Implements rate law calculations, Arrhenius equation, and
half-life computations for common reaction orders.
"""

from __future__ import annotations

import math
from typing import Dict, List


# Constants
R_GAS = 8.314  # J/(mol·K)


def calculate_rate_0th_order(initial_conc: float, k: float, time: float) -> float:
    """Calculate concentration for 0th order reaction.
    
    [A] = [A]₀ - kt
    
    Args:
        initial_conc: Initial concentration in M
        k: Rate constant in M/s
        time: Time in seconds
        
    Returns:
        Concentration at time t in M
    """
    concentration = initial_conc - k * time
    return max(0.0, concentration)  # Concentration can't go negative


def calculate_rate_1st_order(initial_conc: float, k: float, time: float) -> float:
    """Calculate concentration for 1st order reaction.
    
    [A] = [A]₀ * exp(-kt)
    
    Args:
        initial_conc: Initial concentration
        k: Rate constant
        time: Time in seconds
        
    Returns:
        Concentration at time t in M
    """
    return initial_conc * math.exp(-k * time)


def calculate_rate_2nd_order(k: float, time: float, initial_conc: float) -> float:
    """Calculate concentration for 2nd order reaction.
    
    [A] = [A]₀ / (1 + kt[A]₀)
    
    Args:
        k: Rate constant (1/(M·s))
        time: Time in seconds
        initial_conc: Initial concentration in M
        
    Returns:
        Concentration at time t in M
    """
    denominator = 1 + k * time * initial_conc
    return initial_conc / denominator


def calculate_half_life(k: float, order: int, initial_conc: float | None = None) -> float:
    """Calculate half-life for a reaction.
    
    0th order: t₁/₂ = [A]₀ / (2k)
    1st order: t₁/₂ = ln(2) / k
    2nd order: t₁/₂ = 1 / (k[A]₀)
    
    Args:
        k: Rate constant
        order: Reaction order (0, 1, or 2)
        initial_conc: Initial concentration (required for 0th and 2nd order)
        
    Returns:
        Half-life in seconds
        
    Raises:
        ValueError: If order is not 0, 1, or 2, or if initial_conc missing when required
    """
    if order == 0:
        if initial_conc is None:
            raise ValueError("Initial concentration required for 0th order half-life")
        return initial_conc / (2 * k)
    
    elif order == 1:
        return math.log(2) / k
    
    elif order == 2:
        if initial_conc is None:
            raise ValueError("Initial concentration required for 2nd order half-life")
        return 1 / (k * initial_conc)
    
    else:
        raise ValueError("Order must be 0, 1, or 2")


def arrhenius_equation(
    a_factor: float,
    activation_energy: float,
    temperature: float,
) -> float:
    """Calculate rate constant from Arrhenius equation.
    
    k = A * exp(-Ea / RT)
    
    Args:
        a_factor: Pre-exponential factor A (same units as k)
        activation_energy: Activation energy in J/mol
        temperature: Temperature in K
        
    Returns:
        Rate constant k
        
    Example:
        >>> arrhenius_equation(1e13, 50000, 298.15)
        # Calculate k for reaction with Ea = 50000 J/mol at 25°C
    """
    if temperature <= 0:
        raise ValueError("Temperature must be positive")
    if activation_energy < 0:
        raise ValueError("Activation energy must be non-negative")
    
    # k = A * exp(-Ea / RT)
    exponent = -activation_energy / (R_GAS * temperature)
    
    # Protect against underflow
    if exponent < -700:
        return 0.0
    
    k = a_factor * math.exp(exponent)
    return k


def arrhenius_temperature_ratio(
    activation_energy: float,
    t1: float,
    t2: float,
) -> float:
    """Calculate k2/k1 ratio at two temperatures.
    
    k2/k1 = exp(-Ea/R * (1/T2 - 1/T1))
    
    Args:
        activation_energy: Activation energy in J/mol
        t1: First temperature in K
        t2: Second temperature in K
        
    Returns:
        Ratio k2/k1
    """
    if t1 <= 0 or t2 <= 0:
        raise ValueError("Temperatures must be positive")
    
    # k2/k1 = exp(-Ea/R * (1/T2 - 1/T1))
    ln_k_ratio = -(activation_energy / R_GAS) * (1/t2 - 1/t1)
    
    return math.exp(ln_k_ratio)


def calculate_activation_energy(
    k1: float,
    k2: float,
    t1: float,
    t2: float,
) -> float:
    """Calculate activation energy from rate constants at two temperatures.
    
    Ea = -R * ln(k2/k1) / (1/T2 - 1/T1)
    
    Args:
        k1: Rate constant at T1
        k2: Rate constant at T2
        t1: First temperature in K
        t2: Second temperature in K
        
    Returns:
        Activation energy in J/mol
    """
    if k1 <= 0 or k2 <= 0:
        raise ValueError("Rate constants must be positive")
    if t1 <= 0 or t2 <= 0:
        raise ValueError("Temperatures must be positive")
    if t1 == t2:
        raise ValueError("Temperatures must be different")
    
    # Ea = -R * ln(k2/k1) / (1/T2 - 1/T1)
    ln_ratio = math.log(k2 / k1)
    temp_diff = 1/t2 - 1/t1
    
    ea_j = -R_GAS * ln_ratio / temp_diff
    
    return ea_j


def simulate_reaction_kinetics(
    k: float,
    initial_conc: float,
    order: int,
    t_end: float,
    n_points: int = 50,
) -> Dict[str, object]:
    """Simulate reaction concentration vs. time.
    
    Args:
        k: Rate constant
        initial_conc: Initial concentration in M
        order: Reaction order (0, 1, or 2)
        t_end: Total simulation time in seconds
        n_points: Number of time points
        
    Returns:
        Dictionary with time series and concentration data
    """
    if order not in [0, 1, 2]:
        raise ValueError("Order must be 0, 1, or 2")
    
    time_points = [i * t_end / (n_points - 1) for i in range(n_points)]
    concentrations = []
    
    for t in time_points:
        if order == 0:
            conc = calculate_rate_0th_order(initial_conc, k, t)
        elif order == 1:
            conc = calculate_rate_1st_order(initial_conc, k, t)
        else:  # order == 2:
            conc = calculate_rate_2nd_order(initial_conc, k, t)
        
        concentrations.append(conc)
    
    # Calculate half-life
    half_life = calculate_half_life(k, order, initial_conc)
    
    return {
        "k": k,
        "initial_concentration": initial_conc,
        "order": order,
        "half_life": half_life,
        "time_points": time_points,
        "concentrations": concentrations,
        "time_series": [
            {"time": t, "concentration": c}
            for t, c in zip(time_points, concentrations)
        ],
    }


# Module registration
MODULE_KEY = "pchem.kinetics"
MODULE_VERSION = "1.0.0"


def compute_kinetics(
    k: float | None = None,
    initial_conc: float | None = None,
    order: int = 1,
    time: float | None = None,
    a_factor: float | None = None,
    activation_energy: float | None = None,
    temperature: float = 298.15,
    simulate: bool = False,
) -> Dict[str, object]:
    """Comprehensive kinetics calculator.
    
    Main entry point for module operation.
    
    Args:
        k: Rate constant
        initial_conc: Initial concentration in M
        order: Reaction order (0, 1, or 2)
        time: Time for concentration calculation
        a_factor: Arrhenius pre-exponential factor
        activation_energy: Activation energy in kJ/mol
        temperature: Temperature in K
        simulate: Whether to simulate full kinetics profile
        
    Returns:
        Dictionary with kinetics calculations
    """
    result = {"order": order, "temperature": temperature}
    
    # Validate that we have enough data to compute something
    if k is None and (a_factor is None or activation_energy is None):
        raise ValueError("Must provide either k or both a_factor and activation_energy")
    
    # Calculate k from Arrhenius parameters if provided
    if a_factor is not None and activation_energy is not None:
        k_calc = arrhenius_equation(a_factor, activation_energy, temperature)
        result["k"] = k_calc
        result["a_factor"] = a_factor
        result["activation_energy"] = activation_energy
        k = k_calc
    
    # Calculate concentration at specific time
    if k is not None and initial_conc is not None and time is not None:
        if order == 0:
            conc = calculate_rate_0th_order(initial_conc, k, time)
        elif order == 1:
            conc = calculate_rate_1st_order(initial_conc, k, time)
        else:  # order == 2
            conc = calculate_rate_2nd_order(initial_conc, k, time)
        
        result["time"] = time
        result["concentration"] = conc
    
    # Calculate half-life
    if k is not None:
        if order in [0, 2] and initial_conc is not None:
            half_life = calculate_half_life(k, order, initial_conc)
            result["half_life"] = half_life
        elif order == 1:
            half_life = calculate_half_life(k, order)
            result["half_life"] = half_life
    
    # Simulate full kinetics profile
    if simulate and k is not None and initial_conc is not None:
        # Use appropriate total time based on half-life
        if "half_life" in result:
            total_time = result["half_life"] * 5  # Simulate 5 half-lives
        else:
            total_time = 100.0  # Default
        
        simulation = simulate_reaction_kinetics(k, initial_conc, order, total_time)
        result["simulation"] = simulation
    
    if not result.get("k"):
        result["k"] = k
    if initial_conc is not None:
        result["initial_concentration"] = initial_conc
    
    return result


def _register() -> None:
    """Register kinetics calculations with module system."""
    from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor
    
    descriptor = ModuleDescriptor(
        module_id=MODULE_KEY,
        version=MODULE_VERSION,
        description="Calculate reaction rates and kinetic parameters",
    )
    
    descriptor.register_operation(
        ModuleOperation(
            name="compute",
            description="Calculate rate constants and simulate kinetics",
            handler=lambda params: compute_kinetics(**params),
        )
    )
    
    register_descriptor(descriptor)


# Auto-register on import
_register()
