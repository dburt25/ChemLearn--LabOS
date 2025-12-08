"""Tests for physical chemistry thermodynamics module."""

import math
import pytest
from labos.modules.pchem.thermodynamics import (
    R_GAS,
    calculate_gibbs_free_energy,
    calculate_equilibrium_constant,
    calculate_delta_g_from_k,
    vant_hoff_equation,
    predict_spontaneity,
    analyze_temperature_dependence,
    compute_thermodynamics,
)


class TestGibbsFreeEnergy:
    """Test Gibbs free energy calculations."""

    def test_calculate_delta_g_positive(self):
        """Test ΔG calculation for non-spontaneous reaction."""
        # ΔH = 100 kJ/mol, ΔS = 50 J/(mol·K), T = 298 K
        delta_g = calculate_gibbs_free_energy(
            delta_h=100000,  # J/mol
            delta_s=50,      # J/(mol·K)
            temperature=298  # K
        )
        
        # ΔG = ΔH - TΔS = 100000 - 298*50 = 85100 J/mol
        expected = 100000 - 298 * 50
        assert abs(delta_g - expected) < 1

    def test_calculate_delta_g_negative(self):
        """Test ΔG calculation for spontaneous reaction."""
        # ΔH = -50 kJ/mol, ΔS = 100 J/(mol·K), T = 298 K
        delta_g = calculate_gibbs_free_energy(
            delta_h=-50000,
            delta_s=100,
            temperature=298
        )
        
        # ΔG = -50000 - 298*100 = -79800 J/mol (spontaneous)
        expected = -50000 - 298 * 100
        assert abs(delta_g - expected) < 1
        assert delta_g < 0  # Spontaneous

    def test_calculate_delta_g_at_equilibrium(self):
        """Test ΔG calculation near equilibrium (ΔG ≈ 0)."""
        # ΔH = 100 kJ/mol, ΔS = 335.6 J/(mol·K), T = 298 K
        # Designed so ΔG ≈ 0
        delta_g = calculate_gibbs_free_energy(
            delta_h=100000,
            delta_s=335.6,
            temperature=298
        )
        
        # ΔG should be very close to zero
        assert abs(delta_g) < 10


class TestEquilibriumConstant:
    """Test equilibrium constant calculations."""

    def test_calculate_k_from_negative_delta_g(self):
        """Test K calculation for favorable reaction (ΔG < 0)."""
        # ΔG = -10 kJ/mol at 298 K
        k = calculate_equilibrium_constant(
            delta_g=-10000,
            temperature=298
        )
        
        # K = exp(-ΔG/RT) = exp(10000/(8.314*298)) ≈ 56.9
        expected = math.exp(10000 / (R_GAS * 298))
        assert abs(k - expected) / expected < 0.01

    def test_calculate_k_from_positive_delta_g(self):
        """Test K calculation for unfavorable reaction (ΔG > 0)."""
        # ΔG = +10 kJ/mol at 298 K
        k = calculate_equilibrium_constant(
            delta_g=10000,
            temperature=298
        )
        
        # K = exp(-10000/(8.314*298)) ≈ 0.0176
        expected = math.exp(-10000 / (R_GAS * 298))
        assert abs(k - expected) / expected < 0.01
        assert k < 1  # Unfavorable

    def test_k_equals_one_when_delta_g_zero(self):
        """Test K = 1 when ΔG = 0."""
        k = calculate_equilibrium_constant(
            delta_g=0,
            temperature=298
        )
        
        assert abs(k - 1.0) < 0.01

    def test_large_negative_delta_g_gives_large_k(self):
        """Test that very favorable reactions have large K."""
        # ΔG = -50 kJ/mol
        k = calculate_equilibrium_constant(
            delta_g=-50000,
            temperature=298
        )
        
        assert k > 1e8  # Very large K


