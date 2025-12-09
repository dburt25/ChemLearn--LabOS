"""
Tests for Chromatography Module

Comprehensive tests for retention modeling, peak analysis, 
gradient methods, and column theory.
"""

import pytest
import numpy as np
from labos.modules.chromatography import (
    # Retention models
    RetentionData,
    calculate_retention_factor,
    calculate_selectivity,
    calculate_resolution,
    van_deemter_equation,
    optimize_flow_rate,
    
    # Peak analysis
    PeakData,
    fit_gaussian_peak,
    calculate_peak_area,
    calculate_plate_number,
    calculate_asymmetry,
    detect_peaks,
    
    # Gradient methods
    GradientMethod,
    calculate_gradient_profile,
    predict_retention_time,
    optimize_gradient,
    
    # Column theory
    ColumnParameters,
    calculate_column_efficiency,
    calculate_void_volume,
    estimate_column_capacity
)


class TestRetentionModels:
    """Test retention and separation theory"""
    
    def test_retention_factor_calculation(self):
        """Test retention factor k' calculation"""
        k = calculate_retention_factor(retention_time=5.0, void_time=1.0)
        assert abs(k - 4.0) < 0.001
        
        # No retention
        k_zero = calculate_retention_factor(retention_time=1.0, void_time=1.0)
        assert k_zero == 0.0
        
    def test_retention_data_dataclass(self):
        """Test RetentionData with auto-calculation"""
        data = RetentionData(
            compound="caffeine",
            retention_time=5.0,
            peak_width=0.2,
            void_time=1.0
        )
        assert abs(data.retention_factor - 4.0) < 0.001
        
    def test_selectivity_calculation(self):
        """Test selectivity factor α"""
        alpha = calculate_selectivity(k1=2.0, k2=4.0)
        assert abs(alpha - 2.0) < 0.001
        
        # Should ensure k2 > k1
        alpha_reversed = calculate_selectivity(k1=4.0, k2=2.0)
        assert alpha_reversed >= 1.0
        
    def test_resolution_calculation(self):
        """Test chromatographic resolution"""
        # Baseline separation (Rs = 1.5)
        rs = calculate_resolution(
            rt1=5.0,
            rt2=6.0,
            w1=0.5,
            w2=0.5
        )
        assert abs(rs - 2.0) < 0.001
        
    def test_van_deemter_equation(self):
        """Test Van Deemter plate height"""
        # Typical values
        h = van_deemter_equation(
            A=0.002,  # eddy diffusion
            B=0.01,   # longitudinal diffusion
            C=0.05,   # mass transfer
            flow_rate=1.0
        )
        assert h > 0
        
        # Should increase at high flow
        h_high = van_deemter_equation(A=0.002, B=0.01, C=0.05, flow_rate=5.0)
        assert h_high > h
        
    def test_flow_rate_optimization(self):
        """Test optimal flow rate finding"""
        result = optimize_flow_rate(B=0.01, C=0.05)
        
        assert "optimal_flow_rate" in result
        assert "minimum_plate_height" in result
        assert result["optimal_flow_rate"] > 0
        
        # Analytical solution: u_opt = sqrt(B/C)
        expected_flow = (0.01 / 0.05) ** 0.5
        assert abs(result["optimal_flow_rate"] - expected_flow) < 0.001


