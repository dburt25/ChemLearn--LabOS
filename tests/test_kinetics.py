"""Tests for physical chemistry kinetics module."""

import math
import pytest
from labos.modules.pchem.kinetics import (
    calculate_rate_0th_order,
    calculate_rate_1st_order,
    calculate_rate_2nd_order,
    calculate_half_life,
    arrhenius_equation,
    arrhenius_temperature_ratio,
    calculate_activation_energy,
    simulate_reaction_kinetics,
    compute_kinetics,
)


class TestZerothOrderKinetics:
    """Test 0th order reaction kinetics."""

    def test_0th_order_concentration_decrease(self):
        """Test 0th order concentration decreases linearly."""
        conc = calculate_rate_0th_order(
            initial_conc=10.0,
            k=0.5,
            time=2.0
        )
        
        # [A] = [A]₀ - kt = 10 - 0.5*2 = 9.0
        assert abs(conc - 9.0) < 0.01

    def test_0th_order_complete_consumption(self):
        """Test 0th order reaction until complete."""
        conc = calculate_rate_0th_order(
            initial_conc=5.0,
            k=0.5,
            time=10.0
        )
        
        # [A] = 5 - 0.5*10 = 0 (complete consumption)
        assert conc >= 0  # Cannot go negative
        assert conc < 0.1

    def test_0th_order_cannot_go_negative(self):
        """Test 0th order concentration cannot go negative."""
        conc = calculate_rate_0th_order(
            initial_conc=5.0,
            k=1.0,
            time=10.0  # Would give -5 without clamp
        )
        
        assert conc == 0  # Clamped to zero


class TestFirstOrderKinetics:
    """Test 1st order reaction kinetics."""

    def test_1st_order_exponential_decay(self):
        """Test 1st order concentration decays exponentially."""
        conc = calculate_rate_1st_order(
            initial_conc=10.0,
            k=0.1,
            time=5.0
        )
        
        # [A] = [A]₀ * exp(-kt) = 10 * exp(-0.5) ≈ 6.065
        expected = 10.0 * math.exp(-0.1 * 5.0)
        assert abs(conc - expected) < 0.01

    def test_1st_order_half_life(self):
        """Test 1st order at one half-life."""
        k = 0.693  # ln(2)
        conc = calculate_rate_1st_order(
            initial_conc=100.0,
            k=k,
            time=1.0  # t = t₁/₂
        )
        
        # Should be at half concentration
        assert abs(conc - 50.0) < 1.0

    def test_1st_order_never_reaches_zero(self):
        """Test 1st order never quite reaches zero."""
        conc = calculate_rate_1st_order(
            initial_conc=100.0,
            k=0.1,
            time=100.0  # Very long time
        )
        
        # Should be very small but not zero
        assert conc > 0
        assert conc < 0.01


class TestSecondOrderKinetics:
    """Test 2nd order reaction kinetics."""

    def test_2nd_order_concentration_decrease(self):
        """Test 2nd order concentration decrease."""
        conc = calculate_rate_2nd_order(
            initial_conc=1.0,
            k=0.5,
            time=2.0
        )
        
        # [A] = [A]₀ / (1 + kt[A]₀) = 1 / (1 + 0.5*2*1) = 1/2 = 0.5
        expected = 1.0 / (1.0 + 0.5 * 2.0 * 1.0)
        assert abs(conc - expected) < 0.01

    def test_2nd_order_slower_than_1st(self):
        """Test 2nd order is slower than 1st at low concentration."""
        initial = 0.1
        k = 1.0
        t = 5.0
        
        conc_1st = calculate_rate_1st_order(initial, k, t)
        conc_2nd = calculate_rate_2nd_order(initial, k, t)
        
        # At low concentration, 2nd order is slower
        assert conc_2nd > conc_1st


