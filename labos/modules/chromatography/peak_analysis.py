"""
Peak Analysis

Tools for analyzing chromatographic peaks.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math


@dataclass
class PeakData:
    """Chromatographic peak data"""
    retention_time: float
    height: float
    area: float
    width_half_height: float  # w1/2
    width_baseline: float  # wb
    asymmetry: Optional[float] = None
    plate_number: Optional[float] = None


def fit_gaussian_peak(
    times: List[float],
    intensities: List[float],
    peak_index: int,
    window: int = 10
) -> Dict[str, float]:
    """
    Fit Gaussian function to peak
    
    Args:
        times: Time points
        intensities: Intensity values
        peak_index: Index of peak maximum
        window: Points on each side for fitting
        
    Returns:
        Dictionary with fitted parameters
        
    Educational Note:
        Gaussian peak model:
        y = A * exp(-(t - μ)² / (2σ²))
        where:
        - A: amplitude (height)
        - μ: retention time (center)
        - σ: standard deviation (related to peak width)
    """
    if peak_index < 0 or peak_index >= len(times):
        raise ValueError("Peak index out of range")
        
    # Simple moment-based estimation
    start = max(0, peak_index - window)
    end = min(len(times), peak_index + window + 1)
    
    peak_times = times[start:end]
    peak_intensities = intensities[start:end]
    
    # Peak height (amplitude)
    height = peak_intensities[peak_index - start]
    
    # Center (retention time)
    center = times[peak_index]
    
    # Estimate width from half-height points
    half_height = height / 2
    left_idx = peak_index
    while left_idx > start and intensities[left_idx] > half_height:
        left_idx -= 1
    right_idx = peak_index
    while right_idx < end - 1 and intensities[right_idx] > half_height:
        right_idx += 1
        
    if right_idx > left_idx:
        width_half_height = times[right_idx] - times[left_idx]
        sigma = width_half_height / 2.355  # FWHM = 2.355σ
    else:
        sigma = 0.1
        width_half_height = 0.2355
    
    params = {
        "amplitude": round(height, 2),
        "center": round(center, 4),
        "sigma": round(sigma, 4),
        "width_half_height": round(width_half_height, 4)
    }
    
    return params


def calculate_peak_area(
    times: List[float],
    intensities: List[float],
    start_idx: int,
    end_idx: int
) -> float:
    """
    Calculate peak area by trapezoidal integration
    
    Args:
        times: Time points
        intensities: Intensity values
        start_idx: Start index of peak
        end_idx: End index of peak
        
    Returns:
        Peak area
        
    Educational Note:
        Peak area is proportional to analyte amount:
        Area = ∫ signal dt
        Trapezoidal rule approximates:
        Area ≈ Σ[(y_i + y_{i+1})/2 * Δt]
    """
    if start_idx < 0 or end_idx > len(times):
        raise ValueError("Invalid peak boundaries")
    if start_idx >= end_idx:
        raise ValueError("Start must be before end")
        
    area = 0.0
    for i in range(start_idx, end_idx - 1):
        dt = times[i + 1] - times[i]
        avg_height = (intensities[i] + intensities[i + 1]) / 2
        area += avg_height * dt
        
    return area


def calculate_plate_number(
    retention_time: float,
    peak_width: float,
    method: str = "half_height"
) -> float:
    """
    Calculate theoretical plate number
    
    Args:
        retention_time: Peak retention time
        peak_width: Peak width (at base or half-height)
        method: 'half_height' or 'baseline'
        
    Returns:
        Plate number N
        
    Formulas:
        N = 5.54 * (tR / w1/2)²  (half-height method)
        N = 16 * (tR / wb)²      (baseline method)
        
    Educational Note:
        Plate number measures column efficiency:
        N = 1000: poor efficiency
        N = 5000-10000: typical for 15cm column
        N = 50000+: high efficiency (UPLC)
        Higher N → narrower peaks → better separation
    """
    if retention_time <= 0 or peak_width <= 0:
        raise ValueError("Times and widths must be positive")
        
    if method == "half_height":
        N = 5.54 * (retention_time / peak_width) ** 2
    elif method == "baseline":
        N = 16 * (retention_time / peak_width) ** 2
    else:
        raise ValueError("Method must be 'half_height' or 'baseline'")
        
    return N


def calculate_asymmetry(
    peak_width_left: float,
    peak_width_right: float
) -> float:
    """
    Calculate peak asymmetry factor
    
    Args:
        peak_width_left: Width from center to left at 10% height
        peak_width_right: Width from center to right at 10% height
        
    Returns:
        Asymmetry factor As
        
    Formula:
        As = b / a
        where b = right half-width, a = left half-width
        
    Educational Note:
        Peak asymmetry indicates column problems:
        As = 1.0: symmetric peak (ideal)
        As = 0.9-1.2: acceptable
        As > 1.5: tailing (overloaded, secondary interactions)
        As < 0.9: fronting (column issues)
    """
    if peak_width_left <= 0 or peak_width_right <= 0:
        raise ValueError("Peak widths must be positive")
        
    asymmetry = peak_width_right / peak_width_left
    return asymmetry


def detect_peaks(
    times: List[float],
    intensities: List[float],
    threshold: float = 0.1,
    min_distance: int = 5
) -> List[Dict[str, float]]:
    """
    Detect peaks in chromatogram
    
    Args:
        times: Time points
        intensities: Intensity values
        threshold: Minimum relative intensity (0-1)
        min_distance: Minimum points between peaks
        
    Returns:
        List of detected peak dictionaries
        
    Educational Note:
        Peak detection finds local maxima above threshold:
        1. Identify points higher than neighbors
        2. Filter by intensity threshold
        3. Ensure minimum separation
        4. Calculate peak properties
    """
    if len(times) != len(intensities):
        raise ValueError("Times and intensities must have same length")
        
    max_intensity = max(intensities)
    threshold_value = max_intensity * threshold
    
    peaks = []
    i = 1
    
    while i < len(intensities) - 1:
        # Check if local maximum
        if (intensities[i] > intensities[i - 1] and
            intensities[i] > intensities[i + 1] and
            intensities[i] > threshold_value):
            
            # Find peak boundaries
            left = i
            while left > 0 and intensities[left] > threshold_value * 0.1:
                left -= 1
            right = i
            while right < len(intensities) - 1 and intensities[right] > threshold_value * 0.1:
                right += 1
                
            # Calculate peak properties
            area = calculate_peak_area(times, intensities, left, right)
            
            peak = {
                "retention_time": times[i],
                "height": intensities[i],
                "area": round(area, 2),
                "start_time": times[left],
                "end_time": times[right],
                "width": times[right] - times[left]
            }
            
            peaks.append(peak)
            
            # Skip to avoid detecting same peak twice
            i = right + min_distance
        else:
            i += 1
            
    return peaks


def calculate_peak_purity(
    spectrum_start: List[float],
    spectrum_apex: List[float],
    spectrum_end: List[float]
) -> Dict[str, float]:
    """
    Estimate peak purity from spectral comparison
    
    Args:
        spectrum_start: Spectrum at peak start
        spectrum_apex: Spectrum at peak apex
        spectrum_end: Spectrum at peak end
        
    Returns:
        Dictionary with purity metrics
        
    Educational Note:
        Peak purity indicates coelution:
        - Compare spectra across peak
        - Similar spectra → pure peak
        - Different spectra → coelution
        Uses spectral similarity (correlation)
    """
    if len(spectrum_start) != len(spectrum_apex) != len(spectrum_end):
        raise ValueError("Spectra must have same length")
        
    # Calculate correlations
    def correlation(spec1: List[float], spec2: List[float]) -> float:
        n = len(spec1)
        mean1 = sum(spec1) / n
        mean2 = sum(spec2) / n
        
        num = sum((spec1[i] - mean1) * (spec2[i] - mean2) for i in range(n))
        den1 = sum((spec1[i] - mean1) ** 2 for i in range(n)) ** 0.5
        den2 = sum((spec2[i] - mean2) ** 2 for i in range(n)) ** 0.5
        
        if den1 == 0 or den2 == 0:
            return 0.0
        return num / (den1 * den2)
    
    start_apex_corr = correlation(spectrum_start, spectrum_apex)
    apex_end_corr = correlation(spectrum_apex, spectrum_end)
    start_end_corr = correlation(spectrum_start, spectrum_end)
    
    avg_correlation = (start_apex_corr + apex_end_corr + start_end_corr) / 3
    
    purity = {
        "average_correlation": round(avg_correlation, 3),
        "start_apex_correlation": round(start_apex_corr, 3),
        "apex_end_correlation": round(apex_end_corr, 3),
        "is_pure": avg_correlation > 0.98
    }
    
    return purity


def calculate_tailing_factor(
    peak_width_front: float,
    peak_width_total: float
) -> float:
    """
    Calculate USP tailing factor
    
    Args:
        peak_width_front: Width from leading edge to center at 5% height
        peak_width_total: Total width at 5% height
        
    Returns:
        USP tailing factor T
        
    Formula:
        T = W0.05 / (2f)
        where W0.05 = total width at 5% height
        f = front width at 5% height
        
    Educational Note:
        USP tailing factor (T):
        T = 1.0: symmetric (ideal)
        T < 1.2: acceptable
        T > 2.0: severe tailing (requires investigation)
    """
    if peak_width_front <= 0 or peak_width_total <= 0:
        raise ValueError("Peak widths must be positive")
        
    tailing = peak_width_total / (2 * peak_width_front)
    return tailing
