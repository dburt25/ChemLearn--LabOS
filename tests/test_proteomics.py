"""
Tests for Proteomics Module - Digestion, Peptide Analysis, and PTM Analysis
"""

import unittest
from labos.modules.proteomics import digestion, peptide_analysis, ptm_analysis


class TestProteinDigestion(unittest.TestCase):
    """Test enzymatic digestion simulation"""
    
    def test_trypsin_digestion_simple(self):
        """Test basic trypsin digestion"""
        sequence = "MKTAYIAKSQGK"
        result = digestion.simulate_digestion(sequence, digestion.Enzyme.TRYPSIN, missed_cleavages=0)
        
        self.assertEqual(result.enzyme, digestion.Enzyme.TRYPSIN)
        self.assertGreater(len(result.peptides), 0)
        self.assertGreater(result.total_cleavage_sites, 0)
    
    def test_trypsin_cleaves_after_kr(self):
        """Test that trypsin cleaves after K and R"""
        sequence = "PEPTIDEKPEPTIDER"
        result = digestion.simulate_digestion(sequence, digestion.Enzyme.TRYPSIN, missed_cleavages=0)
        
        # Should find cleavage sites after K and R (check all sites, not just cleaved)
        k_site = any(site.residue == "K" for site in result.cleavage_sites)
        r_site = any(site.residue == "R" for site in result.cleavage_sites)
        
        self.assertTrue(k_site, "Trypsin should identify K cleavage site")
        self.assertTrue(r_site, "Trypsin should identify R cleavage site")
    
    def test_trypsin_blocked_by_proline(self):
        """Test that trypsin cleavage is blocked by proline"""
        sequence = "PEPTIDEKPPEPTIDE"
        result = digestion.simulate_digestion(sequence, digestion.Enzyme.TRYPSIN)
        
        # K followed by P should be blocked
        blocked_sites = [site for site in result.cleavage_sites 
                        if site.residue == "K" and not site.is_cleaved]
        self.assertGreater(len(blocked_sites), 0, "K-P site should be blocked")
    
    def test_missed_cleavages(self):
        """Test generation of peptides with missed cleavages"""
        sequence = "MKTAYIAKSQGK"
        result_no_mc = digestion.simulate_digestion(sequence, digestion.Enzyme.TRYPSIN, missed_cleavages=0)
        result_with_mc = digestion.simulate_digestion(sequence, digestion.Enzyme.TRYPSIN, missed_cleavages=1)
        
        # More missed cleavages should generate more peptides
        self.assertGreater(len(result_with_mc.peptides), len(result_no_mc.peptides))
    
    def test_peptide_mass_calculation(self):
        """Test peptide mass calculation"""
        mass = digestion.calculate_peptide_mass("PEPTIDE")
        
        # Should be around 799 Da
        self.assertGreater(mass, 750)
        self.assertLess(mass, 850)
    
    def test_charge_state_prediction(self):
        """Test charge state prediction"""
        # Peptide with multiple basic residues
        charges = digestion.predict_charge_states("PEPTIDEKR")
        self.assertIn(2, charges, "Should predict +2 charge state")
        
        # Short peptide
        charges_short = digestion.predict_charge_states("PEPTIDE")
        self.assertIn(1, charges_short, "Short peptide should have +1")
    
    def test_chymotrypsin_specificity(self):
        """Test chymotrypsin cleavage specificity"""
        sequence = "PEPTIDEFPEPTIDEW"
        result = digestion.simulate_digestion(sequence, digestion.Enzyme.CHYMOTRYPSIN)
        
        # Should cleave after F, W, Y, L
        f_site = any(site.residue == "F" for site in result.cleavage_sites)
        w_site = any(site.residue == "W" for site in result.cleavage_sites)
        
        self.assertTrue(f_site or w_site, "Chymotrypsin should find cleavage sites")
    
    def test_observable_peptides(self):
        """Test prediction of MS-observable peptides"""
        sequence = "MKTAYIAKSQGK"
        result = digestion.simulate_digestion(sequence, digestion.Enzyme.TRYPSIN)
        observable = digestion.predict_observable_peptides(result, min_mz=400, max_mz=2000)
        
        self.assertGreater(len(observable), 0)
        # Check m/z values are in range
        for pep, charge, mz in observable:
            self.assertGreaterEqual(mz, 400)
            self.assertLessEqual(mz, 2000)
    
    def test_sequence_coverage(self):
        """Test sequence coverage calculation"""
        sequence = "MKTAYIAKSQGK"
        result = digestion.simulate_digestion(sequence, digestion.Enzyme.TRYPSIN)
        coverage, covered_positions = digestion.calculate_sequence_coverage(result)
        
        self.assertGreater(coverage, 0)
        self.assertLessEqual(coverage, 100)
        self.assertIsInstance(covered_positions, list)


