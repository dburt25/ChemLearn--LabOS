"""
Tests for Advanced Spectroscopy Module

Comprehensive tests for Raman, fluorescence, circular dichroism,
and 2D NMR spectroscopy.
"""

import pytest
import math
from labos.modules.advanced_spectroscopy import (
    # Raman
    RamanPeak,
    calculate_raman_shift,
    identify_functional_groups,
    calculate_polarizability_derivative,
    analyze_raman_spectrum,
    
    # Fluorescence
    FluorescenceData,
    calculate_stokes_shift,
    calculate_quantum_yield,
    analyze_quenching,
    calculate_fluorescence_lifetime,
    analyze_fluorescence_spectrum,
    
    # Circular Dichroism
    CDSpectrum,
    calculate_ellipticity,
    calculate_mean_residue_ellipticity,
    estimate_secondary_structure,
    analyze_protein_stability,
    analyze_cd_spectrum,
    
    # 2D NMR
    NMR2DPeak,
    COSYCorrelation,
    identify_cosy_correlations,
    identify_hsqc_correlations,
    identify_hmbc_correlations,
    analyze_2d_nmr,
)


class TestRamanSpectroscopy:
    """Test Raman spectroscopy functions"""
    
    def test_calculate_raman_shift(self):
        """Test Raman shift calculation"""
        # 532 nm laser, 550 nm scattered light
        shift = calculate_raman_shift(laser_wavelength=532.0, scattered_wavelength=550.0)
        
        assert shift > 0
        # Expect ~616 cm⁻¹ shift
        assert 500 < shift < 700
    
    def test_raman_shift_stokes(self):
        """Test Stokes Raman shift (energy loss)"""
        shift_stokes = calculate_raman_shift(532.0, 550.0)
        assert shift_stokes > 0
    
    def test_raman_peak_dataclass(self):
        """Test RamanPeak dataclass"""
        peak = RamanPeak(
            wavenumber=1000.0,
            intensity=0.8,
            width=10.0,
            assignment="C-C stretch"
        )
        assert peak.wavenumber == 1000.0
        assert peak.assignment == "C-C stretch"
    
    def test_polarizability_derivative(self):
        """Test polarizability derivative calculation"""
        deriv = calculate_polarizability_derivative(
            raman_intensity=100.0,
            laser_power=10.0,
            concentration=0.5
        )
        assert deriv > 0
    
    def test_identify_functional_groups(self):
        """Test functional group identification"""
        peaks = [
            {"wavenumber": 2900, "intensity": 0.8},  # C-H stretch
            {"wavenumber": 1650, "intensity": 0.6},  # C=C aromatic
            {"wavenumber": 1100, "intensity": 0.5},  # C-O stretch
        ]
        
        assignments = identify_functional_groups(peaks)
        assert len(assignments) >= 2
        assert any("C-H" in a["assignment"] for a in assignments)
    
    def test_analyze_raman_spectrum(self):
        """Test comprehensive Raman analysis"""
        wavenumbers = [1000, 1500, 2000, 2900, 3000]
        intensities = [0.3, 0.5, 0.2, 0.9, 0.4]
        
        analysis = analyze_raman_spectrum(wavenumbers, intensities)
        
        assert "peaks" in analysis
        assert "functional_groups" in analysis
        assert analysis["number_of_peaks"] >= 2