class TestHalfLife:
    """Test half-life calculations."""

    def test_0th_order_half_life(self):
        """Test 0th order half-life."""
        t_half = calculate_half_life(order=0, initial_conc=10.0, k=2.0)
        
        # t₁/₂ = [A]₀ / (2k) = 10 / (2*2) = 2.5
        expected = 10.0 / (2.0 * 2.0)
        assert abs(t_half - expected) < 0.01

    def test_1st_order_half_life(self):
        """Test 1st order half-life."""
        t_half = calculate_half_life(order=1, k=0.693)
        
        # t₁/₂ = ln(2) / k = 0.693 / 0.693 = 1.0
        expected = math.log(2) / 0.693
        assert abs(t_half - expected) < 0.01

    def test_1st_order_half_life_independent_of_concentration(self):
        """Test 1st order half-life is independent of concentration."""
        k = 0.1
        t_half_1 = calculate_half_life(order=1, initial_conc=10.0, k=k)
        t_half_2 = calculate_half_life(order=1, initial_conc=100.0, k=k)
        
        # Should be the same
        assert abs(t_half_1 - t_half_2) < 0.01

    def test_2nd_order_half_life(self):
        """Test 2nd order half-life."""
        t_half = calculate_half_life(order=2, initial_conc=1.0, k=0.5)
        
        # t₁/₂ = 1 / (k[A]₀) = 1 / (0.5*1) = 2.0
        expected = 1.0 / (0.5 * 1.0)
        assert abs(t_half - expected) < 0.01

    def test_2nd_order_half_life_depends_on_concentration(self):
        """Test 2nd order half-life depends on concentration."""
        k = 0.5
        t_half_1 = calculate_half_life(order=2, initial_conc=1.0, k=k)
        t_half_2 = calculate_half_life(order=2, initial_conc=2.0, k=k)
        
        # Higher concentration gives shorter half-life
        assert t_half_2 < t_half_1

    def test_invalid_order_raises_error(self):
        """Test invalid order raises ValueError."""
        with pytest.raises(ValueError):
            calculate_half_life(order=3, k=1.0)


class TestArrheniusEquation:
    """Test Arrhenius equation."""

    def test_arrhenius_basic_calculation(self):
        """Test basic Arrhenius equation calculation."""
        k = arrhenius_equation(
            a_factor=1e10,
            activation_energy=50000,  # J/mol
            temperature=298
        )
        
        # k = A * exp(-Ea/RT)
        r = 8.314
        expected = 1e10 * math.exp(-50000 / (r * 298))
        assert abs(k - expected) / expected < 0.01

    def test_higher_temperature_increases_rate(self):
        """Test higher temperature increases rate constant."""
        a = 1e10
        ea = 50000
        
        k_low = arrhenius_equation(a, ea, 273)
        k_high = arrhenius_equation(a, ea, 373)
        
        # Higher T should give higher k
        assert k_high > k_low

    def test_higher_activation_energy_decreases_rate(self):
        """Test higher activation energy decreases rate constant."""
        a = 1e10
        t = 298
        
        k_low_ea = arrhenius_equation(a, 30000, t)
        k_high_ea = arrhenius_equation(a, 80000, t)
        
        # Higher Ea should give lower k
        assert k_high_ea < k_low_ea


class TestArrheniusTemperatureRatio:
    """Test Arrhenius temperature ratio."""

    def test_temperature_ratio_calculation(self):
        """Test calculation of k ratio at two temperatures."""
        ratio = arrhenius_temperature_ratio(
            activation_energy=50000,
            t1=298,
            t2=308  # 10 K increase
        )
        
        # k2/k1 = exp(Ea/R * (1/T1 - 1/T2))
        r = 8.314
        expected = math.exp(50000 / r * (1/298 - 1/308))
        assert abs(ratio - expected) / expected < 0.01

    def test_temperature_increase_gives_ratio_greater_than_one(self):
        """Test that temperature increase gives ratio > 1."""
        ratio = arrhenius_temperature_ratio(
            activation_energy=50000,
            t1=298,
            t2=350
        )
        
        assert ratio > 1.0

    def test_temperature_decrease_gives_ratio_less_than_one(self):
        """Test that temperature decrease gives ratio < 1."""
        ratio = arrhenius_temperature_ratio(
            activation_energy=50000,
            t1=350,
            t2=298
        )
        
        assert ratio < 1.0


