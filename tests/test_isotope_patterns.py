"""Tests for EI-MS isotope pattern analysis module."""

import pytest
from labos.modules.ei_ms.isotope_patterns import (
    ISOTOPE_DATA,
    IsotopePeak,
    IsotopePattern,
    parse_molecular_formula,
    calculate_monoisotopic_mass,
    calculate_isotope_pattern,
    match_isotope_pattern,
    identify_halogens,
    analyze_isotope_pattern,
)


class TestFormulaParser:
    """Test molecular formula parsing."""

    def test_parse_simple_formula(self):
        """Test parsing simple molecular formula."""
        formula = parse_molecular_formula("CH4")
        assert formula == {"C": 1, "H": 4}

    def test_parse_complex_formula(self):
        """Test parsing complex molecular formula."""
        formula = parse_molecular_formula("C6H12O6")
        assert formula == {"C": 6, "H": 12, "O": 6}

    def test_parse_formula_with_multiple_digits(self):
        """Test parsing formula with multi-digit counts."""
        formula = parse_molecular_formula("C12H22O11")
        assert formula == {"C": 12, "H": 22, "O": 11}

    def test_parse_formula_with_single_element(self):
        """Test parsing formula with single element counts (no digit)."""
        formula = parse_molecular_formula("C2H5OH")
        assert formula == {"C": 2, "H": 6, "O": 1}

    def test_parse_formula_with_halogens(self):
        """Test parsing formula with halogens."""
        formula = parse_molecular_formula("C6H5Cl")
        assert formula == {"C": 6, "H": 5, "Cl": 1}

    def test_parse_formula_with_bromine(self):
        """Test parsing formula with bromine."""
        formula = parse_molecular_formula("CH2Br2")
        assert formula == {"C": 1, "H": 2, "Br": 2}

    def test_empty_formula_returns_empty_dict(self):
        """Test empty formula returns empty dictionary."""
        formula = parse_molecular_formula("")
        assert formula == {}


class TestMonoisotopicMass:
    """Test monoisotopic mass calculation."""

    def test_calculate_methane_mass(self):
        """Test monoisotopic mass of methane (CH4)."""
        mass = calculate_monoisotopic_mass({"C": 1, "H": 4})
        expected = 12.000000 + 4 * 1.007825  # C-12 + 4*H-1
        assert abs(mass - expected) < 0.001

    def test_calculate_ethanol_mass(self):
        """Test monoisotopic mass of ethanol (C2H5OH)."""
        mass = calculate_monoisotopic_mass({"C": 2, "H": 6, "O": 1})
        expected = 2 * 12.000000 + 6 * 1.007825 + 15.994915
        assert abs(mass - expected) < 0.001

    def test_calculate_chlorobenzene_mass(self):
        """Test monoisotopic mass of chlorobenzene (C6H5Cl)."""
        mass = calculate_monoisotopic_mass({"C": 6, "H": 5, "Cl": 1})
        expected = 6 * 12.000000 + 5 * 1.007825 + 34.968853
        assert abs(mass - expected) < 0.001


