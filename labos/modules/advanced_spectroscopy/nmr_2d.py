"""
2D NMR Spectroscopy

Tools for 2D NMR correlation analysis (COSY, HSQC, HMBC).
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional


@dataclass
class NMR2DPeak:
    """2D NMR peak/cross-peak"""
    f1: float  # Chemical shift dimension 1 (ppm)
    f2: float  # Chemical shift dimension 2 (ppm)
    intensity: float
    peak_type: str = "cross_peak"  # or "diagonal"


@dataclass
class COSYCorrelation:
    """COSY correlation between coupled protons"""
    proton1_shift: float  # ppm
    proton2_shift: float  # ppm
    coupling_constant: Optional[float] = None  # Hz
    correlation_type: str = "geminal_or_vicinal"


def identify_cosy_correlations(
    peaks: List[Dict[str, float]],
    diagonal_tolerance: float = 0.1
) -> List[Dict]:
    """
    Identify COSY correlations from 2D NMR peaks
    
    Args:
        peaks: List of 2D peaks with 'f1', 'f2', 'intensity'
        diagonal_tolerance: Tolerance for diagonal peak identification (ppm)
        
    Returns:
        List of COSY correlations
        
    Educational Note:
        COSY (Correlation Spectroscopy):
        - Homonuclear ¹H-¹H correlation
        - Shows coupling between protons (through-bond)
        - Cross-peaks indicate J-coupled protons
        - Geminal (²J): 2-bond coupling (e.g., CH₂)
        - Vicinal (³J): 3-bond coupling (most common, H-C-C-H)
        - Diagonal peaks = 1D spectrum
        - Off-diagonal = correlations
    """
    correlations = []
    
    for peak in peaks:
        f1 = peak.get("f1", 0)
        f2 = peak.get("f2", 0)
        intensity = peak.get("intensity", 0)
        
        # Skip weak peaks
        if intensity < 0.1:
            continue
        
        # Check if diagonal or cross-peak
        if abs(f1 - f2) < diagonal_tolerance:
            # Diagonal peak (not a correlation)
            continue
        
        # Cross-peak = correlation
        correlations.append({
            "proton1_ppm": min(f1, f2),
            "proton2_ppm": max(f1, f2),
            "intensity": intensity,
            "type": "COSY",
            "interpretation": f"¹H at {f1:.2f} ppm coupled to ¹H at {f2:.2f} ppm"
        })
    
    return correlations


def identify_hsqc_correlations(
    peaks: List[Dict[str, float]],
    carbon_shift_range: Tuple[float, float] = (0, 220)
) -> List[Dict]:
    """
    Identify HSQC correlations
    
    Args:
        peaks: List of 2D peaks with 'f1' (¹³C), 'f2' (¹H), 'intensity'
        carbon_shift_range: Expected carbon shift range (ppm)
        
    Returns:
        List of HSQC correlations
        
    Educational Note:
        HSQC (Heteronuclear Single Quantum Coherence):
        - ¹H-¹³C one-bond correlation
        - Shows direct C-H bonds
        - ¹H (horizontal, f2): 0-12 ppm typically
        - ¹³C (vertical, f1): 0-220 ppm
        - Each CH gives one cross-peak
        - CH₂ gives one peak, CH₃ gives one peak
        - Quaternary carbons not observed (no attached H)
        - Edited HSQC: CH/CH₃ positive, CH₂ negative
    """
    correlations = []
    
    for peak in peaks:
        c_shift = peak.get("f1", 0)  # Carbon dimension
        h_shift = peak.get("f2", 0)  # Proton dimension
        intensity = peak.get("intensity", 0)
        
        # Verify in expected ranges
        if not (carbon_shift_range[0] <= c_shift <= carbon_shift_range[1]):
            continue
        if not (0 <= h_shift <= 12):
            continue
        if intensity < 0.1:
            continue
        
        # Classify carbon type based on shift
        if c_shift < 50:
            carbon_type = "aliphatic (sp³)"
        elif 50 <= c_shift < 100:
            carbon_type = "C-O or C-N"
        elif 100 <= c_shift < 160:
            carbon_type = "aromatic or alkene (sp²)"
        else:
            carbon_type = "carbonyl region"
        
        correlations.append({
            "carbon_ppm": c_shift,
            "proton_ppm": h_shift,
            "intensity": intensity,
            "type": "HSQC",
            "carbon_type": carbon_type,
            "interpretation": f"¹H at {h_shift:.2f} ppm directly attached to ¹³C at {c_shift:.1f} ppm ({carbon_type})"
        })
    
    return correlations


def identify_hmbc_correlations(
    peaks: List[Dict[str, float]],
    hsqc_peaks: Optional[List[Dict]] = None
) -> List[Dict]:
    """
    Identify HMBC long-range correlations
    
    Args:
        peaks: List of 2D HMBC peaks with 'f1' (¹³C), 'f2' (¹H), 'intensity'
        hsqc_peaks: Optional HSQC peaks to exclude one-bond correlations
        
    Returns:
        List of HMBC long-range correlations
        
    Educational Note:
        HMBC (Heteronuclear Multiple Bond Correlation):
        - ¹H-¹³C long-range correlation (2-4 bonds)
        - Typically ²J and ³J couplings
        - Shows connectivity across molecule
        - Critical for determining carbon skeleton
        - Sees quaternary carbons (no direct H)
        - Combined with HSQC gives complete structure
        - Key for natural product structure elucidation
    """
    correlations = []
    
    # Build set of HSQC one-bond correlations to exclude
    one_bond_pairs = set()
    if hsqc_peaks:
        for hsqc in hsqc_peaks:
            c_shift = hsqc.get("carbon_ppm", 0)
            h_shift = hsqc.get("proton_ppm", 0)
            # Use tolerance for matching
            one_bond_pairs.add((round(c_shift, 1), round(h_shift, 2)))
    
    for peak in peaks:
        c_shift = peak.get("f1", 0)
        h_shift = peak.get("f2", 0)
        intensity = peak.get("intensity", 0)
        
        if intensity < 0.1:
            continue
        
        # Check if this is a one-bond correlation (should be excluded)
        peak_pair = (round(c_shift, 1), round(h_shift, 2))
        if peak_pair in one_bond_pairs:
            continue
        
        # Estimate bond distance (simplified)
        # Strong correlations usually ²J or ³J
        if intensity > 0.5:
            bond_distance = "2-3 bonds"
        else:
            bond_distance = "3-4 bonds"
        
        correlations.append({
            "carbon_ppm": c_shift,
            "proton_ppm": h_shift,
            "intensity": intensity,
            "type": "HMBC",
            "bond_distance": bond_distance,
            "interpretation": f"¹H at {h_shift:.2f} ppm couples to ¹³C at {c_shift:.1f} ppm ({bond_distance} away)"
        })
    
    return correlations


def analyze_2d_nmr(
    experiment_type: str,
    peaks: List[Dict[str, float]],
    hsqc_reference: Optional[List[Dict]] = None
) -> Dict:
    """
    Comprehensive 2D NMR analysis
    
    Args:
        experiment_type: Type of 2D NMR ('COSY', 'HSQC', 'HMBC')
        peaks: List of 2D peaks
        hsqc_reference: HSQC data for HMBC analysis
        
    Returns:
        Analysis dictionary with correlations and interpretation
        
    Educational Note:
        2D NMR strategy for structure elucidation:
        1. ¹H NMR: identify functional groups
        2. ¹³C NMR: count carbons, identify types
        3. HSQC: assign H-C direct bonds
        4. COSY: find H-H coupling networks
        5. HMBC: connect structural fragments
        6. Combine all data for full structure
        
        Other important 2D experiments:
        - TOCSY: extended spin system correlation
        - NOESY: through-space H-H proximity (NOE)
        - INADEQUATE: C-C connectivity (insensitive)
    """
    if not peaks:
        return {
            "experiment_type": experiment_type,
            "correlations": [],
            "notes": ["No peaks provided"]
        }
    
    experiment_type = experiment_type.upper()
    
    # Route to appropriate analysis
    if experiment_type == "COSY":
        correlations = identify_cosy_correlations(peaks)
        notes = [
            "COSY shows homonuclear ¹H-¹H coupling",
            "Cross-peaks indicate J-coupled protons (2-4 bonds)",
            f"Found {len(correlations)} correlations"
        ]
    elif experiment_type == "HSQC":
        correlations = identify_hsqc_correlations(peaks)
        notes = [
            "HSQC shows direct ¹H-¹³C bonds",
            "Each C-H gives one cross-peak",
            f"Found {len(correlations)} direct C-H correlations"
        ]
    elif experiment_type == "HMBC":
        correlations = identify_hmbc_correlations(peaks, hsqc_reference)
        notes = [
            "HMBC shows long-range ¹H-¹³C correlations (2-4 bonds)",
            "Critical for determining molecular connectivity",
            f"Found {len(correlations)} long-range correlations"
        ]
    else:
        return {
            "error": f"Unknown experiment type: {experiment_type}",
            "supported_types": ["COSY", "HSQC", "HMBC"]
        }
    
    # Count peaks by region
    if experiment_type in ["HSQC", "HMBC"]:
        aliphatic = sum(1 for c in correlations if c.get("carbon_ppm", 0) < 50)
        aromatic = sum(1 for c in correlations if 100 <= c.get("carbon_ppm", 0) < 160)
        heteroatom = sum(1 for c in correlations if 50 <= c.get("carbon_ppm", 0) < 100)
        
        notes.append(f"Aliphatic carbons: {aliphatic}, Aromatic: {aromatic}, C-O/C-N: {heteroatom}")
    
    analysis = {
        "experiment_type": experiment_type,
        "total_peaks": len(peaks),
        "correlations": correlations,
        "num_correlations": len(correlations),
        "notes": notes
    }
    
    return analysis


def interpret_coupling_pattern(
    cosy_correlations: List[Dict],
    proton_shift: float,
    tolerance: float = 0.05
) -> Dict:
    """
    Interpret coupling pattern for a specific proton
    
    Args:
        cosy_correlations: List of COSY correlations
        proton_shift: Chemical shift of proton to analyze (ppm)
        tolerance: Shift matching tolerance (ppm)
        
    Returns:
        Dictionary with coupling partners and pattern
        
    Educational Note:
        Coupling pattern interpretation:
        - Isolated CH₃: singlet (no COSY correlations)
        - CH₃-CH₂: CH₃ couples to CH₂ (quartet/triplet)
        - CH₂-CH₂: vicinal coupling
        - Number of correlations indicates multiplicity
        - COSY helps assign spin systems
    """
    # Find all correlations involving this proton
    coupled_protons = []
    
    for corr in cosy_correlations:
        p1 = corr.get("proton1_ppm", 0)
        p2 = corr.get("proton2_ppm", 0)
        
        if abs(p1 - proton_shift) < tolerance:
            coupled_protons.append(p2)
        elif abs(p2 - proton_shift) < tolerance:
            coupled_protons.append(p1)
    
    # Interpret pattern
    num_couplings = len(coupled_protons)
    
    if num_couplings == 0:
        pattern = "singlet or isolated proton"
        interpretation = "No J-coupling observed - possibly CH₃ next to quaternary C, or aromatic singlet"
    elif num_couplings == 1:
        pattern = "doublet or part of CH/CH₃ group"
        interpretation = f"Coupled to proton at {coupled_protons[0]:.2f} ppm"
    elif num_couplings == 2:
        pattern = "triplet or CH₂ group"
        interpretation = f"Coupled to protons at {coupled_protons[0]:.2f} and {coupled_protons[1]:.2f} ppm"
    else:
        pattern = "multiplet"
        interpretation = f"Multiple couplings ({num_couplings} partners) - complex spin system"
    
    return {
        "proton_shift": proton_shift,
        "num_coupled_protons": num_couplings,
        "coupled_proton_shifts": sorted(coupled_protons),
        "expected_pattern": pattern,
        "interpretation": interpretation
    }
