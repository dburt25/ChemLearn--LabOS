"""Isotope pattern calculator for EI-MS analysis.

Calculates expected isotope distributions based on molecular formulas
using natural abundance data for common elements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


# Natural isotope abundances (relative to most abundant isotope = 100)
ISOTOPE_DATA = {
    "C": [
        {"mass": 12.000000, "abundance": 100.0},  # 12C
        {"mass": 13.003355, "abundance": 1.07},   # 13C
    ],
    "H": [
        {"mass": 1.007825, "abundance": 100.0},   # 1H
        {"mass": 2.014102, "abundance": 0.015},   # 2H (deuterium)
    ],
    "N": [
        {"mass": 14.003074, "abundance": 100.0},  # 14N
        {"mass": 15.000109, "abundance": 0.37},   # 15N
    ],
    "O": [
        {"mass": 15.994915, "abundance": 100.0},  # 16O
        {"mass": 16.999132, "abundance": 0.04},   # 17O
        {"mass": 17.999160, "abundance": 0.20},   # 18O
    ],
    "S": [
        {"mass": 31.972071, "abundance": 100.0},  # 32S
        {"mass": 32.971459, "abundance": 0.80},   # 33S
        {"mass": 33.967867, "abundance": 4.50},   # 34S
    ],
    "Cl": [
        {"mass": 34.968853, "abundance": 100.0},  # 35Cl
        {"mass": 36.965903, "abundance": 32.0},   # 37Cl
    ],
    "Br": [
        {"mass": 78.918336, "abundance": 100.0},  # 79Br
        {"mass": 80.916289, "abundance": 98.0},   # 81Br
    ],
    "F": [
        {"mass": 18.998403, "abundance": 100.0},  # 19F (monoisotopic)
    ],
    "P": [
        {"mass": 30.973762, "abundance": 100.0},  # 31P (monoisotopic)
    ],
    "I": [
        {"mass": 126.904468, "abundance": 100.0}, # 127I (monoisotopic)
    ],
}


@dataclass
class IsotopePeak:
    """Represents a peak in an isotope pattern."""
    
    mass: float
    relative_intensity: float
    label: str  # e.g., "M", "M+1", "M+2"
    
    def __repr__(self) -> str:
        return f"IsotopePeak({self.label}, m/z={self.mass:.1f}, {self.relative_intensity:.1f}%)"


@dataclass
class IsotopePattern:
    """Complete isotope pattern for a molecular formula."""
    
    formula: str
    peaks: List[IsotopePeak]
    monoisotopic_mass: float
    
    def get_peak(self, label: str) -> IsotopePeak | None:
        """Get peak by label (M, M+1, M+2, etc.)."""
        for peak in self.peaks:
            if peak.label == label:
                return peak
        return None
    
    def to_dict(self) -> Dict[str, object]:
        """Serialize to dictionary."""
        return {
            "formula": self.formula,
            "monoisotopic_mass": self.monoisotopic_mass,
            "peaks": [
                {
                    "mass": p.mass,
                    "relative_intensity": p.relative_intensity,
                    "label": p.label,
                }
                for p in self.peaks
            ],
        }


def parse_molecular_formula(formula: str) -> Dict[str, int]:
    """Parse molecular formula into element counts.
    
    Args:
        formula: Molecular formula (e.g., "C6H12O6", "CH3Cl")
        
    Returns:
        Dictionary mapping element symbols to counts
        
    Example:
        >>> parse_molecular_formula("C6H12O6")
        {'C': 6, 'H': 12, 'O': 6}
    """
    import re
    
    element_pattern = r'([A-Z][a-z]?)(\d*)'
    matches = re.findall(element_pattern, formula)
    
    composition = {}
    for element, count_str in matches:
        if element:  # Skip empty matches
            count = int(count_str) if count_str else 1
            composition[element] = composition.get(element, 0) + count
    
    return composition


def calculate_monoisotopic_mass(composition: Dict[str, int]) -> float:
    """Calculate monoisotopic mass from elemental composition.
    
    Uses most abundant isotope for each element.
    
    Args:
        composition: Element symbol to count mapping
        
    Returns:
        Monoisotopic mass in Da
    """
    total_mass = 0.0
    
    for element, count in composition.items():
        if element not in ISOTOPE_DATA:
            raise ValueError(f"Unknown element: {element}")
        
        # Use most abundant isotope (first in list)
        monoisotopic = ISOTOPE_DATA[element][0]["mass"]
        total_mass += monoisotopic * count
    
    return total_mass


def calculate_isotope_pattern(
    formula: str,
    max_peaks: int = 5,
    min_intensity: float = 0.1,
) -> IsotopePattern:
    """Calculate isotope pattern for a molecular formula.
    
    Uses binomial expansion for simple estimation of M, M+1, M+2 peaks.
    
    Args:
        formula: Molecular formula (e.g., "C10H8")
        max_peaks: Maximum number of peaks to calculate
        min_intensity: Minimum relative intensity threshold (%)
        
    Returns:
        IsotopePattern with calculated peaks
        
    Example:
        >>> pattern = calculate_isotope_pattern("C10H8")
        >>> pattern.get_peak("M").relative_intensity
        100.0
        >>> pattern.get_peak("M+1").relative_intensity
        10.7  # ~10 carbons * 1.07% 13C contribution
    """
    # Handle both string and dict input
    if isinstance(formula, dict):
        composition = formula
        formula_str = "".join(f"{elem}{count}" for elem, count in composition.items())
    else:
        composition = parse_molecular_formula(formula)
        formula_str = formula
    
    monoisotopic_mass = calculate_monoisotopic_mass(composition)
    
    # Calculate M+1 and M+2 contributions
    m_plus_1 = 0.0
    m_plus_2 = 0.0
    
    for element, count in composition.items():
        if element not in ISOTOPE_DATA:
            continue
        
        isotopes = ISOTOPE_DATA[element]
        
        # M+1 contribution (first heavy isotope)
        if len(isotopes) > 1:
            heavy_1_abundance = isotopes[1]["abundance"]
            m_plus_1 += count * heavy_1_abundance
        
        # M+2 contribution (second heavy isotope or binomial from M+1)
        if len(isotopes) > 2:
            heavy_2_abundance = isotopes[2]["abundance"]
            m_plus_2 += count * heavy_2_abundance
        
        # Binomial contribution to M+2 from two M+1 isotopes
        if len(isotopes) > 1:
            heavy_1_abundance = isotopes[1]["abundance"]
            # Probability of two M+1 isotopes
            if count > 1:
                m_plus_2 += (count * (count - 1) / 2) * (heavy_1_abundance / 100) ** 2 * 100
    
    peaks = [
        IsotopePeak(mass=monoisotopic_mass, relative_intensity=100.0, label="M"),
        IsotopePeak(mass=monoisotopic_mass + 1, relative_intensity=m_plus_1, label="M+1"),
        IsotopePeak(mass=monoisotopic_mass + 2, relative_intensity=m_plus_2, label="M+2"),
    ]
    
    # Filter by minimum intensity
    peaks = [p for p in peaks if p.relative_intensity >= min_intensity]
    
    # Limit to max_peaks
    peaks = peaks[:max_peaks]
    
    return IsotopePattern(
        formula=formula_str,
        peaks=peaks,
        monoisotopic_mass=monoisotopic_mass,
    )


def match_isotope_pattern(
    experimental_peaks: List[Tuple[float, float]],
    formula: str | Dict[str, int],
    mass_tolerance: float = 0.5,
) -> float:
    """Match experimental peaks to theoretical isotope pattern.
    
    Args:
        experimental_peaks: List of (m/z, intensity) tuples
        formula: Molecular formula string or dict
        mass_tolerance: Mass tolerance in Da
        
    Returns:
        Match score between 0 and 1 (higher is better)
    """
    theoretical = calculate_isotope_pattern(formula)
    
    if not experimental_peaks or not theoretical.peaks:
        return 0.0
    
    # Normalize experimental intensities
    max_exp_int = max(intensity for _, intensity in experimental_peaks)
    norm_exp = [(mz, intensity / max_exp_int * 100) for mz, intensity in experimental_peaks]
    
    # Calculate intensity match score for matched peaks
    total_score = 0.0
    matched_peaks = 0
    
    for theo_peak in theoretical.peaks:
        # Find best matching experimental peak
        best_match = None
        best_error = float('inf')
        
        for exp_mz, exp_int in norm_exp:
            mass_error = abs(exp_mz - theo_peak.mass)
            if mass_error < mass_tolerance and mass_error < best_error:
                best_error = mass_error
                best_match = (exp_mz, exp_int)
        
        if best_match:
            matched_peaks += 1
            # Intensity match score (closer = better)
            intensity_diff = abs(theo_peak.relative_intensity - best_match[1])
            peak_score = max(0, 1.0 - intensity_diff / 100.0)
            total_score += peak_score
    
    # Combine peak matching with intensity matching
    if theoretical.peaks:
        match_ratio = matched_peaks / len(theoretical.peaks)
        avg_intensity_score = total_score / len(theoretical.peaks) if matched_peaks > 0 else 0.0
        final_score = (match_ratio + avg_intensity_score) / 2.0
        return final_score
    
    return 0.0


def identify_halogens(pattern: IsotopePattern) -> List[str]:
    """Identify likely halogen presence from isotope pattern.
    
    Distinctive patterns:
    - Cl: M+2 ~32% of M (35Cl/37Cl ratio)
    - Br: M+2 ~98% of M (79Br/81Br near 1:1)
    - Multiple halogens show characteristic multiplets
    
    Args:
        pattern: Calculated isotope pattern
        
    Returns:
        List of detected halogens (e.g., ["chlorine", "bromine"])
    """
    identifications = []
    
    m_peak = pattern.get_peak("M")
    m2_peak = pattern.get_peak("M+2")
    
    if not m_peak or not m2_peak:
        return identifications
    
    m2_ratio = m2_peak.relative_intensity / m_peak.relative_intensity
    
    # Chlorine signature: M+2 ~30-35% of M
    if 0.25 < m2_ratio < 0.40:
        identifications.append("chlorine")
    
    # Bromine signature: M+2 ~95-100% of M
    if 0.90 < m2_ratio < 1.10:
        identifications.append("bromine")
    
    # Two chlorines: M+2 ~65%
    elif 0.55 < m2_ratio < 0.75:
        identifications.append("chlorine")
    
    return identifications


# Module registration
MODULE_KEY = "ei_ms.isotope_patterns"
MODULE_VERSION = "1.0.0"


def analyze_isotope_pattern(
    molecular_formula: str,
    experimental_peaks: List[Tuple[float, float]] | None = None,
    mass_tolerance: float = 0.5,
) -> Dict[str, object]:
    """Analyze isotope pattern for a molecular formula.
    
    Main entry point for module operation.
    
    Args:
        molecular_formula: Molecular formula string
        experimental_peaks: Optional experimental peaks for matching
        mass_tolerance: Mass tolerance for matching
        
    Returns:
        Analysis results including pattern and identifications
    """
    composition = parse_molecular_formula(molecular_formula)
    pattern = calculate_isotope_pattern(composition)
    halogens = identify_halogens(pattern)
    
    result = {
        "formula": composition,
        "monoisotopic_mass": pattern.monoisotopic_mass,
        "theoretical_pattern": {
            "peaks": [
                {"label": p.label, "mass": p.mass, "intensity": p.relative_intensity}
                for p in pattern.peaks
            ]
        },
        "halogens": halogens,
    }
    
    if experimental_peaks:
        match_score = match_isotope_pattern(experimental_peaks, composition, mass_tolerance)
        result["match_score"] = match_score
    
    return result


def _register() -> None:
    """Register isotope pattern analysis with module system."""
    from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor
    
    descriptor = ModuleDescriptor(
        module_id=MODULE_KEY,
        version=MODULE_VERSION,
        description="Analyze isotope patterns in EI-MS spectra",
    )
    
    descriptor.register_operation(
        ModuleOperation(
            name="analyze",
            description="Calculate and match isotope patterns",
            handler=lambda params: analyze_isotope_pattern(**params),
        )
    )
    
    register_descriptor(descriptor)


# Auto-register on import
_register()