class TestIsotopePatternCalculation:
    """Test isotope pattern calculation."""

    def test_methane_isotope_pattern(self):
        """Test isotope pattern for methane (CH4)."""
        pattern = calculate_isotope_pattern({"C": 1, "H": 4})
        
        # Should have M, M+1, M+2 peaks
        assert len(pattern.peaks) >= 2
        
        # M peak should be most intense
        assert pattern.peaks[0].intensity == 100.0
        
        # M+1 should be much smaller (mainly C-13)
        m_plus_1 = next((p for p in pattern.peaks if abs(p.mass_offset - 1) < 0.1), None)
        assert m_plus_1 is not None
        assert m_plus_1.intensity < 5.0  # ~1.1% for C-13

    def test_chlorobenzene_isotope_pattern(self):
        """Test isotope pattern for chlorobenzene (C6H5Cl)."""
        pattern = calculate_isotope_pattern({"C": 6, "H": 5, "Cl": 1})
        
        # Should have M and M+2 peaks for Cl-35/Cl-37
        m_plus_2 = next((p for p in pattern.peaks if abs(p.mass_offset - 2) < 0.1), None)
        assert m_plus_2 is not None
        
        # M+2 should be significant (~32% for chlorine)
        assert m_plus_2.intensity > 25.0
        assert m_plus_2.intensity < 40.0

    def test_bromoethane_isotope_pattern(self):
        """Test isotope pattern for bromoethane (C2H5Br)."""
        pattern = calculate_isotope_pattern({"C": 2, "H": 5, "Br": 1})
        
        # Bromine has almost 1:1 isotope ratio (Br-79:Br-81)
        m_plus_2 = next((p for p in pattern.peaks if abs(p.mass_offset - 2) < 0.1), None)
        assert m_plus_2 is not None
        
        # M+2 should be approximately equal to M peak for bromine
        assert m_plus_2.intensity > 90.0


class TestHalogenIdentification:
    """Test halogen identification from isotope patterns."""

    def test_identify_chlorine(self):
        """Test chlorine identification."""
        pattern = calculate_isotope_pattern({"C": 6, "H": 5, "Cl": 1})
        halogens = identify_halogens(pattern)
        
        assert "chlorine" in halogens

    def test_identify_bromine(self):
        """Test bromine identification."""
        pattern = calculate_isotope_pattern({"C": 2, "H": 5, "Br": 1})
        halogens = identify_halogens(pattern)
        
        assert "bromine" in halogens

    def test_no_halogens_detected(self):
        """Test no halogens detected for non-halogenated compound."""
        pattern = calculate_isotope_pattern({"C": 6, "H": 6})
        halogens = identify_halogens(pattern)
        
        assert len(halogens) == 0

    def test_multiple_chlorines(self):
        """Test detection of multiple chlorines."""
        pattern = calculate_isotope_pattern({"C": 6, "H": 4, "Cl": 2})
        halogens = identify_halogens(pattern)
        
        # Should detect chlorine (M+2 ratio increases with multiple Cl)
        assert "chlorine" in halogens


class TestPatternMatching:
    """Test isotope pattern matching."""

    def test_match_chlorobenzene_pattern(self):
        """Test matching chlorobenzene spectrum to theoretical pattern."""
        # Simulate experimental spectrum for chlorobenzene
        experimental_peaks = [
            (112.0, 100.0),  # M peak
            (113.0, 6.5),    # M+1 (C-13)
            (114.0, 32.0),   # M+2 (Cl-37)
        ]
        
        score = match_isotope_pattern(
            experimental_peaks=experimental_peaks,
            formula={"C": 6, "H": 5, "Cl": 1},
            mass_tolerance=0.5
        )
        
        # Should have high match score
        assert score > 0.8

    def test_no_match_wrong_formula(self):
        """Test poor matching for incorrect formula."""
        # Spectrum clearly shows chlorine, but formula doesn't have it
        experimental_peaks = [
            (112.0, 100.0),
            (113.0, 6.5),
            (114.0, 32.0),
        ]
        
        score = match_isotope_pattern(
            experimental_peaks=experimental_peaks,
            formula={"C": 8, "H": 8},  # Wrong formula
            mass_tolerance=0.5
        )
        
        # Should have poor match score
        assert score < 0.5

    def test_match_tolerates_intensity_variation(self):
        """Test matching tolerates intensity variations."""
        # Slightly different intensities from theoretical
        experimental_peaks = [
            (112.0, 100.0),
            (113.0, 7.0),   # Slightly higher than expected
            (114.0, 30.0),  # Slightly lower than expected
        ]
        
        score = match_isotope_pattern(
            experimental_peaks=experimental_peaks,
            formula={"C": 6, "H": 5, "Cl": 1},
            mass_tolerance=0.5
        )
        
        # Should still match reasonably well
        assert score > 0.7


