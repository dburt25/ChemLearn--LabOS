"""
Cyclic Voltammetry Module

Electrochemical analysis using cyclic voltammetry.

THEORY:
Cyclic voltammetry measures current as voltage is swept linearly:
E(t) = E_initial + v·t (forward scan)
E(t) = E_vertex - v·(t-t_vertex) (reverse scan)

RANDLES-SEVCIK EQUATION:
For reversible processes at 25°C:
I_p = 0.4463 · n^(3/2) · F^(3/2) · A · C · D^(1/2) · v^(1/2) / (R^(1/2) · T^(1/2))

Simplified: I_p = 2.69×10⁵ · n^(3/2) · A · D^(1/2) · C · v^(1/2)

Where:
- I_p = peak current (A)
- n = number of electrons transferred
- F = Faraday constant (96485 C/mol)
- A = electrode area (cm²)
- D = diffusion coefficient (cm²/s)
- C = concentration (mol/cm³)
- v = scan rate (V/s)
- R = gas constant (8.314 J/(mol·K))
- T = temperature (K)

REVERSIBILITY CRITERIA:
- Reversible: ΔE_p = 59/n mV (25°C)
- Quasi-reversible: 59/n < ΔE_p < 200/n mV
- Irreversible: ΔE_p > 200/n mV
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math

# Constants
FARADAY_CONSTANT = 96485.0  # C/mol
GAS_CONSTANT = 8.314  # J/(mol·K)
TEMPERATURE_DEFAULT = 298.15  # K (25°C)


@dataclass
class VoltammogramData:
    """Cyclic voltammetry data structure"""
    potentials: List[float]  # V vs reference
    currents: List[float]  # A
    scan_rate: float  # V/s
    
    # Peak data
    anodic_peak_potential: Optional[float] = None  # V
    anodic_peak_current: Optional[float] = None  # A
    cathodic_peak_potential: Optional[float] = None  # V
    cathodic_peak_current: Optional[float] = None  # A
    
    # Auto-calculated properties
    peak_separation: Optional[float] = field(init=False, default=None)  # V
    peak_current_ratio: Optional[float] = field(init=False, default=None)
    reversibility: Optional[str] = field(init=False, default=None)
    
    def __post_init__(self):
        """Calculate derived properties if peaks are provided"""
        if self.anodic_peak_potential is not None and self.cathodic_peak_potential is not None:
            self.peak_separation = abs(self.anodic_peak_potential - self.cathodic_peak_potential)
        
        if self.anodic_peak_current is not None and self.cathodic_peak_current is not None:
            if self.cathodic_peak_current != 0:
                self.peak_current_ratio = abs(self.anodic_peak_current / self.cathodic_peak_current)


def calculate_peak_current(
    n_electrons: int,
    electrode_area: float,
    diffusion_coefficient: float,
    concentration: float,
    scan_rate: float,
    temperature: float = TEMPERATURE_DEFAULT
) -> float:
    """
    Calculate peak current using Randles-Sevcik equation
    
    For reversible electron transfer at planar electrode
    
    Parameters:
    - n_electrons: number of electrons transferred
    - electrode_area: electrode surface area (cm²)
    - diffusion_coefficient: diffusion coefficient (cm²/s)
    - concentration: bulk concentration (mol/L = mM)
    - scan_rate: scan rate (V/s)
    - temperature: temperature (K)
    
    Returns:
    - peak_current: peak current (A)
    
    UNITS:
    Concentration converted from mol/L to mol/cm³ (×10⁻³)
    """
    # Convert concentration from mol/L to mol/cm³
    c_mol_cm3 = concentration * 1e-3
    
    # Randles-Sevcik equation
    # I_p = 0.4463 · (F³/(RT))^(1/2) · n^(3/2) · A · D^(1/2) · C · v^(1/2)
    
    factor_1 = 0.4463
    factor_2 = (FARADAY_CONSTANT**3 / (GAS_CONSTANT * temperature))**0.5
    factor_3 = n_electrons**1.5
    factor_4 = electrode_area
    factor_5 = diffusion_coefficient**0.5
    factor_6 = c_mol_cm3
    factor_7 = scan_rate**0.5
    
    peak_current = factor_1 * factor_2 * factor_3 * factor_4 * factor_5 * factor_6 * factor_7
    
    return peak_current


def calculate_diffusion_coefficient(
    peak_current: float,
    n_electrons: int,
    electrode_area: float,
    concentration: float,
    scan_rate: float,
    temperature: float = TEMPERATURE_DEFAULT
) -> float:
    """
    Calculate diffusion coefficient from peak current
    
    Rearranges Randles-Sevcik equation to solve for D
    
    Parameters:
    - peak_current: measured peak current (A)
    - n_electrons: number of electrons
    - electrode_area: electrode area (cm²)
    - concentration: concentration (mol/L)
    - scan_rate: scan rate (V/s)
    - temperature: temperature (K)
    
    Returns:
    - diffusion_coefficient: D (cm²/s)
    
    THEORY:
    D = [I_p / (0.4463 · (F³/RT)^(1/2) · n^(3/2) · A · C · v^(1/2))]²
    """
    # Convert concentration
    c_mol_cm3 = concentration * 1e-3
    
    # Calculate constant factors
    factor_1 = 0.4463
    factor_2 = (FARADAY_CONSTANT**3 / (GAS_CONSTANT * temperature))**0.5
    factor_3 = n_electrons**1.5
    factor_4 = electrode_area
    factor_5 = c_mol_cm3
    factor_6 = scan_rate**0.5
    
    # D = [I_p / (factors)]²
    denominator = factor_1 * factor_2 * factor_3 * factor_4 * factor_5 * factor_6
    
    if denominator == 0:
        return 0.0
    
    diffusion_coefficient = (peak_current / denominator)**2
    
    return diffusion_coefficient


def identify_reversibility(
    peak_separation: float,
    n_electrons: int = 1,
    temperature: float = TEMPERATURE_DEFAULT
) -> Dict[str, any]:
    """
    Identify reversibility from peak separation
    
    Uses Nernstian criteria for reversibility assessment
    
    Parameters:
    - peak_separation: ΔE_p = |E_pa - E_pc| (V)
    - n_electrons: number of electrons transferred
    - temperature: temperature (K)
    
    Returns:
    - reversibility_data: classification and criteria
    
    CRITERIA (25°C):
    - Reversible: ΔE_p ≈ 59/n mV
    - Quasi-reversible: 59/n < ΔE_p < 200/n mV  
    - Irreversible: ΔE_p > 200/n mV
    """
    # Theoretical reversible peak separation (V)
    # ΔE_p = (RT/nF) = 0.0257/n at 25°C
    theoretical_separation = (GAS_CONSTANT * temperature) / (n_electrons * FARADAY_CONSTANT)
    
    # Convert to mV for comparison
    peak_sep_mv = peak_separation * 1000
    theoretical_mv = theoretical_separation * 1000
    
    # Classification thresholds
    threshold_reversible = theoretical_mv * 1.2  # Allow 20% deviation
    threshold_irreversible = theoretical_mv * 3.5  # >3.5× theoretical
    
    if peak_sep_mv <= threshold_reversible:
        classification = "reversible"
        description = "Fast electron transfer, Nernstian behavior"
    elif peak_sep_mv <= threshold_irreversible:
        classification = "quasi-reversible"
        description = "Moderate electron transfer kinetics"
    else:
        classification = "irreversible"
        description = "Slow electron transfer or coupled chemistry"
    
    return {
        "classification": classification,
        "description": description,
        "peak_separation_mv": peak_sep_mv,
        "theoretical_separation_mv": theoretical_mv,
        "deviation_factor": peak_sep_mv / theoretical_mv if theoretical_mv > 0 else float('inf'),
    }


def analyze_cyclic_voltammetry(
    voltammogram: VoltammogramData,
    n_electrons: int = 1,
    concentration: Optional[float] = None,
    electrode_area: Optional[float] = None
) -> Dict[str, any]:
    """
    Comprehensive cyclic voltammetry analysis
    
    Analyzes peaks, reversibility, and calculates parameters
    
    Parameters:
    - voltammogram: CV data
    - n_electrons: electrons transferred
    - concentration: analyte concentration (mol/L), optional
    - electrode_area: electrode area (cm²), optional
    
    Returns:
    - analysis: complete CV analysis results
    """
    analysis = {
        "scan_rate_v_s": voltammogram.scan_rate,
        "n_electrons": n_electrons,
    }
    
    # Peak analysis
    if voltammogram.anodic_peak_potential is not None:
        analysis["anodic_peak_potential_v"] = voltammogram.anodic_peak_potential
        analysis["anodic_peak_current_a"] = voltammogram.anodic_peak_current
    
    if voltammogram.cathodic_peak_potential is not None:
        analysis["cathodic_peak_potential_v"] = voltammogram.cathodic_peak_potential
        analysis["cathodic_peak_current_a"] = voltammogram.cathodic_peak_current
    
    # Reversibility analysis
    if voltammogram.peak_separation is not None:
        reversibility = identify_reversibility(
            voltammogram.peak_separation,
            n_electrons
        )
        analysis["reversibility"] = reversibility
    
    # Peak current ratio
    if voltammogram.peak_current_ratio is not None:
        analysis["peak_current_ratio"] = voltammogram.peak_current_ratio
        analysis["ratio_interpretation"] = (
            "Unity ratio expected for reversible process" 
            if abs(voltammogram.peak_current_ratio - 1.0) < 0.2 
            else "Non-unity ratio suggests coupled chemistry"
        )
    
    # Calculate diffusion coefficient if data available
    if all([
        voltammogram.anodic_peak_current,
        concentration,
        electrode_area
    ]):
        d_coeff = calculate_diffusion_coefficient(
            abs(voltammogram.anodic_peak_current),
            n_electrons,
            electrode_area,
            concentration,
            voltammogram.scan_rate
        )
        analysis["diffusion_coefficient_cm2_s"] = d_coeff
    
    return analysis


def interpret_cv_results(analysis: Dict[str, any]) -> str:
    """
    Interpret cyclic voltammetry results
    
    Provides electrochemical insights
    """
    interpretation = ["Cyclic Voltammetry Analysis", "=" * 40]
    
    interpretation.append(f"\nScan rate: {analysis['scan_rate_v_s']:.3f} V/s")
    interpretation.append(f"Electrons transferred: {analysis['n_electrons']}")
    
    # Peaks
    if "anodic_peak_potential_v" in analysis:
        interpretation.append(f"\nAnodic peak: {analysis['anodic_peak_potential_v']:.3f} V")
        interpretation.append(f"  Current: {analysis['anodic_peak_current_a']*1e6:.2f} µA")
    
    if "cathodic_peak_potential_v" in analysis:
        interpretation.append(f"\nCathodic peak: {analysis['cathodic_peak_potential_v']:.3f} V")
        interpretation.append(f"  Current: {abs(analysis['cathodic_peak_current_a'])*1e6:.2f} µA")
    
    # Reversibility
    if "reversibility" in analysis:
        rev = analysis["reversibility"]
        interpretation.append(f"\nReversibility: {rev['classification'].upper()}")
        interpretation.append(f"  Peak separation: {rev['peak_separation_mv']:.1f} mV")
        interpretation.append(f"  Theoretical: {rev['theoretical_separation_mv']:.1f} mV")
        interpretation.append(f"  {rev['description']}")
    
    # Diffusion coefficient
    if "diffusion_coefficient_cm2_s" in analysis:
        d = analysis["diffusion_coefficient_cm2_s"]
        interpretation.append(f"\nDiffusion coefficient: {d:.2e} cm²/s")
        
        # Typical range: 10⁻⁶ to 10⁻⁵ cm²/s for small molecules
        if 1e-6 <= d <= 1e-5:
            interpretation.append("  (typical for small molecules in solution)")
    
    return "\n".join(interpretation)