class TestFluorescenceSpectroscopy:
    """Test fluorescence spectroscopy functions"""
    
    def test_calculate_stokes_shift(self):
        """Test Stokes shift calculation"""
        result = calculate_stokes_shift(
            excitation_wavelength=400.0,
            emission_wavelength=450.0
        )
        
        assert result["wavelength_shift_nm"] == 50.0
        assert result["energy_shift_ev"] > 0
    
    def test_stokes_shift_always_positive(self):
        """Test Stokes shift is energy loss"""
        result = calculate_stokes_shift(350.0, 420.0)
        assert result["wavelength_shift_nm"] > 0
        assert result["energy_shift_ev"] > 0
    
    def test_fluorescence_data_dataclass(self):
        """Test FluorescenceData dataclass"""
        data = FluorescenceData(
            excitation_wavelength=350.0,
            emission_wavelength=450.0,
            intensity=1000.0,
            quantum_yield=0.8
        )
        assert data.quantum_yield == 0.8
    
    def test_calculate_quantum_yield(self):
        """Test quantum yield calculation"""
        qy = calculate_quantum_yield(
            sample_integrated_intensity=1000.0,
            sample_absorbance=0.1,
            standard_integrated_intensity=500.0,
            standard_absorbance=0.1,
            standard_quantum_yield=0.5
        )
        
        assert 0 <= qy <= 1
        assert abs(qy - 1.0) < 0.1  # Should be ~1.0 (2x intensity, same abs)
    
    def test_quantum_yield_bounds(self):
        """Test quantum yield is bounded 0-1"""
        qy = calculate_quantum_yield(
            sample_integrated_intensity=10000.0,  # Very high
            sample_absorbance=0.1,
            standard_integrated_intensity=100.0,
            standard_absorbance=0.1,
            standard_quantum_yield=0.5
        )
        assert 0 <= qy <= 1  # Should be capped at 1.0
    
    def test_analyze_quenching(self):
        """Test fluorescence quenching analysis"""
        result = analyze_quenching(
            intensity_no_quencher=1000.0,
            intensity_with_quencher=500.0,
            quencher_concentration=0.01
        )
        
        assert result["stern_volmer_ratio"] == 2.0
        assert result["quenching_efficiency"] == 0.5
        assert result["stern_volmer_constant"] > 0
    
    def test_quenching_no_effect(self):
        """Test quenching with no quencher"""
        result = analyze_quenching(
            intensity_no_quencher=1000.0,
            intensity_with_quencher=1000.0,
            quencher_concentration=0.0
        )
        assert result["stern_volmer_ratio"] == 1.0
        assert result["quenching_efficiency"] == 0.0
    
    def test_calculate_fluorescence_lifetime(self):
        """Test fluorescence lifetime calculation"""
        # Exponential decay
        times = [0, 1, 2, 3, 4, 5]
        intensities = [100, 37, 14, 5, 2, 1]  # Roughly exp(-t)
        
        result = calculate_fluorescence_lifetime(intensities, times)
        
        assert "lifetime_ns" in result
        assert result["lifetime_ns"] > 0
        assert 0.5 < result["lifetime_ns"] < 2  # Should be ~1 ns
    
    def test_analyze_fluorescence_spectrum(self):
        """Test comprehensive fluorescence analysis"""
        emission_wl = [400, 450, 500, 550, 600]
        emission_int = [10, 50, 100, 60, 20]
        
        analysis = analyze_fluorescence_spectrum(
            excitation_wavelength=350.0,
            emission_wavelengths=emission_wl,
            emission_intensities=emission_int
        )
        
        assert analysis["emission_maximum"] == 500.0
        assert analysis["stokes_shift_nm"] == 150.0


