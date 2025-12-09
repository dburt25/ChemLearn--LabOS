"""Tests for enhanced NMR spectroscopy analysis."""

import pytest

from labos.modules.spectroscopy.nmr_analysis import (
    NMRPeak,
    analyze_nmr_spectrum_enhanced,
    classify_chemical_shift_environment,
    detect_multiplicity_from_peaks,
)


class TestClassifyChemicalShiftEnvironment:
    """Test chemical shift environment classification."""

    def test_alkyl_region(self):
        """Test classification of alkyl region."""
        envs = classify_chemical_shift_environment(1.5)
        assert any("alkyl" in env.lower() for env in envs)

    def test_aromatic_region(self):
        """Test classification of aromatic region."""
        envs = classify_chemical_shift_environment(7.2)
        assert any("aromatic" in env.lower() for env in envs)

    def test_aldehydic_region(self):
        """Test classification of aldehydic region."""
        envs = classify_chemical_shift_environment(9.5)
        assert any("aldehyd" in env.lower() for env in envs)

    def test_adjacent_to_oxygen(self):
        """Test classification of protons adjacent to oxygen."""
        envs = classify_chemical_shift_environment(3.8)
        assert any("oxygen" in env.lower() for env in envs)


class TestDetectMultiplicityFromPeaks:
    """Test multiplicity detection from peak patterns."""

    def test_singlet_detection(self):
        """Test detection of singlet (single peak)."""
        peaks = [7.2]
        mult, j = detect_multiplicity_from_peaks(peaks)
        assert mult == "s"
        assert len(j) == 0

    def test_doublet_detection(self):
        """Test detection of doublet (2 peaks)."""
        peaks = [7.0, 7.05]
        mult, j = detect_multiplicity_from_peaks(peaks)
        assert mult == "d"
        assert len(j) == 1

    def test_triplet_detection(self):
        """Test detection of triplet (3 peaks)."""
        peaks = [3.0, 3.05, 3.10]
        mult, j = detect_multiplicity_from_peaks(peaks)
        assert mult == "t"
        assert len(j) == 1

    def test_quartet_detection(self):
        """Test detection of quartet (4 equally-spaced peaks)."""
        peaks = [2.0, 2.05, 2.10, 2.15]
        mult, j = detect_multiplicity_from_peaks(peaks)
        assert mult == "q"
        assert len(j) == 1

    def test_quintet_detection(self):
        """Test detection of quintet (5 peaks)."""
        peaks = [1.5, 1.55, 1.60, 1.65, 1.70]
        mult, j = detect_multiplicity_from_peaks(peaks)
        assert mult == "quint"

    def test_doublet_of_doublets(self):
        """Test detection of doublet of doublets (4 peaks with unequal spacing)."""
        peaks = [5.0, 5.02, 5.08, 5.10]
        mult, j = detect_multiplicity_from_peaks(peaks, tolerance=0.005)
        assert mult == "dd"
        assert len(j) == 2

    def test_complex_multiplet(self):
        """Test detection of complex multiplet."""
        peaks = [7.2, 7.22, 7.25, 7.28, 7.32]
        mult, j = detect_multiplicity_from_peaks(peaks, tolerance=0.01)
        assert mult == "m"


