"""Tests for error propagation utilities."""

import math
import pytest
from labos.modules.pchem.error_propagation import (
    propagate_addition,
    propagate_subtraction,
    propagate_multiplication,
    propagate_division,
    propagate_power,
    propagate_function,
    propagate_correlated,
    relative_error,
    percent_error,
    weighted_average,
    calculate_error_propagation,
)


class TestAddition:
    """Test error propagation for addition."""

    def test_add_two_values(self):
        """Test adding two values with errors."""
        result, error = propagate_addition([
            (10.0, 0.5),
            (5.0, 0.3)
        ])
        
        assert result == 15.0
        # σ = √(0.5² + 0.3²) = √(0.25 + 0.09) = √0.34 ≈ 0.583
        expected_error = math.sqrt(0.5**2 + 0.3**2)
        assert abs(error - expected_error) < 0.01

    def test_add_multiple_values(self):
        """Test adding multiple values."""
        result, error = propagate_addition([
            (10.0, 0.5),
            (5.0, 0.3),
            (3.0, 0.2)
        ])
        
        assert result == 18.0
        expected_error = math.sqrt(0.5**2 + 0.3**2 + 0.2**2)
        assert abs(error - expected_error) < 0.01

    def test_add_with_zero_error(self):
        """Test addition when one value has zero error."""
        result, error = propagate_addition([
            (10.0, 0.5),
            (5.0, 0.0)
        ])
        
        assert result == 15.0
        assert abs(error - 0.5) < 0.01


class TestSubtraction:
    """Test error propagation for subtraction."""

    def test_subtract_two_values(self):
        """Test subtracting two values with errors."""
        result, error = propagate_subtraction(
            minuend=(10.0, 0.5),
            subtrahend=(3.0, 0.2)
        )
        
        assert result == 7.0
        # σ = √(0.5² + 0.2²) = √(0.25 + 0.04) = √0.29 ≈ 0.539
        expected_error = math.sqrt(0.5**2 + 0.2**2)
        assert abs(error - expected_error) < 0.01

    def test_subtraction_errors_add_in_quadrature(self):
        """Test that errors add in quadrature (not linearly)."""
        result, error = propagate_subtraction(
            minuend=(100.0, 5.0),
            subtrahend=(50.0, 3.0)
        )
        
        # Error should be √(5² + 3²) = √34 ≈ 5.83, NOT 5+3=8
        expected = math.sqrt(5**2 + 3**2)
        assert abs(error - expected) < 0.01
        assert error < 8.0  # Not linear addition


class TestMultiplication:
    """Test error propagation for multiplication."""

    def test_multiply_two_values(self):
        """Test multiplying two values with errors."""
        result, error = propagate_multiplication([
            (10.0, 0.5),
            (5.0, 0.2)
        ])
        
        assert result == 50.0
        
        # Relative errors: 0.5/10 = 0.05, 0.2/5 = 0.04
        # Combined: √(0.05² + 0.04²) = 0.0640
        # Absolute: 50 * 0.0640 = 3.20
        rel_error = math.sqrt((0.5/10)**2 + (0.2/5)**2)
        expected_error = 50.0 * rel_error
        assert abs(error - expected_error) < 0.1

    def test_multiply_multiple_values(self):
        """Test multiplying multiple values."""
        result, error = propagate_multiplication([
            (2.0, 0.1),
            (3.0, 0.15),
            (4.0, 0.2)
        ])
        
        assert result == 24.0
        
        # Relative errors combine in quadrature
        rel_error = math.sqrt((0.1/2)**2 + (0.15/3)**2 + (0.2/4)**2)
        expected_error = 24.0 * rel_error
        assert abs(error - expected_error) < 0.5

    def test_multiply_zero_value_raises_error(self):
        """Test that multiplying by zero raises ValueError."""
        with pytest.raises(ValueError):
            propagate_multiplication([
                (10.0, 0.5),
                (0.0, 0.1)
            ])


class TestDivision:
    """Test error propagation for division."""

    def test_divide_two_values(self):
        """Test dividing two values with errors."""
        result, error = propagate_division(
            numerator=(10.0, 0.5),
            denominator=(2.0, 0.1)
        )
        
        assert result == 5.0
        
        # Relative errors: 0.5/10 = 0.05, 0.1/2 = 0.05
        # Combined: √(0.05² + 0.05²) = 0.0707
        # Absolute: 5 * 0.0707 = 0.354
        rel_error = math.sqrt((0.5/10)**2 + (0.1/2)**2)
        expected_error = 5.0 * rel_error
        assert abs(error - expected_error) < 0.01

    def test_divide_by_zero_raises_error(self):
        """Test that division by zero raises ValueError."""
        with pytest.raises(ValueError):
            propagate_division(
                numerator=(10.0, 0.5),
                denominator=(0.0, 0.1)
            )


