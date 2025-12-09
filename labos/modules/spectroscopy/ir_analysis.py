"""Enhanced IR spectroscopy analysis with comprehensive functional group recognition.

Provides expanded wavenumber correlation tables and intelligent peak annotation
for educational chemistry applications.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class IRPeak:
    """IR spectral peak with functional group annotation.
    
    Attributes:
        wavenumber: Peak position in cm⁻¹
        intensity: Relative intensity (0-1 scale)
        functional_groups: List of possible functional group assignments
        peak_type: Description (strong, medium, weak, broad)
    """
    
    wavenumber: float
    intensity: float
    functional_groups: List[str]
    peak_type: str


# Comprehensive IR correlation table
# Format: (min_wavenumber, max_wavenumber, functional_group, description)
IR_CORRELATION_TABLE = [
    # O-H stretches
    (3200, 3650, "O-H (alcohol)", "Strong, broad - alcohol hydroxyl stretch"),
    (2500, 3300, "O-H (carboxylic acid)", "Very broad - carboxylic acid hydroxyl stretch"),
    
    # N-H stretches
    (3300, 3500, "N-H (amine, primary)", "Medium, sharp doublet - primary amine"),
    (3250, 3400, "N-H (amine, secondary)", "Medium, sharp singlet - secondary amine"),
    (3100, 3400, "N-H (amide)", "Medium - amide N-H stretch"),
    
    # C-H stretches
    (2850, 3000, "C-H (alkane)", "Medium to strong - aliphatic C-H stretch"),
    (3000, 3100, "C-H (alkene)", "Medium - vinyl C-H stretch"),
    (3260, 3330, "C-H (alkyne)", "Strong, sharp - terminal alkyne C-H stretch"),
    (2700, 2850, "C-H (aldehyde)", "Medium, doublet - aldehydic C-H stretch"),
    (3000, 3150, "C-H (aromatic)", "Medium - aromatic C-H stretch"),
    
    # C≡C and C≡N stretches
    (2100, 2260, "C≡C (alkyne)", "Weak to medium - alkyne C≡C stretch"),
    (2210, 2260, "C≡N (nitrile)", "Medium, sharp - nitrile C≡N stretch"),
    
    # C=O stretches (most diagnostic region)
    (1680, 1750, "C=O (ketone)", "Strong, sharp - ketone carbonyl stretch"),
    (1720, 1740, "C=O (aldehyde)", "Strong, sharp - aldehyde carbonyl stretch"),
    (1735, 1750, "C=O (ester)", "Strong, sharp - ester carbonyl stretch"),
    (1650, 1690, "C=O (amide)", "Strong - amide carbonyl stretch (amide I band)"),
    (1700, 1725, "C=O (carboxylic acid)", "Strong - carboxylic acid carbonyl stretch"),
    (1760, 1815, "C=O (acyl chloride)", "Strong - acyl chloride carbonyl stretch"),
    (1800, 1870, "C=O (anhydride)", "Strong, doublet - anhydride carbonyl stretch"),
    
    # C=C stretches
    (1620, 1680, "C=C (alkene)", "Variable - alkene C=C stretch"),
    (1450, 1650, "C=C (aromatic)", "Variable - aromatic C=C stretch"),
    
    # N-H bends
    (1550, 1650, "N-H (amide II)", "Medium to strong - amide N-H bend (amide II band)"),
    (1550, 1650, "N-H (amine)", "Medium - amine N-H bend"),
    
    # C-O stretches
    (1000, 1300, "C-O (alcohol)", "Strong - alcohol C-O stretch"),
    (1000, 1300, "C-O (ether)", "Strong - ether C-O stretch"),
    (1050, 1150, "C-O (ester)", "Strong, doublet - ester C-O stretch"),
    (1250, 1300, "C-O (carboxylic acid)", "Strong - carboxylic acid C-O stretch"),
    
    # C-N stretches
    (1020, 1250, "C-N (amine)", "Medium - amine C-N stretch"),
    (1180, 1360, "C-N (amide III)", "Medium - amide C-N stretch (amide III band)"),
    
    # S=O stretches
    (1030, 1060, "S=O (sulfoxide)", "Strong - sulfoxide S=O stretch"),
    (1300, 1350, "S=O (sulfone)", "Strong - sulfone S=O stretch"),
    
    # C-X stretches (halogens)
    (700, 800, "C-Cl", "Strong - C-Cl stretch"),
    (500, 600, "C-Br", "Strong - C-Br stretch"),
    (500, 600, "C-I", "Strong - C-I stretch"),
    (1000, 1400, "C-F", "Strong - C-F stretch"),
    
    # Fingerprint region indicators
    (650, 900, "Aromatic C-H bend", "Strong - out-of-plane aromatic C-H bending"),
    (690, 900, "Alkene C-H bend", "Strong - alkene C-H out-of-plane bending"),
]


def classify_peak_intensity(intensity: float) -> str:
    """Classify IR peak intensity.
    
    Args:
        intensity: Normalized intensity (0-1)
        
    Returns:
        Peak type description
    """
    if intensity >= 0.8:
        return "very strong"
    elif intensity >= 0.6:
        return "strong"
    elif intensity >= 0.4:
        return "medium"
    elif intensity >= 0.2:
        return "weak"
    else:
        return "very weak"


def is_broad_peak(spectrum: List[Tuple[float, float]], 
                  peak_wavenumber: float,
                  width_threshold: float = 100.0) -> bool:
    """Determine if a peak is broad based on neighboring points.
    
    Args:
        spectrum: Full spectrum as (wavenumber, intensity) pairs
        peak_wavenumber: The wavenumber of the peak to check
        width_threshold: Minimum width in cm⁻¹ to be considered broad
        
    Returns:
        True if peak appears broad
    """
    # Find peak index
    peak_idx = None
    for i, (wn, _) in enumerate(spectrum):
        if abs(wn - peak_wavenumber) < 5:  # Close enough
            peak_idx = i
            break
    
    if peak_idx is None or peak_idx == 0 or peak_idx == len(spectrum) - 1:
        return False
    
    peak_intensity = spectrum[peak_idx][1]
    half_max = peak_intensity / 2
    
    # Find left and right half-max points
    left_wn = right_wn = peak_wavenumber
    for i in range(peak_idx - 1, -1, -1):
        if spectrum[i][1] < half_max:
            left_wn = spectrum[i][0]
            break
    
    for i in range(peak_idx + 1, len(spectrum)):
        if spectrum[i][1] < half_max:
            right_wn = spectrum[i][0]
            break
    
    width = abs(right_wn - left_wn)
    return width > width_threshold


def annotate_ir_peak(wavenumber: float, 
                     intensity: float,
                     spectrum: List[Tuple[float, float]] | None = None) -> IRPeak:
    """Annotate an IR peak with functional group assignments.
    
    Args:
        wavenumber: Peak position in cm⁻¹
        intensity: Peak intensity (0-1 scale)
        spectrum: Optional full spectrum for breadth analysis
        
    Returns:
        IRPeak with functional group annotations
    """
    functional_groups = []
    
    # Check correlation table
    for min_wn, max_wn, group, description in IR_CORRELATION_TABLE:
        if min_wn <= wavenumber <= max_wn:
            functional_groups.append(f"{group}: {description}")
    
    if not functional_groups:
        functional_groups.append("No specific functional group assignment")
    
    # Determine peak type
    intensity_class = classify_peak_intensity(intensity)
    is_broad = False
    if spectrum:
        is_broad = is_broad_peak(spectrum, wavenumber)
    
    peak_type = f"{intensity_class}{', broad' if is_broad else ''}"
    
    return IRPeak(
        wavenumber=wavenumber,
        intensity=intensity,
        functional_groups=functional_groups,
        peak_type=peak_type
    )


def analyze_ir_spectrum_enhanced(
    spectrum: List[Tuple[float, float]],
    threshold: float = 0.3,
    detect_peaks: bool = True
) -> Dict[str, object]:
    """Enhanced IR spectrum analysis with comprehensive functional group recognition.
    
    Args:
        spectrum: List of (wavenumber_cm⁻¹, intensity) tuples
        threshold: Minimum intensity to report a peak
        detect_peaks: If True, automatically detect local maxima; if False, treat all points above threshold as peaks
        
    Returns:
        Dictionary containing:
            - peaks: List of IRPeak objects
            - functional_group_summary: Dictionary mapping functional groups to detected wavenumbers
            - notes: Analysis notes and interpretation guidance
    """
    if not spectrum:
        return {
            "peaks": [],
            "functional_group_summary": {},
            "notes": ["Empty spectrum provided"]
        }
    
    # Sort spectrum by wavenumber
    sorted_spectrum = sorted(spectrum, key=lambda x: x[0])
    
    detected_peaks: List[IRPeak] = []
    
    if detect_peaks:
        # Detect local maxima
        for i in range(1, len(sorted_spectrum) - 1):
            wn, intensity = sorted_spectrum[i]
            prev_intensity = sorted_spectrum[i - 1][1]
            next_intensity = sorted_spectrum[i + 1][1]
            
            if intensity >= threshold and intensity > prev_intensity and intensity > next_intensity:
                peak = annotate_ir_peak(wn, intensity, sorted_spectrum)
                detected_peaks.append(peak)
    else:
        # Use all points above threshold
        for wn, intensity in sorted_spectrum:
            if intensity >= threshold:
                peak = annotate_ir_peak(wn, intensity, sorted_spectrum)
                detected_peaks.append(peak)
    
    # Build functional group summary
    functional_group_summary: Dict[str, List[float]] = {}
    for peak in detected_peaks:
        for fg_annotation in peak.functional_groups:
            # Extract just the functional group name (before the colon)
            fg_name = fg_annotation.split(":")[0].strip()
            if fg_name not in functional_group_summary:
                functional_group_summary[fg_name] = []
            functional_group_summary[fg_name].append(peak.wavenumber)
    
    # Generate interpretation notes
    notes = []
    if detected_peaks:
        notes.append(f"Detected {len(detected_peaks)} significant peaks above threshold {threshold}")
        
        # Key diagnostic regions
        has_carbonyl = any(1650 <= p.wavenumber <= 1850 for p in detected_peaks)
        has_oh_broad = any(2500 <= p.wavenumber <= 3650 and "broad" in p.peak_type for p in detected_peaks)
        has_nh = any(3100 <= p.wavenumber <= 3500 for p in detected_peaks)
        
        if has_carbonyl:
            notes.append("Strong carbonyl region absorption suggests C=O functional group present")
        if has_oh_broad:
            notes.append("Broad O-H stretch suggests alcohol or carboxylic acid present")
        if has_nh:
            notes.append("N-H stretch region absorption suggests amine or amide present")
    else:
        notes.append("No significant peaks detected above threshold")
    
    return {
        "peaks": detected_peaks,
        "functional_group_summary": functional_group_summary,
        "notes": notes
    }


# Module metadata
MODULE_KEY = "spectroscopy.ir_enhanced"
MODULE_VERSION = "1.0.0"

__all__ = [
    "IRPeak",
    "annotate_ir_peak",
    "analyze_ir_spectrum_enhanced",
    "IR_CORRELATION_TABLE",
]