class TestDeltaGFromK:
    """Test calculating ΔG from equilibrium constant."""

    def test_calculate_delta_g_from_large_k(self):
        """Test ΔG calculation from large K (favorable reaction)."""
        # K = 100 at 298 K
        delta_g = calculate_delta_g_from_k(
            k_eq=100,
            temperature=298
        )
        
        # ΔG = -RT ln(K) = -8.314 * 298 * ln(100) ≈ -11408 J/mol
        expected = -R_GAS * 298 * math.log(100)
        assert abs(delta_g - expected) < 1
        assert delta_g < 0  # Favorable

    def test_calculate_delta_g_from_small_k(self):
        """Test ΔG calculation from small K (unfavorable reaction)."""
        # K = 0.01 at 298 K
        delta_g = calculate_delta_g_from_k(
            k_eq=0.01,
            temperature=298
        )
        
        # ΔG = -RT ln(0.01) = +8.314 * 298 * ln(100) ≈ +11408 J/mol
        expected = -R_GAS * 298 * math.log(0.01)
        assert abs(delta_g - expected) < 1
        assert delta_g > 0  # Unfavorable

    def test_delta_g_zero_when_k_equals_one(self):
        """Test ΔG = 0 when K = 1."""
        delta_g = calculate_delta_g_from_k(
            k_eq=1.0,
            temperature=298
        )
        
        assert abs(delta_g) < 0.1


class TestVantHoffEquation:
    """Test van't Hoff equation for temperature-dependent K."""

    def test_k_increases_with_temperature_for_endothermic(self):
        """Test that K increases with T for endothermic reactions (ΔH > 0)."""
        # ΔH = +50 kJ/mol (endothermic)
        k1 = 1.0  # K at 298 K
        
        k2 = vant_hoff_equation(
            k1=k1,
            delta_h=50000,
            t1=298,
            t2=350  # Higher temperature
        )
        
        # K should increase for endothermic reactions at higher T
        assert k2 > k1

    def test_k_decreases_with_temperature_for_exothermic(self):
        """Test that K decreases with T for exothermic reactions (ΔH < 0)."""
        # ΔH = -50 kJ/mol (exothermic)
        k1 = 100.0  # K at 298 K
        
        k2 = vant_hoff_equation(
            k1=k1,
            delta_h=-50000,
            t1=298,
            t2=350  # Higher temperature
        )
        
        # K should decrease for exothermic reactions at higher T
        assert k2 < k1

    def test_vant_hoff_reversibility(self):
        """Test that van't Hoff equation is reversible."""
        k1 = 10.0
        delta_h = 50000
        t1 = 298
        t2 = 350
        
        # Calculate K at T2
        k2 = vant_hoff_equation(k1, delta_h, t1, t2)
        
        # Calculate back to K at T1
        k1_calc = vant_hoff_equation(k2, delta_h, t2, t1)
        
        assert abs(k1 - k1_calc) / k1 < 0.01


class TestSpontaneityPrediction:
    """Test spontaneity prediction."""

    def test_spontaneous_at_all_temperatures(self):
        """Test spontaneous at all temperatures (ΔH < 0, ΔS > 0)."""
        result = predict_spontaneity(
            delta_h=-50000,  # Exothermic
            delta_s=100,     # Entropy increase
            temperature=298
        )
        
        assert result["delta_g"] < 0
        assert result["is_spontaneous"] is True
        assert "all temperatures" in result["interpretation"].lower()

    def test_non_spontaneous_at_all_temperatures(self):
        """Test non-spontaneous at all temperatures (ΔH > 0, ΔS < 0)."""
        result = predict_spontaneity(
            delta_h=50000,   # Endothermic
            delta_s=-100,    # Entropy decrease
            temperature=298
        )
        
        assert result["delta_g"] > 0
        assert result["is_spontaneous"] is False
        assert "not spontaneous" in result["interpretation"].lower()

    def test_spontaneous_at_high_temperature(self):
        """Test spontaneous only at high T (ΔH > 0, ΔS > 0)."""
        result = predict_spontaneity(
            delta_h=50000,   # Endothermic
            delta_s=200,     # Entropy increase
            temperature=400  # High temperature
        )
        
        # At high T, TΔS term dominates, making ΔG negative
        # ΔG = 50000 - 400*200 = -30000 (spontaneous)
        assert result["delta_g"] < 0
        assert result["is_spontaneous"] is True

    def test_spontaneous_at_low_temperature(self):
        """Test spontaneous only at low T (ΔH < 0, ΔS < 0)."""
        result = predict_spontaneity(
            delta_h=-50000,  # Exothermic
            delta_s=-100,    # Entropy decrease
            temperature=298  # Low temperature
        )
        
        # At low T, ΔH term dominates, making ΔG negative
        # ΔG = -50000 - 298*(-100) = -20200 (spontaneous)
        assert result["delta_g"] < 0
        assert result["is_spontaneous"] is True