class TestCircularDichroism:
    """Test circular dichroism spectroscopy functions"""
    
    def test_calculate_ellipticity(self):
        """Test ellipticity calculation"""
        theta = calculate_ellipticity(
            absorbance_left=0.5,
            absorbance_right=0.4
        )
        assert theta > 0  # Positive CD signal
    
    def test_ellipticity_negative(self):
        """Test negative ellipticity"""
        theta = calculate_ellipticity(
            absorbance_left=0.3,
            absorbance_right=0.5
        )
        assert theta < 0  # Negative CD signal
    
    def test_cd_spectrum_dataclass(self):
        """Test CDSpectrum dataclass"""
        spectrum = CDSpectrum(
            wavelength=222.0,
            ellipticity=-30000.0,
            absorbance_left=0.5,
            absorbance_right=0.6
        )
        assert spectrum.ellipticity == -30000.0
    
    def test_calculate_mean_residue_ellipticity(self):
        """Test mean residue ellipticity"""
        mre = calculate_mean_residue_ellipticity(
            ellipticity_mdeg=-10000.0,
            concentration=1.0,
            path_length=1.0,
            num_residues=100
        )
        assert mre < 0  # Negative for α-helix
    
    def test_estimate_secondary_structure_helix(self):
        """Test α-helix structure estimation"""
        # Typical α-helix values
        structure = estimate_secondary_structure(
            ellipticity_208nm=-30000.0,
            ellipticity_222nm=-35000.0,
            num_residues=100
        )
        
        assert structure["alpha_helix_percent"] > 50
        assert sum(structure.values()) == pytest.approx(100, abs=0.1)
    
    def test_estimate_secondary_structure_sum(self):
        """Test secondary structure percentages sum to 100"""
        structure = estimate_secondary_structure(
            ellipticity_208nm=-15000.0,
            ellipticity_222nm=-10000.0,
            num_residues=100
        )
        
        total = (structure["alpha_helix_percent"] + 
                structure["beta_sheet_percent"] + 
                structure["random_coil_percent"])
        assert total == pytest.approx(100, abs=0.1)
    
    def test_analyze_protein_stability(self):
        """Test protein stability analysis"""
        # Simulated melting curve
        temps = [20, 30, 40, 50, 60, 70, 80]
        ellips = [-30000, -29000, -25000, -15000, -8000, -5000, -4000]
        
        result = analyze_protein_stability(temps, ellips)
        
        assert "melting_temperature_celsius" in result
        assert 40 < result["melting_temperature_celsius"] < 70
    
    def test_analyze_cd_spectrum(self):
        """Test comprehensive CD analysis"""
        wavelengths = [190, 200, 208, 222, 250]
        ellipticities = [-5000, -15000, -30000, -35000, -2000]
        
        analysis = analyze_cd_spectrum(
            wavelengths=wavelengths,
            ellipticities=ellipticities,
            concentration=1.0,
            path_length=1.0,
            num_residues=100
        )
        
        assert "secondary_structure" in analysis
        assert "mean_residue_ellipticities" in analysis


