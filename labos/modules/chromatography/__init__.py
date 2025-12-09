"""
Chromatography Module

Separation science tools for LC/GC analysis.
"""

from labos.modules.chromatography.retention_models import (
    calculate_retention_factor,
    calculate_selectivity,
    calculate_resolution,
    van_deemter_equation,
    optimize_flow_rate,
    RetentionData
)
from labos.modules.chromatography.peak_analysis import (
    fit_gaussian_peak,
    calculate_peak_area,
    calculate_plate_number,
    calculate_asymmetry,
    detect_peaks,
    PeakData
)
from labos.modules.chromatography.gradient_methods import (
    calculate_gradient_profile,
    predict_retention_time,
    optimize_gradient,
    GradientMethod
)
from labos.modules.chromatography.column_theory import (
    calculate_column_efficiency,
    calculate_void_volume,
    estimate_column_capacity,
    ColumnParameters
)

__all__ = [
    # Retention models
    "calculate_retention_factor",
    "calculate_selectivity",
    "calculate_resolution",
    "van_deemter_equation",
    "optimize_flow_rate",
    "RetentionData",
    
    # Peak analysis
    "fit_gaussian_peak",
    "calculate_peak_area",
    "calculate_plate_number",
    "calculate_asymmetry",
    "detect_peaks",
    "PeakData",
    
    # Gradient methods
    "calculate_gradient_profile",
    "predict_retention_time",
    "optimize_gradient",
    "GradientMethod",
    
    # Column theory
    "calculate_column_efficiency",
    "calculate_void_volume",
    "estimate_column_capacity",
    "ColumnParameters"
]
