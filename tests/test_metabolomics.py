"""
Comprehensive tests for Metabolomics module
"""

import pytest
import math
from labos.modules.metabolomics.pathway_analysis import (
    Metabolite, Pathway,
    identify_pathways, calculate_pathway_enrichment, map_metabolites_to_pathways,
    calculate_pathway_impact, perform_pathway_analysis
)
from labos.modules.metabolomics.flux_balance import (
    ReactionFlux,
    construct_stoichiometric_matrix, perform_fba, calculate_reaction_bounds,
    analyze_flux_distribution, perform_flux_variability_analysis
)
from labos.modules.metabolomics.metabolite_identification import (
    MetaboliteFeatures,
    calculate_mass_error, predict_metabolite_formula, identify_metabolite_by_mass,
    calculate_fragment_match_score, predict_isotope_pattern, annotate_metabolites
)


class TestPathwayAnalysis:
    """Test metabolic pathway analysis"""
    
    def test_metabolite_creation(self):
        """Test Metabolite dataclass"""
        met = Metabolite(
            id="M001",
            name="Glucose",
            formula="C6H12O6",
            mass=180.156,
            pathways=["Glycolysis", "Pentose phosphate"],
            kegg_id="C00031"
        )
        
        assert met.id == "M001"
        assert met.name == "Glucose"
        assert len(met.pathways) == 2
    
    def test_pathway_creation(self):
        """Test Pathway dataclass"""
        metabolites = [
            Metabolite("M1", "Glucose", "C6H12O6", 180.156),
            Metabolite("M2", "Pyruvate", "C3H3O3", 88.062)
        ]
        
        pathway = Pathway(
            id="P001",
            name="Glycolysis",
            metabolites=metabolites,
            reactions=["R1", "R2"]
        )
        
        assert pathway.get_metabolite_count() == 2
        assert len(pathway.reactions) == 2
    
    def test_identify_pathways(self):
        """Test pathway identification"""
        metabolites = [
            Metabolite("M1", "Glucose", "C6H12O6", 180.156),
            Metabolite("M2", "Pyruvate", "C3H3O3", 88.062)
        ]
        
        pathway = Pathway("P001", "Glycolysis", metabolites)
        database = {"P001": pathway}
        
        detected_ids = ["M1", "M2"]
        matching_pathways = identify_pathways(detected_ids, database)
        
        assert len(matching_pathways) == 1
        assert matching_pathways[0].id == "P001"
    
    def test_pathway_enrichment(self):
        """Test pathway enrichment calculation"""
        metabolites = [
            Metabolite(f"M{i}", f"Metabolite{i}", "C6H12O6", 180.0)
            for i in range(10)
        ]
        
        pathway = Pathway("P001", "Test Pathway", metabolites)
        
        # 5 out of 10 metabolites detected
        experimental = ["M0", "M1", "M2", "M3", "M4"]
        
        enrichment = calculate_pathway_enrichment(
            experimental,
            pathway,
            total_metabolites_in_database=100
        )
        
        assert "p_value" in enrichment
        assert "fold_enrichment" in enrichment
        assert enrichment["n_overlap"] == 5
        assert 0 <= enrichment["p_value"] <= 1
    
    def test_pathway_impact_score(self):
        """Test pathway impact calculation"""
        impact = calculate_pathway_impact(
            enrichment_pvalue=0.001,
            pathway_centrality=0.8
        )
        
        assert impact > 0
        # Lower p-value and higher centrality = higher impact
    
    def test_complete_pathway_analysis(self):
        """Test complete pathway enrichment analysis"""
        # Create metabolite database
        metabolites_1 = [Metabolite(f"M{i}", f"Met{i}", "C6H12O6", 180.0) for i in range(5)]
        metabolites_2 = [Metabolite(f"M{i}", f"Met{i}", "C6H12O6", 180.0) for i in range(5, 10)]
        
        pathways = {
            "P1": Pathway("P1", "Pathway 1", metabolites_1),
            "P2": Pathway("P2", "Pathway 2", metabolites_2),
        }
        
        experimental = ["M0", "M1", "M2"]  # Only in Pathway 1
        
        results = perform_pathway_analysis(experimental, pathways, total_metabolites=20)
        
        assert len(results) > 0
        assert all("pathway_name" in r for r in results)
        assert all("p_value" in r for r in results)


