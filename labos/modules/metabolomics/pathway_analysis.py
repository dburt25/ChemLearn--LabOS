"""
Metabolic Pathway Analysis Module

Pathway mapping, enrichment analysis, and systems biology.

THEORY:
Metabolic pathways are series of chemical reactions catalyzed by enzymes.
Key databases: KEGG, Reactome, BioCyc

PATHWAY ENRICHMENT:
Uses hypergeometric test to find over-represented pathways:
P(X≥k) = Σ[i=k to n] (K choose i)(N-K choose n-i)/(N choose n)

Where:
- N = total metabolites in database
- K = metabolites in specific pathway
- n = metabolites in experimental set
- k = metabolites from experiment found in pathway

PATHWAY IMPACT:
Combines enrichment p-value with pathway topology:
Impact = -log(p) × Centrality
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import math

@dataclass
class Metabolite:
    """Metabolite data structure"""
    id: str
    name: str
    formula: str
    mass: float
    pathways: List[str] = field(default_factory=list)
    
    # Database IDs
    kegg_id: Optional[str] = None
    hmdb_id: Optional[str] = None
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return isinstance(other, Metabolite) and self.id == other.id


@dataclass
class Pathway:
    """Metabolic pathway structure"""
    id: str
    name: str
    metabolites: List[Metabolite]
    reactions: List[str] = field(default_factory=list)
    
    # Enrichment statistics
    enrichment_pvalue: Optional[float] = None
    fold_enrichment: Optional[float] = None
    impact_score: Optional[float] = None
    
    def get_metabolite_count(self) -> int:
        """Get number of metabolites in pathway"""
        return len(self.metabolites)


def identify_pathways(
    metabolite_ids: List[str],
    database: Dict[str, Pathway]
) -> List[Pathway]:
    """
    Identify pathways containing given metabolites
    
    Parameters:
    - metabolite_ids: list of metabolite identifiers
    - database: pathway database
    
    Returns:
    - pathways: list of matching pathways
    """
    matching_pathways = []
    metabolite_set = set(metabolite_ids)
    
    for pathway in database.values():
        pathway_metabolite_ids = {m.id for m in pathway.metabolites}
        
        # Check overlap
        overlap = metabolite_set & pathway_metabolite_ids
        if overlap:
            matching_pathways.append(pathway)
    
    return matching_pathways


def calculate_pathway_enrichment(
    experimental_metabolites: List[str],
    pathway: Pathway,
    total_metabolites_in_database: int
) -> Dict[str, float]:
    """
    Calculate pathway enrichment using hypergeometric test
    
    Tests whether a pathway is over-represented in experimental metabolites
    
    Parameters:
    - experimental_metabolites: metabolites detected in experiment
    - pathway: pathway to test for enrichment
    - total_metabolites_in_database: total unique metabolites in database
    
    Returns:
    - enrichment_stats: p-value, fold enrichment, significance
    
    THEORY:
    Hypergeometric distribution models sampling without replacement
    Null hypothesis: metabolites randomly distributed across pathways
    """
    # Convert to sets
    exp_set = set(experimental_metabolites)
    pathway_metabolite_ids = {m.id for m in pathway.metabolites}
    
    # Calculate overlap
    n_exp = len(exp_set)  # total experimental metabolites
    k_pathway = len(pathway_metabolite_ids)  # metabolites in this pathway
    k_overlap = len(exp_set & pathway_metabolite_ids)  # overlap
    n_total = total_metabolites_in_database
    
    # Hypergeometric p-value (right-tail)
    # P(X ≥ k_overlap)
    p_value = 0.0
    for i in range(k_overlap, min(n_exp, k_pathway) + 1):
        # Combination calculations
        # (K choose i) * (N-K choose n-i) / (N choose n)
        
        # Simplified calculation using logs to avoid overflow
        log_comb_1 = log_combination(k_pathway, i)
        log_comb_2 = log_combination(n_total - k_pathway, n_exp - i)
        log_comb_3 = log_combination(n_total, n_exp)
        
        log_p = log_comb_1 + log_comb_2 - log_comb_3
        p_value += math.exp(log_p)
    
    # Fold enrichment
    # Ratio of observed to expected overlap
    expected_overlap = (n_exp * k_pathway) / n_total
    fold_enrichment = k_overlap / expected_overlap if expected_overlap > 0 else 0.0
    
    # FDR correction (Benjamini-Hochberg) - simplified single-test
    fdr = min(1.0, p_value)
    
    return {
        "p_value": p_value,
        "fold_enrichment": fold_enrichment,
        "n_overlap": k_overlap,
        "n_expected": expected_overlap,
        "fdr": fdr,
        "significant": p_value < 0.05,
    }


def log_combination(n: int, k: int) -> float:
    """Calculate log of binomial coefficient to avoid overflow"""
    if k > n or k < 0:
        return float('-inf')
    if k == 0 or k == n:
        return 0.0
    
    # log(n choose k) = log(n!) - log(k!) - log((n-k)!)
    result = 0.0
    for i in range(1, k + 1):
        result += math.log(n - i + 1) - math.log(i)
    
    return result


def map_metabolites_to_pathways(
    metabolites: List[Metabolite],
    pathway_database: Dict[str, Pathway]
) -> Dict[str, List[str]]:
    """
    Map metabolites to their associated pathways
    
    Parameters:
    - metabolites: list of metabolite objects
    - pathway_database: pathway database
    
    Returns:
    - mapping: dict of metabolite_id -> list of pathway names
    """
    mapping = {}
    
    for metabolite in metabolites:
        metabolite_pathways = []
        
        for pathway in pathway_database.values():
            pathway_metabolite_ids = {m.id for m in pathway.metabolites}
            if metabolite.id in pathway_metabolite_ids:
                metabolite_pathways.append(pathway.name)
        
        mapping[metabolite.id] = metabolite_pathways
    
    return mapping


def calculate_pathway_impact(
    enrichment_pvalue: float,
    pathway_centrality: float
) -> float:
    """
    Calculate pathway impact score
    
    Combines statistical significance with topological importance
    
    Parameters:
    - enrichment_pvalue: pathway enrichment p-value
    - pathway_centrality: betweenness centrality or similar metric
    
    Returns:
    - impact_score: combined impact score
    
    THEORY:
    Impact integrates:
    1. Statistical significance: -log(p)
    2. Topological importance: centrality in metabolic network
    
    High-impact pathways are both:
    - Significantly enriched (low p-value)
    - Topologically important (high centrality)
    """
    # Avoid log(0)
    if enrichment_pvalue <= 0:
        enrichment_pvalue = 1e-10
    
    # Impact score
    impact = -math.log10(enrichment_pvalue) * pathway_centrality
    
    return impact


def perform_pathway_analysis(
    experimental_metabolites: List[str],
    pathway_database: Dict[str, Pathway],
    total_metabolites: int = 10000
) -> List[Dict[str, any]]:
    """
    Perform complete pathway enrichment analysis
    
    Parameters:
    - experimental_metabolites: detected metabolite IDs
    - pathway_database: pathway database
    - total_metabolites: total metabolites in database
    
    Returns:
    - enriched_pathways: list of enriched pathways with statistics
    """
    results = []
    
    for pathway_id, pathway in pathway_database.items():
        # Calculate enrichment
        enrichment = calculate_pathway_enrichment(
            experimental_metabolites,
            pathway,
            total_metabolites
        )
        
        # Only include if some overlap
        if enrichment["n_overlap"] > 0:
            # Calculate impact (assume centrality = 0.5 for demo)
            centrality = 0.5
            impact = calculate_pathway_impact(enrichment["p_value"], centrality)
            
            results.append({
                "pathway_id": pathway_id,
                "pathway_name": pathway.name,
                "n_metabolites_pathway": len(pathway.metabolites),
                "n_overlap": enrichment["n_overlap"],
                "p_value": enrichment["p_value"],
                "fold_enrichment": enrichment["fold_enrichment"],
                "impact_score": impact,
                "significant": enrichment["significant"],
            })
    
    # Sort by p-value (most significant first)
    results.sort(key=lambda x: x["p_value"])
    
    return results


def interpret_pathway_results(results: List[Dict[str, any]], top_n: int = 5) -> str:
    """
    Interpret pathway enrichment results
    
    Provides biological insights from enriched pathways
    """
    if not results:
        return "No enriched pathways found."
    
    interpretation = ["Pathway Enrichment Analysis Results", "=" * 40]
    
    significant_results = [r for r in results if r["significant"]]
    interpretation.append(f"\nTotal pathways analyzed: {len(results)}")
    interpretation.append(f"Significantly enriched: {len(significant_results)}")
    
    interpretation.append(f"\nTop {top_n} Enriched Pathways:")
    interpretation.append("-" * 40)
    
    for i, result in enumerate(results[:top_n], 1):
        interpretation.append(f"\n{i}. {result['pathway_name']}")
        interpretation.append(f"   P-value: {result['p_value']:.2e}")
        interpretation.append(f"   Fold enrichment: {result['fold_enrichment']:.2f}x")
        interpretation.append(f"   Overlap: {result['n_overlap']}/{result['n_metabolites_pathway']} metabolites")
        interpretation.append(f"   Impact score: {result['impact_score']:.3f}")
        
        if result["significant"]:
            interpretation.append("   Status: SIGNIFICANT ✓")
    
    return "\n".join(interpretation)
