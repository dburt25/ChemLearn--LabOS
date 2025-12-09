"""
Test Data Generators

Generate realistic scientific test data for various modules.
"""

from typing import Dict, List, Any, Optional
import random
import string
from datetime import datetime, timedelta


class DataGenerator:
    """
    Base class for test data generation
    
    Educational Note:
        Realistic test data improves test quality by exercising
        code paths with data that resembles production scenarios.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize generator
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
            
    @staticmethod
    def random_string(length: int = 10, chars: str = string.ascii_letters) -> str:
        """Generate random string"""
        return ''.join(random.choice(chars) for _ in range(length))
    
    @staticmethod
    def random_timestamp(
        start_date: Optional[datetime] = None,
        days_range: int = 30
    ) -> str:
        """
        Generate random timestamp
        
        Args:
            start_date: Starting date (defaults to now)
            days_range: Range of days to sample from
            
        Returns:
            ISO format timestamp string
        """
        if start_date is None:
            start_date = datetime.utcnow()
            
        random_days = random.uniform(0, days_range)
        timestamp = start_date + timedelta(days=random_days)
        
        return timestamp.isoformat() + "Z"


def generate_molecular_formula(
    elements: Optional[List[str]] = None,
    max_count: int = 20,
    seed: Optional[int] = None
) -> str:
    """
    Generate random molecular formula
    
    Args:
        elements: List of elements to use (defaults to C, H, O, N)
        max_count: Maximum count per element
        seed: Random seed for reproducibility
        
    Returns:
        Molecular formula string
        
    Educational Note:
        Realistic formulas follow chemical constraints:
        - Carbon counts typically largest
        - Hydrogen roughly 2x carbon for organic molecules
        - Heteroatoms less common
    """
    if seed is not None:
        random.seed(seed)
        
    if elements is None:
        elements = ["C", "H", "O", "N"]
        
    formula = ""
    
    for element in elements:
        if element == "C":
            count = random.randint(1, max_count)
        elif element == "H":
            # Hydrogen roughly 2x carbon count
            count = random.randint(2, max_count * 2)
        else:
            # Heteroatoms less common
            count = random.randint(0, max_count // 2)
            
        if count > 0:
            formula += element
            if count > 1:
                formula += str(count)
                
    return formula if formula else "CH4"


def generate_spectrum_data(
    n_peaks: int = 20,
    mass_range: tuple = (50, 500),
    include_isotopes: bool = True,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate realistic mass spectrum data
    
    Args:
        n_peaks: Number of peaks
        mass_range: (min, max) m/z range
        include_isotopes: Include isotope peaks
        seed: Random seed
        
    Returns:
        Spectrum data dictionary
        
    Educational Note:
        Realistic spectra show:
        - Base peak at 100% intensity
        - Isotope peaks at M+1, M+2
        - Fragment peaks with decreasing intensity
    """
    if seed is not None:
        random.seed(seed)
        
    min_mz, max_mz = mass_range
    
    # Generate molecular ion
    molecular_ion = random.uniform(max_mz * 0.7, max_mz)
    
    peaks = []
    
    # Add molecular ion
    peaks.append({
        "mz": round(molecular_ion, 2),
        "intensity": random.uniform(30.0, 100.0),
        "label": "M+"
    })
    
    # Add isotope peaks if requested
    if include_isotopes:
        # M+1 peak (13C)
        peaks.append({
            "mz": round(molecular_ion + 1.003, 2),
            "intensity": random.uniform(5.0, 15.0),
            "label": "M+1"
        })
        
        # M+2 peak (less common)
        if random.random() > 0.5:
            peaks.append({
                "mz": round(molecular_ion + 2.006, 2),
                "intensity": random.uniform(1.0, 5.0),
                "label": "M+2"
            })
    
    # Add fragment peaks
    for i in range(n_peaks - len(peaks)):
        fragment_mz = random.uniform(min_mz, molecular_ion * 0.9)
        intensity = random.uniform(1.0, 80.0)
        
        peaks.append({
            "mz": round(fragment_mz, 2),
            "intensity": round(intensity, 2)
        })
    
    # Normalize to base peak = 100
    max_intensity = max(p["intensity"] for p in peaks)
    for peak in peaks:
        peak["intensity"] = round(peak["intensity"] / max_intensity * 100.0, 2)
    
    # Sort by m/z
    peaks.sort(key=lambda p: p["mz"])
    
    spectrum = {
        "peaks": peaks,
        "molecular_ion": round(molecular_ion, 2),
        "base_peak": peaks[0]["mz"],
        "n_peaks": len(peaks)
    }
    
    return spectrum


