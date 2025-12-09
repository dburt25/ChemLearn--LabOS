"""Tests for UV-Visible Absorption Spectroscopy Module."""

import pytest
from labos.modules.spectroscopy.uv_vis import (
    UVVisResult,
    analyze_uv_vis_spectrum,
    beer_lambert_law,
    calculate_absorbance,
    detect_absorption_peaks,
    find_lambda_max,
)


class TestBeerLambertLaw:
    """Test Beer-Lambert law calculations."""

    def test_basic_concentration_calculation(self):
        """Test basic concentration from absorbance."""
        # A = 0.5, ε = 25000 M^-1 cm^-1, l = 1 cm
        # c = 0.5 / 25000 = 2×10^-5 M = 20 µM
        conc = beer_lambert_law(0.5, 25000, 1.0)
        assert abs(conc - 2e-5) < 1e-7

    def test_concentration_with_different_path_length(self):
        """Test calculation with 10 cm cuvette."""
        # A = 1.0, ε = 10000 M^-1 cm^-1, l = 10 cm
        # c = 1.0 / (10000 * 10) = 1×10^-5 M
        conc = beer_lambert_law(1.0, 10000, 10.0)
        assert abs(conc - 1e-5) < 1e-7

    def test_high_absorbance_gives_high_concentration(self):
        """Test that higher absorbance yields higher concentration."""
        conc1 = beer_lambert_law(0.5, 25000, 1.0)
        conc2 = beer_lambert_law(1.0, 25000, 1.0)
        assert conc2 > conc1

    def test_zero_epsilon_raises_error(self):
        """Test that zero epsilon is rejected."""
        with pytest.raises(ValueError, match="Molar absorptivity must be positive"):
            beer_lambert_law(0.5, 0, 1.0)

    def test_negative_epsilon_raises_error(self):
        """Test that negative epsilon is rejected."""
        with pytest.raises(ValueError, match="Molar absorptivity must be positive"):
            beer_lambert_law(0.5, -100, 1.0)

    def test_negative_absorbance_raises_error(self):
        """Test that negative absorbance is rejected."""
        with pytest.raises(ValueError, match="Absorbance cannot be negative"):
            beer_lambert_law(-0.5, 25000, 1.0)

    def test_zero_path_length_raises_error(self):
        """Test that zero path length is rejected."""
        with pytest.raises(ValueError, match="Path length must be positive"):
            beer_lambert_law(0.5, 25000, 0)


class TestCalculateAbsorbance:
    """Test absorbance calculation from concentration."""

    def test_basic_absorbance_calculation(self):
        """Test basic absorbance from concentration."""
        # c = 1×10^-5 M, ε = 25000 M^-1 cm^-1, l = 1 cm
        # A = 25000 * 1e-5 * 1 = 0.25
        absorbance = calculate_absorbance(1e-5, 25000, 1.0)
        assert abs(absorbance - 0.25) < 1e-7

    def test_absorbance_with_long_path(self):
        """Test absorbance with 10 cm path length."""
        # c = 1×10^-6 M, ε = 10000 M^-1 cm^-1, l = 10 cm
        # A = 10000 * 1e-6 * 10 = 0.1
        absorbance = calculate_absorbance(1e-6, 10000, 10.0)
        assert abs(absorbance - 0.1) < 1e-7

    def test_zero_concentration_gives_zero_absorbance(self):
        """Test that zero concentration gives zero absorbance."""
        absorbance = calculate_absorbance(0, 25000, 1.0)
        assert absorbance == 0.0

    def test_negative_concentration_raises_error(self):
        """Test that negative concentration is rejected."""
        with pytest.raises(ValueError, match="Concentration cannot be negative"):
            calculate_absorbance(-1e-5, 25000, 1.0)


class TestRoundTripBeerLambert:
    """Test that Beer-Lambert calculations are reversible."""

    def test_concentration_to_absorbance_and_back(self):
        """Test round-trip: concentration → absorbance → concentration."""
        conc_original = 5e-5  # M
        epsilon = 15000  # M^-1 cm^-1
        path_length = 1.0  # cm
        
        # Forward: calculate absorbance
        absorbance = calculate_absorbance(conc_original, epsilon, path_length)
        
        # Backward: calculate concentration
        conc_calc = beer_lambert_law(absorbance, epsilon, path_length)
        
        # Should match original
        assert abs(conc_calc - conc_original) / conc_original < 1e-10


class TestFindLambdaMax:
    """Test wavelength of maximum absorption detection."""

    def test_find_single_maximum(self):
        """Test finding λmax in simple spectrum."""
        spectrum = [(250, 0.1), (280, 0.8), (300, 0.3)]
        lambda_max, abs_max = find_lambda_max(spectrum)
        assert lambda_max == 280.0
        assert abs_max == 0.8

    def test_find_maximum_at_edge(self):
        """Test when maximum is at spectrum edge."""
        spectrum = [(250, 0.1), (280, 0.3), (300, 0.9)]
        lambda_max, abs_max = find_lambda_max(spectrum)
        assert lambda_max == 300.0
        assert abs_max == 0.9

    def test_wavelength_range_restriction(self):
        """Test λmax search within restricted range."""
        spectrum = [(250, 0.9), (280, 0.5), (350, 0.7)]
        # Restrict to 270-360 nm (excludes 250 nm peak)
        lambda_max, abs_max = find_lambda_max(spectrum, wavelength_range=(270, 360))
        assert lambda_max == 350.0
        assert abs_max == 0.7

    def test_empty_spectrum_raises_error(self):
        """Test that empty spectrum is rejected."""
        with pytest.raises(ValueError, match="Spectrum cannot be empty"):
            find_lambda_max([])

    def test_no_data_in_range_raises_error(self):
        """Test error when no data in specified range."""
        spectrum = [(250, 0.5), (280, 0.8)]
        with pytest.raises(ValueError, match="No data points in specified wavelength range"):
            find_lambda_max(spectrum, wavelength_range=(300, 400))