class TestTemperatureDependence:
    """Test temperature dependence analysis."""

    def test_temperature_series_generation(self):
        """Test generation of temperature series."""
        result = analyze_temperature_dependence(
            delta_h=50000,
            delta_s=100,
            t_start=273,
            t_end=373,
            t_step=20
        )
        
        assert "temperature_series" in result
        temps = result["temperature_series"]
        
        # Should have 6 points: 273, 293, 313, 333, 353, 373
        assert len(temps) >= 5
        assert temps[0]["temperature"] == 273
        assert temps[-1]["temperature"] <= 373

    def test_delta_g_changes_with_temperature(self):
        """Test that ΔG values change across temperature range."""
        result = analyze_temperature_dependence(
            delta_h=50000,
            delta_s=100,
            t_start=273,
            t_end=373,
            t_step=50
        )
        
        temps = result["temperature_series"]
        delta_g_values = [t["delta_g"] for t in temps]
        
        # ΔG should be different at different temperatures
        assert len(set(delta_g_values)) > 1

    def test_spontaneity_transition_point(self):
        """Test finding temperature where reaction becomes spontaneous."""
        result = analyze_temperature_dependence(
            delta_h=50000,   # Endothermic
            delta_s=200,     # Entropy increase
            t_start=200,
            t_end=400,
            t_step=20
        )
        
        # Reaction should be non-spontaneous at low T, spontaneous at high T
        temps = result["temperature_series"]
        
        # Find transition point
        spontaneous_at_low = temps[0]["is_spontaneous"]
        spontaneous_at_high = temps[-1]["is_spontaneous"]
        
        # Should transition from non-spontaneous to spontaneous
        assert spontaneous_at_low is False
        assert spontaneous_at_high is True


class TestComputeThermodynamics:
    """Test main compute_thermodynamics function."""

    def test_compute_from_delta_h_and_delta_s(self):
        """Test computation from ΔH and ΔS."""
        result = compute_thermodynamics(
            delta_h=50000,
            delta_s=100,
            temperature=298
        )
        
        assert "delta_g" in result
        assert "k_eq" in result
        assert "is_spontaneous" in result
        
        # ΔG = 50000 - 298*100 = 20200 J/mol (positive)
        assert result["delta_g"] > 0
        assert result["is_spontaneous"] is False

    def test_compute_from_delta_g(self):
        """Test computation from ΔG directly."""
        result = compute_thermodynamics(
            delta_g=-10000,
            temperature=298
        )
        
        assert "delta_g" in result
        assert "k_eq" in result
        assert result["delta_g"] == -10000
        assert result["k_eq"] > 1  # Favorable

    def test_compute_from_k_eq(self):
        """Test computation from equilibrium constant."""
        result = compute_thermodynamics(
            k_eq=100,
            temperature=298
        )
        
        assert "delta_g" in result
        assert "k_eq" in result
        assert result["k_eq"] == 100
        assert result["delta_g"] < 0  # K > 1 means favorable

    def test_temperature_dependence_analysis(self):
        """Test temperature dependence analysis."""
        result = compute_thermodynamics(
            delta_h=50000,
            delta_s=100,
            temperature=298,
            analyze_temp_dependence=True
        )
        
        assert "temperature_analysis" in result
        assert "temperature_series" in result["temperature_analysis"]

    def test_no_temperature_dependence_by_default(self):
        """Test that temperature dependence is not analyzed by default."""
        result = compute_thermodynamics(
            delta_h=50000,
            delta_s=100,
            temperature=298
        )
        
        assert "temperature_analysis" not in result

    def test_missing_required_data_raises_error(self):
        """Test that missing required data raises ValueError."""
        with pytest.raises(ValueError):
            compute_thermodynamics(temperature=298)  # No thermodynamic data


class TestRGasConstant:
    """Test R gas constant value."""

    def test_r_gas_constant_value(self):
        """Test that R has correct value."""
        assert abs(R_GAS - 8.314) < 0.001

    def test_r_gas_used_in_calculations(self):
        """Test that R is used in calculations."""
        # ΔG = -RT ln(K)
        k = 10.0
        t = 298
        
        delta_g = calculate_delta_g_from_k(k, t)
        expected = -R_GAS * t * math.log(k)
        
        assert abs(delta_g - expected) < 0.1