class TestPower:
    """Test error propagation for power function."""

    def test_square_value(self):
        """Test squaring a value with error."""
        result, error = propagate_power(
            value=10.0,
            error=0.5,
            exponent=2.0
        )
        
        assert result == 100.0
        
        # σ_z/z = |n| * σ_x/x = 2 * 0.5/10 = 0.1
        # σ_z = 100 * 0.1 = 10.0
        expected_error = 100.0 * 2.0 * (0.5 / 10.0)
        assert abs(error - expected_error) < 0.1

    def test_cube_value(self):
        """Test cubing a value with error."""
        result, error = propagate_power(
            value=5.0,
            error=0.2,
            exponent=3.0
        )
        
        assert result == 125.0
        
        # σ_z/z = |3| * 0.2/5 = 0.12
        # σ_z = 125 * 0.12 = 15.0
        expected_error = 125.0 * 3.0 * (0.2 / 5.0)
        assert abs(error - expected_error) < 0.1

    def test_square_root(self):
        """Test square root (exponent = 0.5) with error."""
        result, error = propagate_power(
            value=100.0,
            error=2.0,
            exponent=0.5
        )
        
        assert result == 10.0
        
        # σ_z/z = |0.5| * 2/100 = 0.01
        # σ_z = 10 * 0.01 = 0.1
        expected_error = 10.0 * 0.5 * (2.0 / 100.0)
        assert abs(error - expected_error) < 0.01

    def test_power_zero_base_raises_error(self):
        """Test that zero base raises ValueError."""
        with pytest.raises(ValueError):
            propagate_power(0.0, 0.1, 2.0)


class TestFunctionPropagation:
    """Test error propagation through arbitrary functions."""

    def test_linear_function(self):
        """Test propagation through linear function."""
        # f(x) = 2x, df/dx = 2
        error = propagate_function(
            value=10.0,
            error=0.5,
            derivative=2.0
        )
        
        # σ_f = |df/dx| * σ_x = 2 * 0.5 = 1.0
        assert abs(error - 1.0) < 0.01

    def test_sine_function(self):
        """Test propagation through sine function."""
        # f(x) = sin(x), df/dx = cos(x)
        # At x = 0.5 rad, cos(0.5) ≈ 0.8776
        error = propagate_function(
            value=0.5,
            error=0.01,
            derivative=0.8776
        )
        
        expected = 0.8776 * 0.01
        assert abs(error - expected) < 0.001


class TestCorrelatedVariables:
    """Test error propagation with correlated variables."""

    def test_perfect_correlation_addition(self):
        """Test addition with perfect correlation (ρ=1)."""
        result, error = propagate_correlated(
            x=10.0,
            sigma_x=0.5,
            y=5.0,
            sigma_y=0.3,
            correlation=1.0,
            operation="add"
        )
        
        assert result == 15.0
        
        # σ² = 0.5² + 0.3² + 2*1*0.5*0.3 = 0.25 + 0.09 + 0.30 = 0.64
        # σ = 0.8 (linear addition when perfectly correlated)
        expected_error = math.sqrt(0.5**2 + 0.3**2 + 2*1*0.5*0.3)
        assert abs(error - expected_error) < 0.01

    def test_no_correlation(self):
        """Test addition with no correlation (ρ=0)."""
        result, error = propagate_correlated(
            x=10.0,
            sigma_x=0.5,
            y=5.0,
            sigma_y=0.3,
            correlation=0.0,
            operation="add"
        )
        
        # Should be same as normal addition
        expected_error = math.sqrt(0.5**2 + 0.3**2)
        assert abs(error - expected_error) < 0.01

    def test_negative_correlation(self):
        """Test addition with negative correlation."""
        result, error = propagate_correlated(
            x=10.0,
            sigma_x=0.5,
            y=5.0,
            sigma_y=0.3,
            correlation=-0.5,
            operation="add"
        )
        
        # Negative correlation reduces combined error
        expected_error = math.sqrt(0.5**2 + 0.3**2 - 2*0.5*0.5*0.3)
        assert abs(error - expected_error) < 0.01

    def test_invalid_correlation_raises_error(self):
        """Test that invalid correlation coefficient raises ValueError."""
        with pytest.raises(ValueError):
            propagate_correlated(10.0, 0.5, 5.0, 0.3, correlation=1.5, operation="add")


