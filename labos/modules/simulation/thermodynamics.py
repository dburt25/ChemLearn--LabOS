"""
Thermodynamics Simulation Module

Educational thermodynamics calculations and predictions.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict
import math


@dataclass
class ThermodynamicState:
    """Thermodynamic state of a system"""
    temperature: float  # K
    pressure: float  # atm
    volume: float  # L
    moles: float  # mol
    internal_energy: float  # kJ
    enthalpy: float  # kJ
    entropy: float  # J/K
    gibbs_free_energy: float  # kJ


@dataclass
class ReactionThermodynamics:
    """Thermodynamic properties of a chemical reaction"""
    delta_h: float  # Enthalpy change (kJ/mol)
    delta_s: float  # Entropy change (J/(mol·K))
    delta_g: float  # Gibbs free energy change (kJ/mol)
    temperature: float  # K
    is_spontaneous: bool
    equilibrium_constant: float
    notes: List[str]


@dataclass
class PhaseTransition:
    """Phase transition properties"""
    substance: str
    initial_phase: str
    final_phase: str
    transition_temperature: float  # K
    transition_enthalpy: float  # kJ/mol
    transition_entropy: float  # J/(mol·K)
    notes: List[str]


# Constants
R_GAS = 8.314  # J/(mol·K)
R_ATM = 0.08206  # L·atm/(mol·K)


def ideal_gas_law(
    pressure: float = None,
    volume: float = None,
    moles: float = None,
    temperature: float = None
) -> float:
    """
    Calculate missing variable from ideal gas law: PV = nRT
    
    Provide 3 of 4 variables, returns the 4th.
    
    Args:
        pressure: Pressure (atm)
        volume: Volume (L)
        moles: Amount (mol)
        temperature: Temperature (K)
        
    Returns:
        Missing variable value
    """
    if pressure is None:
        return (moles * R_ATM * temperature) / volume
    elif volume is None:
        return (moles * R_ATM * temperature) / pressure
    elif moles is None:
        return (pressure * volume) / (R_ATM * temperature)
    elif temperature is None:
        return (pressure * volume) / (moles * R_ATM)
    else:
        raise ValueError("Must provide exactly 3 of 4 variables")


def calculate_gibbs_free_energy(
    delta_h: float,
    delta_s: float,
    temperature: float
) -> float:
    """
    Calculate Gibbs free energy: ΔG = ΔH - TΔS
    
    Args:
        delta_h: Enthalpy change (kJ/mol)
        delta_s: Entropy change (J/(mol·K))
        temperature: Temperature (K)
        
    Returns:
        Gibbs free energy (kJ/mol)
    """
    delta_s_kj = delta_s / 1000.0  # Convert J to kJ
    return delta_h - temperature * delta_s_kj


def is_spontaneous(delta_g: float) -> bool:
    """Determine if reaction is spontaneous"""
    return delta_g < 0


def calculate_equilibrium_constant(
    delta_g: float,
    temperature: float = 298.15
) -> float:
    """
    Calculate equilibrium constant: K = exp(-ΔG / RT)
    
    Args:
        delta_g: Standard Gibbs free energy (kJ/mol)
        temperature: Temperature (K)
        
    Returns:
        Equilibrium constant K
    """
    delta_g_j = delta_g * 1000  # Convert to J/mol
    exponent = -delta_g_j / (R_GAS * temperature)
    return math.exp(exponent)


def analyze_reaction_thermodynamics(
    delta_h: float,
    delta_s: float,
    temperature: float = 298.15
) -> ReactionThermodynamics:
    """
    Comprehensive thermodynamic analysis of a reaction.
    
    Args:
        delta_h: Standard enthalpy change (kJ/mol)
        delta_s: Standard entropy change (J/(mol·K))
        temperature: Temperature (K)
        
    Returns:
        ReactionThermodynamics with complete analysis
    """
    delta_g = calculate_gibbs_free_energy(delta_h, delta_s, temperature)
    spontaneous = is_spontaneous(delta_g)
    k_eq = calculate_equilibrium_constant(delta_g, temperature)
    
    notes = [
        f"Temperature: {temperature} K",
        f"ΔH° = {delta_h:.2f} kJ/mol",
        f"ΔS° = {delta_s:.2f} J/(mol·K)",
        f"ΔG° = {delta_g:.2f} kJ/mol"
    ]
    
    # Interpret thermodynamics
    if delta_h < 0:
        notes.append("Exothermic reaction (releases heat)")
    else:
        notes.append("Endothermic reaction (absorbs heat)")
    
    if delta_s > 0:
        notes.append("Entropy increases (more disorder)")
    else:
        notes.append("Entropy decreases (more order)")
    
    if spontaneous:
        notes.append("Spontaneous under standard conditions (ΔG < 0)")
        if k_eq > 1000:
            notes.append(f"Strongly favors products (K = {k_eq:.2e})")
        elif k_eq > 1:
            notes.append(f"Moderately favors products (K = {k_eq:.2f})")
    else:
        notes.append("Non-spontaneous under standard conditions (ΔG > 0)")
        if k_eq < 0.001:
            notes.append(f"Strongly favors reactants (K = {k_eq:.2e})")
        else:
            notes.append(f"Moderately favors reactants (K = {k_eq:.4f})")
    
    # Temperature dependence analysis
    if delta_h < 0 and delta_s < 0:
        notes.append("Spontaneous at low T, non-spontaneous at high T")
    elif delta_h > 0 and delta_s > 0:
        notes.append("Non-spontaneous at low T, spontaneous at high T")
    elif delta_h < 0 and delta_s > 0:
        notes.append("Spontaneous at all temperatures")
    else:  # delta_h > 0 and delta_s < 0
        notes.append("Non-spontaneous at all temperatures")
    
    return ReactionThermodynamics(
        delta_h=delta_h,
        delta_s=delta_s,
        delta_g=delta_g,
        temperature=temperature,
        is_spontaneous=spontaneous,
        equilibrium_constant=k_eq,
        notes=notes
    )


def calculate_transition_temperature(
    delta_h: float,
    delta_s: float
) -> float:
    """
    Calculate temperature at which ΔG = 0 (equilibrium).
    T = ΔH / ΔS
    
    Args:
        delta_h: Enthalpy change (kJ/mol)
        delta_s: Entropy change (J/(mol·K))
        
    Returns:
        Transition temperature (K)
    """
    if delta_s == 0:
        return float('inf')
    
    delta_s_kj = delta_s / 1000.0
    return delta_h / delta_s_kj


def analyze_phase_transition(
    substance: str,
    initial_phase: str,
    final_phase: str,
    delta_h: float,
    temperature: float
) -> PhaseTransition:
    """
    Analyze a phase transition.
    
    Args:
        substance: Name of substance
        initial_phase: Starting phase
        final_phase: Ending phase
        delta_h: Enthalpy of transition (kJ/mol)
        temperature: Transition temperature (K)
        
    Returns:
        PhaseTransition with analysis
    """
    # Calculate entropy of transition: ΔS = ΔH / T
    delta_s = (delta_h * 1000) / temperature  # J/(mol·K)
    
    notes = [
        f"Phase transition: {initial_phase} → {final_phase}",
        f"Transition T: {temperature} K ({temperature - 273.15:.2f} °C)",
        f"ΔH_transition: {delta_h:.2f} kJ/mol",
        f"ΔS_transition: {delta_s:.2f} J/(mol·K)"
    ]
    
    # Common phase transitions
    if initial_phase == "solid" and final_phase == "liquid":
        notes.append("Melting/fusion process")
    elif initial_phase == "liquid" and final_phase == "gas":
        notes.append("Vaporization/boiling process")
    elif initial_phase == "solid" and final_phase == "gas":
        notes.append("Sublimation process")
    
    return PhaseTransition(
        substance=substance,
        initial_phase=initial_phase,
        final_phase=final_phase,
        transition_temperature=temperature,
        transition_enthalpy=delta_h,
        transition_entropy=delta_s,
        notes=notes
    )


def hess_law_calculate(
    reactions: List[Tuple[float, float]]
) -> Tuple[float, float]:
    """
    Apply Hess's Law to calculate overall ΔH and ΔS.
    
    Args:
        reactions: List of (delta_h, delta_s) for each step
        
    Returns:
        (total_delta_h, total_delta_s)
    """
    total_h = sum(dh for dh, ds in reactions)
    total_s = sum(ds for dh, ds in reactions)
    return total_h, total_s


def van_t_hoff_equation(
    k1: float,
    t1: float,
    t2: float,
    delta_h: float
) -> float:
    """
    Calculate k2 using van't Hoff equation:
    ln(k2/k1) = -ΔH/R * (1/T2 - 1/T1)
    
    Args:
        k1: Equilibrium constant at T1
        t1: Temperature 1 (K)
        t2: Temperature 2 (K)
        delta_h: Enthalpy change (kJ/mol)
        
    Returns:
        k2: Equilibrium constant at T2
    """
    delta_h_j = delta_h * 1000  # Convert to J/mol
    exponent = -(delta_h_j / R_GAS) * (1/t2 - 1/t1)
    k2 = k1 * math.exp(exponent)
    return k2


def carnot_efficiency(
    t_hot: float,
    t_cold: float
) -> float:
    """
    Calculate maximum (Carnot) efficiency for heat engine.
    η = 1 - T_cold / T_hot
    
    Args:
        t_hot: Hot reservoir temperature (K)
        t_cold: Cold reservoir temperature (K)
        
    Returns:
        Efficiency (fraction, 0-1)
    """
    if t_hot <= t_cold or t_hot <= 0:
        return 0.0
    return 1.0 - (t_cold / t_hot)


def maxwell_boltzmann_distribution(
    temperature: float,
    mass: float,
    velocities: List[float]
) -> List[float]:
    """
    Calculate Maxwell-Boltzmann distribution for molecular speeds.
    
    Args:
        temperature: Temperature (K)
        mass: Molecular mass (kg/mol)
        velocities: Velocity values to calculate (m/s)
        
    Returns:
        Probability densities at each velocity
    """
    kt = R_GAS * temperature
    
    probabilities = []
    for v in velocities:
        # f(v) = (m/(2πkT))^(3/2) * 4πv² * exp(-mv²/(2kT))
        factor = (mass / (2 * math.pi * kt)) ** 1.5
        v_term = 4 * math.pi * v * v
        exp_term = math.exp(-mass * v * v / (2 * kt))
        
        prob = factor * v_term * exp_term
        probabilities.append(prob)
    
    return probabilities