class TestFluxBalanceAnalysis:
    """Test flux balance analysis"""
    
    def test_reaction_flux_creation(self):
        """Test ReactionFlux dataclass"""
        rxn = ReactionFlux(
            reaction_id="R1",
            reaction_name="Glucose uptake",
            stoichiometry={"glucose": -1, "g6p": 1},
            lower_bound=-10.0,
            upper_bound=0.0
        )
        
        assert rxn.is_reversible()
        assert not rxn.is_exchange()  # Two metabolites
    
    def test_stoichiometric_matrix(self):
        """Test stoichiometric matrix construction"""
        reactions = [
            ReactionFlux("R1", "R1", {"A": -1, "B": 1}),
            ReactionFlux("R2", "R2", {"B": -1, "C": 1}),
        ]
        
        metabolites = ["A", "B", "C"]
        
        S, met_idx, rxn_idx = construct_stoichiometric_matrix(reactions, metabolites)
        
        assert len(S) == 3  # 3 metabolites
        assert len(S[0]) == 2  # 2 reactions
        assert met_idx["A"] == 0
        assert rxn_idx["R1"] == 0
    
    def test_reaction_bounds(self):
        """Test reaction bound calculation"""
        lower, upper = calculate_reaction_bounds("irreversible")
        assert lower == 0.0
        assert upper > 0
        
        lower, upper = calculate_reaction_bounds("reversible")
        assert lower < 0
        assert upper > 0
    
    def test_fba_execution(self):
        """Test FBA calculation"""
        reactions = [
            ReactionFlux("R1", "Glucose uptake", {"glucose": -1, "g6p": 1}, -10, 0),
            ReactionFlux("R2", "Biomass", {"g6p": -1, "biomass": 1}, 0, 1000),
        ]
        
        objective = {"R2": 1.0}  # Maximize biomass
        
        results = perform_fba(reactions, objective)
        
        assert results["status"] == "optimal"
        assert "objective_value" in results
        assert "fluxes" in results
        assert len(results["fluxes"]) == 2
    
    def test_flux_distribution_analysis(self):
        """Test flux distribution analysis"""
        reactions = [
            ReactionFlux(f"R{i}", f"Reaction {i}", {"A": -1, "B": 1})
            for i in range(5)
        ]
        
        fba_results = perform_fba(reactions, {"R0": 1.0})
        
        analysis = analyze_flux_distribution(fba_results, reactions)
        
        assert "n_active_reactions" in analysis
        assert "n_inactive_reactions" in analysis
        assert "fraction_active" in analysis
    
    def test_flux_variability_analysis(self):
        """Test FVA"""
        reactions = [
            ReactionFlux("R1", "R1", {"A": -1, "B": 1}, 0, 10),
            ReactionFlux("R2", "R2", {"B": -1, "C": 1}, 0, 10),
        ]
        
        optimal_value = 5.0
        objective = {"R2": 1.0}
        
        fva_results = perform_flux_variability_analysis(
            reactions,
            optimal_value,
            objective,
            fraction_of_optimum=0.9
        )
        
        assert len(fva_results) == 2
        assert all("min" in fva_results[r.reaction_id] for r in reactions)
        assert all("max" in fva_results[r.reaction_id] for r in reactions)