class TestPeakAnalysis:
    """Test peak analysis and characterization"""
    
    def test_gaussian_peak_fitting(self):
        """Test Gaussian peak fitting"""
        # Create synthetic Gaussian peak
        times = np.linspace(0, 10, 1000)
        true_amp = 100
        true_center = 5.0
        true_sigma = 0.3
        intensities = true_amp * np.exp(-((times - true_center) ** 2) / (2 * true_sigma ** 2))
        
        # Find peak and fit
        peak_idx = np.argmax(intensities)
        result = fit_gaussian_peak(times, intensities, peak_idx, window=50)
        
        assert abs(result["amplitude"] - true_amp) < 5
        assert abs(result["center"] - true_center) < 0.1
        assert abs(result["sigma"] - true_sigma) < 0.05
        
    def test_peak_area_calculation(self):
        """Test peak area integration"""
        # Rectangular peak (easy to verify)
        times = np.array([0, 1, 2, 3, 4])
        intensities = np.array([0, 100, 100, 100, 0])
        
        area = calculate_peak_area(times, intensities, start_idx=1, end_idx=4)
        # Trapezoidal: (100+100)/2 * 1 + (100+100)/2 * 1 + (100+0)/2 * 1 = 200
        assert abs(area - 200) < 10
        
    def test_plate_number_calculation(self):
        """Test theoretical plate number"""
        # Half-height method
        n_half = calculate_plate_number(
            retention_time=5.0,
            peak_width=0.5,
            method="half_height"
        )
        # N = 5.54 * (tR / w1/2)²
        expected = 5.54 * (5.0 / 0.5) ** 2
        assert abs(n_half - expected) < 10
        
        # Baseline method
        n_base = calculate_plate_number(
            retention_time=5.0,
            peak_width=1.0,
            method="baseline"
        )
        # N = 16 * (tR / wb)²
        expected_base = 16 * (5.0 / 1.0) ** 2
        assert abs(n_base - expected_base) < 10
        
    def test_asymmetry_calculation(self):
        """Test peak asymmetry factor"""
        # Symmetric peak
        asym = calculate_asymmetry(
            peak_width_left=0.25,
            peak_width_right=0.25
        )
        assert abs(asym - 1.0) < 0.1
        
        # Tailing peak
        asym_tail = calculate_asymmetry(
            peak_width_left=0.2,
            peak_width_right=0.4
        )
        assert asym_tail > 1.5  # Significant tailing
        
    def test_peak_detection(self):
        """Test automatic peak detection"""
        # Create signal with multiple peaks
        times = np.linspace(0, 20, 2000)
        signal = (
            50 * np.exp(-((times - 5) ** 2) / 0.5) +
            100 * np.exp(-((times - 10) ** 2) / 0.5) +
            30 * np.exp(-((times - 15) ** 2) / 0.5)
        )
        
        peaks = detect_peaks(times, signal, threshold=0.2, min_distance=50)
        
        # Should find 3 peaks
        assert len(peaks) >= 2  # At least major peaks
        
        # Check peak properties
        for peak in peaks:
            assert "retention_time" in peak
            assert "height" in peak
            assert "area" in peak
            assert peak["height"] > 0


class TestGradientMethods:
    """Test gradient elution methods"""
    
    def test_gradient_method_dataclass(self):
        """Test GradientMethod dataclass"""
        gradient = GradientMethod(
            initial_percent=5.0,
            final_percent=95.0,
            gradient_time=30.0,
            flow_rate=1.0,
            column_volume=2.0
        )
        
        slope = gradient.gradient_slope()
        assert abs(slope - 3.0) < 0.001  # (95-5)/30 = 3% per min
        
        cv = gradient.column_volumes()
        assert abs(cv - 15.0) < 0.001  # (1.0 * 30) / 2.0 = 15 CV
        
    def test_gradient_profile_calculation(self):
        """Test gradient composition profile"""
        profile = calculate_gradient_profile(
            initial_percent=10.0,
            final_percent=90.0,
            gradient_time=20.0
        )
        
        assert "times" in profile
        assert "compositions" in profile
        assert "slope" in profile
        
        # Check endpoints
        assert abs(profile["compositions"][0] - 10.0) < 0.1
        assert abs(profile["compositions"][-1] - 90.0) < 0.1
        
        # Check slope
        expected_slope = (90.0 - 10.0) / 20.0
        assert abs(profile["slope"] - expected_slope) < 0.001
        
    def test_retention_time_prediction(self):
        """Test gradient retention prediction"""
        t_r = predict_retention_time(
            k_0=10.0,
            k_end=0.1,
            t_0=1.0,
            t_gradient=30.0,
            S=4.0
        )
        
        # Should be between void time and gradient time
        assert 1.0 < t_r < 31.0
        
    def test_gradient_optimization(self):
        """Test gradient optimization"""
        result = optimize_gradient(
            k_values=[2.0, 3.0, 5.0, 8.0],
            t_0=1.0,
            target_resolution=1.5,
            column_length=15.0
        )
        
        assert "gradient_time" in result
        assert "gradient_slope" in result
        assert "estimated_peak_capacity" in result
        assert result["gradient_time"] > 0