class TestTwoDimensionalNMR:
    """Test 2D NMR spectroscopy functions"""
    
    def test_nmr2d_peak_dataclass(self):
        """Test NMR2DPeak dataclass"""
        peak = NMR2DPeak(
            f1=7.5,
            f2=7.2,
            intensity=0.8,
            peak_type="cross_peak"
        )
        assert peak.f1 == 7.5
        assert peak.peak_type == "cross_peak"
    
    def test_cosy_correlation_dataclass(self):
        """Test COSYCorrelation dataclass"""
        corr = COSYCorrelation(
            proton1_shift=7.5,
            proton2_shift=7.2,
            coupling_constant=8.0
        )
        assert corr.coupling_constant == 8.0
    
    def test_identify_cosy_correlations(self):
        """Test COSY correlation identification"""
        peaks = [
            {"f1": 7.5, "f2": 7.5, "intensity": 1.0},  # Diagonal
            {"f1": 7.5, "f2": 7.2, "intensity": 0.6},  # Cross-peak
            {"f1": 3.8, "f2": 2.5, "intensity": 0.4},  # Cross-peak
        ]
        
        correlations = identify_cosy_correlations(peaks)
        
        # Should find 2 cross-peaks (diagonal excluded)
        assert len(correlations) == 2
        assert all(c["type"] == "COSY" for c in correlations)
    
    def test_cosy_excludes_diagonal(self):
        """Test COSY excludes diagonal peaks"""
        peaks = [
            {"f1": 7.5, "f2": 7.5, "intensity": 1.0},  # Diagonal
            {"f1": 8.0, "f2": 8.01, "intensity": 0.9},  # Near diagonal
        ]
        
        correlations = identify_cosy_correlations(peaks, diagonal_tolerance=0.1)
        
        # Both should be excluded as diagonal/near-diagonal
        assert len(correlations) == 0
    
    def test_identify_hsqc_correlations(self):
        """Test HSQC correlation identification"""
        peaks = [
            {"f1": 30.0, "f2": 2.5, "intensity": 0.8},  # Aliphatic C-H
            {"f1": 128.0, "f2": 7.5, "intensity": 0.9},  # Aromatic C-H
            {"f1": 70.0, "f2": 3.8, "intensity": 0.7},  # C-O
        ]
        
        correlations = identify_hsqc_correlations(peaks)
        
        assert len(correlations) == 3
        assert all(c["type"] == "HSQC" for c in correlations)
        
        # Check carbon type classification
        carbon_types = [c["carbon_type"] for c in correlations]
        assert any("aliphatic" in ct for ct in carbon_types)
        assert any("aromatic" in ct for ct in carbon_types)
    
    def test_hsqc_carbon_classification(self):
        """Test HSQC carbon type classification"""
        peaks = [
            {"f1": 20.0, "f2": 1.5, "intensity": 0.8},  # Aliphatic
            {"f1": 75.0, "f2": 4.2, "intensity": 0.7},  # C-O
            {"f1": 130.0, "f2": 7.8, "intensity": 0.9},  # Aromatic
        ]
        
        correlations = identify_hsqc_correlations(peaks)
        
        assert correlations[0]["carbon_type"] == "aliphatic (sp³)"
        assert "C-O" in correlations[1]["carbon_type"]
        assert "aromatic" in correlations[2]["carbon_type"]
    
    def test_identify_hmbc_correlations(self):
        """Test HMBC long-range correlation identification"""
        peaks = [
            {"f1": 140.0, "f2": 7.5, "intensity": 0.5},  # Long-range
            {"f1": 30.0, "f2": 2.5, "intensity": 0.4},   # Long-range
        ]
        
        correlations = identify_hmbc_correlations(peaks)
        
        assert len(correlations) == 2
        assert all(c["type"] == "HMBC" for c in correlations)
        assert all("bond" in c["bond_distance"] for c in correlations)
    
    def test_hmbc_excludes_one_bond(self):
        """Test HMBC excludes HSQC one-bond correlations"""
        hmbc_peaks = [
            {"f1": 30.0, "f2": 2.5, "intensity": 0.8},  # Should be excluded
            {"f1": 140.0, "f2": 2.5, "intensity": 0.5},  # Long-range
        ]
        
        hsqc_reference = [
            {"carbon_ppm": 30.0, "proton_ppm": 2.5}  # One-bond correlation
        ]
        
        correlations = identify_hmbc_correlations(hmbc_peaks, hsqc_reference)
        
        # Should only find long-range correlation
        assert len(correlations) == 1
        assert correlations[0]["carbon_ppm"] == 140.0
    
    def test_analyze_2d_nmr_cosy(self):
        """Test comprehensive COSY analysis"""
        peaks = [
            {"f1": 7.5, "f2": 7.2, "intensity": 0.6},
            {"f1": 3.8, "f2": 2.5, "intensity": 0.4},
        ]
        
        analysis = analyze_2d_nmr("COSY", peaks)
        
        assert analysis["experiment_type"] == "COSY"
        assert analysis["num_correlations"] == 2
        assert len(analysis["notes"]) > 0
    
    def test_analyze_2d_nmr_hsqc(self):
        """Test comprehensive HSQC analysis"""
        peaks = [
            {"f1": 30.0, "f2": 2.5, "intensity": 0.8},
            {"f1": 128.0, "f2": 7.5, "intensity": 0.9},
        ]
        
        analysis = analyze_2d_nmr("HSQC", peaks)
        
        assert analysis["experiment_type"] == "HSQC"
        assert analysis["num_correlations"] == 2
    
    def test_analyze_2d_nmr_hmbc(self):
        """Test comprehensive HMBC analysis"""
        peaks = [
            {"f1": 140.0, "f2": 7.5, "intensity": 0.5},
            {"f1": 30.0, "f2": 2.5, "intensity": 0.4},
        ]
        
        analysis = analyze_2d_nmr("HMBC", peaks)
        
        assert analysis["experiment_type"] == "HMBC"
        assert "long-range" in analysis["notes"][0].lower()
    
    def test_analyze_2d_nmr_unknown_type(self):
        """Test analysis with unknown experiment type"""
        peaks = [{"f1": 7.5, "f2": 7.2, "intensity": 0.6}]
        
        analysis = analyze_2d_nmr("UNKNOWN", peaks)
        
        assert "error" in analysis
        assert "supported_types" in analysis


