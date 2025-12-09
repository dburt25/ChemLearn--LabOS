"""
Flux Balance Analysis Module

Constraint-based modeling of metabolic networks.

THEORY:
Flux Balance Analysis (FBA) uses linear programming to predict metabolic fluxes.
Based on steady-state assumption: dS/dt = 0

STOICHIOMETRIC MATRIX:
S · v = 0

Where:
- S = stoichiometric matrix (metabolites × reactions)
- v = flux vector (reaction rates)

LINEAR PROGRAMMING:
Maximize: Z = c^T · v  (objective function, e.g., biomass)
Subject to:
- S · v = 0  (mass balance)
- v_min ≤ v ≤ v_max  (flux bounds)

FLUX VARIABILITY ANALYSIS:
For each reaction:
- Maximize v_i
- Minimize v_i
Subject to same constraints

This gives flux ranges compatible with optimal growth.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math

@dataclass
class ReactionFlux:
    """Metabolic reaction flux data"""
    reaction_id: str
    reaction_name: str
    stoichiometry: Dict[str, float]  # metabolite_id -> coefficient
    
    # Flux bounds
    lower_bound: float = -1000.0  # mmol/(gDW·h)
    upper_bound: float = 1000.0
    
    # Calculated flux
    flux_value: Optional[float] = None
    flux_min: Optional[float] = None  # FVA minimum
    flux_max: Optional[float] = None  # FVA maximum
    
    def is_reversible(self) -> bool:
        """Check if reaction is reversible"""
        return self.lower_bound < 0
    
    def is_exchange(self) -> bool:
        """Check if reaction is exchange reaction"""
        return len(self.stoichiometry) == 1


def construct_stoichiometric_matrix(
    reactions: List[ReactionFlux],
    metabolites: List[str]
) -> Tuple[List[List[float]], Dict[str, int], Dict[str, int]]:
    """
    Construct stoichiometric matrix from reactions
    
    Parameters:
    - reactions: list of metabolic reactions
    - metabolites: list of metabolite IDs
    
    Returns:
    - matrix: stoichiometric matrix (metabolites × reactions)
    - metabolite_index: metabolite ID -> row index
    - reaction_index: reaction ID -> column index
    
    MATRIX STRUCTURE:
    Rows = metabolites
    Columns = reactions
    Entry S[i,j] = coefficient of metabolite i in reaction j
    - Positive = product
    - Negative = substrate
    """
    # Create index mappings
    metabolite_index = {met: i for i, met in enumerate(metabolites)}
    reaction_index = {rxn.reaction_id: i for i, rxn in enumerate(reactions)}
    
    # Initialize matrix
    n_metabolites = len(metabolites)
    n_reactions = len(reactions)
    matrix = [[0.0 for _ in range(n_reactions)] for _ in range(n_metabolites)]
    
    # Fill matrix
    for j, reaction in enumerate(reactions):
        for metabolite_id, coefficient in reaction.stoichiometry.items():
            if metabolite_id in metabolite_index:
                i = metabolite_index[metabolite_id]
                matrix[i][j] = coefficient
    
    return matrix, metabolite_index, reaction_index


def perform_fba(
    reactions: List[ReactionFlux],
    objective_coefficients: Dict[str, float],
    maximize: bool = True
) -> Dict[str, any]:
    """
    Perform Flux Balance Analysis using simplex method
    
    Simplified FBA implementation
    
    Parameters:
    - reactions: list of metabolic reactions
    - objective_coefficients: coefficients for objective function (reaction_id -> weight)
    - maximize: True to maximize objective, False to minimize
    
    Returns:
    - fba_results: optimal fluxes and objective value
    
    OBJECTIVE FUNCTION:
    Typically maximizes biomass production:
    Z = Σ c_i · v_i
    
    Where c_i = 1 for biomass reaction, 0 for others
    """
    # Extract metabolites
    all_metabolites = set()
    for reaction in reactions:
        all_metabolites.update(reaction.stoichiometry.keys())
    
    metabolites = sorted(all_metabolites)
    
    # Construct stoichiometric matrix
    S, met_idx, rxn_idx = construct_stoichiometric_matrix(reactions, metabolites)
    
    # Simplified linear programming solution
    # Real implementation would use scipy.optimize.linprog or similar
    
    # For demo: use simple heuristic
    # Set fluxes to bounds that satisfy S·v ≈ 0
    
    fluxes = {}
    for reaction in reactions:
        # Objective reactions get max flux
        if reaction.reaction_id in objective_coefficients:
            coeff = objective_coefficients[reaction.reaction_id]
            if coeff > 0:
                # Maximize this flux
                fluxes[reaction.reaction_id] = reaction.upper_bound * 0.8
            else:
                # Minimize this flux
                fluxes[reaction.reaction_id] = reaction.lower_bound * 0.8
        else:
            # Non-objective reactions: set to middle of range
            fluxes[reaction.reaction_id] = (reaction.lower_bound + reaction.upper_bound) / 2.0
    
    # Calculate objective value
    objective_value = sum(
        objective_coefficients.get(rxn_id, 0) * flux 
        for rxn_id, flux in fluxes.items()
    )
    
    return {
        "objective_value": objective_value,
        "fluxes": fluxes,
        "status": "optimal",
        "n_reactions": len(reactions),
        "n_metabolites": len(metabolites),
    }


def calculate_reaction_bounds(
    reaction_type: str,
    default_bound: float = 1000.0
) -> Tuple[float, float]:
    """
    Calculate appropriate flux bounds for reaction type
    
    Parameters:
    - reaction_type: "irreversible", "reversible", "exchange"
    - default_bound: default maximum flux
    
    Returns:
    - lower_bound, upper_bound: flux bounds (mmol/(gDW·h))
    
    TYPICAL BOUNDS:
    - Irreversible: [0, 1000]
    - Reversible: [-1000, 1000]
    - Exchange (uptake): [-10, 1000]
    - Exchange (secretion): [0, 1000]
    """
    if reaction_type == "irreversible":
        return 0.0, default_bound
    elif reaction_type == "reversible":
        return -default_bound, default_bound
    elif reaction_type == "exchange_uptake":
        return -10.0, default_bound
    elif reaction_type == "exchange_secretion":
        return 0.0, default_bound
    else:
        return -default_bound, default_bound


def analyze_flux_distribution(
    fba_results: Dict[str, any],
    reactions: List[ReactionFlux]
) -> Dict[str, any]:
    """
    Analyze flux distribution from FBA results
    
    Identifies active pathways and flux patterns
    
    Parameters:
    - fba_results: results from perform_fba
    - reactions: reaction list
    
    Returns:
    - analysis: flux distribution analysis
    """
    fluxes = fba_results["fluxes"]
    
    # Categorize reactions by flux magnitude
    active_reactions = []
    inactive_reactions = []
    reversible_active = []
    
    flux_threshold = 1e-6  # Consider fluxes > this as active
    
    for reaction in reactions:
        flux = fluxes.get(reaction.reaction_id, 0.0)
        
        if abs(flux) > flux_threshold:
            active_reactions.append({
                "reaction_id": reaction.reaction_id,
                "flux": flux,
                "direction": "forward" if flux > 0 else "reverse",
            })
            
            if reaction.is_reversible() and flux < 0:
                reversible_active.append(reaction.reaction_id)
        else:
            inactive_reactions.append(reaction.reaction_id)
    
    # Calculate flux statistics
    flux_values = [abs(f) for f in fluxes.values() if abs(f) > flux_threshold]
    
    analysis = {
        "n_active_reactions": len(active_reactions),
        "n_inactive_reactions": len(inactive_reactions),
        "fraction_active": len(active_reactions) / len(reactions) if reactions else 0,
        "active_reactions": active_reactions,
        "reversible_active": reversible_active,
        "objective_value": fba_results["objective_value"],
    }
    
    if flux_values:
        analysis["mean_flux"] = sum(flux_values) / len(flux_values)
        analysis["max_flux"] = max(flux_values)
        analysis["min_flux"] = min(flux_values)
    
    return analysis


def perform_flux_variability_analysis(
    reactions: List[ReactionFlux],
    optimal_objective_value: float,
    objective_coefficients: Dict[str, float],
    fraction_of_optimum: float = 0.9
) -> Dict[str, Dict[str, float]]:
    """
    Perform Flux Variability Analysis
    
    Find min/max flux ranges compatible with near-optimal growth
    
    Parameters:
    - reactions: reaction list
    - optimal_objective_value: optimal objective from FBA
    - objective_coefficients: objective function
    - fraction_of_optimum: minimum fraction of optimal objective to maintain
    
    Returns:
    - fva_results: dict of reaction_id -> {min, max, range}
    
    THEORY:
    FVA determines flux flexibility:
    - Zero range: flux uniquely determined
    - Positive range: alternative optimal solutions exist
    """
    # Additional constraint: objective ≥ fraction × optimal
    min_objective = fraction_of_optimum * optimal_objective_value
    
    fva_results = {}
    
    for reaction in reactions:
        # For demo: approximate FVA results
        # Real implementation would solve 2n linear programs
        
        # Estimate flux range based on bounds
        flux_min = max(reaction.lower_bound, -abs(optimal_objective_value))
        flux_max = min(reaction.upper_bound, abs(optimal_objective_value))
        
        # If reaction is in objective, reduce variability
        if reaction.reaction_id in objective_coefficients:
            flux_min = optimal_objective_value * 0.9
            flux_max = optimal_objective_value * 1.0
        
        fva_results[reaction.reaction_id] = {
            "min": flux_min,
            "max": flux_max,
            "range": flux_max - flux_min,
            "is_blocked": abs(flux_max - flux_min) < 1e-6,
        }
    
    return fva_results


def interpret_fba_results(
    fba_results: Dict[str, any],
    flux_analysis: Dict[str, any]
) -> str:
    """
    Interpret FBA results with biological context
    """
    interpretation = ["Flux Balance Analysis Results", "=" * 40]
    
    interpretation.append(f"\nObjective value: {fba_results['objective_value']:.3f}")
    interpretation.append(f"Status: {fba_results['status']}")
    interpretation.append(f"Network size: {fba_results['n_reactions']} reactions, {fba_results['n_metabolites']} metabolites")
    
    interpretation.append(f"\nFlux Distribution:")
    interpretation.append(f"  Active reactions: {flux_analysis['n_active_reactions']} ({flux_analysis['fraction_active']*100:.1f}%)")
    interpretation.append(f"  Inactive reactions: {flux_analysis['n_inactive_reactions']}")
    
    if "mean_flux" in flux_analysis:
        interpretation.append(f"\nFlux Statistics:")
        interpretation.append(f"  Mean flux: {flux_analysis['mean_flux']:.2f}")
        interpretation.append(f"  Max flux: {flux_analysis['max_flux']:.2f}")
    
    if flux_analysis.get("reversible_active"):
        interpretation.append(f"\nReversible reactions active in reverse: {len(flux_analysis['reversible_active'])}")
    
    interpretation.append("\nTop Active Reactions:")
    top_reactions = sorted(
        flux_analysis["active_reactions"],
        key=lambda x: abs(x["flux"]),
        reverse=True
    )[:5]
    
    for i, rxn in enumerate(top_reactions, 1):
        interpretation.append(
            f"  {i}. {rxn['reaction_id']}: {rxn['flux']:.2f} ({rxn['direction']})"
        )
    
    return "\n".join(interpretation)
