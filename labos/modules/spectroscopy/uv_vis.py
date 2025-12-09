"""UV-Visible Absorption Spectroscopy Module.

Provides Beer-Lambert law calculations, concentration determination,
and absorption spectrum analysis for educational chemistry applications.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class UVVisResult:
    """Result container for UV-Vis spectroscopy analysis.
    
    Attributes:
        lambda_max: Wavelength of maximum absorption in nm
        absorbance_max: Maximum absorbance value
        concentration: Calculated concentration in M (if applicable)
        epsilon: Molar absorptivity in M^-1 cm^-1 (if known)
        path_length: Path length in cm
        peaks: List of detected absorption peaks
        notes: Analysis notes and warnings
    """
    
    lambda_max: float | None = None
    absorbance_max: float | None = None
    concentration: float | None = None
    epsilon: float | None = None
    path_length: float = 1.0
    peaks: List[Dict[str, float]] = None
    notes: List[str] = None
    
    def __post_init__(self):
        if self.peaks is None:
            self.peaks = []
        if self.notes is None:
            self.notes = []


def beer_lambert_law(
    absorbance: float,
    epsilon: float,
    path_length: float = 1.0,
) -> float:
    """Calculate concentration using Beer-Lambert law.
    
    A = ε × c × l
    c = A / (ε × l)
    
    Args:
        absorbance: Measured absorbance (unitless)
        epsilon: Molar absorptivity in M^-1 cm^-1
        path_length: Path length in cm (default 1.0 cm)
        
    Returns:
        Concentration in M (mol/L)
        
    Raises:
        ValueError: If epsilon or path_length are zero or negative
        
    Example:
        >>> beer_lambert_law(0.5, 25000, 1.0)
        2e-05  # 20 µM
    """
    if epsilon <= 0:
        raise ValueError("Molar absorptivity must be positive")
    if path_length <= 0:
        raise ValueError("Path length must be positive")
    if absorbance < 0:
        raise ValueError("Absorbance cannot be negative")
    
    concentration = absorbance / (epsilon * path_length)
    return concentration


def calculate_absorbance(
    concentration: float,
    epsilon: float,
    path_length: float = 1.0,
) -> float:
    """Calculate expected absorbance using Beer-Lambert law.
    
    A = ε × c × l
    
    Args:
        concentration: Concentration in M (mol/L)
        epsilon: Molar absorptivity in M^-1 cm^-1
        path_length: Path length in cm (default 1.0 cm)
        
    Returns:
        Absorbance (unitless)
        
    Raises:
        ValueError: If inputs are negative
        
    Example:
        >>> calculate_absorbance(1e-5, 25000, 1.0)
        0.25
    """
    if concentration < 0:
        raise ValueError("Concentration cannot be negative")
    if epsilon < 0:
        raise ValueError("Molar absorptivity cannot be negative")
    if path_length <= 0:
        raise ValueError("Path length must be positive")
    
    absorbance = epsilon * concentration * path_length
    return absorbance


def find_lambda_max(
    spectrum: List[Tuple[float, float]],
    wavelength_range: Tuple[float, float] | None = None,
) -> Tuple[float, float]:
    """Find wavelength of maximum absorption (λmax) in a spectrum.
    
    Args:
        spectrum: List of (wavelength_nm, absorbance) tuples
        wavelength_range: Optional (min_nm, max_nm) to restrict search
        
    Returns:
        Tuple of (lambda_max_nm, absorbance_max)
        
    Raises:
        ValueError: If spectrum is empty
        
    Example:
        >>> spectrum = [(250, 0.1), (280, 0.8), (300, 0.3)]
        >>> find_lambda_max(spectrum)
        (280.0, 0.8)
    """
    if not spectrum:
        raise ValueError("Spectrum cannot be empty")
    
    # Filter by wavelength range if specified
    if wavelength_range:
        min_wl, max_wl = wavelength_range
        spectrum = [(wl, abs_val) for wl, abs_val in spectrum 
                    if min_wl <= wl <= max_wl]
        
        if not spectrum:
            raise ValueError("No data points in specified wavelength range")
    
    # Find maximum
    lambda_max, absorbance_max = max(spectrum, key=lambda x: x[1])
    
    return lambda_max, absorbance_max


def detect_absorption_peaks(
    spectrum: List[Tuple[float, float]],
    threshold: float = 0.1,
    min_separation: float = 10.0,
) -> List[Dict[str, float]]:
    """Detect absorption peaks in a UV-Vis spectrum.
    
    Uses simple local maximum detection with threshold filtering.
    
    Args:
        spectrum: List of (wavelength_nm, absorbance) tuples (must be sorted)
        threshold: Minimum absorbance to consider a peak
        min_separation: Minimum wavelength separation between peaks (nm)
        
    Returns:
        List of detected peaks with wavelength and absorbance
        
    Example:
        >>> spectrum = [(250, 0.05), (280, 0.8), (285, 0.7), (350, 0.4)]
        >>> detect_absorption_peaks(spectrum, threshold=0.3)
        [{'wavelength': 280.0, 'absorbance': 0.8}, {'wavelength': 350.0, 'absorbance': 0.4}]
    """
    if not spectrum:
        return []
    
    # Sort by wavelength
    spectrum = sorted(spectrum, key=lambda x: x[0])
    
    peaks = []
    
    # Find all local maxima (interior points)
    local_maxima = []
    for i in range(1, len(spectrum) - 1):
        wl, abs_val = spectrum[i]
        prev_abs = spectrum[i - 1][1]
        next_abs = spectrum[i + 1][1]
        
        # Check if local maximum
        if abs_val > prev_abs and abs_val > next_abs and abs_val >= threshold:
            local_maxima.append((i, wl, abs_val))
    
    # Check if first point is edge peak (higher than next)
    if len(spectrum) >= 2:
        first_wl, first_abs = spectrum[0]
        next_abs = spectrum[1][1]
        if first_abs > next_abs and first_abs >= threshold:
            local_maxima.insert(0, (0, first_wl, first_abs))
    
    # Check if last point is edge peak (higher than previous OR just above threshold if far enough)
    if len(spectrum) >= 2:
        last_wl, last_abs = spectrum[-1]
        prev_abs = spectrum[-2][1]
        # Accept last point as peak if it's above threshold and far enough from any found peaks
        if last_abs >= threshold:
            if last_abs > prev_abs or (not local_maxima or (last_wl - local_maxima[-1][1]) >= min_separation):
                local_maxima.append((len(spectrum) - 1, last_wl, last_abs))
    
    # Filter by minimum separation
    for i, wl, abs_val in local_maxima:
        if not peaks or (wl - peaks[-1]["wavelength"]) >= min_separation:
            peaks.append({"wavelength": wl, "absorbance": abs_val})
    
    return peaks


def analyze_uv_vis_spectrum(
    spectrum: List[Tuple[float, float]],
    epsilon: float | None = None,
    path_length: float = 1.0,
    wavelength_range: Tuple[float, float] | None = None,
) -> UVVisResult:
    """Comprehensive analysis of UV-Vis absorption spectrum.
    
    Args:
        spectrum: List of (wavelength_nm, absorbance) tuples
        epsilon: Known molar absorptivity in M^-1 cm^-1 (for concentration calc)
        path_length: Path length in cm
        wavelength_range: Optional (min_nm, max_nm) for λmax search
        
    Returns:
        UVVisResult with detected peaks and calculated values
        
    Example:
        >>> spectrum = [(250, 0.1), (280, 0.5), (350, 0.3)]
        >>> result = analyze_uv_vis_spectrum(spectrum, epsilon=25000)
        >>> result.lambda_max
        280.0
        >>> result.concentration
        2e-05
    """
    result = UVVisResult(path_length=path_length, epsilon=epsilon)
    
    if not spectrum:
        result.notes.append("Empty spectrum provided")
        return result
    
    # Find λmax
    try:
        lambda_max, absorbance_max = find_lambda_max(spectrum, wavelength_range)
        result.lambda_max = lambda_max
        result.absorbance_max = absorbance_max
        
        # Calculate concentration if epsilon known
        if epsilon is not None:
            try:
                conc = beer_lambert_law(absorbance_max, epsilon, path_length)
                result.concentration = conc
                result.notes.append(
                    f"Calculated concentration: {conc:.2e} M using Beer-Lambert law"
                )
            except ValueError as e:
                result.notes.append(f"Concentration calculation failed: {e}")
        
    except ValueError as e:
        result.notes.append(f"λmax detection failed: {e}")
    
    # Detect all peaks
    peaks = detect_absorption_peaks(spectrum)
    result.peaks = peaks
    result.notes.append(f"Detected {len(peaks)} absorption peaks")
    
    # Warnings
    if result.absorbance_max and result.absorbance_max > 2.0:
        result.notes.append(
            "WARNING: Absorbance > 2.0 may be outside linear range"
        )
    
    return result


# Module registration metadata
MODULE_KEY = "spectroscopy.uv_vis"
MODULE_VERSION = "1.0.0"

__all__ = [
    "UVVisResult",
    "beer_lambert_law",
    "calculate_absorbance",
    "find_lambda_max",
    "detect_absorption_peaks",
    "analyze_uv_vis_spectrum",
]


def _register() -> None:
    """Register UV-Vis spectroscopy with module system."""
    from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor
    
    descriptor = ModuleDescriptor(
        module_id=MODULE_KEY,
        version=MODULE_VERSION,
        description="UV-Visible absorption spectroscopy with Beer-Lambert law",
    )
    
    descriptor.register_operation(
        ModuleOperation(
            name="analyze_spectrum",
            description="Analyze UV-Vis spectrum and calculate concentration",
            handler=lambda params: analyze_uv_vis_spectrum(**params),
        )
    )
    
    descriptor.register_operation(
        ModuleOperation(
            name="calculate_concentration",
            description="Calculate concentration from absorbance using Beer-Lambert law",
            handler=lambda params: beer_lambert_law(**params),
        )
    )
    
    descriptor.register_operation(
        ModuleOperation(
            name="calculate_absorbance",
            description="Calculate absorbance from concentration",
            handler=lambda params: calculate_absorbance(**params),
        )
    )
    
    register_descriptor(descriptor)


# Auto-register on import
_register()
