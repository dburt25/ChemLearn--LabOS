"""
Impedance Spectroscopy Module

Electrochemical impedance spectroscopy (EIS) analysis.

THEORY:
EIS applies small AC voltage and measures current response:
E(t) = E₀ sin(ωt)
I(t) = I₀ sin(ωt + φ)

IMPEDANCE:
Z(ω) = E(ω)/I(ω) = |Z| exp(jφ)

Where:
- |Z| = impedance magnitude
- φ = phase angle
- ω = angular frequency (rad/s)

COMPLEX IMPEDANCE:
Z = Z' + jZ''
- Z' = real part (resistance)
- Z'' = imaginary part (reactance)

NYQUIST PLOT:
Plot -Z'' vs Z'
- Semi-circle: charge transfer process
- Straight line (45°): Warburg diffusion
- Vertical line: capacitive behavior

RANDLES CIRCUIT:
R_s + [R_ct || C_dl] + W

Where:
- R_s = solution resistance
- R_ct = charge transfer resistance
- C_dl = double layer capacitance
- W = Warburg impedance (diffusion)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math

@dataclass
class ImpedanceData:
    """EIS measurement data"""
    frequencies: List[float]  # Hz
    z_real: List[float]  # Ω
    z_imag: List[float]  # Ω
    
    # Circuit parameters (fitted)
    r_solution: Optional[float] = None  # Ω
    r_charge_transfer: Optional[float] = None  # Ω
    capacitance: Optional[float] = None  # F
    warburg_coefficient: Optional[float] = None  # Ω·s^(-1/2)
    
    def get_impedance_magnitude(self, index: int) -> float:
        """Calculate impedance magnitude at specific frequency"""
        return math.sqrt(self.z_real[index]**2 + self.z_imag[index]**2)
    
    def get_phase_angle(self, index: int) -> float:
        """Calculate phase angle (degrees) at specific frequency"""
        phase_rad = math.atan2(-self.z_imag[index], self.z_real[index])
        return math.degrees(phase_rad)


def calculate_impedance_magnitude(
    z_real: float,
    z_imaginary: float
) -> float:
    """
    Calculate impedance magnitude
    
    |Z| = √(Z'² + Z''²)
    
    Parameters:
    - z_real: real part of impedance (Ω)
    - z_imaginary: imaginary part of impedance (Ω)
    
    Returns:
    - magnitude: impedance magnitude (Ω)
    """
    magnitude = math.sqrt(z_real**2 + z_imaginary**2)
    return magnitude


def calculate_phase_angle(
    z_real: float,
    z_imaginary: float
) -> float:
    """
    Calculate phase angle
    
    φ = arctan(-Z''/Z')
    
    Parameters:
    - z_real: real part (Ω)
    - z_imaginary: imaginary part (Ω)
    
    Returns:
    - phase: phase angle (degrees)
    
    INTERPRETATION:
    - φ = 0°: pure resistance
    - φ = -90°: pure capacitance
    - φ = 90°: pure inductance
    - 0° > φ > -90°: RC circuit
    """
    phase_rad = math.atan2(-z_imaginary, z_real)
    phase_deg = math.degrees(phase_rad)
    return phase_deg


def fit_randles_circuit(
    impedance_data: ImpedanceData
) -> Dict[str, float]:
    """
    Fit Randles equivalent circuit to impedance data
    
    Circuit: R_s + [R_ct || C_dl] + W
    
    Parameters:
    - impedance_data: measured EIS data
    
    Returns:
    - circuit_parameters: fitted R_s, R_ct, C_dl, W
    
    THEORY:
    Randles circuit impedance:
    Z(ω) = R_s + R_ct/(1 + jωR_ct·C_dl) + W/(jω)^(1/2)
    
    FITTING STRATEGY:
    1. High-frequency limit → R_s
    2. Low-frequency limit → R_s + R_ct
    3. Peak frequency → τ = R_ct·C_dl
    4. Low-frequency slope → Warburg coefficient
    """
    # High-frequency limit (real axis intercept)
    # At ω → ∞, Z → R_s
    high_freq_idx = 0  # Assuming frequencies sorted high to low
    r_solution = impedance_data.z_real[high_freq_idx]
    
    # Low-frequency limit (real axis intercept)
    # At ω → 0, Z → R_s + R_ct (ignoring Warburg for simplicity)
    low_freq_idx = len(impedance_data.z_real) - 1
    r_total = impedance_data.z_real[low_freq_idx]
    r_charge_transfer = max(0, r_total - r_solution)
    
    # Find semicircle peak to estimate capacitance
    # Peak occurs at ω = 1/(R_ct·C_dl)
    max_z_imag_idx = 0
    max_z_imag = 0
    for i, z_imag in enumerate(impedance_data.z_imag):
        if abs(z_imag) > abs(max_z_imag):
            max_z_imag = z_imag
            max_z_imag_idx = i
    
    # Peak frequency
    if max_z_imag_idx < len(impedance_data.frequencies):
        omega_peak = 2 * math.pi * impedance_data.frequencies[max_z_imag_idx]
        
        # τ = R_ct·C_dl = 1/ω_peak
        if omega_peak > 0 and r_charge_transfer > 0:
            capacitance = 1 / (omega_peak * r_charge_transfer)
        else:
            capacitance = 1e-6  # Default 1 µF
    else:
        capacitance = 1e-6
    
    # Estimate Warburg coefficient from low-frequency slope
    # Simplified: use last two points
    if len(impedance_data.z_real) >= 2:
        dz_real = impedance_data.z_real[-1] - impedance_data.z_real[-2]
        dz_imag = impedance_data.z_imag[-1] - impedance_data.z_imag[-2]
        
        # Warburg has 45° slope in Nyquist plot
        warburg_coeff = abs(dz_real) if abs(dz_real) > 0 else 1.0
    else:
        warburg_coeff = 1.0
    
    return {
        "r_solution": r_solution,
        "r_charge_transfer": r_charge_transfer,
        "capacitance": capacitance,
        "warburg_coefficient": warburg_coeff,
        "total_resistance": r_solution + r_charge_transfer,
    }


def analyze_nyquist_plot(
    impedance_data: ImpedanceData
) -> Dict[str, any]:
    """
    Analyze Nyquist plot features
    
    Identifies characteristic impedance behaviors
    
    Parameters:
    - impedance_data: EIS measurements
    
    Returns:
    - analysis: Nyquist plot interpretation
    
    FEATURES:
    - Semicircle: kinetic control (charge transfer)
    - 45° line: diffusion control (Warburg)
    - Vertical line: capacitive behavior
    - Intercept: solution resistance
    """
    analysis = {}
    
    # High-frequency intercept
    hf_intercept = impedance_data.z_real[0]
    analysis["high_freq_intercept"] = hf_intercept
    analysis["solution_resistance"] = hf_intercept
    
    # Low-frequency intercept
    lf_intercept = impedance_data.z_real[-1]
    analysis["low_freq_intercept"] = lf_intercept
    
    # Diameter (charge transfer resistance)
    diameter = lf_intercept - hf_intercept
    analysis["semicircle_diameter"] = diameter
    analysis["charge_transfer_resistance"] = diameter
    
    # Peak imaginary impedance
    max_z_imag = max(abs(z) for z in impedance_data.z_imag)
    analysis["max_imaginary_impedance"] = max_z_imag
    
    # Identify dominating process
    if diameter > 10 * hf_intercept:
        analysis["limiting_process"] = "charge_transfer"
        analysis["interpretation"] = "Kinetically limited (slow electron transfer)"
    elif max_z_imag < 0.1 * hf_intercept:
        analysis["limiting_process"] = "capacitive"
        analysis["interpretation"] = "Capacitive behavior (blocking electrode)"
    else:
        analysis["limiting_process"] = "mixed"
        analysis["interpretation"] = "Mixed kinetic and diffusion control"
    
    # Calculate characteristic frequency
    # Frequency where -Z'' is maximum
    max_idx = 0
    max_imag = 0
    for i, z_imag in enumerate(impedance_data.z_imag):
        if abs(z_imag) > abs(max_imag):
            max_imag = z_imag
            max_idx = i
    
    if max_idx < len(impedance_data.frequencies):
        char_freq = impedance_data.frequencies[max_idx]
        analysis["characteristic_frequency"] = char_freq
        
        # Time constant
        analysis["time_constant"] = 1 / (2 * math.pi * char_freq) if char_freq > 0 else float('inf')
    
    return analysis


def calculate_double_layer_capacitance(
    capacitance: float,
    electrode_area: float
) -> float:
    """
    Calculate specific double layer capacitance
    
    C_dl,specific = C_dl / A
    
    Parameters:
    - capacitance: measured capacitance (F)
    - electrode_area: electrode area (cm²)
    
    Returns:
    - specific_capacitance: C_dl per area (F/cm²)
    
    TYPICAL VALUES:
    - Smooth metal: 10-40 µF/cm²
    - Porous electrode: 1-10 mF/cm²
    - Supercapacitor: 10-300 F/cm²
    """
    if electrode_area <= 0:
        return 0.0
    
    specific_capacitance = capacitance / electrode_area
    return specific_capacitance


def interpret_impedance_results(
    circuit_params: Dict[str, float],
    nyquist_analysis: Dict[str, any]
) -> str:
    """
    Interpret impedance spectroscopy results
    
    Provides electrochemical insights from EIS
    """
    interpretation = ["Impedance Spectroscopy Analysis", "=" * 40]
    
    interpretation.append("\nEquivalent Circuit Parameters:")
    interpretation.append(f"  Solution resistance (R_s): {circuit_params['r_solution']:.2f} Ω")
    interpretation.append(f"  Charge transfer resistance (R_ct): {circuit_params['r_charge_transfer']:.2f} Ω")
    interpretation.append(f"  Double layer capacitance (C_dl): {circuit_params['capacitance']*1e6:.2f} µF")
    interpretation.append(f"  Total resistance: {circuit_params['total_resistance']:.2f} Ω")
    
    interpretation.append("\nNyquist Plot Analysis:")
    interpretation.append(f"  Semicircle diameter: {nyquist_analysis['semicircle_diameter']:.2f} Ω")
    interpretation.append(f"  Limiting process: {nyquist_analysis['limiting_process']}")
    interpretation.append(f"  {nyquist_analysis['interpretation']}")
    
    if "characteristic_frequency" in nyquist_analysis:
        interpretation.append(f"\nCharacteristic frequency: {nyquist_analysis['characteristic_frequency']:.2f} Hz")
        interpretation.append(f"Time constant: {nyquist_analysis['time_constant']*1e3:.2f} ms")
    
    # Interpretation guidelines
    interpretation.append("\nInterpretation Guidelines:")
    
    if circuit_params['r_charge_transfer'] > 1000:
        interpretation.append("  • High R_ct: slow electron transfer kinetics")
    elif circuit_params['r_charge_transfer'] < 10:
        interpretation.append("  • Low R_ct: fast electron transfer kinetics")
    
    if circuit_params['capacitance'] > 1e-4:
        interpretation.append("  • High C_dl: large electrode area or porous structure")
    elif circuit_params['capacitance'] < 1e-6:
        interpretation.append("  • Low C_dl: small electrode area or blocking layer")
    
    return "\n".join(interpretation)