class TestActivationEnergy:
    """Test activation energy calculation."""

    def test_calculate_ea_from_two_temperatures(self):
        """Test calculating Ea from rate constants at two temperatures."""
        # Use Arrhenius to generate test data
        a = 1e10
        ea_true = 50000
        t1 = 298
        t2 = 350
        
        k1 = arrhenius_equation(a, ea_true, t1)
        k2 = arrhenius_equation(a, ea_true, t2)
        
        # Calculate Ea back
        ea_calc = calculate_activation_energy(k1, k2, t1, t2)
        
        # Should recover the original Ea
        assert abs(ea_calc - ea_true) / ea_true < 0.01

    def test_ea_positive_for_temperature_dependent_reaction(self):
        """Test that Ea is positive for normal reactions."""
        # k increases with temperature
        ea = calculate_activation_energy(
            k1=1.0,
            k2=2.0,
            t1=298,
            t2=350
        )
        
        assert ea > 0


class TestReactionSimulation:
    """Test reaction kinetics simulation."""

    def test_simulate_1st_order_reaction(self):
        """Test simulation of 1st order reaction."""
        result = simulate_reaction_kinetics(
            initial_conc=100.0,
            k=0.1,
            order=1,
            t_end=10.0,
            n_points=11
        )
        
        assert "time_points" in result
        assert "concentrations" in result
        
        # Should have 11 points
        assert len(result["time_points"]) == 11
        assert len(result["concentrations"]) == 11
        
        # First point should be initial concentration
        assert abs(result["concentrations"][0] - 100.0) < 0.1
        
        # Last point should be lower
        assert result["concentrations"][-1] < 100.0

    def test_simulate_shows_concentration_decrease(self):
        """Test that simulation shows concentration decreasing."""
        result = simulate_reaction_kinetics(
            initial_conc=100.0,
            k=0.5,
            order=1,
            t_end=5.0,
            n_points=6
        )
        
        conc = result["concentrations"]
        
        # Concentration should monotonically decrease
        for i in range(len(conc) - 1):
            assert conc[i] >= conc[i+1]

    def test_simulate_0th_order_linear(self):
        """Test 0th order simulation is linear."""
        result = simulate_reaction_kinetics(
            initial_conc=10.0,
            k=1.0,
            order=0,
            t_end=5.0,
            n_points=6
        )
        
        conc = result["concentrations"]
        times = result["time_points"]
        
        # Check linearity: Δ[A] = k*Δt
        for i in range(1, len(conc) - 1):
            if conc[i] > 0:  # Before complete consumption
                delta_conc = conc[i-1] - conc[i]
                delta_time = times[i] - times[i-1]
                rate = delta_conc / delta_time
                assert abs(rate - 1.0) < 0.1  # k = 1.0


class TestComputeKinetics:
    """Test main compute_kinetics function."""

    def test_compute_with_rate_constant(self):
        """Test computation with given rate constant."""
        result = compute_kinetics(
            k=0.1,
            initial_conc=100.0,
            order=1,
            time=5.0
        )
        
        assert "k" in result
        assert "concentration" in result
        assert "half_life" in result
        
        assert result["k"] == 0.1
        assert result["concentration"] < 100.0  # Decreased

    def test_compute_with_arrhenius(self):
        """Test computation with Arrhenius parameters."""
        result = compute_kinetics(
            a_factor=1e10,
            activation_energy=50000,
            temperature=298,
            initial_conc=100.0,
            order=1,
            time=5.0
        )
        
        assert "k" in result
        assert "concentration" in result
        assert result["k"] > 0

    def test_compute_with_simulation(self):
        """Test computation with time series simulation."""
        result = compute_kinetics(
            k=0.1,
            initial_conc=100.0,
            order=1,
            simulate=True
        )
        
        assert "simulation" in result
        assert "time_points" in result["simulation"]
        assert "concentrations" in result["simulation"]

    def test_compute_without_simulation(self):
        """Test computation without simulation."""
        result = compute_kinetics(
            k=0.1,
            initial_conc=100.0,
            order=1,
            simulate=False
        )
        
        assert "simulation" not in result

    def test_compute_calculates_half_life(self):
        """Test that half-life is calculated."""
        result = compute_kinetics(
            k=0.693,
            initial_conc=100.0,
            order=1
        )
        
        assert "half_life" in result
        # t₁/₂ ≈ 1.0 for k=0.693
        assert abs(result["half_life"] - 1.0) < 0.1

    def test_compute_missing_data_raises_error(self):
        """Test that missing required data raises ValueError."""
        with pytest.raises(ValueError):
            compute_kinetics(temperature=298)  # No k or Arrhenius params