class TestDetectAbsorptionPeaks:
    """Test absorption peak detection."""

    def test_detect_single_peak(self):
        """Test detection of single absorption peak."""
        spectrum = [(250, 0.05), (280, 0.8), (300, 0.3)]
        peaks = detect_absorption_peaks(spectrum, threshold=0.5)
        assert len(peaks) == 1
        assert peaks[0]["wavelength"] == 280.0
        assert peaks[0]["absorbance"] == 0.8

    def test_detect_multiple_peaks(self):
        """Test detection of multiple separated peaks."""
        spectrum = [
            (250, 0.1),
            (280, 0.8),  # Peak 1
            (300, 0.3),
            (350, 0.6),  # Peak 2
            (380, 0.2),
        ]
        peaks = detect_absorption_peaks(spectrum, threshold=0.5)
        assert len(peaks) == 2
        assert peaks[0]["wavelength"] == 280.0
        assert peaks[1]["wavelength"] == 350.0

    def test_threshold_filters_small_peaks(self):
        """Test that low peaks below threshold are ignored."""
        spectrum = [(250, 0.3), (280, 0.5), (300, 0.2)]
        # Only peak at 280 above threshold
        peaks = detect_absorption_peaks(spectrum, threshold=0.4)
        assert len(peaks) == 1
        assert peaks[0]["wavelength"] == 280.0

    def test_min_separation_merges_close_peaks(self):
        """Test that closely spaced peaks are separated."""
        spectrum = [
            (250, 0.1),
            (280, 0.8),  # Peak 1
            (285, 0.7),  # Too close to 280
            (350, 0.6),  # Peak 2
        ]
        peaks = detect_absorption_peaks(spectrum, threshold=0.5, min_separation=10.0)
        # Should only get 280 and 350, not 285
        assert len(peaks) == 2
        assert peaks[0]["wavelength"] == 280.0
        assert peaks[1]["wavelength"] == 350.0

    def test_empty_spectrum_returns_empty_list(self):
        """Test that empty spectrum returns no peaks."""
        peaks = detect_absorption_peaks([])
        assert peaks == []


class TestAnalyzeUVVisSpectrum:
    """Test comprehensive UV-Vis spectrum analysis."""

    def test_basic_analysis_without_epsilon(self):
        """Test analysis without molar absorptivity."""
        spectrum = [(250, 0.1), (280, 0.8), (300, 0.3)]
        result = analyze_uv_vis_spectrum(spectrum)
        
        assert isinstance(result, UVVisResult)
        assert result.lambda_max == 280.0
        assert result.absorbance_max == 0.8
        assert result.concentration is None  # No epsilon provided
        assert len(result.peaks) > 0

    def test_analysis_with_epsilon_calculates_concentration(self):
        """Test that concentration is calculated when epsilon provided."""
        spectrum = [(250, 0.1), (280, 0.5), (300, 0.3)]
        result = analyze_uv_vis_spectrum(spectrum, epsilon=25000, path_length=1.0)
        
        assert result.concentration is not None
        # c = 0.5 / 25000 = 2×10^-5 M
        assert abs(result.concentration - 2e-5) < 1e-7

    def test_analysis_with_wavelength_range(self):
        """Test analysis with restricted wavelength range."""
        spectrum = [(250, 0.9), (280, 0.5), (350, 0.7)]
        result = analyze_uv_vis_spectrum(
            spectrum, 
            wavelength_range=(270, 360)
        )
        
        # Should find max at 350, not 250
        assert result.lambda_max == 350.0
        assert result.absorbance_max == 0.7

    def test_warning_for_high_absorbance(self):
        """Test that high absorbance triggers warning."""
        spectrum = [(280, 2.5)]
        result = analyze_uv_vis_spectrum(spectrum)
        
        # Check for warning about non-linear range
        assert any("WARNING" in note for note in result.notes)

    def test_empty_spectrum_handled_gracefully(self):
        """Test that empty spectrum is handled without error."""
        result = analyze_uv_vis_spectrum([])
        
        assert result.lambda_max is None
        assert result.absorbance_max is None
        assert len(result.peaks) == 0
        assert any("Empty spectrum" in note for note in result.notes)


class TestUVVisResultDataclass:
    """Test UVVisResult dataclass."""

    def test_default_initialization(self):
        """Test default values."""
        result = UVVisResult()
        assert result.lambda_max is None
        assert result.concentration is None
        assert result.path_length == 1.0
        assert result.peaks == []
        assert result.notes == []

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        result = UVVisResult(
            lambda_max=280.0,
            absorbance_max=0.5,
            concentration=2e-5,
            path_length=10.0,
        )
        assert result.lambda_max == 280.0
        assert result.absorbance_max == 0.5
        assert result.concentration == 2e-5
        assert result.path_length == 10.0
