"""Enhanced NMR spectroscopy analysis with multiplicity recognition and coupling constants.

Provides intelligent peak splitting pattern analysis and J-coupling extraction
for educational chemistry applications.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class NMRPeak:
    """NMR spectral peak with multiplicity analysis.
    
    Attributes:
        chemical_shift: Peak position in ppm
        intensity: Relative intensity (integrated area)
        multiplicity: Peak splitting pattern (s, d, t, q, m, etc.)
        j_coupling: List of coupling constants in Hz (if applicable)
        integration: Relative integration value
        notes: Additional annotations
    """
    
    chemical_shift: float
    intensity: float
    multiplicity: str
    j_coupling: List[float]
    integration: float
    notes: List[str]


# Common NMR multiplicity patterns
MULTIPLICITY_PATTERNS = {
    "s": "singlet (no neighboring protons)",
    "d": "doublet (1 neighboring proton)",
    "t": "triplet (2 neighboring protons)",
    "q": "quartet (3 neighboring protons)",
    "quint": "quintet (4 neighboring protons)",
    "sext": "sextet (5 neighboring protons)",
    "sept": "septet (6 neighboring protons)",
    "m": "multiplet (complex splitting)",
    "dd": "doublet of doublets (2 different couplings)",
    "dt": "doublet of triplets",
    "td": "triplet of doublets",
    "dq": "doublet of quartets",
    "br": "broad signal",
}


# Chemical shift correlation table (1H NMR)
# Format: (min_ppm, max_ppm, environment_description)
H1_NMR_CORRELATION_TABLE = [
    (0.0, 1.0, "Alkyl C-H (methyl groups on saturated carbons)"),
    (1.0, 2.0, "Alkyl C-H (methylene and methine on saturated carbons)"),
    (2.0, 3.0, "Alkyl C-H (alpha to carbonyl or other electron-withdrawing groups)"),
    (3.0, 4.5, "C-H adjacent to oxygen (alcohols, ethers)"),
    (4.5, 6.0, "C-H adjacent to oxygen (acetals, glycosides) or vinyl protons"),
    (6.0, 8.5, "Aromatic C-H"),
    (8.5, 10.0, "Aldehydic C-H"),
    (10.0, 13.0, "Carboxylic acid O-H"),
    (2.0, 5.0, "Amine N-H (variable, often broad)"),
    (1.0, 5.5, "Alcohol O-H (variable, often broad)"),
]


def classify_chemical_shift_environment(chemical_shift: float) -> List[str]:
    """Classify the chemical environment based on chemical shift.
    
    Args:
        chemical_shift: Peak position in ppm
        
    Returns:
        List of possible chemical environments
    """
    environments = []
    for min_ppm, max_ppm, description in H1_NMR_CORRELATION_TABLE:
        if min_ppm <= chemical_shift <= max_ppm:
            environments.append(description)
    
    if not environments:
        environments.append("Chemical shift outside typical 1H NMR range")
    
    return environments


def detect_multiplicity_from_peaks(
    peak_positions: List[float],
    tolerance: float = 0.05
) -> Tuple[str, List[float]]:
    """Detect multiplicity pattern from a cluster of peaks.
    
    Args:
        peak_positions: List of peak positions (in ppm) that form a multiplet
        tolerance: Tolerance for determining equal spacing (in ppm)
        
    Returns:
        Tuple of (multiplicity_code, coupling_constants)
    """
    if len(peak_positions) == 1:
        return ("s", [])
    
    # Sort peaks
    sorted_peaks = sorted(peak_positions)
    
    # Calculate spacings
    spacings = []
    for i in range(len(sorted_peaks) - 1):
        spacing = sorted_peaks[i + 1] - sorted_peaks[i]
        spacings.append(spacing)
    
    if not spacings:
        return ("s", [])
    
    # Check if spacings are approximately equal (simple multiplet)
    avg_spacing = sum(spacings) / len(spacings)
    is_equal_spacing = all(abs(s - avg_spacing) < tolerance for s in spacings)
    
    if is_equal_spacing:
        # Simple first-order multiplet
        n_peaks = len(sorted_peaks)
        if n_peaks == 2:
            multiplicity = "d"
        elif n_peaks == 3:
            multiplicity = "t"
        elif n_peaks == 4:
            multiplicity = "q"
        elif n_peaks == 5:
            multiplicity = "quint"
        elif n_peaks == 6:
            multiplicity = "sext"
        elif n_peaks == 7:
            multiplicity = "sept"
        else:
            multiplicity = "m"
        
        # Estimate J coupling (convert ppm spacing to Hz, assuming 400 MHz spectrometer)
        j_coupling_hz = avg_spacing * 400  # Rough estimate
        return (multiplicity, [j_coupling_hz])
    
    else:
        # Complex multiplet - check for doublet of doublets pattern
        if len(sorted_peaks) == 4:
            # Could be doublet of doublets
            space1 = sorted_peaks[1] - sorted_peaks[0]
            space2 = sorted_peaks[2] - sorted_peaks[1]
            space3 = sorted_peaks[3] - sorted_peaks[2]
            
            # dd pattern: spacing pattern should be A-B-A or similar
            if abs(space1 - space3) < tolerance:
                j1 = space1 * 400
                j2 = space2 * 400
                return ("dd", [j1, j2])
        
        return ("m", [])


def estimate_integration(
    spectrum: List[Tuple[float, float]],
    peak_center: float,
    window: float = 0.5
) -> float:
    """Estimate peak integration by summing intensities in a window.
    
    Args:
        spectrum: Full spectrum as (chemical_shift, intensity) tuples
        peak_center: Center of the peak in ppm
        window: Integration window width in ppm (total, ±window/2)
        
    Returns:
        Integrated area
    """
    total = 0.0
    half_window = window / 2
    
    for shift, intensity in spectrum:
        if abs(shift - peak_center) <= half_window:
            total += intensity
    
    return total


def analyze_nmr_spectrum_enhanced(
    spectrum: List[Tuple[float, float]],
    threshold: float = 0.1,
    spectrometer_frequency: float = 400.0,
    detect_multiplets: bool = True
) -> Dict[str, object]:
    """Enhanced NMR spectrum analysis with multiplicity recognition.
    
    Args:
        spectrum: List of (chemical_shift_ppm, intensity) tuples
        threshold: Minimum intensity to report a peak
        spectrometer_frequency: Spectrometer frequency in MHz (for J-coupling estimation)
        detect_multiplets: If True, attempt to group nearby peaks into multiplets
        
    Returns:
        Dictionary containing:
            - peaks: List of NMRPeak objects with multiplicity assignments
            - total_integration: Sum of all peak integrations
            - chemical_shift_regions: Dictionary mapping regions to peak counts
            - notes: Analysis notes and interpretation guidance
    """
    if not spectrum:
        return {
            "peaks": [],
            "total_integration": 0.0,
            "chemical_shift_regions": {},
            "notes": ["Empty spectrum provided"]
        }
    
    # Sort spectrum by chemical shift
    sorted_spectrum = sorted(spectrum, key=lambda x: x[0])
    
    # Find local maxima above threshold (including edge peaks)
    peak_candidates: List[Tuple[float, float]] = []
    
    # Check interior points
    for i in range(1, len(sorted_spectrum) - 1):
        shift, intensity = sorted_spectrum[i]
        prev_intensity = sorted_spectrum[i - 1][1]
        next_intensity = sorted_spectrum[i + 1][1]
        
        if intensity >= threshold and intensity > prev_intensity and intensity > next_intensity:
            peak_candidates.append((shift, intensity))
    
    # Check first point as potential edge peak
    if len(sorted_spectrum) >= 2:
        first_shift, first_intensity = sorted_spectrum[0]
        next_intensity = sorted_spectrum[1][1]
        if first_intensity >= threshold and first_intensity > next_intensity:
            peak_candidates.insert(0, (first_shift, first_intensity))
    
    # Check last point as potential edge peak
    if len(sorted_spectrum) >= 2:
        last_shift, last_intensity = sorted_spectrum[-1]
        prev_intensity = sorted_spectrum[-2][1]
        if last_intensity >= threshold and last_intensity > prev_intensity:
            peak_candidates.append((last_shift, last_intensity))
    
    # Group peaks into multiplets if requested
    analyzed_peaks: List[NMRPeak] = []
    
    if detect_multiplets and len(peak_candidates) > 1:
        # Group nearby peaks (within 0.3 ppm)
        multiplet_tolerance = 0.3
        groups: List[List[Tuple[float, float]]] = []
        current_group = [peak_candidates[0]]
        
        for i in range(1, len(peak_candidates)):
            prev_shift = peak_candidates[i - 1][0]
            curr_shift, curr_intensity = peak_candidates[i]
            
            if abs(curr_shift - prev_shift) <= multiplet_tolerance:
                current_group.append((curr_shift, curr_intensity))
            else:
                groups.append(current_group)
                current_group = [(curr_shift, curr_intensity)]
        
        groups.append(current_group)
        
        # Analyze each group
        for group in groups:
            if not group:
                continue
            
            # Calculate center of multiplet
            center_shift = sum(p[0] for p in group) / len(group)
            total_intensity = sum(p[1] for p in group)
            
            # Detect multiplicity
            peak_positions = [p[0] for p in group]
            multiplicity, j_couplings = detect_multiplicity_from_peaks(peak_positions)
            
            # Estimate integration
            integration = estimate_integration(sorted_spectrum, center_shift)
            
            # Get chemical shift environment
            environments = classify_chemical_shift_environment(center_shift)
            
            # Build notes
            notes = []
            for env in environments:
                notes.append(f"Chemical environment: {env}")
            if multiplicity in MULTIPLICITY_PATTERNS:
                notes.append(f"Splitting: {MULTIPLICITY_PATTERNS[multiplicity]}")
            
            peak = NMRPeak(
                chemical_shift=center_shift,
                intensity=total_intensity,
                multiplicity=multiplicity,
                j_coupling=j_couplings,
                integration=integration,
                notes=notes
            )
            analyzed_peaks.append(peak)
    
    else:
        # Treat each peak independently
        for shift, intensity in peak_candidates:
            integration = estimate_integration(sorted_spectrum, shift)
            environments = classify_chemical_shift_environment(shift)
            
            notes = []
            for env in environments:
                notes.append(f"Chemical environment: {env}")
            
            peak = NMRPeak(
                chemical_shift=shift,
                intensity=intensity,
                multiplicity="s",  # Default to singlet
                j_coupling=[],
                integration=integration,
                notes=notes
            )
            analyzed_peaks.append(peak)
    
    # Calculate total integration
    total_integration = sum(p.integration for p in analyzed_peaks)
    
    # Classify peaks by region
    chemical_shift_regions = {
        "alkyl (0-2 ppm)": 0,
        "alpha to EWG (2-3 ppm)": 0,
        "adjacent to O (3-5 ppm)": 0,
        "aromatic (6-8.5 ppm)": 0,
        "aldehydic (8.5-10 ppm)": 0,
        "acidic (10-13 ppm)": 0,
    }
    
    for peak in analyzed_peaks:
        shift = peak.chemical_shift
        if 0 <= shift < 2:
            chemical_shift_regions["alkyl (0-2 ppm)"] += 1
        elif 2 <= shift < 3:
            chemical_shift_regions["alpha to EWG (2-3 ppm)"] += 1
        elif 3 <= shift < 5:
            chemical_shift_regions["adjacent to O (3-5 ppm)"] += 1
        elif 6 <= shift < 8.5:
            chemical_shift_regions["aromatic (6-8.5 ppm)"] += 1
        elif 8.5 <= shift < 10:
            chemical_shift_regions["aldehydic (8.5-10 ppm)"] += 1
        elif 10 <= shift <= 13:
            chemical_shift_regions["acidic (10-13 ppm)"] += 1
    
    # Generate interpretation notes
    notes = []
    if analyzed_peaks:
        notes.append(f"Detected {len(analyzed_peaks)} multiplets with total integration: {total_integration:.2f}")
        
        # Count multiplicities
        mult_counts: Dict[str, int] = {}
        for peak in analyzed_peaks:
            mult_counts[peak.multiplicity] = mult_counts.get(peak.multiplicity, 0) + 1
        
        mult_summary = ", ".join(f"{count} {mult}" for mult, count in sorted(mult_counts.items()))
        notes.append(f"Multiplicity distribution: {mult_summary}")
        
        # Check for aromatic signals
        aromatic_count = chemical_shift_regions["aromatic (6-8.5 ppm)"]
        if aromatic_count > 0:
            notes.append(f"Aromatic region contains {aromatic_count} multiplet(s), suggesting aromatic compound")
    else:
        notes.append("No significant peaks detected above threshold")
    
    return {
        "peaks": analyzed_peaks,
        "total_integration": total_integration,
        "chemical_shift_regions": chemical_shift_regions,
        "notes": notes
    }


# Module metadata
MODULE_KEY = "spectroscopy.nmr_enhanced"
MODULE_VERSION = "1.0.0"

__all__ = [
    "NMRPeak",
    "analyze_nmr_spectrum_enhanced",
    "detect_multiplicity_from_peaks",
    "classify_chemical_shift_environment",
    "MULTIPLICITY_PATTERNS",
    "H1_NMR_CORRELATION_TABLE",
]