class TestIsotopePatternAnalysis:
    """Test main analyze_isotope_pattern function."""

    def test_analyze_chlorobenzene(self):
        """Test full analysis of chlorobenzene spectrum."""
        result = analyze_isotope_pattern(
            molecular_formula="C6H5Cl",
            experimental_peaks=[
                (112.0, 100.0),
                (113.0, 6.5),
                (114.0, 32.0),
            ],
            mass_tolerance=0.5
        )
        
        assert "formula" in result
        assert "monoisotopic_mass" in result
        assert "theoretical_pattern" in result
        assert "halogens" in result
        assert "match_score" in result
        
        assert result["formula"] == {"C": 6, "H": 5, "Cl": 1}
        assert "chlorine" in result["halogens"]
        assert result["match_score"] > 0.8

    def test_analyze_without_experimental_peaks(self):
        """Test analysis with only theoretical calculation."""
        result = analyze_isotope_pattern(
            molecular_formula="C6H5Br"
        )
        
        assert "formula" in result
        assert "monoisotopic_mass" in result
        assert "theoretical_pattern" in result
        assert "halogens" in result
        assert "match_score" not in result  # No experimental data
        
        assert "bromine" in result["halogens"]

    def test_analyze_parses_formula_string(self):
        """Test that analysis accepts formula as string."""
        result = analyze_isotope_pattern(
            molecular_formula="CH4"
        )
        
        assert result["formula"] == {"C": 1, "H": 4}
        assert len(result["halogens"]) == 0


class TestIsotopeData:
    """Test isotope database completeness."""

    def test_isotope_data_has_common_elements(self):
        """Test that isotope data includes common organic elements."""
        assert "C" in ISOTOPE_DATA
        assert "H" in ISOTOPE_DATA
        assert "N" in ISOTOPE_DATA
        assert "O" in ISOTOPE_DATA
        assert "S" in ISOTOPE_DATA
        assert "Cl" in ISOTOPE_DATA
        assert "Br" in ISOTOPE_DATA

    def test_carbon_isotopes(self):
        """Test carbon isotope data."""
        c_isotopes = ISOTOPE_DATA["C"]
        
        # Should have C-12 and C-13
        assert len(c_isotopes) == 2
        
        c12 = next(iso for iso in c_isotopes if iso["mass"] == 12.000000)
        c13 = next(iso for iso in c_isotopes if abs(iso["mass"] - 13.003355) < 0.001)
        
        assert c12["abundance"] > 98.0
        assert c13["abundance"] < 2.0

    def test_chlorine_isotopes(self):
        """Test chlorine isotope data."""
        cl_isotopes = ISOTOPE_DATA["Cl"]
        
        # Should have Cl-35 and Cl-37
        assert len(cl_isotopes) == 2
        
        cl35 = next(iso for iso in cl_isotopes if abs(iso["mass"] - 34.968853) < 0.001)
        cl37 = next(iso for iso in cl_isotopes if abs(iso["mass"] - 36.965903) < 0.001)
        
        # Cl-35:Cl-37 ratio approximately 3:1
        assert cl35["abundance"] > 70.0
        assert cl37["abundance"] > 20.0

    def test_bromine_isotopes(self):
        """Test bromine isotope data."""
        br_isotopes = ISOTOPE_DATA["Br"]
        
        # Should have Br-79 and Br-81
        assert len(br_isotopes) == 2
        
        br79 = next(iso for iso in br_isotopes if abs(iso["mass"] - 78.918336) < 0.001)
        br81 = next(iso for iso in br_isotopes if abs(iso["mass"] - 80.916289) < 0.001)
        
        # Br-79:Br-81 ratio approximately 1:1
        assert abs(br79["abundance"] - 50.0) < 5.0
        assert abs(br81["abundance"] - 50.0) < 5.0
