"""
Gradient Methods

Gradient elution optimization and prediction.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math


@dataclass
class GradientMethod:
    """Gradient elution method definition"""
    initial_percent: float  # % organic modifier
    final_percent: float
    gradient_time: float  # minutes
    flow_rate: float  # mL/min
    column_volume: float  # mL
    
    def gradient_slope(self) -> float:
        """Calculate gradient slope (% per minute)"""
        return (self.final_percent - self.initial_percent) / self.gradient_time
    
    def column_volumes(self) -> float:
        """Calculate gradient in column volumes"""
        total_volume = self.flow_rate * self.gradient_time
        return total_volume / self.column_volume


def calculate_gradient_profile(
    initial_percent: float,
    final_percent: float,
    gradient_time: float,
    time_points: Optional[List[float]] = None
) -> Dict[str, List[float]]:
    """
    Calculate gradient composition over time
    
    Args:
        initial_percent: Starting % organic modifier
        final_percent: Ending % organic modifier
        gradient_time: Gradient duration (minutes)
        time_points: Optional specific times to calculate
        
    Returns:
        Dictionary with times and compositions
        
    Educational Note:
        Linear gradient profile:
        φ(t) = φ_initial + (φ_final - φ_initial) * (t / t_gradient)
        
        Common gradient shapes:
        - Linear: constant slope (most common)
        - Step: discrete jumps
        - Curved: accelerating or decelerating slope
    """
    if gradient_time <= 0:
        raise ValueError("Gradient time must be positive")
    if not (0 <= initial_percent <= 100 and 0 <= final_percent <= 100):
        raise ValueError("Percentages must be between 0 and 100")
        
    if time_points is None:
        time_points = [i * gradient_time / 100 for i in range(101)]
        
    compositions = []
    for t in time_points:
        if t <= 0:
            comp = initial_percent
        elif t >= gradient_time:
            comp = final_percent
        else:
            fraction = t / gradient_time
            comp = initial_percent + (final_percent - initial_percent) * fraction
        compositions.append(comp)
        
    profile = {
        "times": time_points,
        "compositions": compositions,
        "slope": (final_percent - initial_percent) / gradient_time
    }
    
    return profile


def predict_retention_time(
    k_0: float,
    k_end: float,
    t_0: float,
    t_gradient: float,
    S: float = 4.0
) -> float:
    """
    Predict retention time in gradient elution
    
    Args:
        k_0: Retention factor at gradient start
        k_end: Retention factor at gradient end
        t_0: Void time (minutes)
        t_gradient: Gradient time (minutes)
        S: Solvent strength parameter
        
    Returns:
        Predicted retention time
        
    Educational Note:
        Linear solvent strength (LSS) theory for gradients:
        - Analyte retention decreases as organic % increases
        - Gradient compression reduces peak width
        - Steeper gradients → faster elution, lower resolution
        - Shallow gradients → better resolution, longer analysis
    """
    if k_0 <= 0:
        raise ValueError("Initial retention factor must be positive")
    if t_0 <= 0 or t_gradient <= 0:
        raise ValueError("Times must be positive")
        
    # Simplified gradient retention prediction
    # More complex models exist (e.g., numerical integration)
    
    # Approximate gradient retention
    k_average = math.sqrt(k_0 * k_end)  # Geometric mean
    
    # Gradient retention time
    t_R = t_0 * (1 + k_average)
    
    # Adjust for gradient effects
    gradient_factor = t_gradient / (S * math.log10(k_0 / k_end))
    t_R = t_0 + gradient_factor * math.log(2.3 * k_0 * S / t_gradient + 1)
    
    return t_R


def optimize_gradient(
    k_values: List[float],
    t_0: float,
    target_resolution: float = 1.5,
    column_length: float = 15.0
) -> Dict[str, float]:
    """
    Optimize gradient for target resolution
    
    Args:
        k_values: Retention factors of compounds to separate
        t_0: Void time (minutes)
        target_resolution: Desired resolution
        column_length: Column length (cm)
        
    Returns:
        Dictionary with optimized gradient parameters
        
    Educational Note:
        Gradient optimization balances:
        - Analysis time (faster is better)
        - Resolution (adequate separation)
        - Peak capacity (number of peaks that can be separated)
        
        Key relationships:
        - Longer gradients → better resolution but slower
        - Steeper gradients → faster but poorer resolution
        - Optimum depends on sample complexity
    """
    if not k_values or len(k_values) < 2:
        raise ValueError("Need at least 2 compounds")
    if t_0 <= 0:
        raise ValueError("Void time must be positive")
        
    k_values = sorted(k_values)
    k_min = k_values[0]
    k_max = k_values[-1]
    
    # Calculate required gradient time for target resolution
    # Simplified approach based on typical gradient behavior
    
    # Estimate gradient time (rule of thumb)
    gradient_time = t_0 * (k_max - k_min) / 0.25
    
    # Adjust for target resolution
    resolution_factor = target_resolution / 1.5  # 1.5 is typical baseline
    gradient_time *= resolution_factor ** 2
    
    # Calculate gradient slope
    # Assume 5-95% organic range
    gradient_slope = 90 / gradient_time
    
    # Estimate peak capacity
    peak_capacity = 1 + gradient_time / (4 * t_0)
    
    optimization = {
        "gradient_time": round(gradient_time, 2),
        "gradient_slope": round(gradient_slope, 2),
        "initial_percent": 5.0,
        "final_percent": 95.0,
        "estimated_peak_capacity": round(peak_capacity, 1),
        "total_analysis_time": round(gradient_time + 5 * t_0, 2)  # Including equilibration
    }
    
    return optimization


def calculate_peak_capacity(
    gradient_time: float,
    average_peak_width: float
) -> float:
    """
    Calculate gradient peak capacity
    
    Args:
        gradient_time: Gradient duration (minutes)
        average_peak_width: Average peak width (minutes)
        
    Returns:
        Peak capacity nc
        
    Formula:
        nc = 1 + t_gradient / (4σ)
        where σ = peak width standard deviation
        
    Educational Note:
        Peak capacity = maximum number of peaks that
        can be baseline separated in the gradient.
        
        Typical values:
        - nc = 50-100: typical HPLC gradient
        - nc = 200-500: UPLC or long gradients
        - nc = 1000+: comprehensive 2D separations
    """
    if gradient_time <= 0 or average_peak_width <= 0:
        raise ValueError("Times must be positive")
        
    # Convert peak width to standard deviation
    sigma = average_peak_width / 4  # For Gaussian peaks: w_base = 4σ
    
    peak_capacity = 1 + gradient_time / (4 * sigma)
    return peak_capacity


def calculate_gradient_delay_volume(
    dwell_volume: float,
    flow_rate: float
) -> float:
    """
    Calculate gradient delay time
    
    Args:
        dwell_volume: System dwell volume (mL)
        flow_rate: Flow rate (mL/min)
        
    Returns:
        Gradient delay time (minutes)
        
    Educational Note:
        Gradient delay = time between gradient program start
        and gradient reaching column inlet.
        
        Caused by:
        - Mixer volume
        - Tubing volume
        - Pump to column distance
        
        Important for method transfer between systems!
    """
    if dwell_volume < 0 or flow_rate <= 0:
        raise ValueError("Invalid volume or flow rate")
        
    delay_time = dwell_volume / flow_rate
    return delay_time


def design_multistep_gradient(
    compound_groups: List[Tuple[float, float]],
    t_0: float,
    total_time: float = 30.0
) -> List[Dict[str, float]]:
    """
    Design multi-step gradient for grouped compounds
    
    Args:
        compound_groups: List of (k_start, k_end) for each group
        t_0: Void time
        total_time: Total gradient time budget
        
    Returns:
        List of gradient step definitions
        
    Educational Note:
        Multi-step gradients:
        - Fast initial gradient for early eluters
        - Shallow gradient for critical separation
        - Fast final gradient for late eluters
        - Reduces total analysis time vs linear gradient
    """
    if not compound_groups:
        raise ValueError("Need at least one compound group")
        
    n_steps = len(compound_groups)
    time_per_step = total_time / n_steps
    
    steps = []
    current_percent = 5.0
    
    for i, (k_start, k_end) in enumerate(compound_groups):
        # Calculate slope needed for this group
        # More retained compounds need steeper gradient
        slope_factor = math.log10(k_end / k_start) if k_start > 0 else 1.0
        step_time = time_per_step * (1 + 0.5 * slope_factor)
        
        # Calculate final percent for this step
        delta_percent = 15 * (i + 1) / n_steps  # Progressive increase
        final_percent = current_percent + delta_percent
        
        step = {
            "initial_percent": round(current_percent, 1),
            "final_percent": round(final_percent, 1),
            "time": round(step_time, 2),
            "slope": round(delta_percent / step_time, 2)
        }
        
        steps.append(step)
        current_percent = final_percent
        
    return steps