class TestPeptideAnalysis(unittest.TestCase):
    """Test peptide property analysis"""
    
    def test_molecular_formula(self):
        """Test molecular formula calculation"""
        formula = peptide_analysis.calculate_molecular_formula("PEPTIDE")
        
        self.assertIn("C", formula)
        self.assertIn("H", formula)
        self.assertIn("N", formula)
        self.assertIn("O", formula)
        self.assertGreater(formula["C"], 0)
    
    def test_formula_to_string(self):
        """Test formula string representation"""
        formula = {"C": 10, "H": 15, "N": 3, "O": 4}
        formula_str = peptide_analysis.formula_to_string(formula)
        
        self.assertIn("C10", formula_str)
        self.assertIn("H15", formula_str)
    
    def test_isoelectric_point(self):
        """Test pI calculation"""
        # Basic peptide (lots of K, R)
        pi_basic = peptide_analysis.calculate_isoelectric_point("KKKRRR")
        self.assertGreater(pi_basic, 10, "Basic peptide should have high pI")
        
        # Acidic peptide (lots of D, E)
        pi_acidic = peptide_analysis.calculate_isoelectric_point("DDDEEEE")
        self.assertLess(pi_acidic, 5, "Acidic peptide should have low pI")
    
    def test_charge_at_ph7(self):
        """Test charge calculation at pH 7"""
        # Basic peptide
        charge_basic = peptide_analysis.calculate_charge_at_ph("KKKRRR", ph=7.0)
        self.assertGreater(charge_basic, 0, "Basic peptide should be positive at pH 7")
        
        # Acidic peptide
        charge_acidic = peptide_analysis.calculate_charge_at_ph("DDDEEEE", ph=7.0)
        self.assertLess(charge_acidic, 0, "Acidic peptide should be negative at pH 7")
    
    def test_hydrophobicity(self):
        """Test GRAVY score calculation"""
        # Hydrophobic peptide
        gravy_hydro = peptide_analysis.calculate_hydrophobicity("AVILMFW")
        self.assertGreater(gravy_hydro, 0, "Hydrophobic peptide should have positive GRAVY")
        
        # Hydrophilic peptide
        gravy_hydro_neg = peptide_analysis.calculate_hydrophobicity("DERKST")
        self.assertLess(gravy_hydro_neg, 0, "Hydrophilic peptide should have negative GRAVY")
    
    def test_extinction_coefficient(self):
        """Test extinction coefficient calculation"""
        # Peptide with Trp
        ext_w = peptide_analysis.calculate_extinction_coefficient("PEPTIDEW")
        self.assertEqual(ext_w, 5500, "Single Trp should give 5500")
        
        # Peptide with Tyr
        ext_y = peptide_analysis.calculate_extinction_coefficient("PEPTIDEY")
        self.assertEqual(ext_y, 1490, "Single Tyr should give 1490")
        
        # Peptide with both
        ext_both = peptide_analysis.calculate_extinction_coefficient("PEPTIDEWY")
        self.assertEqual(ext_both, 5500 + 1490)
    
    def test_peptide_properties_comprehensive(self):
        """Test comprehensive peptide property analysis"""
        props = peptide_analysis.analyze_peptide_properties("PEPTIDE")
        
        self.assertEqual(props.sequence, "PEPTIDE")
        self.assertEqual(props.length, 7)
        self.assertGreater(props.monoisotopic_mass, 700)
        self.assertIsInstance(props.molecular_formula, str)
        self.assertGreater(props.isoelectric_point, 0)
        self.assertIsInstance(props.composition, dict)
    
    def test_b_ion_generation(self):
        """Test b-ion series generation"""
        ions = peptide_analysis.generate_b_ions("PEPTIDE", charge=1)
        
        self.assertGreater(len(ions), 0)
        # Should have n-1 b-ions for n-length peptide
        self.assertEqual(len(ions), 6)  # PEPTIDE is 7 aa, so 6 b-ions
        
        # Check ion labels
        labels = [ion.label for ion in ions]
        self.assertIn("b1+", labels)
        self.assertIn("b2+", labels)
    
    def test_y_ion_generation(self):
        """Test y-ion series generation"""
        ions = peptide_analysis.generate_y_ions("PEPTIDE", charge=1)
        
        self.assertGreater(len(ions), 0)
        self.assertEqual(len(ions), 6)  # n-1 y-ions
        
        labels = [ion.label for ion in ions]
        self.assertIn("y1+", labels)
        self.assertIn("y2+", labels)
    
    def test_theoretical_spectrum_generation(self):
        """Test theoretical MS/MS spectrum generation"""
        spectrum = peptide_analysis.generate_theoretical_spectrum(
            "PEPTIDE",
            precursor_charge=2,
            include_b_ions=True,
            include_y_ions=True
        )
        
        self.assertEqual(spectrum.peptide_sequence, "PEPTIDE")
        self.assertEqual(spectrum.precursor_charge, 2)
        self.assertGreater(spectrum.total_ions, 0)
        self.assertGreater(len(spectrum.fragment_ions), 0)
        
        # Should have both b and y ions
        has_b = any(ion.ion_type == peptide_analysis.FragmentType.B_ION 
                    for ion in spectrum.fragment_ions)
        has_y = any(ion.ion_type == peptide_analysis.FragmentType.Y_ION 
                    for ion in spectrum.fragment_ions)
        
        self.assertTrue(has_b, "Should have b-ions")
        self.assertTrue(has_y, "Should have y-ions")


