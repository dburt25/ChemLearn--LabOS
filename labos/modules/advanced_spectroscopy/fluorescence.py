"""
Fluorescence Spectroscopy

Tools for fluorescence emission and quenching analysis.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import math


@dataclass
class FluorescenceData:
    """Fluorescence spectroscopy data"""
    excitation_wavelength: float  # nm
    emission_wavelength: float  # nm
    intensity: float
    quantum_yield: Optional[float] = None
    lifetime: Optional[float] = None  # nanoseconds


def calculate_stokes_shift(
    excitation_wavelength: float,
    emission_wavelength: float
) -> Dict[str, float]:
    """
    Calculate Stokes shift
    
    Args:
        excitation_wavelength: Excitation wavelength (nm)
        emission_wavelength: Emission wavelength (nm)
        
    Returns:
        Dictionary with wavelength shift and energy shift
        
    Formula:
        Δλ = λ_em - λ_ex
        ΔE = hc(1/λ_ex - 1/λ_em)
        
    Educational Note:
        Stokes shift = emission at longer wavelength than absorption
        Caused by:
        - Vibrational relaxation in excited state
        - Solvent relaxation
        - Conformational changes
        
        Typical Stokes shifts:
        - Small molecules: 20-50 nm
        - Conjugated systems: 50-100 nm
        - Quantum dots: 20-40 nm
    """
    if excitation_wavelength <= 0 or emission_wavelength <= 0:
        raise ValueError("Wavelengths must be positive")
    
    # Wavelength shift
    wavelength_shift = emission_wavelength - excitation_wavelength
    
    # Energy shift (eV)
    h = 6.626e-34  # Planck constant (J·s)
    c = 3.0e8  # Speed of light (m/s)
    e = 1.602e-19  # Elementary charge (J/eV)
    
    ex_energy = (h * c) / (excitation_wavelength * 1e-9 * e)
    em_energy = (h * c) / (emission_wavelength * 1e-9 * e)
    energy_shift = ex_energy - em_energy
    
    return {
        "wavelength_shift_nm": wavelength_shift,
        "energy_shift_ev": energy_shift,
        "excitation_wavelength": excitation_wavelength,
        "emission_wavelength": emission_wavelength
    }


def calculate_quantum_yield(
    sample_integrated_intensity: float,
    sample_absorbance: float,
    standard_integrated_intensity: float,
    standard_absorbance: float,
    standard_quantum_yield: float,
    sample_refractive_index: float = 1.33,
    standard_refractive_index: float = 1.33
) -> float:
    """
    Calculate fluorescence quantum yield
    
    Args:
        sample_integrated_intensity: Integrated emission of sample
        sample_absorbance: Absorbance at excitation wavelength
        standard_integrated_intensity: Integrated emission of standard
        standard_absorbance: Standard absorbance
        standard_quantum_yield: Known quantum yield of standard
        sample_refractive_index: Solvent refractive index
        standard_refractive_index: Standard solvent refractive index
        
    Returns:
        Quantum yield of sample
        
    Formula:
        Φ_sample = Φ_std × (I_sample/I_std) × (A_std/A_sample) × (n_sample²/n_std²)
        
    Educational Note:
        Quantum yield (Φ) = photons emitted / photons absorbed
        - Φ = 0: no fluorescence (quenched)
        - Φ = 1: perfect fluorescence (rare)
        - Typical organic dyes: Φ = 0.1-0.9
        - Common standards: quinine sulfate (Φ = 0.54), fluorescein (Φ = 0.95)
    """
    if sample_absorbance <= 0 or standard_absorbance <= 0:
        raise ValueError("Absorbances must be positive")
    if not (0 <= standard_quantum_yield <= 1):
        raise ValueError("Standard quantum yield must be between 0 and 1")
    
    # Relative method
    intensity_ratio = sample_integrated_intensity / standard_integrated_intensity
    absorbance_ratio = standard_absorbance / sample_absorbance
    refractive_index_ratio = (sample_refractive_index / standard_refractive_index) ** 2
    
    quantum_yield = standard_quantum_yield * intensity_ratio * absorbance_ratio * refractive_index_ratio
    
    # Ensure physical bounds
    quantum_yield = max(0.0, min(1.0, quantum_yield))
    
    return quantum_yield


def analyze_quenching(
    intensity_no_quencher: float,
    intensity_with_quencher: float,
    quencher_concentration: float
) -> Dict[str, float]:
    """
    Analyze fluorescence quenching
    
    Args:
        intensity_no_quencher: Fluorescence intensity without quencher (F₀)
        intensity_with_quencher: Fluorescence intensity with quencher (F)
        quencher_concentration: Quencher concentration (M)
        
    Returns:
        Dictionary with quenching parameters
        
    Formula (Stern-Volmer):
        F₀/F = 1 + K_SV[Q]
        where K_SV = k_q × τ₀
        
    Educational Note:
        Fluorescence quenching types:
        - Static quenching: ground-state complex formation
        - Dynamic quenching: collisional deactivation
        - Stern-Volmer constant K_SV indicates quenching efficiency
        - Linear plot → single quenching mechanism
        - Upward curvature → combined static + dynamic
    """
    if intensity_no_quencher <= 0 or intensity_with_quencher <= 0:
        raise ValueError("Intensities must be positive")
    if quencher_concentration < 0:
        raise ValueError("Concentration must be non-negative")
    
    # Stern-Volmer ratio
    stern_volmer_ratio = intensity_no_quencher / intensity_with_quencher
    
    # Quenching efficiency
    quenching_efficiency = 1 - (intensity_with_quencher / intensity_no_quencher)
    
    # Stern-Volmer constant (if single data point)
    if quencher_concentration > 0:
        k_sv = (stern_volmer_ratio - 1) / quencher_concentration
    else:
        k_sv = 0.0
    
    return {
        "stern_volmer_ratio": stern_volmer_ratio,
        "quenching_efficiency": quenching_efficiency,
        "stern_volmer_constant": k_sv,
        "quencher_concentration": quencher_concentration
    }


def calculate_fluorescence_lifetime(
    intensity_at_time: List[float],
    time_points: List[float]
) -> Dict[str, float]:
    """
    Calculate fluorescence lifetime from decay curve
    
    Args:
        intensity_at_time: Fluorescence intensity values
        time_points: Time points (nanoseconds)
        
    Returns:
        Dictionary with lifetime parameters
        
    Formula:
        I(t) = I₀ × exp(-t/τ)
        τ = fluorescence lifetime
        
    Educational Note:
        Fluorescence lifetime:
        - Time for intensity to decay to 1/e (37%)
        - Typical range: 0.1-10 nanoseconds
        - Intrinsic property (independent of concentration)
        - Applications: FRET, sensing, imaging
        - Measured by time-correlated single photon counting (TCSPC)
    """
    if len(intensity_at_time) != len(time_points):
        raise ValueError("Intensity and time arrays must have same length")
    if len(time_points) < 2:
        raise ValueError("Need at least 2 time points")
    
    # Simple exponential fit (single exponential decay)
    # In real analysis, use nonlinear least squares
    
    # Log-linear fit: ln(I) = ln(I₀) - t/τ
    import math
    
    valid_points = [(t, i) for t, i in zip(time_points, intensity_at_time) if i > 0]
    
    if len(valid_points) < 2:
        raise ValueError("Need at least 2 positive intensity values")
    
    # Simple two-point estimate
    t1, i1 = valid_points[0]
    t2, i2 = valid_points[-1]
    
    if i1 <= 0 or i2 <= 0:
        raise ValueError("Intensities must be positive")
    
    # τ = -(t2 - t1) / ln(I2/I1)
    lifetime = -(t2 - t1) / math.log(i2 / i1)
    
    # Initial intensity (extrapolate to t=0)
    i0 = i1 * math.exp(t1 / lifetime)
    
    return {
        "lifetime_ns": lifetime,
        "initial_intensity": i0,
        "decay_rate": 1 / lifetime
    }


def calculate_forster_distance(
    quantum_yield_donor: float,
    refractive_index: float,
    overlap_integral: float,
    orientation_factor: float = 2/3
) -> float:
    """
    Calculate Förster distance for FRET
    
    Args:
        quantum_yield_donor: Donor quantum yield
        refractive_index: Medium refractive index
        overlap_integral: Spectral overlap integral (M⁻¹ cm³)
        orientation_factor: Dipole orientation factor κ² (default 2/3 for random)
        
    Returns:
        Förster distance R₀ (Angstroms)
        
    Formula:
        R₀⁶ = (8.79 × 10⁻²⁵) × κ² × n⁻⁴ × Φ_D × J
        
    Educational Note:
        Förster Resonance Energy Transfer (FRET):
        - Non-radiative energy transfer (dipole-dipole)
        - Efficiency = R₀⁶ / (R₀⁶ + r⁶) where r = donor-acceptor distance
        - R₀ = Förster distance (50% efficiency)
        - Typical R₀: 20-60 Å
        - Applications: biosensors, protein interactions, molecular rulers
    """
    if not (0 <= quantum_yield_donor <= 1):
        raise ValueError("Quantum yield must be between 0 and 1")
    if refractive_index <= 0:
        raise ValueError("Refractive index must be positive")
    if overlap_integral <= 0:
        raise ValueError("Overlap integral must be positive")
    
    # Förster distance calculation
    # R₀ in Angstroms
    r0_sixth = 8.79e-25 * orientation_factor * (refractive_index ** -4) * quantum_yield_donor * overlap_integral
    r0 = r0_sixth ** (1/6)
    
    # Convert to Angstroms (formula gives cm, need Å)
    r0_angstrom = r0 * 1e8
    
    return r0_angstrom


def analyze_fluorescence_spectrum(
    excitation_wavelength: float,
    emission_wavelengths: List[float],
    emission_intensities: List[float],
    absorbance: Optional[float] = None
) -> Dict:
    """
    Comprehensive fluorescence spectrum analysis
    
    Args:
        excitation_wavelength: Excitation wavelength (nm)
        emission_wavelengths: Emission wavelengths (nm)
        emission_intensities: Emission intensities
        absorbance: Optional absorbance at excitation wavelength
        
    Returns:
        Analysis dictionary
        
    Educational Note:
        Fluorescence spectroscopy:
        - Emission spectrum: intensity vs wavelength
        - Mirror image of absorption (Kasha's rule)
        - Highly sensitive (picomolar detection)
        - Applications: biochemistry, environmental, clinical
        - Jablonski diagram shows electronic transitions
    """
    if len(emission_wavelengths) != len(emission_intensities):
        raise ValueError("Wavelengths and intensities must match")
    
    if not emission_wavelengths:
        return {
            "emission_maximum": None,
            "stokes_shift": None,
            "notes": ["No emission detected"]
        }
    
    # Find emission maximum
    max_idx = emission_intensities.index(max(emission_intensities))
    emission_max = emission_wavelengths[max_idx]
    max_intensity = emission_intensities[max_idx]
    
    # Calculate Stokes shift
    stokes = calculate_stokes_shift(excitation_wavelength, emission_max)
    
    # Integrated intensity (trapezoidal)
    integrated_intensity = 0
    for i in range(len(emission_wavelengths) - 1):
        dλ = emission_wavelengths[i+1] - emission_wavelengths[i]
        avg_intensity = (emission_intensities[i] + emission_intensities[i+1]) / 2
        integrated_intensity += avg_intensity * dλ
    
    analysis = {
        "excitation_wavelength": excitation_wavelength,
        "emission_maximum": emission_max,
        "maximum_intensity": max_intensity,
        "stokes_shift_nm": stokes["wavelength_shift_nm"],
        "stokes_shift_ev": stokes["energy_shift_ev"],
        "integrated_intensity": integrated_intensity,
        "emission_range": {
            "min": min(emission_wavelengths),
            "max": max(emission_wavelengths),
            "span": max(emission_wavelengths) - min(emission_wavelengths)
        }
    }
    
    # Add notes
    notes = []
    if stokes["wavelength_shift_nm"] > 100:
        notes.append("Large Stokes shift - possible conformational change or solvent effects")
    if stokes["wavelength_shift_nm"] < 20:
        notes.append("Small Stokes shift - rigid molecular structure")
    
    analysis["notes"] = notes
    
    return analysis
