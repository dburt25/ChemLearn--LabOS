"""
Raman Spectroscopy

Tools for Raman vibrational spectroscopy analysis.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import math


@dataclass
class RamanPeak:
    """Raman spectroscopy peak data"""
    wavenumber: float  # cm⁻¹
    intensity: float
    width: float  # cm⁻¹
    assignment: str = ""
    
    def raman_shift_from_laser(self, laser_wavelength: float) -> float:
        """Calculate Raman shift from laser wavelength"""
        return self.wavenumber


def calculate_raman_shift(
    laser_wavelength: float,
    scattered_wavelength: float
) -> float:
    """
    Calculate Raman shift in wavenumbers
    
    Args:
        laser_wavelength: Incident laser wavelength (nm)
        scattered_wavelength: Scattered light wavelength (nm)
        
    Returns:
        Raman shift (cm⁻¹)
        
    Formula:
        Δν = (1/λ_laser - 1/λ_scattered) × 10⁷
        
    Educational Note:
        Raman shift measures vibrational energy:
        - Stokes shift: scattered wavelength > laser (energy loss)
        - Anti-Stokes: scattered wavelength < laser (energy gain)
        - Shift independent of laser wavelength (intrinsic to molecule)
        - Typical range: 100-4000 cm⁻¹
    """
    if laser_wavelength <= 0 or scattered_wavelength <= 0:
        raise ValueError("Wavelengths must be positive")
    
    # Convert to wavenumbers (cm⁻¹)
    laser_wn = 1e7 / laser_wavelength  # nm to cm⁻¹
    scattered_wn = 1e7 / scattered_wavelength
    
    # Raman shift
    shift = abs(laser_wn - scattered_wn)
    
    return shift


def calculate_polarizability_derivative(
    raman_intensity: float,
    laser_power: float,
    concentration: float = 1.0
) -> float:
    """
    Estimate polarizability derivative from Raman intensity
    
    Args:
        raman_intensity: Measured Raman intensity
        laser_power: Laser power (mW)
        concentration: Sample concentration (M)
        
    Returns:
        Relative polarizability derivative
        
    Educational Note:
        Raman activity requires change in polarizability:
        - Polarizability (α) = induced dipole / electric field
        - Raman intensity ∝ (dα/dQ)² where Q is normal coordinate
        - Symmetric vibrations often Raman active
        - Complementary to IR (dipole moment change)
    """
    if laser_power <= 0 or concentration <= 0:
        raise ValueError("Power and concentration must be positive")
    
    # Normalize by laser power and concentration
    normalized_intensity = raman_intensity / (laser_power * concentration)
    
    # Relative polarizability derivative (arbitrary units)
    # In real analysis, requires calibration standards
    polarizability_deriv = math.sqrt(normalized_intensity)
    
    return polarizability_deriv


def identify_functional_groups(
    peaks: List[Dict[str, float]]
) -> List[Dict[str, str]]:
    """
    Identify functional groups from Raman peaks
    
    Args:
        peaks: List of peak dictionaries with 'wavenumber' and 'intensity'
        
    Returns:
        List of functional group assignments
        
    Educational Note:
        Characteristic Raman bands:
        - 2800-3000 cm⁻¹: C-H stretching
        - 1600-1680 cm⁻¹: C=C aromatic stretching
        - 1000-1200 cm⁻¹: C-O stretching
        - 600-800 cm⁻¹: C-S stretching
        - 400-600 cm⁻¹: Metal-ligand stretching
    """
    assignments = []
    
    # Raman correlation table
    raman_bands = {
        (2800, 3000): "C-H stretching (alkyl)",
        (3000, 3100): "C-H stretching (aromatic)",
        (2100, 2300): "C≡C or C≡N stretching",
        (1600, 1680): "C=C aromatic stretching",
        (1640, 1680): "C=O stretching (amide I)",
        (1450, 1480): "CH₂ bending",
        (1000, 1200): "C-O stretching",
        (900, 1000): "C-C stretching (aliphatic)",
        (600, 800): "C-S stretching",
        (400, 600): "Metal-ligand stretching",
        (200, 400): "Lattice modes (inorganics)",
    }
    
    for peak in peaks:
        wn = peak.get("wavenumber", 0)
        intensity = peak.get("intensity", 0)
        
        if intensity < 0.1:  # Skip weak peaks
            continue
            
        for (low, high), assignment in raman_bands.items():
            if low <= wn <= high:
                assignments.append({
                    "wavenumber": wn,
                    "assignment": assignment,
                    "intensity": intensity
                })
                break
    
    return assignments


def calculate_depolarization_ratio(
    parallel_intensity: float,
    perpendicular_intensity: float
) -> float:
    """
    Calculate depolarization ratio
    
    Args:
        parallel_intensity: Intensity with parallel polarization
        perpendicular_intensity: Intensity with perpendicular polarization
        
    Returns:
        Depolarization ratio ρ
        
    Formula:
        ρ = I_⊥ / I_∥
        
    Educational Note:
        Depolarization ratio indicates molecular symmetry:
        - ρ < 0.75: polarized band (symmetric vibration)
        - ρ = 0.75: depolarized band (asymmetric vibration)
        - Used to assign vibrational modes
        - Helpful for symmetric/asymmetric stretch distinction
    """
    if parallel_intensity <= 0:
        raise ValueError("Parallel intensity must be positive")
    
    ratio = perpendicular_intensity / parallel_intensity
    
    return ratio


def analyze_raman_spectrum(
    wavenumbers: List[float],
    intensities: List[float],
    laser_wavelength: float = 532.0,
    threshold: float = 0.1
) -> Dict:
    """
    Comprehensive Raman spectrum analysis
    
    Args:
        wavenumbers: Raman shift values (cm⁻¹)
        intensities: Peak intensities
        laser_wavelength: Laser wavelength (nm)
        threshold: Minimum relative intensity
        
    Returns:
        Analysis dictionary with peaks and assignments
        
    Educational Note:
        Raman spectroscopy advantages:
        - Non-destructive, minimal sample prep
        - Works with aqueous solutions (water weak Raman scatter)
        - Complementary to IR (different selection rules)
        - Good for symmetric vibrations, skeletal modes
        - Useful for inorganics, polymers, biological samples
    """
    if len(wavenumbers) != len(intensities):
        raise ValueError("Wavenumbers and intensities must have same length")
    
    if not wavenumbers:
        return {
            "peaks": [],
            "functional_groups": [],
            "laser_wavelength": laser_wavelength,
            "notes": ["No peaks detected"]
        }
    
    # Normalize intensities
    max_intensity = max(intensities) if intensities else 1.0
    normalized = [i / max_intensity for i in intensities]
    
    # Find peaks
    peaks = []
    for i, (wn, intensity) in enumerate(zip(wavenumbers, normalized)):
        if intensity > threshold:
            peaks.append({
                "wavenumber": wn,
                "intensity": intensity,
                "relative_intensity": f"{intensity*100:.1f}%"
            })
    
    # Identify functional groups
    functional_groups = identify_functional_groups(peaks)
    
    # Generate notes
    notes = []
    if any(2800 <= p["wavenumber"] <= 3100 for p in peaks):
        notes.append("C-H stretching observed (organic compound)")
    if any(1600 <= p["wavenumber"] <= 1680 for p in peaks):
        notes.append("Aromatic ring vibrations present")
    if any(400 <= p["wavenumber"] <= 600 for p in peaks):
        notes.append("Low-frequency modes (possible metal-ligand bonds)")
    
    analysis = {
        "peaks": peaks,
        "functional_groups": functional_groups,
        "laser_wavelength": laser_wavelength,
        "number_of_peaks": len(peaks),
        "strongest_peak": max(peaks, key=lambda x: x["intensity"]) if peaks else None,
        "notes": notes
    }
    
    return analysis


def calculate_resonance_raman_enhancement(
    resonance_intensity: float,
    normal_intensity: float
) -> float:
    """
    Calculate resonance Raman enhancement factor
    
    Args:
        resonance_intensity: Intensity at resonance wavelength
        normal_intensity: Intensity off-resonance
        
    Returns:
        Enhancement factor
        
    Educational Note:
        Resonance Raman enhancement:
        - Occurs when laser near electronic absorption
        - Enhancement factor: 10³-10⁶ times
        - Selective enhancement of chromophore modes
        - Used for trace analysis, biological systems
        - Example: heme groups in proteins
    """
    if normal_intensity <= 0:
        raise ValueError("Normal intensity must be positive")
    
    enhancement = resonance_intensity / normal_intensity
    
    return enhancement


def calculate_surface_enhanced_raman(
    enhanced_intensity: float,
    normal_intensity: float
) -> float:
    """
    Calculate SERS enhancement factor
    
    Args:
        enhanced_intensity: Intensity on metal surface
        normal_intensity: Normal Raman intensity
        
    Returns:
        SERS enhancement factor
        
    Educational Note:
        Surface-Enhanced Raman Spectroscopy (SERS):
        - Massive enhancement (10⁶-10¹⁴) on metal nanoparticles
        - Mechanisms: electromagnetic and chemical enhancement
        - Single-molecule detection possible
        - Gold, silver nanoparticles most common
        - Applications: biosensing, trace detection
    """
    if normal_intensity <= 0:
        raise ValueError("Normal intensity must be positive")
    
    enhancement = enhanced_intensity / normal_intensity
    
    return enhancement
