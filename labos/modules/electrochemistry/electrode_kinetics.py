"""
Electrode Kinetics Module

Butler-Volmer equation and electrode kinetics analysis.

THEORY:
Electrode reactions involve electron transfer at electrode/solution interface.

BUTLER-VOLMER EQUATION:
i = i₀[exp(αₐnFη/RT) - exp(-αcnFη/RT)]

Where:
- i = current density (A/cm²)
- i₀ = exchange current density (A/cm²)
- αₐ = anodic transfer coefficient
- αc = cathodic transfer coefficient
- n = number of electrons
- F = Faraday constant (96485 C/mol)
- η = overpotential = E - E_eq (V)
- R = gas constant (8.314 J/(mol·K))
- T = temperature (K)

NERNST EQUATION:
E_eq = E° - (RT/nF)ln(Q)

Where Q = product of activities

TAFEL EQUATION:
At high overpotential (|η| > 118/n mV):
η = a + b·log(i)

Where:
- a = Tafel intercept
- b = Tafel slope = 2.303RT/(αnF)

LEVICH EQUATION (rotating disk):
i_L = 0.620nFAD^(2/3)ν^(-1/6)C_bulk·ω^(1/2)

For mass transport limited current
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math

# Constants
FARADAY_CONSTANT = 96485.0  # C/mol
GAS_CONSTANT = 8.314  # J/(mol·K)
TEMPERATURE_DEFAULT = 298.15  # K


@dataclass
class ElectrodeReaction:
    """Electrode reaction parameters"""
    n_electrons: int
    standard_potential: float  # E° vs reference (V)
    
    # Kinetic parameters
    alpha_anodic: float = 0.5  # Transfer coefficient
    alpha_cathodic: float = 0.5
    exchange_current_density: Optional[float] = None  # A/cm²
    
    # Mass transport
    diffusion_coefficient: Optional[float] = None  # cm²/s
    concentration_bulk: Optional[float] = None  # mol/L
    
    def is_reversible(self, overpotential: float) -> bool:
        """Check if reaction is reversible at given overpotential"""
        # Reversible if |η| < RT/(nF) ≈ 25/n mV at 25°C
        threshold = 0.025 / self.n_electrons
        return abs(overpotential) < threshold


def calculate_nernst_potential(
    standard_potential: float,
    n_electrons: int,
    activity_ratio: float,
    temperature: float = TEMPERATURE_DEFAULT
) -> float:
    """
    Calculate equilibrium potential using Nernst equation
    
    E = E° - (RT/nF)ln(Q)
    
    Parameters:
    - standard_potential: E° vs reference (V)
    - n_electrons: electrons transferred
    - activity_ratio: Q = a_products/a_reactants
    - temperature: temperature (K)
    
    Returns:
    - equilibrium_potential: E_eq (V)
    
    EXAMPLE:
    For Fe³⁺ + e⁻ → Fe²⁺:
    E = E° - (RT/F)ln([Fe²⁺]/[Fe³⁺])
    """
    # Nernst equation
    if activity_ratio <= 0:
        activity_ratio = 1e-10  # Avoid log(0)
    
    rt_over_nf = (GAS_CONSTANT * temperature) / (n_electrons * FARADAY_CONSTANT)
    
    e_equilibrium = standard_potential - rt_over_nf * math.log(activity_ratio)
    
    return e_equilibrium


def calculate_nernst_potential_with_ph(
    standard_potential: float,
    n_electrons: int,
    n_protons: int,
    ph: float,
    concentration_ratio: float = 1.0,
    temperature: float = TEMPERATURE_DEFAULT
) -> float:
    """
    Calculate potential for pH-dependent reactions
    
    For reactions involving H⁺:
    E = E° - (RT/nF)ln([Red]/[Ox]) - (2.303RT/nF)·n_H⁺·pH
    
    Parameters:
    - standard_potential: E° at pH 0 (V)
    - n_electrons: electrons transferred
    - n_protons: protons involved
    - ph: solution pH
    - concentration_ratio: [Red]/[Ox]
    - temperature: temperature (K)
    
    Returns:
    - potential: E at given pH (V)
    
    EXAMPLE:
    O₂ + 4H⁺ + 4e⁻ → 2H₂O
    E shifts -59 mV/pH unit at 25°C
    """
    rt_over_nf = (GAS_CONSTANT * temperature) / (n_electrons * FARADAY_CONSTANT)
    
    # Concentration term
    e_conc = -rt_over_nf * math.log(concentration_ratio)
    
    # pH term: -0.059 V/pH at 25°C
    e_ph = -(2.303 * rt_over_nf * n_protons) * ph
    
    potential = standard_potential + e_conc + e_ph
    
    return potential


def calculate_butler_volmer_current(
    overpotential: float,
    exchange_current_density: float,
    n_electrons: int,
    alpha_anodic: float = 0.5,
    alpha_cathodic: float = 0.5,
    temperature: float = TEMPERATURE_DEFAULT
) -> float:
    """
    Calculate current density using Butler-Volmer equation
    
    i = i₀[exp(αₐnFη/RT) - exp(-αcnFη/RT)]
    
    Parameters:
    - overpotential: η = E - E_eq (V)
    - exchange_current_density: i₀ (A/cm²)
    - n_electrons: electrons transferred
    - alpha_anodic, alpha_cathodic: transfer coefficients
    - temperature: temperature (K)
    
    Returns:
    - current_density: i (A/cm²)
    
    INTERPRETATION:
    - η > 0: anodic (oxidation)
    - η < 0: cathodic (reduction)
    - i₀: intrinsic reaction rate
    - α: symmetry of energy barrier
    """
    # Calculate exponential terms
    f = FARADAY_CONSTANT / (GAS_CONSTANT * temperature)
    
    exp_anodic = math.exp(alpha_anodic * n_electrons * f * overpotential)
    exp_cathodic = math.exp(-alpha_cathodic * n_electrons * f * overpotential)
    
    current_density = exchange_current_density * (exp_anodic - exp_cathodic)
    
    return current_density


def calculate_exchange_current(
    reaction: ElectrodeReaction,
    electrode_area: float,
    temperature: float = TEMPERATURE_DEFAULT
) -> Dict[str, float]:
    """
    Calculate exchange current from reaction parameters
    
    i₀ = nFk₀[Ox]^(1-α)[Red]^α
    
    Parameters:
    - reaction: electrode reaction parameters
    - electrode_area: electrode area (cm²)
    - temperature: temperature (K)
    
    Returns:
    - exchange_current_data: i₀ per area and total
    
    TYPICAL VALUES:
    - Fast: i₀ > 10⁻³ A/cm² (Pt, Ag)
    - Moderate: 10⁻⁶ < i₀ < 10⁻³ A/cm²
    - Slow: i₀ < 10⁻⁶ A/cm² (Hg, glassy carbon)
    """
    if reaction.exchange_current_density is None:
        # Estimate from standard rate constant (if available)
        # For demo, use typical value
        i0 = 1e-6  # A/cm²
    else:
        i0 = reaction.exchange_current_density
    
    total_exchange_current = i0 * electrode_area
    
    # Classify kinetics
    if i0 > 1e-3:
        kinetics_classification = "fast (reversible)"
    elif i0 > 1e-6:
        kinetics_classification = "moderate (quasi-reversible)"
    else:
        kinetics_classification = "slow (irreversible)"
    
    return {
        "exchange_current_density": i0,
        "total_exchange_current": total_exchange_current,
        "electrode_area": electrode_area,
        "classification": kinetics_classification,
    }


def analyze_tafel_plot(
    overpotentials: List[float],
    current_densities: List[float],
    n_electrons: int,
    temperature: float = TEMPERATURE_DEFAULT
) -> Dict[str, any]:
    """
    Analyze Tafel plot to extract kinetic parameters
    
    Linear regression of η vs log|i|:
    η = a + b·log|i|
    
    Parameters:
    - overpotentials: list of η values (V)
    - current_densities: list of i values (A/cm²)
    - n_electrons: electrons transferred
    - temperature: temperature (K)
    
    Returns:
    - tafel_analysis: slopes, intercepts, transfer coefficients
    
    TAFEL SLOPE:
    b = 2.303RT/(αnF)
    
    At 25°C: b = 59/αn mV/decade
    """
    # Separate anodic and cathodic branches
    anodic_data = [(eta, i) for eta, i in zip(overpotentials, current_densities) if i > 0]
    cathodic_data = [(eta, i) for eta, i in zip(overpotentials, current_densities) if i < 0]
    
    analysis = {}
    
    # Analyze anodic branch
    if len(anodic_data) >= 2:
        eta_a = [d[0] for d in anodic_data]
        log_i_a = [math.log10(abs(d[1])) for d in anodic_data]
        
        # Linear regression (simplified)
        n_points = len(eta_a)
        sum_x = sum(log_i_a)
        sum_y = sum(eta_a)
        sum_xy = sum(x * y for x, y in zip(log_i_a, eta_a))
        sum_x2 = sum(x**2 for x in log_i_a)
        
        if n_points * sum_x2 - sum_x**2 != 0:
            slope_a = (n_points * sum_xy - sum_x * sum_y) / (n_points * sum_x2 - sum_x**2)
            intercept_a = (sum_y - slope_a * sum_x) / n_points
            
            # Extract transfer coefficient
            # b = 2.303RT/(αnF) → α = 2.303RT/(bnF)
            theoretical_b = (2.303 * GAS_CONSTANT * temperature) / (n_electrons * FARADAY_CONSTANT)
            alpha_anodic = theoretical_b / slope_a if slope_a > 0 else 0.5
            
            # Exchange current density from intercept
            # At η = 0, log(i₀) = -intercept/slope
            log_i0_a = -intercept_a / slope_a if slope_a != 0 else -6
            i0_anodic = 10**log_i0_a
            
            analysis["anodic"] = {
                "tafel_slope": slope_a,
                "tafel_intercept": intercept_a,
                "alpha": alpha_anodic,
                "exchange_current_density": i0_anodic,
            }
    
    # Analyze cathodic branch
    if len(cathodic_data) >= 2:
        eta_c = [d[0] for d in cathodic_data]
        log_i_c = [math.log10(abs(d[1])) for d in cathodic_data]
        
        n_points = len(eta_c)
        sum_x = sum(log_i_c)
        sum_y = sum(eta_c)
        sum_xy = sum(x * y for x, y in zip(log_i_c, eta_c))
        sum_x2 = sum(x**2 for x in log_i_c)
        
        if n_points * sum_x2 - sum_x**2 != 0:
            slope_c = (n_points * sum_xy - sum_x * sum_y) / (n_points * sum_x2 - sum_x**2)
            intercept_c = (sum_y - slope_c * sum_x) / n_points
            
            theoretical_b = (2.303 * GAS_CONSTANT * temperature) / (n_electrons * FARADAY_CONSTANT)
            alpha_cathodic = theoretical_b / abs(slope_c) if slope_c < 0 else 0.5
            
            log_i0_c = -intercept_c / slope_c if slope_c != 0 else -6
            i0_cathodic = 10**log_i0_c
            
            analysis["cathodic"] = {
                "tafel_slope": slope_c,
                "tafel_intercept": intercept_c,
                "alpha": alpha_cathodic,
                "exchange_current_density": i0_cathodic,
            }
    
    return analysis


def calculate_levich_current(
    n_electrons: int,
    electrode_area: float,
    diffusion_coefficient: float,
    kinematic_viscosity: float,
    concentration: float,
    rotation_rate: float
) -> float:
    """
    Calculate limiting current for rotating disk electrode
    
    Levich equation:
    i_L = 0.620nFAD^(2/3)ν^(-1/6)C·ω^(1/2)
    
    Parameters:
    - n_electrons: electrons transferred
    - electrode_area: area (cm²)
    - diffusion_coefficient: D (cm²/s)
    - kinematic_viscosity: ν (cm²/s)
    - concentration: bulk concentration (mol/L = mM)
    - rotation_rate: ω (rad/s)
    
    Returns:
    - limiting_current: i_L (A)
    
    THEORY:
    Rotating disk creates controlled convection
    Nernst diffusion layer thickness: δ ~ ω^(-1/2)
    """
    # Convert concentration to mol/cm³
    c_mol_cm3 = concentration * 1e-3
    
    # Levich equation
    i_limiting = (
        0.620 * 
        n_electrons * 
        FARADAY_CONSTANT * 
        electrode_area * 
        diffusion_coefficient**(2/3) * 
        kinematic_viscosity**(-1/6) * 
        c_mol_cm3 * 
        rotation_rate**(1/2)
    )
    
    return i_limiting


def interpret_kinetics_results(
    reaction: ElectrodeReaction,
    tafel_analysis: Dict[str, any]
) -> str:
    """
    Interpret electrode kinetics results
    """
    interpretation = ["Electrode Kinetics Analysis", "=" * 40]
    
    interpretation.append(f"\nReaction: {reaction.n_electrons}e⁻ transfer")
    interpretation.append(f"Standard potential: {reaction.standard_potential:.3f} V")
    
    if "anodic" in tafel_analysis:
        interpretation.append("\nAnodic Branch (Oxidation):")
        anodic = tafel_analysis["anodic"]
        interpretation.append(f"  Tafel slope: {anodic['tafel_slope']*1000:.1f} mV/decade")
        interpretation.append(f"  Transfer coefficient α: {anodic['alpha']:.3f}")
        interpretation.append(f"  Exchange current density: {anodic['exchange_current_density']:.2e} A/cm²")
    
    if "cathodic" in tafel_analysis:
        interpretation.append("\nCathodic Branch (Reduction):")
        cathodic = tafel_analysis["cathodic"]
        interpretation.append(f"  Tafel slope: {abs(cathodic['tafel_slope'])*1000:.1f} mV/decade")
        interpretation.append(f"  Transfer coefficient α: {cathodic['alpha']:.3f}")
        interpretation.append(f"  Exchange current density: {cathodic['exchange_current_density']:.2e} A/cm²")
    
    return "\n".join(interpretation)
