"""
Circular Dichroism Spectroscopy

Tools for CD spectroscopy and protein secondary structure analysis.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import math


@dataclass
class CDSpectrum:
    """Circular dichroism spectrum data"""
    wavelength: float  # nm
    ellipticity: float  # mdeg (millidegrees)
    absorbance_left: Optional[float] = None  # Left circularly polarized
    absorbance_right: Optional[float] = None  # Right circularly polarized


def calculate_ellipticity(
    absorbance_left: float,
    absorbance_right: float
) -> float:
    """
    Calculate ellipticity from differential absorbance
    
    Args:
        absorbance_left: Absorbance of left circularly polarized light
        absorbance_right: Absorbance of right circularly polarized light
        
    Returns:
        Ellipticity θ (degrees)
        
    Formula:
        θ = (A_L - A_R) × 32.98
        
    Educational Note:
        Ellipticity measures circular dichroism:
        - CD = differential absorption of left vs right polarized light
        - Arises from chiral (optically active) molecules
        - Sign indicates absolute configuration
        - Magnitude indicates chromophore environment
    """
    # Differential absorbance
    delta_a = absorbance_left - absorbance_right
    
    # Convert to ellipticity (degrees)
    # Conversion factor from ln(10)/4 ≈ 0.576, but use 32.98 for mdeg
    ellipticity_mdeg = delta_a * 32.98
    
    return ellipticity_mdeg


def calculate_mean_residue_ellipticity(
    ellipticity_mdeg: float,
    concentration: float,
    path_length: float,
    num_residues: int
) -> float:
    """
    Calculate mean residue ellipticity
    
    Args:
        ellipticity_mdeg: Measured ellipticity (millidegrees)
        concentration: Protein concentration (mg/mL)
        path_length: Cuvette path length (cm)
        num_residues: Number of amino acid residues
        
    Returns:
        Mean residue ellipticity [θ] (deg·cm²·dmol⁻¹)
        
    Formula:
        [θ] = θ_obs × (MW / (10 × c × l × n))
        
    Educational Note:
        Mean residue ellipticity normalizes for:
        - Protein concentration
        - Path length
        - Number of residues
        
        Allows comparison between different proteins
        Standard units: deg·cm²·dmol⁻¹
    """
    if concentration <= 0 or path_length <= 0 or num_residues <= 0:
        raise ValueError("Concentration, path length, and residues must be positive")
    
    # Mean residue weight (average ~110 Da for amino acids)
    mean_residue_weight = 110
    
    # Mean residue ellipticity
    mre = (ellipticity_mdeg * mean_residue_weight) / (10 * concentration * path_length * num_residues)
    
    return mre


def estimate_secondary_structure(
    ellipticity_208nm: float,
    ellipticity_222nm: float,
    num_residues: int
) -> Dict[str, float]:
    """
    Estimate protein secondary structure content from CD
    
    Args:
        ellipticity_208nm: Mean residue ellipticity at 208 nm
        ellipticity_222nm: Mean residue ellipticity at 222 nm
        num_residues: Number of amino acid residues
        
    Returns:
        Dictionary with secondary structure percentages
        
    Educational Note:
        Characteristic CD signatures:
        - α-helix: minima at 208 and 222 nm ([θ]₂₂₂ ≈ -30,000)
        - β-sheet: minimum at 218 nm, maximum at 195 nm
        - Random coil: minimum at 198 nm
        
        Methods for quantification:
        - Reference spectra deconvolution
        - Neural networks (e.g., BeStSel, Dichroweb)
        - This simplified method uses characteristic ratios
    """
    # Simplified estimation based on empirical correlations
    # Real analysis uses reference protein databases
    
    # α-helix estimation from 222 nm minimum
    # Pure α-helix: [θ]₂₂₂ ≈ -30,000 to -40,000
    if ellipticity_222nm < -25000:
        helix_content = min(100, abs(ellipticity_222nm) / 400)
    else:
        helix_content = 0
    
    # β-sheet estimation (simplified)
    # Ratio of 208/222 nm helps distinguish structures
    if abs(ellipticity_222nm) > 1000:
        ratio = ellipticity_208nm / ellipticity_222nm
        if ratio < 0.9:
            # Low ratio suggests β-sheet
            sheet_content = min(50, (1 - ratio) * 100)
        else:
            sheet_content = 0
    else:
        sheet_content = 0
    
    # Random coil = remainder
    helix_content = max(0, min(100, helix_content))
    sheet_content = max(0, min(100 - helix_content, sheet_content))
    random_coil = 100 - helix_content - sheet_content
    
    return {
        "alpha_helix_percent": round(helix_content, 1),
        "beta_sheet_percent": round(sheet_content, 1),
        "random_coil_percent": round(random_coil, 1)
    }


def analyze_protein_stability(
    temperatures: List[float],
    ellipticities: List[float]
) -> Dict[str, float]:
    """
    Analyze protein thermal stability from CD melting curve
    
    Args:
        temperatures: Temperature points (°C)
        ellipticities: Ellipticity values at each temperature
        
    Returns:
        Dictionary with melting temperature and cooperativity
        
    Educational Note:
        CD thermal denaturation:
        - Monitor ellipticity vs temperature
        - Unfolding causes loss of secondary structure
        - Melting temperature (T_m) = midpoint of transition
        - Cooperativity indicates folding mechanism
        - Reversibility indicates stable native state
    """
    if len(temperatures) != len(ellipticities):
        raise ValueError("Temperature and ellipticity arrays must match")
    if len(temperatures) < 3:
        raise ValueError("Need at least 3 temperature points")
    
    # Find maximum change (inflection point = T_m)
    # Simplified: find steepest slope
    max_slope = 0
    tm_index = len(temperatures) // 2
    
    for i in range(1, len(temperatures) - 1):
        slope = abs((ellipticities[i+1] - ellipticities[i-1]) / (temperatures[i+1] - temperatures[i-1]))
        if slope > max_slope:
            max_slope = slope
            tm_index = i
    
    tm = temperatures[tm_index]
    
    # Estimate cooperativity from sharpness of transition
    # More sophisticated analysis uses van't Hoff equation
    transition_width = 0
    half_max_ellipticity = (ellipticities[0] + ellipticities[-1]) / 2
    
    # Find temperatures where ellipticity crosses midpoint
    for i in range(len(ellipticities) - 1):
        if (ellipticities[i] - half_max_ellipticity) * (ellipticities[i+1] - half_max_ellipticity) < 0:
            transition_width = abs(temperatures[i] - tm)
            break
    
    return {
        "melting_temperature_celsius": round(tm, 1),
        "max_slope": round(max_slope, 2),
        "transition_width": round(transition_width, 1),
        "cooperativity": "high" if transition_width < 10 else "low"
    }


def analyze_cd_spectrum(
    wavelengths: List[float],
    ellipticities: List[float],
    concentration: float,
    path_length: float,
    num_residues: int
) -> Dict:
    """
    Comprehensive CD spectrum analysis
    
    Args:
        wavelengths: Wavelength points (nm)
        ellipticities: Ellipticity values (mdeg)
        concentration: Protein concentration (mg/mL)
        path_length: Path length (cm)
        num_residues: Number of residues
        
    Returns:
        Analysis dictionary
        
    Educational Note:
        CD spectroscopy applications:
        - Protein secondary structure determination
        - Protein folding/unfolding studies
        - Ligand binding effects
        - Chiral molecule analysis
        - Quality control (biosimilars, biopharmaceuticals)
    """
    if len(wavelengths) != len(ellipticities):
        raise ValueError("Wavelengths and ellipticities must match")
    
    if not wavelengths:
        return {
            "notes": ["No CD data provided"]
        }
    
    # Calculate mean residue ellipticities
    mre_values = []
    for theta in ellipticities:
        mre = calculate_mean_residue_ellipticity(theta, concentration, path_length, num_residues)
        mre_values.append(mre)
    
    # Find key wavelengths
    mre_dict = dict(zip(wavelengths, mre_values))
    
    # Get ellipticities at characteristic wavelengths
    mre_208 = mre_dict.get(208, None)
    mre_222 = mre_dict.get(222, None)
    
    # Estimate secondary structure if we have the key wavelengths
    if mre_208 is not None and mre_222 is not None:
        secondary_structure = estimate_secondary_structure(mre_208, mre_222, num_residues)
    else:
        # Use closest available wavelengths
        closest_208 = min(wavelengths, key=lambda x: abs(x - 208))
        closest_222 = min(wavelengths, key=lambda x: abs(x - 222))
        mre_208_approx = mre_dict[closest_208]
        mre_222_approx = mre_dict[closest_222]
        secondary_structure = estimate_secondary_structure(mre_208_approx, mre_222_approx, num_residues)
    
    # Find minima and maxima
    min_mre = min(mre_values)
    max_mre = max(mre_values)
    min_wavelength = wavelengths[mre_values.index(min_mre)]
    max_wavelength = wavelengths[mre_values.index(max_mre)]
    
    analysis = {
        "secondary_structure": secondary_structure,
        "mean_residue_ellipticities": {
            "208nm": mre_208,
            "222nm": mre_222
        },
        "spectrum_features": {
            "minimum_mre": round(min_mre, 0),
            "minimum_wavelength": min_wavelength,
            "maximum_mre": round(max_mre, 0),
            "maximum_wavelength": max_wavelength
        },
        "num_residues": num_residues
    }
    
    # Generate interpretation notes
    notes = []
    if secondary_structure["alpha_helix_percent"] > 50:
        notes.append("Predominantly α-helical structure")
    if secondary_structure["beta_sheet_percent"] > 30:
        notes.append("Significant β-sheet content")
    if secondary_structure["random_coil_percent"] > 60:
        notes.append("Largely unstructured or denatured")
    
    if min_wavelength < 210:
        notes.append("Strong far-UV CD signal indicates ordered structure")
    
    analysis["notes"] = notes
    
    return analysis