class TestAnalyzeNMRSpectrumEnhanced:
    """Test enhanced NMR spectrum analysis."""

    def test_empty_spectrum(self):
        """Test handling of empty spectrum."""
        result = analyze_nmr_spectrum_enhanced([])
        assert result["peaks"] == []
        assert result["total_integration"] == 0.0
        assert "Empty spectrum" in result["notes"][0]

    def test_simple_singlet(self):
        """Test analysis of a simple singlet."""
        spectrum = [
            (7.0, 0.1),
            (7.1, 0.3),
            (7.2, 0.8),  # Peak
            (7.3, 0.3),
            (7.4, 0.1),
        ]
        result = analyze_nmr_spectrum_enhanced(spectrum, threshold=0.5)
        
        assert len(result["peaks"]) == 1
        peak = result["peaks"][0]
        assert peak.multiplicity == "s"
        assert 7.1 <= peak.chemical_shift <= 7.3

    def test_doublet_detection(self):
        """Test detection and analysis of a doublet."""
        spectrum = [
            (3.0, 0.2),
            (3.05, 0.9),  # Peak 1
            (3.10, 0.3),
            (3.15, 0.9),  # Peak 2
            (3.20, 0.2),
        ]
        result = analyze_nmr_spectrum_enhanced(spectrum, threshold=0.5, detect_multiplets=True)
        
        assert len(result["peaks"]) == 1
        peak = result["peaks"][0]
        assert peak.multiplicity == "d"
        assert len(peak.j_coupling) > 0

    def test_triplet_detection(self):
        """Test detection and analysis of a triplet."""
        spectrum = [
            (1.0, 0.2),
            (1.05, 0.5),  # Peak 1
            (1.10, 0.3),
            (1.15, 0.9),  # Peak 2 (center)
            (1.20, 0.3),
            (1.25, 0.5),  # Peak 3
            (1.30, 0.2),
        ]
        result = analyze_nmr_spectrum_enhanced(spectrum, threshold=0.4, detect_multiplets=True)
        
        assert len(result["peaks"]) == 1
        peak = result["peaks"][0]
        assert peak.multiplicity == "t"

    def test_multiple_multiplets(self):
        """Test analysis of spectrum with multiple separated multiplets."""
        spectrum = [
            (0.8, 0.1),
            (1.0, 0.8),   # Peak 1 (singlet in alkyl region)
            (1.2, 0.1),
            (3.0, 0.1),
            (3.5, 0.7),   # Peak 2 (singlet near O)
            (3.8, 0.1),
            (7.0, 0.1),
            (7.2, 0.9),   # Peak 3 (singlet in aromatic)
            (7.4, 0.1),
        ]
        result = analyze_nmr_spectrum_enhanced(spectrum, threshold=0.5)
        
        assert len(result["peaks"]) >= 2
        # Should have peaks in different regions
        shifts = [p.chemical_shift for p in result["peaks"]]
        assert any(s < 2 for s in shifts)  # Alkyl
        assert any(s > 6 for s in shifts)  # Aromatic

    def test_integration_calculation(self):
        """Test that integration values are calculated."""
        spectrum = [
            (7.0, 0.2),
            (7.1, 0.5),
            (7.2, 0.9),
            (7.3, 0.5),
            (7.4, 0.2),
        ]
        result = analyze_nmr_spectrum_enhanced(spectrum, threshold=0.4)
        
        assert result["total_integration"] > 0
        assert all(p.integration > 0 for p in result["peaks"])

    def test_chemical_shift_regions(self):
        """Test classification of peaks by chemical shift region."""
        spectrum = [
            (0.8, 0.1),
            (1.0, 0.8),   # Alkyl
            (1.2, 0.1),
            (3.3, 0.1),
            (3.5, 0.7),   # Adjacent to O
            (3.7, 0.1),
            (7.0, 0.1),
            (7.2, 0.9),   # Aromatic
            (7.4, 0.1),
        ]
        result = analyze_nmr_spectrum_enhanced(spectrum, threshold=0.5)
        
        regions = result["chemical_shift_regions"]
        assert regions["alkyl (0-2 ppm)"] > 0
        assert regions["adjacent to O (3-5 ppm)"] > 0
        assert regions["aromatic (6-8.5 ppm)"] > 0

    def test_aromatic_detection_note(self):
        """Test that aromatic compounds are noted in analysis."""
        spectrum = [
            (7.0, 0.8),
            (7.2, 0.9),
            (7.4, 0.7),
        ]
        result = analyze_nmr_spectrum_enhanced(spectrum, threshold=0.5)
        
        assert any("aromatic" in note.lower() for note in result["notes"])

    def test_threshold_filtering(self):
        """Test that threshold correctly filters low-intensity peaks."""
        spectrum = [
            (0.8, 0.1),
            (1.0, 0.2),  # Below threshold
            (1.2, 0.1),
            (2.8, 0.1),
            (3.0, 0.8),  # Above threshold
            (3.2, 0.1),
            (4.8, 0.1),
            (5.0, 0.3),  # Below threshold
            (5.2, 0.1),
            (6.8, 0.1),
            (7.0, 0.9),  # Above threshold
            (7.2, 0.1),
        ]
        result = analyze_nmr_spectrum_enhanced(spectrum, threshold=0.5, detect_multiplets=False)
        
        assert len(result["peaks"]) == 2
        shifts = [p.chemical_shift for p in result["peaks"]]
        assert 3.0 in shifts
        assert 7.0 in shifts


class TestNMRPeakDataclass:
    """Test NMRPeak dataclass."""

    def test_creation(self):
        """Test NMRPeak creation."""
        peak = NMRPeak(
            chemical_shift=7.2,
            intensity=0.8,
            multiplicity="d",
            j_coupling=[7.5],
            integration=1.0,
            notes=["Aromatic region"]
        )
        assert peak.chemical_shift == 7.2
        assert peak.intensity == 0.8
        assert peak.multiplicity == "d"
        assert peak.j_coupling == [7.5]
        assert peak.integration == 1.0
        assert len(peak.notes) == 1


class TestMultiplicityPatternCoverage:
    """Test multiplicity detection covers common patterns."""

    def test_all_simple_patterns_detected(self):
        """Test that common splitting patterns are detected."""
        test_cases = [
            ([1.0], "s"),
            ([1.0, 1.05], "d"),
            ([1.0, 1.05, 1.10], "t"),
            ([1.0, 1.05, 1.10, 1.15], "q"),
            ([1.0, 1.05, 1.10, 1.15, 1.20], "quint"),
        ]
        
        for peaks, expected_mult in test_cases:
            mult, _ = detect_multiplicity_from_peaks(peaks)
            assert mult == expected_mult


class TestChemicalShiftCorrelation:
    """Test chemical shift correlation table coverage."""

    def test_all_major_regions_covered(self):
        """Test that all major chemical shift regions are covered."""
        test_shifts = [
            (0.9, "alkyl"),      # Methyl
            (1.5, "alkyl"),      # Methylene
            (2.5, "alpha"),      # Alpha to carbonyl
            (3.8, "oxygen"),     # OCH3
            (7.2, "aromatic"),   # Benzene
            (9.5, "aldehyd"),    # Aldehyde
        ]
        
        for shift, expected_keyword in test_shifts:
            envs = classify_chemical_shift_environment(shift)
            assert any(expected_keyword.lower() in env.lower() for env in envs)
