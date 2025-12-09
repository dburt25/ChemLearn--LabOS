"""Tests for enhanced IR spectroscopy analysis."""

import pytest

from labos.modules.spectroscopy.ir_analysis import (
    IRPeak,
    annotate_ir_peak,
    analyze_ir_spectrum_enhanced,
    classify_peak_intensity,
    is_broad_peak,
)


class TestClassifyPeakIntensity:
    """Test peak intensity classification."""

    def test_very_strong_peak(self):
        assert classify_peak_intensity(0.9) == "very strong"
        assert classify_peak_intensity(0.8) == "very strong"

    def test_strong_peak(self):
        assert classify_peak_intensity(0.7) == "strong"
        assert classify_peak_intensity(0.6) == "strong"

    def test_medium_peak(self):
        assert classify_peak_intensity(0.5) == "medium"
        assert classify_peak_intensity(0.4) == "medium"

    def test_weak_peak(self):
        assert classify_peak_intensity(0.3) == "weak"
        assert classify_peak_intensity(0.2) == "weak"

    def test_very_weak_peak(self):
        assert classify_peak_intensity(0.1) == "very weak"
        assert classify_peak_intensity(0.05) == "very weak"


class TestBroadPeakDetection:
    """Test broad peak detection."""

    def test_sharp_peak(self):
        """Test that a sharp peak is not classified as broad."""
        spectrum = [
            (1700, 0.1),
            (1710, 0.5),
            (1720, 0.9),  # Peak
            (1730, 0.5),
            (1740, 0.1),
        ]
        assert not is_broad_peak(spectrum, 1720)

    def test_broad_peak(self):
        """Test that a broad peak is correctly identified."""
        # Create a broad peak spanning ~200 cm-1
        spectrum = [
            (3000, 0.1),
            (3050, 0.5),
            (3100, 0.7),
            (3150, 0.8),
            (3200, 0.9),  # Peak
            (3250, 0.8),
            (3300, 0.7),
            (3350, 0.5),
            (3400, 0.1),
        ]
        assert is_broad_peak(spectrum, 3200, width_threshold=100.0)


class TestAnnotateIRPeak:
    """Test IR peak annotation."""

    def test_carbonyl_peak(self):
        """Test annotation of a carbonyl peak."""
        peak = annotate_ir_peak(1720, 0.8)
        assert peak.wavenumber == 1720
        assert peak.intensity == 0.8
        assert any("C=O" in fg for fg in peak.functional_groups)
        assert "strong" in peak.peak_type

    def test_oh_stretch(self):
        """Test annotation of O-H stretch."""
        peak = annotate_ir_peak(3400, 0.7)
        assert peak.wavenumber == 3400
        assert any("O-H" in fg for fg in peak.functional_groups)

    def test_ch_alkane(self):
        """Test annotation of C-H alkane stretch."""
        peak = annotate_ir_peak(2900, 0.6)
        assert peak.wavenumber == 2900
        assert any("C-H (alkane)" in fg for fg in peak.functional_groups)

    def test_multiple_assignments(self):
        """Test that a peak can have multiple functional group assignments."""
        # Peak at 1650 could be C=O (amide) or C=C (alkene)
        peak = annotate_ir_peak(1650, 0.8)
        assert len(peak.functional_groups) >= 2


