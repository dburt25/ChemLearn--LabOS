"""
Chemical Kinetics Simulation Module

Models reaction kinetics, rate laws, and concentration profiles over time.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Callable, Tuple
import math


class ReactionOrder(Enum):
    """Reaction order types"""
    ZERO_ORDER = 0
    FIRST_ORDER = 1
    SECOND_ORDER = 2
    PSEUDO_FIRST_ORDER = "pseudo_first"


@dataclass
class Species:
    """Chemical species in a reaction"""
    name: str
    initial_concentration: float  # mol/L
    stoichiometry: float  # Coefficient in reaction (negative for reactants)


@dataclass
class RateConstant:
    """Rate constant with temperature dependence"""
    k_value: float  # Rate constant
    temperature: float  # Kelvin
    activation_energy: float  # kJ/mol (for Arrhenius)
    pre_exponential_factor: float  # A in Arrhenius equation


@dataclass
class KineticsResult:
    """Results from kinetics simulation"""
    times: List[float]  # Time points (seconds or appropriate unit)
    concentrations: Dict[str, List[float]]  # Species name -> concentration profile
    rate_constant: float
    reaction_order: ReactionOrder
    half_life: float  # Time for [A] to reach [A]₀/2
    rate_law: str  # Mathematical expression
    notes: List[str]


@dataclass
class EquilibriumResult:
    """Results from equilibrium calculation"""
    equilibrium_constant: float  # K_eq
    initial_concentrations: Dict[str, float]
    equilibrium_concentrations: Dict[str, float]
    reaction_quotient: float  # Q
    delta_g: float  # Standard Gibbs free energy (kJ/mol)
    temperature: float
    direction: str  # "forward", "reverse", or "equilibrium"
    notes: List[str]


# Universal gas constant
R = 8.314  # J/(mol·K)


def arrhenius_equation(
    temperature: float,
    pre_exponential_factor: float,
    activation_energy: float
) -> float:
    """
    Calculate rate constant using Arrhenius equation:
    k = A * exp(-Ea / (R*T))
    
    Args:
        temperature: Temperature in Kelvin
        pre_exponential_factor: A (frequency factor)
        activation_energy: Ea in kJ/mol
        
    Returns:
        Rate constant k
    """
    ea_joules = activation_energy * 1000  # Convert kJ to J
    exponent = -ea_joules / (R * temperature)
    return pre_exponential_factor * math.exp(exponent)


def calculate_half_life(
    k: float,
    order: ReactionOrder,
    initial_concentration: float = 1.0
) -> float:
    """
    Calculate half-life based on reaction order.
    
    Args:
        k: Rate constant
        order: Reaction order
        initial_concentration: Initial concentration (for 2nd order)
        
    Returns:
        Half-life (same time units as k)
    """
    if order == ReactionOrder.ZERO_ORDER:
        # t₁/₂ = [A]₀ / (2k)
        return initial_concentration / (2 * k)
    
    elif order == ReactionOrder.FIRST_ORDER or order == ReactionOrder.PSEUDO_FIRST_ORDER:
        # t₁/₂ = ln(2) / k
        return math.log(2) / k
    
    elif order == ReactionOrder.SECOND_ORDER:
        # t₁/₂ = 1 / (k[A]₀)
        return 1.0 / (k * initial_concentration)
    
    return 0.0


def simulate_zero_order(
    initial_concentration: float,
    rate_constant: float,
    time_points: List[float]
) -> List[float]:
    """
    Simulate zero-order kinetics: [A] = [A]₀ - kt
    Rate = k (constant)
    
    Args:
        initial_concentration: Initial [A]₀
        rate_constant: k
        time_points: Time values to calculate
        
    Returns:
        Concentration at each time point
    """
    concentrations = []
    for t in time_points:
        conc = initial_concentration - rate_constant * t
        # Concentration cannot be negative
        concentrations.append(max(0.0, conc))
    return concentrations


def simulate_first_order(
    initial_concentration: float,
    rate_constant: float,
    time_points: List[float]
) -> List[float]:
    """
    Simulate first-order kinetics: [A] = [A]₀ * exp(-kt)
    Rate = k[A]
    
    Args:
        initial_concentration: Initial [A]₀
        rate_constant: k
        time_points: Time values to calculate
        
    Returns:
        Concentration at each time point
    """
    concentrations = []
    for t in time_points:
        conc = initial_concentration * math.exp(-rate_constant * t)
        concentrations.append(conc)
    return concentrations


def simulate_second_order(
    initial_concentration: float,
    rate_constant: float,
    time_points: List[float]
) -> List[float]:
    """
    Simulate second-order kinetics: 1/[A] = 1/[A]₀ + kt
    Rate = k[A]²
    
    Args:
        initial_concentration: Initial [A]₀
        rate_constant: k
        time_points: Time values to calculate
        
    Returns:
        Concentration at each time point
    """
    concentrations = []
    inv_initial = 1.0 / initial_concentration if initial_concentration > 0 else 1e10
    
    for t in time_points:
        inv_conc = inv_initial + rate_constant * t
        conc = 1.0 / inv_conc if inv_conc > 0 else 0.0
        concentrations.append(conc)
    return concentrations


def simulate_reaction_kinetics(
    initial_concentration: float,
    rate_constant: float,
    reaction_order: ReactionOrder,
    time_start: float = 0.0,
    time_end: float = 100.0,
    num_points: int = 100,
    species_name: str = "A"
) -> KineticsResult:
    """
    Simulate reaction kinetics for simple A → products.
    
    Args:
        initial_concentration: Initial [A]₀ (mol/L)
        rate_constant: Rate constant k
        reaction_order: Order of reaction
        time_start: Start time
        time_end: End time
        num_points: Number of time points
        species_name: Name of reactant species
        
    Returns:
        KineticsResult with concentration vs time
    """
    # Generate time points
    time_points = []
    dt = (time_end - time_start) / (num_points - 1)
    for i in range(num_points):
        time_points.append(time_start + i * dt)
    
    # Simulate based on order
    if reaction_order == ReactionOrder.ZERO_ORDER:
        concentrations = simulate_zero_order(initial_concentration, rate_constant, time_points)
        rate_law = f"Rate = {rate_constant:.4f}"
    
    elif reaction_order == ReactionOrder.FIRST_ORDER or reaction_order == ReactionOrder.PSEUDO_FIRST_ORDER:
        concentrations = simulate_first_order(initial_concentration, rate_constant, time_points)
        rate_law = f"Rate = {rate_constant:.4f}[{species_name}]"
    
    elif reaction_order == ReactionOrder.SECOND_ORDER:
        concentrations = simulate_second_order(initial_concentration, rate_constant, time_points)
        rate_law = f"Rate = {rate_constant:.4f}[{species_name}]²"
    
    else:
        concentrations = [initial_concentration] * num_points
        rate_law = "Unknown"
    
    # Calculate half-life
    half_life = calculate_half_life(rate_constant, reaction_order, initial_concentration)
    
    # Package results
    conc_dict = {species_name: concentrations}
    
    notes = [
        f"{reaction_order.value}-order reaction",
        f"Initial [{species_name}] = {initial_concentration:.4f} M",
        f"Rate constant k = {rate_constant:.4e}",
        f"Half-life = {half_life:.4f} time units",
        rate_law
    ]
    
    return KineticsResult(
        times=time_points,
        concentrations=conc_dict,
        rate_constant=rate_constant,
        reaction_order=reaction_order,
        half_life=half_life,
        rate_law=rate_law,
        notes=notes
    )


def simulate_reversible_reaction(
    initial_a: float,
    initial_b: float,
    k_forward: float,
    k_reverse: float,
    time_end: float = 100.0,
    num_points: int = 100
) -> KineticsResult:
    """
    Simulate reversible first-order reaction: A ⇌ B
    
    Args:
        initial_a: Initial [A]
        initial_b: Initial [B]
        k_forward: Forward rate constant
        k_reverse: Reverse rate constant
        time_end: End time
        num_points: Number of time points
        
    Returns:
        KineticsResult with [A] and [B] vs time
    """
    dt = time_end / (num_points - 1)
    times = []
    conc_a = []
    conc_b = []
    
    # Initial conditions
    a = initial_a
    b = initial_b
    
    # Numerical integration (Euler method)
    for i in range(num_points):
        t = i * dt
        times.append(t)
        conc_a.append(a)
        conc_b.append(b)
        
        # Calculate rates
        rate_forward = k_forward * a
        rate_reverse = k_reverse * b
        
        # Update concentrations
        da = -rate_forward + rate_reverse
        db = rate_forward - rate_reverse
        
        a += da * dt
        b += db * dt
    
    # Calculate equilibrium constant
    k_eq = k_forward / k_reverse if k_reverse > 0 else float('inf')
    
    notes = [
        f"Reversible reaction: A ⇌ B",
        f"k_forward = {k_forward:.4e}",
        f"k_reverse = {k_reverse:.4e}",
        f"K_eq = {k_eq:.4f}",
        f"Initial [A] = {initial_a:.4f} M, [B] = {initial_b:.4f} M"
    ]
    
    return KineticsResult(
        times=times,
        concentrations={"A": conc_a, "B": conc_b},
        rate_constant=k_forward,
        reaction_order=ReactionOrder.FIRST_ORDER,
        half_life=calculate_half_life(k_forward, ReactionOrder.FIRST_ORDER),
        rate_law=f"Rate_fwd = {k_forward:.4e}[A], Rate_rev = {k_reverse:.4e}[B]",
        notes=notes
    )


def calculate_equilibrium_constant(
    delta_g_standard: float,
    temperature: float = 298.15
) -> float:
    """
    Calculate equilibrium constant from ΔG°: K = exp(-ΔG° / RT)
    
    Args:
        delta_g_standard: Standard Gibbs free energy (kJ/mol)
        temperature: Temperature (K)
        
    Returns:
        Equilibrium constant K
    """
    delta_g_joules = delta_g_standard * 1000  # Convert to J/mol
    exponent = -delta_g_joules / (R * temperature)
    return math.exp(exponent)


def calculate_reaction_quotient(
    products: Dict[str, float],
    reactants: Dict[str, float],
    stoichiometry: Dict[str, float]
) -> float:
    """
    Calculate reaction quotient Q = [products]^p / [reactants]^r
    
    Args:
        products: Product concentrations
        reactants: Reactant concentrations
        stoichiometry: Stoichiometric coefficients (positive for products)
        
    Returns:
        Reaction quotient Q
    """
    q = 1.0
    
    # Products in numerator
    for species, conc in products.items():
        if conc > 0:
            power = stoichiometry.get(species, 1.0)
            q *= conc ** power
    
    # Reactants in denominator
    for species, conc in reactants.items():
        if conc > 0:
            power = abs(stoichiometry.get(species, 1.0))
            q /= conc ** power
    
    return q


def predict_equilibrium(
    delta_g_standard: float,
    initial_concentrations: Dict[str, float],
    stoichiometry: Dict[str, float],
    temperature: float = 298.15
) -> EquilibriumResult:
    """
    Predict equilibrium position and direction.
    
    Args:
        delta_g_standard: ΔG° (kJ/mol)
        initial_concentrations: Initial concentrations for all species
        stoichiometry: Stoichiometric coefficients (+ for products, - for reactants)
        temperature: Temperature (K)
        
    Returns:
        EquilibriumResult with equilibrium analysis
    """
    # Calculate K_eq
    k_eq = calculate_equilibrium_constant(delta_g_standard, temperature)
    
    # Separate products and reactants
    products = {s: c for s, c in initial_concentrations.items() if stoichiometry.get(s, 0) > 0}
    reactants = {s: c for s, c in initial_concentrations.items() if stoichiometry.get(s, 0) < 0}
    
    # Calculate Q
    q = calculate_reaction_quotient(products, reactants, stoichiometry)
    
    # Determine direction
    if abs(q - k_eq) < k_eq * 0.01:  # Within 1% of equilibrium
        direction = "equilibrium"
    elif q < k_eq:
        direction = "forward"
    else:
        direction = "reverse"
    
    # Simplified equilibrium concentrations (placeholder)
    # In reality, would solve equilibrium equations
    equilibrium_conc = initial_concentrations.copy()
    
    notes = [
        f"Temperature: {temperature} K",
        f"ΔG° = {delta_g_standard:.2f} kJ/mol",
        f"K_eq = {k_eq:.4e}",
        f"Q = {q:.4e}",
        f"Reaction will proceed {direction}"
    ]
    
    if direction == "forward":
        notes.append("Q < K: Reaction shifts toward products")
    elif direction == "reverse":
        notes.append("Q > K: Reaction shifts toward reactants")
    else:
        notes.append("Q ≈ K: System is at equilibrium")
    
    return EquilibriumResult(
        equilibrium_constant=k_eq,
        initial_concentrations=initial_concentrations,
        equilibrium_concentrations=equilibrium_conc,
        reaction_quotient=q,
        delta_g=delta_g_standard,
        temperature=temperature,
        direction=direction,
        notes=notes
    )