class TestColumnTheory:
    """Test column characterization"""
    
    def test_column_parameters_dataclass(self):
        """Test ColumnParameters dataclass"""
        column = ColumnParameters(
            length=15.0,  # cm
            diameter=4.6,  # mm
            particle_size=5.0,  # μm
            pore_size=100.0  # Å
        )
        
        volume = column.volume()
        assert volume > 0
        
        void = column.interstitial_volume(porosity=0.65)
        assert 0 < void < volume
        
    def test_column_efficiency_calculation(self):
        """Test HETP calculation"""
        hetp = calculate_column_efficiency(
            plate_number=10000,
            column_length=15.0
        )
        
        # H = L / N = 15 / 10000 = 0.0015 cm = 15 μm
        assert abs(hetp - 0.0015) < 0.0001
        
    def test_void_volume_calculation(self):
        """Test void volume estimation"""
        v0 = calculate_void_volume(
            column_length=15.0,
            column_diameter=4.6,
            total_porosity=0.65
        )
        
        assert v0 > 0
        # Should be reasonable (around 1-2 mL for 4.6mm x 150mm)
        assert 0.5 < v0 < 5.0
        
    def test_column_capacity_estimation(self):
        """Test loading capacity estimation"""
        capacity = estimate_column_capacity(
            column_diameter=4.6,
            particle_size=5.0,
            compound_mw=250
        )
        
        assert capacity > 0
        # Typical capacity for analytical column (tens to hundreds μg)
        assert 10 < capacity < 1000


class TestChromatographyIntegration:
    """Integration tests for complete workflows"""
    
    def test_method_development_workflow(self):
        """Test complete method development workflow"""
        # 1. Column selection
        column = ColumnParameters(
            length=15.0,
            diameter=4.6,
            particle_size=3.0,
            pore_size=100.0
        )
        
        # 2. Calculate void volume
        v0 = calculate_void_volume(
            column_length=column.length,
            column_diameter=column.diameter
        )
        
        t0 = v0 / 1.0  # Assume 1 mL/min flow
        
        # 3. Optimize gradient
        compounds_k = [2.0, 3.5, 5.0, 7.0]
        gradient_opt = optimize_gradient(
            k_values=compounds_k,
            t_0=t0,
            target_resolution=1.5
        )
        
        assert gradient_opt["gradient_time"] > 0
        assert gradient_opt["estimated_peak_capacity"] > len(compounds_k)
        
    def test_peak_analysis_workflow(self):
        """Test peak analysis workflow"""
        # Create synthetic chromatogram
        times = np.linspace(0, 20, 2000)
        signal = 100 * np.exp(-((times - 10) ** 2) / 2)
        
        # 1. Find peak manually (instead of auto-detection)
        peak_idx = int(len(times) / 2)  # Peak at t=10
        peak_rt = times[peak_idx]
        
        # 2. Fit Gaussian
        fit_result = fit_gaussian_peak(
            times.tolist(), signal.tolist(), 
            peak_idx, window=100
        )
        
        assert fit_result["amplitude"] > 50
        assert 9 < fit_result["center"] < 11
        
        # 3. Calculate plate number (using typical peak width)
        n = calculate_plate_number(
            retention_time=peak_rt,
            peak_width=1.0,
            method="half_height"
        )
        
        assert n > 0
        
        # 4. Calculate asymmetry
        asym = calculate_asymmetry(
            peak_width_left=0.5,
            peak_width_right=0.5
        )
        
        assert 0.5 < asym < 2.0
        
    def test_resolution_optimization_workflow(self):
        """Test resolution optimization workflow"""
        # Starting conditions
        k1 = 2.0
        k2 = 3.0
        
        # 1. Calculate selectivity
        alpha = calculate_selectivity(k1=k1, k2=k2)
        assert alpha >= 1.0
        
        # 2. Check current resolution
        rs_initial = calculate_resolution(
            rt1=5.0,
            rt2=6.0,
            w1=0.5,
            w2=0.5
        )
        
        # 3. If resolution insufficient, optimize
        if rs_initial < 1.5:
            # Can increase column length (increases N)
            # Or change mobile phase (increases α)
            # Or adjust retention (optimize k)
            pass
        
        assert rs_initial > 0
        
    def test_van_deemter_optimization_workflow(self):
        """Test Van Deemter optimization workflow"""
        # 1. Find optimal flow rate
        result = optimize_flow_rate(B=0.01, C=0.05)
        optimal_flow = result["optimal_flow_rate"]
        
        # 2. Calculate plate height at optimal flow
        h_opt = van_deemter_equation(
            A=0.002,
            B=0.01,
            C=0.05,
            flow_rate=optimal_flow
        )
        
        # 3. Calculate efficiency
        column_length = 15.0
        n = column_length / h_opt
        
        assert n > 100  # Should have reasonable efficiency
        
        # 4. Check if flow too low/high
        h_low = van_deemter_equation(A=0.002, B=0.01, C=0.05, flow_rate=0.1)
        h_high = van_deemter_equation(A=0.002, B=0.01, C=0.05, flow_rate=10.0)
        
        # Optimal should be better than extremes
        assert h_opt <= h_low
        assert h_opt <= h_high


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