def generate_kinetics_data(
    reaction_order: int = 1,
    n_timepoints: int = 20,
    initial_concentration: float = 1.0,
    rate_constant: float = 0.1,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate kinetic reaction data
    
    Args:
        reaction_order: Reaction order (0, 1, or 2)
        n_timepoints: Number of time points
        initial_concentration: Initial concentration [M]
        rate_constant: Rate constant
        seed: Random seed
        
    Returns:
        Kinetics data dictionary
        
    Educational Note:
        Kinetic data follows integrated rate laws:
        - 0th order: [A] = [A]₀ - kt
        - 1st order: [A] = [A]₀e^(-kt)
        - 2nd order: 1/[A] = 1/[A]₀ + kt
    """
    if seed is not None:
        random.seed(seed)
        
    timepoints = []
    concentrations = []
    
    max_time = 50.0
    
    for i in range(n_timepoints):
        t = (i / n_timepoints) * max_time
        
        # Calculate concentration based on order
        if reaction_order == 0:
            conc = max(0.0, initial_concentration - rate_constant * t)
        elif reaction_order == 1:
            conc = initial_concentration * (2.718 ** (-rate_constant * t))
        else:  # 2nd order
            conc = initial_concentration / (1 + rate_constant * initial_concentration * t)
        
        # Add noise
        noise = random.uniform(-0.02, 0.02)
        conc = max(0.0, conc + noise)
        
        timepoints.append(round(t, 2))
        concentrations.append(round(conc, 4))
    
    kinetics = {
        "times": timepoints,
        "concentrations": concentrations,
        "reaction_order": reaction_order,
        "rate_constant": rate_constant,
        "initial_concentration": initial_concentration,
        "units": {"time": "seconds", "concentration": "M"}
    }
    
    return kinetics


def generate_proteomics_data(
    n_peptides: int = 10,
    mass_range: tuple = (500, 3000),
    charge_states: Optional[List[int]] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate proteomics peptide data
    
    Args:
        n_peptides: Number of peptides
        mass_range: (min, max) mass range
        charge_states: Possible charge states
        seed: Random seed
        
    Returns:
        Proteomics data dictionary
        
    Educational Note:
        Proteomics data includes:
        - Peptide sequences
        - m/z values for different charge states
        - Retention times
        - Identification scores
    """
    if seed is not None:
        random.seed(seed)
        
    if charge_states is None:
        charge_states = [1, 2, 3]
        
    amino_acids = "ACDEFGHIKLMNPQRSTVWY"
    
    peptides = []
    
    for _ in range(n_peptides):
        # Generate sequence
        length = random.randint(6, 20)
        sequence = ''.join(random.choice(amino_acids) for _ in range(length))
        
        # Generate mass
        mass = random.uniform(*mass_range)
        
        # Generate charge state
        z = random.choice(charge_states)
        mz = (mass + z * 1.008) / z  # Add protons
        
        # Generate retention time
        rt = random.uniform(10.0, 60.0)
        
        # Generate score
        score = random.uniform(0.7, 1.0)
        
        peptides.append({
            "sequence": sequence,
            "mass": round(mass, 4),
            "charge": z,
            "mz": round(mz, 4),
            "retention_time": round(rt, 2),
            "score": round(score, 3)
        })
    
    proteomics = {
        "peptides": peptides,
        "n_peptides": len(peptides),
        "mass_range": mass_range,
        "charge_states_used": list(set(p["charge"] for p in peptides))
    }
    
    return proteomics


def generate_timeseries_data(
    n_points: int = 100,
    trend: str = "linear",
    noise_level: float = 0.1,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate time series data with various patterns
    
    Args:
        n_points: Number of data points
        trend: Trend type ('linear', 'exponential', 'periodic', 'random')
        noise_level: Noise amplitude
        seed: Random seed
        
    Returns:
        Time series data dictionary
    """
    if seed is not None:
        random.seed(seed)
        
    times = [i for i in range(n_points)]
    values = []
    
    for t in times:
        # Generate base value
        if trend == "linear":
            base = t * 0.5
        elif trend == "exponential":
            base = 2.718 ** (t / 20.0)
        elif trend == "periodic":
            import math
            base = 10 * math.sin(t / 10.0) + 50
        else:  # random
            base = random.uniform(0, 100)
        
        # Add noise
        noise = random.uniform(-noise_level, noise_level) * base
        value = base + noise
        
        values.append(round(value, 2))
    
    timeseries = {
        "times": times,
        "values": values,
        "trend": trend,
        "noise_level": noise_level,
        "n_points": n_points
    }
    
    return timeseries