class TestAdvancedSpectroscopyIntegration:
    """Integration tests for advanced spectroscopy workflows"""
    
    def test_raman_functional_group_workflow(self):
        """Test complete Raman analysis workflow"""
        # Simulate Raman spectrum of organic compound
        wavenumbers = list(range(500, 3500, 100))
        intensities = [0.1] * len(wavenumbers)
        
        # Add characteristic peaks
        for i, wn in enumerate(wavenumbers):
            if 2800 <= wn <= 3000:
                intensities[i] = 0.9  # C-H stretch
            elif 1600 <= wn <= 1680:
                intensities[i] = 0.7  # Aromatic
        
        analysis = analyze_raman_spectrum(wavenumbers, intensities, threshold=0.5)
        
        assert len(analysis["peaks"]) >= 2
        assert len(analysis["functional_groups"]) >= 1
    
    def test_fluorescence_quantum_yield_workflow(self):
        """Test fluorescence quantum yield determination"""
        # Calculate quantum yield using standard
        qy = calculate_quantum_yield(
            sample_integrated_intensity=5000.0,
            sample_absorbance=0.05,
            standard_integrated_intensity=2500.0,
            standard_absorbance=0.05,
            standard_quantum_yield=0.54  # Quinine sulfate
        )
        
        assert 0 <= qy <= 1
        # Should be approximately 2x standard
    
    def test_cd_protein_characterization_workflow(self):
        """Test complete CD protein analysis"""
        # Simulated α-helical protein
        wavelengths = [190, 200, 208, 222, 250]
        ellipticities = [-10000, -20000, -32000, -33000, -5000]
        
        analysis = analyze_cd_spectrum(
            wavelengths=wavelengths,
            ellipticities=ellipticities,
            concentration=0.5,
            path_length=0.1,
            num_residues=150
        )
        
        # Should detect high α-helix content
        assert analysis["secondary_structure"]["alpha_helix_percent"] > 30
    
    def test_2d_nmr_structure_elucidation_workflow(self):
        """Test 2D NMR structure elucidation workflow"""
        # Simulate HSQC data
        hsqc_peaks = [
            {"f1": 25.0, "f2": 1.5, "intensity": 0.8},  # CH₃
            {"f1": 35.0, "f2": 2.8, "intensity": 0.7},  # CH₂
            {"f1": 128.0, "f2": 7.5, "intensity": 0.9},  # Aromatic CH
        ]
        
        hsqc_analysis = analyze_2d_nmr("HSQC", hsqc_peaks)
        
        # Should identify 3 C-H correlations
        assert hsqc_analysis["num_correlations"] == 3
        
        # Now analyze HMBC for connectivity
        hmbc_peaks = [
            {"f1": 140.0, "f2": 2.8, "intensity": 0.5},  # Long-range
            {"f1": 25.0, "f2": 7.5, "intensity": 0.3},   # Long-range
        ]
        
        # Convert HSQC correlations to reference format
        hsqc_ref = [
            {"carbon_ppm": c["carbon_ppm"], "proton_ppm": c["proton_ppm"]}
            for c in hsqc_analysis["correlations"]
        ]
        
        hmbc_analysis = analyze_2d_nmr("HMBC", hmbc_peaks, hsqc_reference=hsqc_ref)
        
        # Should find long-range correlations
        assert hmbc_analysis["num_correlations"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
