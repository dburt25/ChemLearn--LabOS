"""
Retention Models

Chromatographic retention and separation theory.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math


@dataclass
class RetentionData:
    """Chromatographic retention data"""
    compound: str
    retention_time: float  # minutes
    peak_width: float  # minutes
    void_time: float  # minutes (t0)
    retention_factor: Optional[float] = None
    
    def __post_init__(self):
        """Calculate retention factor if not provided"""
        if self.retention_factor is None and self.void_time > 0:
            self.retention_factor = (self.retention_time - self.void_time) / self.void_time


def calculate_retention_factor(
    retention_time: float,
    void_time: float
) -> float:
    """
    Calculate retention factor (capacity factor)
    
    Args:
        retention_time: Retention time (tR)
        void_time: Void time (t0)
        
    Returns:
        Retention factor k'
        
    Formula:
        k' = (tR - t0) / t0
        
    Educational Note:
        Retention factor represents the equilibrium distribution
        of analyte between stationary and mobile phases.
        k' = 0: no retention (elutes at t0)
        k' = 1: equal time in both phases
        k' > 10: excessively retained
    """
    if void_time <= 0:
        raise ValueError("Void time must be positive")
    if retention_time < void_time:
        raise ValueError("Retention time must be >= void time")
        
    k_prime = (retention_time - void_time) / void_time
    return k_prime


def calculate_selectivity(
    k1: float,
    k2: float
) -> float:
    """
    Calculate selectivity (separation factor)
    
    Args:
        k1: Retention factor of first peak
        k2: Retention factor of second peak
        
    Returns:
        Selectivity α (alpha)
        
    Formula:
        α = k2 / k1  (where k2 > k1)
        
    Educational Note:
        Selectivity measures relative retention of two compounds.
        α = 1: no separation (coelution)
        α > 1: compounds separated
        α ≥ 1.05: baseline separation typically achievable
    """
    if k1 <= 0 or k2 <= 0:
        raise ValueError("Retention factors must be positive")
        
    # Ensure k2 > k1 by convention
    if k2 < k1:
        k1, k2 = k2, k1
        
    alpha = k2 / k1
    return alpha


def calculate_resolution(
    rt1: float,
    rt2: float,
    w1: float,
    w2: float
) -> float:
    """
    Calculate chromatographic resolution
    
    Args:
        rt1: Retention time of first peak
        rt2: Retention time of second peak
        w1: Peak width (base) of first peak
        w2: Peak width (base) of second peak
        
    Returns:
        Resolution Rs
        
    Formula:
        Rs = 2(tR2 - tR1) / (w1 + w2)
        
    Educational Note:
        Resolution quantifies separation quality:
        Rs < 1.0: peaks overlap significantly
        Rs = 1.0: 98% separated (2% overlap)
        Rs = 1.5: baseline separation
        Rs > 2.0: excellent separation
    """
    if w1 <= 0 or w2 <= 0:
        raise ValueError("Peak widths must be positive")
    if rt2 < rt1:
        rt1, rt2 = rt2, rt1
        w1, w2 = w2, w1
        
    resolution = 2 * (rt2 - rt1) / (w1 + w2)
    return resolution


def van_deemter_equation(
    flow_rate: float,
    A: float = 0.001,
    B: float = 0.01,
    C: float = 0.0001
) -> float:
    """
    Calculate plate height using Van Deemter equation
    
    Args:
        flow_rate: Mobile phase flow rate (mL/min)
        A: Eddy diffusion coefficient
        B: Longitudinal diffusion coefficient
        C: Mass transfer coefficient
        
    Returns:
        Plate height H (cm)
        
    Formula:
        H = A + B/u + Cu
        where u = linear velocity (flow rate)
        
    Educational Note:
        Van Deemter equation describes band broadening:
        - A term: multiple flow paths (eddy diffusion)
        - B term: longitudinal diffusion (decreases with flow)
        - C term: mass transfer resistance (increases with flow)
        Optimal flow rate minimizes H (maximizes efficiency)
    """
    if flow_rate <= 0:
        raise ValueError("Flow rate must be positive")
        
    H = A + B / flow_rate + C * flow_rate
    return H


def optimize_flow_rate(
    B: float = 0.01,
    C: float = 0.0001,
    flow_range: Tuple[float, float] = (0.1, 5.0),
    n_points: int = 100
) -> Dict[str, float]:
    """
    Find optimal flow rate for minimum plate height
    
    Args:
        B: Longitudinal diffusion coefficient
        C: Mass transfer coefficient
        flow_range: (min, max) flow rates to test
        n_points: Number of points to evaluate
        
    Returns:
        Dictionary with optimal flow rate and minimum H
        
    Educational Note:
        Optimal flow rate occurs at minimum of Van Deemter curve:
        dH/du = 0
        u_opt = sqrt(B/C)
        This balances diffusion and mass transfer effects.
    """
    # Analytical solution: u_opt = sqrt(B/C)
    optimal_flow = math.sqrt(B / C)
    
    # Ensure within range
    min_flow, max_flow = flow_range
    if optimal_flow < min_flow:
        optimal_flow = min_flow
    elif optimal_flow > max_flow:
        optimal_flow = max_flow
        
    # Calculate minimum H (using A=0.001 as default)
    min_H = van_deemter_equation(optimal_flow, B=B, C=C)
    
    result = {
        "optimal_flow_rate": round(optimal_flow, 3),
        "minimum_plate_height": round(min_H, 6),
        "theoretical_optimum": round(math.sqrt(B / C), 3)
    }
    
    return result


def calculate_adjusted_retention_time(
    retention_time: float,
    void_time: float
) -> float:
    """
    Calculate adjusted retention time
    
    Args:
        retention_time: Retention time (tR)
        void_time: Void time (t0)
        
    Returns:
        Adjusted retention time t'R
        
    Formula:
        t'R = tR - t0
        
    Educational Note:
        Adjusted retention time represents time spent
        in stationary phase, independent of column
        geometry and flow rate effects.
    """
    if retention_time < void_time:
        raise ValueError("Retention time must be >= void time")
        
    adjusted_time = retention_time - void_time
    return adjusted_time


def predict_retention_isocratic(
    k_ref: float,
    phi_ref: float,
    phi_new: float,
    S: float = 4.0
) -> float:
    """
    Predict retention factor at different mobile phase composition
    
    Args:
        k_ref: Retention factor at reference composition
        phi_ref: Reference organic modifier fraction (0-1)
        phi_new: New organic modifier fraction (0-1)
        S: Solvent strength parameter (typical: 3-5 for RP-LC)
        
    Returns:
        Predicted retention factor at new composition
        
    Formula:
        log(k) = log(k_ref) - S(φ - φ_ref)
        
    Educational Note:
        Linear solvent strength (LSS) model predicts retention
        changes with mobile phase composition. S depends on:
        - Analyte properties (size, polarity)
        - Stationary phase type
        - Solvent type (S higher for methanol vs acetonitrile)
    """
    if not (0 <= phi_ref <= 1 and 0 <= phi_new <= 1):
        raise ValueError("Organic fractions must be between 0 and 1")
        
    log_k_ref = math.log10(k_ref) if k_ref > 0 else -10
    log_k_new = log_k_ref - S * (phi_new - phi_ref)
    
    k_new = 10 ** log_k_new
    return k_new


def calculate_fundamental_resolution_equation(
    N: float,
    alpha: float,
    k: float
) -> float:
    """
    Calculate resolution from fundamental parameters
    
    Args:
        N: Plate number (efficiency)
        alpha: Selectivity
        k: Average retention factor
        
    Returns:
        Resolution Rs
        
    Formula:
        Rs = (√N / 4) * ((α - 1) / α) * (k / (1 + k))
        
    Educational Note:
        Fundamental resolution equation shows three factors:
        1. Efficiency (√N): increase column length or efficiency
        2. Selectivity ((α-1)/α): optimize mobile phase
        3. Retention (k/(1+k)): optimize retention factor
        Doubling resolution requires 4x column length (N factor)
    """
    if N <= 0:
        raise ValueError("Plate number must be positive")
    if alpha < 1:
        raise ValueError("Selectivity must be >= 1")
    if k < 0:
        raise ValueError("Retention factor must be non-negative")
        
    efficiency_term = math.sqrt(N) / 4
    selectivity_term = (alpha - 1) / alpha
    retention_term = k / (1 + k)
    
    resolution = efficiency_term * selectivity_term * retention_term
    return resolution