class TestPTMAnalysis(unittest.TestCase):
    """Test post-translational modification analysis"""
    
    def test_phosphorylation_prediction(self):
        """Test phosphorylation site prediction"""
        # Sequence with S, T, Y
        sequence = "PEPTIDESTPEPTIDE"
        sites = ptm_analysis.predict_phosphorylation_sites(sequence)
        
        self.assertGreater(len(sites), 0)
        
        # Check that S, T are found
        residues = [site.residue for site in sites]
        self.assertIn("S", residues)
        self.assertIn("T", residues)
    
    def test_proline_directed_motif(self):
        """Test high confidence for proline-directed sites"""
        sequence = "PEPTIDESP"  # S followed by P
        sites = ptm_analysis.predict_phosphorylation_sites(sequence, motif_scoring=True)
        
        # Find the S-P site
        sp_sites = [site for site in sites if site.residue == "S" and site.motif_match]
        self.assertGreater(len(sp_sites), 0, "Should detect S-P motif")
        
        if sp_sites:
            self.assertGreater(sp_sites[0].confidence, 0.5, "S-P should have high confidence")
    
    def test_acetylation_prediction(self):
        """Test lysine acetylation prediction"""
        sequence = "PEPTIDEKPEPTIDE"
        sites = ptm_analysis.predict_acetylation_sites(sequence)
        
        self.assertGreater(len(sites), 0)
        
        # Should find K and N-terminal
        has_k = any(site.ptm_type == ptm_analysis.PTMType.ACETYLATION for site in sites)
        has_nterm = any(site.ptm_type == ptm_analysis.PTMType.N_TERMINAL_ACETYLATION 
                       for site in sites)
        
        self.assertTrue(has_k, "Should find lysine acetylation")
        self.assertTrue(has_nterm, "Should find N-terminal acetylation")
    
    def test_oxidation_prediction(self):
        """Test oxidation site prediction"""
        sequence = "PEPTIDEMWP"
        sites = ptm_analysis.predict_oxidation_sites(sequence)
        
        # Should find M, W, P
        residues = [site.residue for site in sites]
        self.assertIn("M", residues)
        self.assertIn("W", residues)
        self.assertIn("P", residues)
    
    def test_ptm_database_completeness(self):
        """Test PTM database has expected entries"""
        db = ptm_analysis.PTM_DATABASE
        
        self.assertIn(ptm_analysis.PTMType.PHOSPHORYLATION, db)
        self.assertIn(ptm_analysis.PTMType.ACETYLATION, db)
        self.assertIn(ptm_analysis.PTMType.OXIDATION, db)
        
        # Check mass shifts are reasonable
        phos_def = db[ptm_analysis.PTMType.PHOSPHORYLATION]
        self.assertAlmostEqual(phos_def.mass_shift, 79.966, places=2)
    
    def test_comprehensive_ptm_prediction(self):
        """Test comprehensive PTM analysis"""
        sequence = "PEPTIDEKSTY"
        result = ptm_analysis.predict_all_modifications(sequence, include_artifacts=False)
        
        self.assertEqual(result.sequence, sequence)
        self.assertGreater(result.total_modification_sites, 0)
        self.assertGreater(len(result.ptm_types_found), 0)
    
    def test_modification_application(self):
        """Test applying modifications to peptide"""
        sequence = "PEPTIDES"
        base_mass = 799.36  # Approximate
        
        # Create phosphorylation site
        site = ptm_analysis.ModificationSite(
            position=7,
            residue="S",
            ptm_type=ptm_analysis.PTMType.PHOSPHORYLATION,
            mass_shift=79.966,
            confidence=0.8,
            motif_match=True,
            surrounding_sequence="IDES",
            notes="Test phosphorylation"
        )
        
        modified = ptm_analysis.apply_modifications_to_peptide(sequence, [site], base_mass)
        
        self.assertEqual(modified.sequence, sequence)
        self.assertEqual(len(modified.modifications), 1)
        self.assertAlmostEqual(modified.total_mass_shift, 79.966, places=2)
        self.assertGreater(modified.modified_mass, base_mass)
    
    def test_multiple_modifications(self):
        """Test peptide with multiple modifications"""
        sequence = "PEPTIDEKST"
        base_mass = 1000.0
        
        sites = [
            ptm_analysis.ModificationSite(
                position=7, residue="K", ptm_type=ptm_analysis.PTMType.ACETYLATION,
                mass_shift=42.011, confidence=0.7, motif_match=False,
                surrounding_sequence="IDEK", notes="Ac"
            ),
            ptm_analysis.ModificationSite(
                position=8, residue="S", ptm_type=ptm_analysis.PTMType.PHOSPHORYLATION,
                mass_shift=79.966, confidence=0.8, motif_match=True,
                surrounding_sequence="DEKS", notes="Phos"
            ),
        ]
        
        modified = ptm_analysis.apply_modifications_to_peptide(sequence, sites, base_mass)
        
        self.assertTrue(modified.is_multiply_modified)
        self.assertEqual(len(modified.modifications), 2)
        expected_shift = 42.011 + 79.966
        self.assertAlmostEqual(modified.total_mass_shift, expected_shift, places=2)