class TestAnalyzeIRSpectrumEnhanced:
    """Test enhanced IR spectrum analysis."""

    def test_empty_spectrum(self):
        """Test handling of empty spectrum."""
        result = analyze_ir_spectrum_enhanced([])
        assert result["peaks"] == []
        assert result["functional_group_summary"] == {}
        assert "Empty spectrum" in result["notes"][0]

    def test_simple_carbonyl_spectrum(self):
        """Test analysis of a spectrum with a carbonyl peak."""
        spectrum = [
            (1500, 0.1),
            (1650, 0.3),
            (1700, 0.5),
            (1720, 0.9),  # Strong carbonyl
            (1740, 0.5),
            (1800, 0.2),
        ]
        result = analyze_ir_spectrum_enhanced(spectrum, threshold=0.3)
        
        assert len(result["peaks"]) > 0
        carbonyl_detected = any(
            any("C=O" in fg for fg in peak.functional_groups)
            for peak in result["peaks"]
        )
        assert carbonyl_detected
        assert any("carbonyl" in note.lower() for note in result["notes"])

    def test_alcohol_spectrum(self):
        """Test analysis of a spectrum with O-H stretch."""
        spectrum = [
            (2800, 0.3),
            (2900, 0.5),
            (3200, 0.6),
            (3400, 0.9),  # O-H stretch
            (3600, 0.5),
        ]
        result = analyze_ir_spectrum_enhanced(spectrum, threshold=0.3)
        
        oh_detected = any(
            any("O-H" in fg for fg in peak.functional_groups)
            for peak in result["peaks"]
        )
        assert oh_detected

    def test_functional_group_summary(self):
        """Test that functional group summary is correctly built."""
        spectrum = [
            (1720, 0.9),  # Carbonyl
            (2900, 0.7),  # C-H
            (3400, 0.8),  # O-H
        ]
        result = analyze_ir_spectrum_enhanced(spectrum, threshold=0.5, detect_peaks=False)
        
        summary = result["functional_group_summary"]
        assert len(summary) > 0
        # Should have detected multiple functional groups
        assert any("C=O" in key for key in summary.keys())

    def test_threshold_filtering(self):
        """Test that threshold correctly filters low-intensity peaks."""
        spectrum = [
            (1700, 0.2),  # Below threshold
            (1720, 0.8),  # Above threshold
            (1740, 0.3),  # Below threshold
        ]
        result = analyze_ir_spectrum_enhanced(spectrum, threshold=0.5, detect_peaks=False)
        
        assert len(result["peaks"]) == 1
        assert result["peaks"][0].wavenumber == 1720

    def test_aromatic_and_carbonyl(self):
        """Test spectrum with both aromatic and carbonyl features."""
        spectrum = [
            (700, 0.7),    # Aromatic C-H bend
            (1600, 0.6),   # Aromatic C=C
            (1720, 0.9),   # Carbonyl
            (3050, 0.5),   # Aromatic C-H stretch
        ]
        result = analyze_ir_spectrum_enhanced(spectrum, threshold=0.4)
        
        assert len(result["peaks"]) > 0
        summary = result["functional_group_summary"]
        assert len(summary) > 2  # Should have multiple functional groups


class TestIRPeakDataclass:
    """Test IRPeak dataclass."""

    def test_creation(self):
        """Test IRPeak creation."""
        peak = IRPeak(
            wavenumber=1720.0,
            intensity=0.8,
            functional_groups=["C=O (ketone)"],
            peak_type="strong"
        )
        assert peak.wavenumber == 1720.0
        assert peak.intensity == 0.8
        assert peak.functional_groups == ["C=O (ketone)"]
        assert peak.peak_type == "strong"


class TestCorrelationTable:
    """Test that correlation table covers expected ranges."""

    def test_carbonyl_region_covered(self):
        """Test that carbonyl region (1650-1850) has assignments."""
        test_wavenumbers = [1680, 1720, 1750, 1800]
        for wn in test_wavenumbers:
            peak = annotate_ir_peak(wn, 0.8)
            assert len(peak.functional_groups) > 0
            assert any("C=O" in fg for fg in peak.functional_groups)

    def test_oh_region_covered(self):
        """Test that O-H region (2500-3650) has assignments."""
        test_wavenumbers = [2800, 3200, 3500]
        for wn in test_wavenumbers:
            peak = annotate_ir_peak(wn, 0.8)
            assert any("O-H" in fg for fg in peak.functional_groups)

    def test_ch_region_covered(self):
        """Test that C-H region (2850-3100) has assignments."""
        test_wavenumbers = [2900, 2950, 3050]
        for wn in test_wavenumbers:
            peak = annotate_ir_peak(wn, 0.7)
            assert any("C-H" in fg for fg in peak.functional_groups)
