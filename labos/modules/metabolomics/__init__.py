"""
Metabolomics Module

Metabolic pathway analysis and flux balance analysis.
"""

from .pathway_analysis import (
    Metabolite,
    Pathway,
    identify_pathways,
    calculate_pathway_enrichment,
    map_metabolites_to_pathways,
)

from .flux_balance import (
    ReactionFlux,
    construct_stoichiometric_matrix,
    perform_fba,
    calculate_reaction_bounds,
    analyze_flux_distribution,
)

from .metabolite_identification import (
    MetaboliteFeatures,
    identify_metabolite_by_mass,
    predict_metabolite_formula,
    calculate_mass_error,
    annotate_metabolites,
)

__all__ = [
    # Pathway Analysis
    "Metabolite",
    "Pathway",
    "identify_pathways",
    "calculate_pathway_enrichment",
    "map_metabolites_to_pathways",
    
    # Flux Balance
    "ReactionFlux",
    "construct_stoichiometric_matrix",
    "perform_fba",
    "calculate_reaction_bounds",
    "analyze_flux_distribution",
    
    # Metabolite Identification
    "MetaboliteFeatures",
    "identify_metabolite_by_mass",
    "predict_metabolite_formula",
    "calculate_mass_error",
    "annotate_metabolites",
]