class TestMetaboliteIdentification:
    """Test metabolite identification"""
    
    def test_metabolite_features_creation(self):
        """Test MetaboliteFeatures dataclass"""
        features = MetaboliteFeatures(
            measured_mass=180.0634,
            retention_time=5.2,
            ms2_fragments=[161.0, 119.0, 89.0]
        )
        
        assert features.measured_mass == 180.0634
        assert len(features.ms2_fragments) == 3
    
    def test_mass_error_calculation(self):
        """Test mass error calculation"""
        error_ppm = calculate_mass_error(180.0650, 180.0634, "ppm")
        
        assert abs(error_ppm - 8.89) < 0.1
        
        error_da = calculate_mass_error(180.0650, 180.0634, "Da")
        assert abs(error_da - 0.0016) < 0.0001
    
    def test_formula_prediction(self):
        """Test molecular formula prediction"""
        # Glucose: C6H12O6 = 180.0634 Da
        candidates = predict_metabolite_formula(
            measured_mass=181.0712,  # [M+H]+
            adduct="[M+H]+",
            tolerance_ppm=5.0
        )
        
        assert len(candidates) > 0
        assert all("formula" in c for c in candidates)
        assert all("error_ppm" in c for c in candidates)
        
        # Check if C6H12O6 is among candidates
        formulas = [c["formula"] for c in candidates[:5]]
        assert any("C6" in f for f in formulas)
    
    def test_fragment_matching(self):
        """Test MS/MS fragment matching"""
        experimental = [161.0, 119.0, 89.0]
        database = [161.1, 119.1, 89.1, 71.0]
        
        score = calculate_fragment_match_score(
            experimental,
            database,
            tolerance_da=0.2
        )
        
        assert 0 <= score <= 1
        assert score > 0.5  # Should match 3 out of 3
    
    def test_isotope_pattern_prediction(self):
        """Test isotope pattern prediction"""
        # Glucose C6H12O6
        pattern = predict_isotope_pattern("C6H12O6", charge=1)
        
        assert len(pattern) >= 1  # At least M+0 peak
        
        # M+0 should be most abundant
        m0_intensity = pattern[0][1]
        assert m0_intensity == 100.0
        
        # M+1 should be ~6.6% (1.1% × 6 carbons)
        if len(pattern) > 1:
            m1_intensity = pattern[1][1]
            assert 5.0 < m1_intensity < 8.0
    
    def test_metabolite_identification(self):
        """Test database search for identification"""
        database = {
            "M001": {
                "name": "Glucose",
                "mass": 180.0634,
                "formula": "C6H12O6",
                "fragments": [161.0, 119.0, 89.0]
            }
        }
        
        features = MetaboliteFeatures(
            measured_mass=180.0640,  # 3.3 ppm error
            retention_time=5.2,
            ms2_fragments=[161.0, 119.0]
        )
        
        matches = identify_metabolite_by_mass(features, database, tolerance_ppm=10.0)
        
        assert len(matches) > 0
        assert matches[0]["name"] == "Glucose"
        assert abs(matches[0]["mass_error_ppm"]) < 10
    
    def test_batch_annotation(self):
        """Test batch metabolite annotation"""
        database = {
            "M001": {"name": "Glucose", "mass": 180.0634, "formula": "C6H12O6"},
            "M002": {"name": "Fructose", "mass": 180.0634, "formula": "C6H12O6"},
        }
        
        features_list = [
            MetaboliteFeatures(180.0640, 5.2, []),
            MetaboliteFeatures(150.0528, 3.1, []),
        ]
        
        annotated = annotate_metabolites(features_list, database, mass_tolerance_ppm=5.0)
        
        assert len(annotated) == 2
        assert annotated[0].name is not None  # Should match glucose/fructose
        assert annotated[0].confidence_level in [1, 2, 3, 4]


class TestMetabolomicsIntegration:
    """Integration tests for complete metabolomics workflows"""
    
    def test_pathway_to_fba_workflow(self):
        """Test pathway analysis followed by FBA"""
        # Create pathway
        metabolites = [Metabolite(f"M{i}", f"Met{i}", "C6H12O6", 180.0) for i in range(3)]
        pathway = Pathway("P1", "Test Pathway", metabolites)
        
        # Create reactions from pathway
        reactions = [
            ReactionFlux("R1", "R1", {"M0": -1, "M1": 1}, 0, 10),
            ReactionFlux("R2", "R2", {"M1": -1, "M2": 1}, 0, 10),
        ]
        
        # Run FBA
        fba_results = perform_fba(reactions, {"R2": 1.0})
        
        assert fba_results["status"] == "optimal"
        assert len(fba_results["fluxes"]) == 2
    
    def test_identification_to_pathway_workflow(self):
        """Test metabolite identification followed by pathway analysis"""
        # Identify metabolites
        database_met = {
            "M1": {"name": "Glucose", "mass": 180.0634, "formula": "C6H12O6"},
            "M2": {"name": "Pyruvate", "mass": 88.016, "formula": "C3H3O3"},
        }
        
        features = [
            MetaboliteFeatures(180.065, 5.0, []),
            MetaboliteFeatures(88.018, 3.0, []),
        ]
        
        annotated = annotate_metabolites(features, database_met, 10.0)
        
        # Map to pathways
        metabolites = [
            Metabolite("M1", "Glucose", "C6H12O6", 180.0634, ["Glycolysis"]),
            Metabolite("M2", "Pyruvate", "C3H3O3", 88.016, ["Glycolysis"]),
        ]
        
        pathway = Pathway("P1", "Glycolysis", metabolites)
        pathway_db = {"P1": pathway}
        
        identified_ids = ["M1", "M2"]
        pathways_found = identify_pathways(identified_ids, pathway_db)
        
        assert len(pathways_found) == 1
        assert pathways_found[0].name == "Glycolysis"