class TestRelativeError:
    """Test relative and percent error calculations."""

    def test_relative_error_calculation(self):
        """Test relative error calculation."""
        rel_err = relative_error(value=100.0, error=5.0)
        
        assert abs(rel_err - 0.05) < 0.001

    def test_percent_error_calculation(self):
        """Test percent error calculation."""
        pct_err = percent_error(value=100.0, error=5.0)
        
        assert abs(pct_err - 5.0) < 0.01

    def test_relative_error_zero_value_raises_error(self):
        """Test that zero value raises ValueError."""
        with pytest.raises(ValueError):
            relative_error(0.0, 0.1)


class TestWeightedAverage:
    """Test weighted average calculation."""

    def test_weighted_average_calculation(self):
        """Test weighted average gives more weight to precise measurements."""
        avg, uncertainty = weighted_average([
            (10.0, 0.5),  # More precise (higher weight)
            (10.2, 1.0),  # Less precise (lower weight)
            (9.8, 0.3),   # Most precise (highest weight)
        ])
        
        # Average should be close to 9.8 (most precise measurement)
        assert abs(avg - 9.9) < 0.2
        
        # Uncertainty should be smaller than any individual measurement
        assert uncertainty < 0.3

    def test_weighted_average_single_measurement(self):
        """Test weighted average with single measurement."""
        avg, uncertainty = weighted_average([
            (10.0, 0.5)
        ])
        
        assert avg == 10.0
        assert abs(uncertainty - 0.5) < 0.01

    def test_empty_list_raises_error(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError):
            weighted_average([])


class TestCalculateErrorPropagation:
    """Test main calculate_error_propagation function."""

    def test_addition_operation(self):
        """Test addition operation through main function."""
        result = calculate_error_propagation(
            operation="add",
            values=[10.0, 5.0],
            errors=[0.5, 0.3]
        )
        
        assert "result" in result
        assert "absolute_error" in result
        assert "relative_error" in result
        assert "percent_error" in result
        
        assert result["result"] == 15.0

    def test_subtraction_operation(self):
        """Test subtraction operation."""
        result = calculate_error_propagation(
            operation="subtract",
            values=[10.0, 3.0],
            errors=[0.5, 0.2]
        )
        
        assert result["result"] == 7.0

    def test_multiplication_operation(self):
        """Test multiplication operation."""
        result = calculate_error_propagation(
            operation="multiply",
            values=[10.0, 5.0],
            errors=[0.5, 0.2]
        )
        
        assert result["result"] == 50.0

    def test_division_operation(self):
        """Test division operation."""
        result = calculate_error_propagation(
            operation="divide",
            values=[10.0, 2.0],
            errors=[0.5, 0.1]
        )
        
        assert result["result"] == 5.0

    def test_power_operation(self):
        """Test power operation."""
        result = calculate_error_propagation(
            operation="power",
            values=[10.0],
            errors=[0.5],
            exponent=2.0
        )
        
        assert result["result"] == 100.0

    def test_weighted_average_operation(self):
        """Test weighted average operation."""
        result = calculate_error_propagation(
            operation="weighted_average",
            values=[10.0, 10.2, 9.8],
            errors=[0.5, 1.0, 0.3]
        )
        
        assert "result" in result
        assert abs(result["result"] - 10.0) < 0.5

    def test_result_includes_all_error_types(self):
        """Test that result includes absolute, relative, and percent errors."""
        result = calculate_error_propagation(
            operation="add",
            values=[10.0, 5.0],
            errors=[0.5, 0.3]
        )
        
        assert result["absolute_error"] > 0
        assert result["relative_error"] > 0
        assert result["percent_error"] > 0
        
        # Check relationship: percent = relative * 100
        expected_percent = result["relative_error"] * 100
        assert abs(result["percent_error"] - expected_percent) < 0.01

    def test_mismatched_values_errors_raises_error(self):
        """Test that mismatched lengths raise ValueError."""
        with pytest.raises(ValueError):
            calculate_error_propagation(
                operation="add",
                values=[10.0, 5.0],
                errors=[0.5]  # Wrong length
            )

    def test_unknown_operation_raises_error(self):
        """Test that unknown operation raises ValueError."""
        with pytest.raises(ValueError):
            calculate_error_propagation(
                operation="unknown",
                values=[10.0],
                errors=[0.5]
            )

    def test_power_missing_exponent_raises_error(self):
        """Test that power operation without exponent raises ValueError."""
        with pytest.raises(ValueError):
            calculate_error_propagation(
                operation="power",
                values=[10.0],
                errors=[0.5]
                # Missing exponent parameter
            )
