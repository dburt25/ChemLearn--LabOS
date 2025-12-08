"""Error propagation utilities for uncertainty analysis.

Implements standard error propagation formulas for common
mathematical operations following Taylor series expansion.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple


def propagate_addition(
    values_with_errors: List[Tuple[float, float]],
) -> Tuple[float, float]:
    """Propagate uncertainty for addition/subtraction.
    
    For z = x ± y:
    σ_z = √(σ_x² + σ_y²)
    
    Args:
        values_with_errors: List of (value, error) tuples
        
    Returns:
        Tuple of (sum, propagated_error)
        
    Example:
        >>> propagate_addition([(10.0, 0.5), (5.0, 0.3)])
        (15.0, 0.583)  # 10±0.5 + 5±0.3 = 15±0.58
    """
    total = sum(value for value, _ in values_with_errors)
    
    # Error propagation: σ_z² = σ_x² + σ_y² + ...
    error_squared_sum = sum(error**2 for _, error in values_with_errors)
    propagated_error = math.sqrt(error_squared_sum)
    
    return total, propagated_error


def propagate_subtraction(
    minuend: Tuple[float, float],
    subtrahend: Tuple[float, float],
) -> Tuple[float, float]:
    """Propagate uncertainty for subtraction.
    
    For z = x - y:
    σ_z = √(σ_x² + σ_y²)
    
    Args:
        minuend: (value, error) for first term
        subtrahend: (value, error) for second term
        
    Returns:
        Tuple of (difference, propagated_error)
    """
    x, sigma_x = minuend
    y, sigma_y = subtrahend
    
    difference = x - y
    propagated_error = math.sqrt(sigma_x**2 + sigma_y**2)
    
    return difference, propagated_error


def propagate_multiplication(
    factors: List[Tuple[float, float]],
) -> Tuple[float, float]:
    """Propagate uncertainty for multiplication.
    
    For z = x * y * ...:
    (σ_z/z)² = (σ_x/x)² + (σ_y/y)² + ...
    
    Args:
        factors: List of (value, error) tuples
        
    Returns:
        Tuple of (product, propagated_error)
        
    Example:
        >>> propagate_multiplication([(10.0, 0.5), (5.0, 0.2)])
        (50.0, 2.69)  # 10±0.5 * 5±0.2 = 50±2.7
    """
    product = 1.0
    for value, _ in factors:
        if value == 0:
            raise ValueError("Cannot propagate error through zero value in multiplication")
        product *= value
    
    # Relative error propagation: (σ_z/z)² = (σ_x/x)² + (σ_y/y)² + ...
    relative_error_squared_sum = sum((error/value)**2 for value, error in factors)
    relative_error = math.sqrt(relative_error_squared_sum)
    
    propagated_error = abs(product) * relative_error
    
    return product, propagated_error


def propagate_division(
    numerator: Tuple[float, float],
    denominator: Tuple[float, float],
) -> Tuple[float, float]:
    """Propagate uncertainty for division.
    
    For z = x / y:
    (σ_z/z)² = (σ_x/x)² + (σ_y/y)²
    
    Args:
        numerator: (value, error) for numerator
        denominator: (value, error) for denominator
        
    Returns:
        Tuple of (quotient, propagated_error)
    """
    x, sigma_x = numerator
    y, sigma_y = denominator
    
    if y == 0:
        raise ValueError("Cannot divide by zero")
    
    quotient = x / y
    
    # Relative error propagation
    relative_error = math.sqrt((sigma_x/x)**2 + (sigma_y/y)**2)
    propagated_error = abs(quotient) * relative_error
    
    return quotient, propagated_error


def propagate_power(
    value: float,
    error: float,
    exponent: float,
) -> Tuple[float, float]:
    """Propagate uncertainty for power function.
    
    For z = x^n:
    σ_z/z = |n| * σ_x/x
    
    Args:
        value: Base value
        error: Uncertainty in base
        exponent: Power exponent
        
    Returns:
        Tuple of (result, propagated_error)
        
    Example:
        >>> propagate_power(10.0, 0.5, 2.0)
        (100.0, 10.0)  # (10±0.5)² = 100±10
    """
    if value == 0:
        raise ValueError("Cannot propagate error through zero base in power")
    
    result = value ** exponent
    
    # σ_z/z = |n| * σ_x/x
    relative_error = abs(exponent) * (error / abs(value))
    propagated_error = abs(result) * relative_error
    
    return result, propagated_error


def propagate_function(
    value: float,
    error: float,
    derivative: float,
) -> float:
    """Propagate uncertainty through arbitrary function using derivative.
    
    For z = f(x):
    σ_z = |df/dx| * σ_x
    
    Args:
        value: Input value x
        error: Uncertainty in x
        derivative: Value of df/dx at x
        
    Returns:
        Propagated error σ_z
        
    Example:
        >>> # For sin(x) at x=0.5, derivative is cos(0.5)=0.878
        >>> propagate_function(0.5, 0.01, 0.878)
        0.00878
    """
    return abs(derivative) * error


def propagate_correlated(
    x: float,
    sigma_x: float,
    y: float,
    sigma_y: float,
    correlation: float,
    operation: str = "add",
) -> Tuple[float, float]:
    """Propagate uncertainty with correlation between variables.
    
    For z = x ± y with correlation coefficient ρ:
    σ_z² = σ_x² + σ_y² ± 2ρσ_xσ_y
    
    Args:
        x: First value
        sigma_x: Error in first value
        y: Second value
        sigma_y: Error in second value
        correlation: Correlation coefficient ρ (-1 to 1)
        operation: "add" or "subtract"
        
    Returns:
        Tuple of (result, propagated_error)
    """
    if not -1 <= correlation <= 1:
        raise ValueError("Correlation coefficient must be between -1 and 1")
    
    if operation == "add":
        result = x + y
        sign = 1
    elif operation == "subtract":
        result = x - y
        sign = -1
    else:
        raise ValueError("Operation must be 'add' or 'subtract'")
    
    # σ_z² = σ_x² + σ_y² + 2ρσ_xσ_y (for addition)
    # σ_z² = σ_x² + σ_y² - 2ρσ_xσ_y (for subtraction)
    error_squared = sigma_x**2 + sigma_y**2 + sign * 2 * correlation * sigma_x * sigma_y
    
    # Ensure non-negative (can happen due to rounding with strong negative correlation)
    error_squared = max(0, error_squared)
    propagated_error = math.sqrt(error_squared)
    
    return result, propagated_error


def relative_error(value: float, error: float) -> float:
    """Calculate relative error (fractional uncertainty).
    
    Relative error = σ / |x|
    
    Args:
        value: Measured value
        error: Absolute error
        
    Returns:
        Relative error (dimensionless)
    """
    if value == 0:
        raise ValueError("Cannot calculate relative error for zero value")
    
    return error / abs(value)


def percent_error(value: float, error: float) -> float:
    """Calculate percent error.
    
    Percent error = (σ / |x|) * 100%
    
    Args:
        value: Measured value
        error: Absolute error
        
    Returns:
        Percent error
    """
    return relative_error(value, error) * 100


def weighted_average(
    values_with_errors: List[Tuple[float, float]],
) -> Tuple[float, float]:
    """Calculate weighted average and its uncertainty.
    
    Weight each measurement by 1/σ².
    
    Args:
        values_with_errors: List of (value, error) tuples
        
    Returns:
        Tuple of (weighted_average, uncertainty)
        
    Example:
        >>> weighted_average([(10.0, 0.5), (10.2, 1.0), (9.8, 0.3)])
        # Measurements with smaller errors get higher weight
    """
    if not values_with_errors:
        raise ValueError("Need at least one measurement")
    
    # Weights: w_i = 1/σ_i²
    weights = [1.0 / error**2 for _, error in values_with_errors]
    total_weight = sum(weights)
    
    # Weighted average: x̄ = Σ(w_i * x_i) / Σw_i
    weighted_sum = sum(w * value for w, (value, _) in zip(weights, values_with_errors))
    average = weighted_sum / total_weight
    
    # Uncertainty: σ_x̄ = 1/√(Σw_i)
    uncertainty = 1.0 / math.sqrt(total_weight)
    
    return average, uncertainty


# Module registration
MODULE_KEY = "pchem.error_propagation"
MODULE_VERSION = "1.0.0"


def calculate_error_propagation(
    operation: str,
    values: List[float],
    errors: List[float],
    exponent: float | None = None,
    correlation: float | None = None,
) -> Dict[str, object]:
    """Calculate error propagation for various operations.
    
    Main entry point for module operation.
    
    Args:
        operation: Operation type ("add", "subtract", "multiply", "divide", "power", "weighted_average")
        values: List of measured values
        errors: List of uncertainties
        exponent: Exponent for power operation
        correlation: Correlation coefficient for correlated operations
        
    Returns:
        Dictionary with result and propagated error
    """
    if len(values) != len(errors):
        raise ValueError("Number of values must match number of errors")
    
    values_with_errors = list(zip(values, errors))
    
    if operation == "add":
        result, error = propagate_addition(values_with_errors)
        
    elif operation == "subtract":
        if len(values) != 2:
            raise ValueError("Subtraction requires exactly 2 values")
        result, error = propagate_subtraction(values_with_errors[0], values_with_errors[1])
        
    elif operation == "multiply":
        result, error = propagate_multiplication(values_with_errors)
        
    elif operation == "divide":
        if len(values) != 2:
            raise ValueError("Division requires exactly 2 values")
        result, error = propagate_division(values_with_errors[0], values_with_errors[1])
        
    elif operation == "power":
        if len(values) != 1:
            raise ValueError("Power operation requires exactly 1 value")
        if exponent is None:
            raise ValueError("Exponent required for power operation")
        result, error = propagate_power(values[0], errors[0], exponent)
        
    elif operation == "weighted_average":
        result, error = weighted_average(values_with_errors)
        
    else:
        raise ValueError(f"Unknown operation: {operation}")
    
    return {
        "operation": operation,
        "inputs": [{"value": v, "error": e} for v, e in values_with_errors],
        "result": result,
        "absolute_error": error,
        "relative_error": relative_error(result, error) if result != 0 else None,
        "percent_error": percent_error(result, error) if result != 0 else None,
    }


def _register() -> None:
    """Register error propagation operations with module system."""
    from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor
    
    descriptor = ModuleDescriptor(
        module_id=MODULE_KEY,
        version=MODULE_VERSION,
        description="Propagate measurement uncertainties through calculations",
    )
    
    descriptor.register_operation(
        ModuleOperation(
            name="calculate",
            description="Propagate errors through mathematical operations",
            handler=lambda params: calculate_error_propagation(**params),
        )
    )
    
    register_descriptor(descriptor)


# Auto-register on import
_register()