class TestProteomicsIntegration(unittest.TestCase):
    """Integration tests combining multiple proteomics functions"""
    
    def test_digestion_to_spectrum(self):
        """Test workflow from digestion to spectrum generation"""
        # 1. Digest protein
        protein = "MKTAYIAKSQGK"
        digestion_result = digestion.simulate_digestion(protein, digestion.Enzyme.TRYPSIN)
        
        self.assertGreater(len(digestion_result.peptides), 0)
        
        # 2. Analyze first peptide
        peptide = digestion_result.peptides[0]
        props = peptide_analysis.analyze_peptide_properties(peptide.sequence)
        
        self.assertIsInstance(props, peptide_analysis.PeptideProperties)
        
        # 3. Generate theoretical spectrum
        spectrum = peptide_analysis.generate_theoretical_spectrum(
            peptide.sequence,
            precursor_charge=2
        )
        
        self.assertGreater(spectrum.total_ions, 0)
    
    def test_digestion_with_ptm(self):
        """Test digestion followed by PTM prediction"""
        protein = "MKTAYIAKSQGKST"
        
        # Digest
        digestion_result = digestion.simulate_digestion(protein, digestion.Enzyme.TRYPSIN)
        
        # Predict PTMs on peptides
        for peptide in digestion_result.peptides:
            ptm_result = ptm_analysis.predict_all_modifications(peptide.sequence)
            self.assertIsInstance(ptm_result, ptm_analysis.PTMAnalysisResult)
    
    def test_realistic_protein_workflow(self):
        """Test realistic proteomics workflow"""
        # Small protein sequence
        protein = "MKTAYIAKSQGKSTDEYPDPSPGGKQAEHQRFLGPVFDEIKKFYK"
        
        # Step 1: Digest
        digest = digestion.simulate_digestion(
            protein,
            enzyme=digestion.Enzyme.TRYPSIN,
            missed_cleavages=1
        )
        
        self.assertGreater(len(digest.peptides), 0)
        
        # Step 2: Get observable peptides
        observable = digestion.predict_observable_peptides(digest, min_mz=400, max_mz=2000)
        self.assertGreater(len(observable), 0)
        
        # Step 3: Calculate coverage
        coverage, _ = digestion.calculate_sequence_coverage(digest)
        self.assertGreater(coverage, 50, "Should have reasonable coverage")
        
        # Step 4: Analyze peptide properties
        if digest.peptides:
            props = peptide_analysis.analyze_peptide_properties(digest.peptides[0].sequence)
            self.assertIsInstance(props.molecular_formula, str)
        
        # Step 5: PTM prediction
        ptm_result = ptm_analysis.predict_all_modifications(protein, include_artifacts=True)
        self.assertGreater(ptm_result.total_modification_sites, 0)


if __name__ == "__main__":
    unittest.main()
