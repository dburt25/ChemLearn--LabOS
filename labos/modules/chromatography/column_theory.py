"""
Column Theory

Column characterization and performance metrics.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import math


@dataclass
class ColumnParameters:
    """Chromatography column specifications"""
    length: float  # cm
    diameter: float  # mm
    particle_size: float  # μm
    pore_size: float  # Å (angstroms)
    
    def volume(self) -> float:
        """Calculate column volume (mL)"""
        radius_cm = self.diameter / 20  # mm to cm, then radius
        volume = math.pi * (radius_cm ** 2) * self.length
        return volume
    
    def interstitial_volume(self, porosity: float = 0.65) -> float:
        """Calculate interstitial volume (void volume)"""
        return self.volume() * porosity


def calculate_column_efficiency(
    plate_number: float,
    column_length: float
) -> float:
    """
    Calculate plate height (HETP)
    
    Args:
        plate_number: Theoretical plates (N)
        column_length: Column length (cm)
        
    Returns:
        Height equivalent to theoretical plate (cm)
        
    Formula:
        H = L / N
        
    Educational Note:
        HETP (plate height) measures efficiency per unit length:
        - Lower H = better efficiency
        - Typical H = 2-3× particle size for well-packed columns
        - H increases with flow rate (see Van Deemter)
        - Modern columns: H = 10-50 μm
    """
    if plate_number <= 0 or column_length <= 0:
        raise ValueError("Plate number and length must be positive")
        
    hetp = column_length / plate_number
    return hetp


def calculate_void_volume(
    column_length: float,
    column_diameter: float,
    total_porosity: float = 0.65
) -> float:
    """
    Calculate column void volume
    
    Args:
        column_length: Length (cm)
        column_diameter: Inner diameter (mm)
        total_porosity: Total porosity (typical 0.6-0.7)
        
    Returns:
        Void volume V0 (mL)
        
    Educational Note:
        Void volume = volume of mobile phase in column
        Includes:
        - Interstitial volume (between particles)
        - Intraparticle pores (inside porous particles)
        
        Total porosity = interstitial + intraparticle porosities
    """
    if column_length <= 0 or column_diameter <= 0:
        raise ValueError("Dimensions must be positive")
    if not (0 < total_porosity < 1):
        raise ValueError("Porosity must be between 0 and 1")
        
    # Convert diameter to cm and calculate radius
    radius_cm = column_diameter / 20
    
    # Column volume
    column_volume = math.pi * (radius_cm ** 2) * column_length
    
    # Void volume
    void_volume = column_volume * total_porosity
    
    return void_volume


def estimate_column_capacity(
    column_diameter: float,
    particle_size: float,
    compound_mw: float
) -> float:
    """
    Estimate column loading capacity
    
    Args:
        column_diameter: Inner diameter (mm)
        particle_size: Particle size (μm)
        compound_mw: Compound molecular weight (g/mol)
        
    Returns:
        Estimated loading capacity (μg)
        
    Educational Note:
        Column capacity = maximum sample amount before overload
        Depends on:
        - Column diameter (larger → more capacity)
        - Particle size (larger → more surface area)
        - Molecular weight (larger molecules → lower capacity)
        
        Overloading causes:
        - Peak distortion (fronting)
        - Loss of resolution
        - Non-linear retention
    """
    if column_diameter <= 0 or particle_size <= 0 or compound_mw <= 0:
        raise ValueError("All parameters must be positive")
        
    # Empirical capacity estimation
    # Typical: 1-10 μg per mm² for small molecules
    
    # Surface area factor (diameter squared)
    diameter_factor = (column_diameter / 4.6) ** 2  # Normalized to 4.6mm standard
    
    # Particle size factor
    particle_factor = particle_size / 5.0  # Normalized to 5μm
    
    # Molecular weight factor (larger molecules need less mass)
    mw_factor = 500 / compound_mw if compound_mw > 0 else 1.0
    
    # Base capacity for standard 4.6mm column with 5μm particles
    base_capacity = 100  # μg
    
    capacity = base_capacity * diameter_factor * particle_factor * mw_factor
    
    return capacity


def calculate_reduced_plate_height(
    hetp: float,
    particle_size: float
) -> float:
    """
    Calculate reduced plate height
    
    Args:
        hetp: Height equivalent to theoretical plate (cm)
        particle_size: Particle diameter (μm)
        
    Returns:
        Reduced plate height h
        
    Formula:
        h = H / dp
        
    Educational Note:
        Reduced plate height h normalizes efficiency by particle size:
        - h = 2: excellent packing (theoretical minimum)
        - h = 2-3: good commercial columns
        - h > 5: poor packing or extra-column effects
        
        Allows comparing columns with different particle sizes
    """
    if hetp <= 0 or particle_size <= 0:
        raise ValueError("HETP and particle size must be positive")
        
    # Convert units: hetp in cm, particle_size in μm
    hetp_um = hetp * 10000  # cm to μm
    
    h = hetp_um / particle_size
    return h


def calculate_linear_velocity(
    flow_rate: float,
    column_diameter: float,
    total_porosity: float = 0.65
) -> float:
    """
    Calculate linear velocity
    
    Args:
        flow_rate: Volumetric flow rate (mL/min)
        column_diameter: Inner diameter (mm)
        total_porosity: Total porosity
        
    Returns:
        Linear velocity u (cm/s)
        
    Educational Note:
        Linear velocity = mobile phase velocity through column
        u = F / (ε × A)
        where:
        - F = volumetric flow rate
        - ε = total porosity
        - A = column cross-sectional area
        
        Used in Van Deemter and other rate equations
    """
    if flow_rate <= 0 or column_diameter <= 0:
        raise ValueError("Flow rate and diameter must be positive")
        
    # Column cross-sectional area (cm²)
    radius_cm = column_diameter / 20
    area = math.pi * (radius_cm ** 2)
    
    # Interstitial area (accounts for particle packing)
    effective_area = area * total_porosity
    
    # Linear velocity (cm/min)
    u_cm_min = flow_rate / effective_area
    
    # Convert to cm/s
    u_cm_s = u_cm_min / 60
    
    return u_cm_s


def calculate_back_pressure(
    flow_rate: float,
    viscosity: float,
    column_length: float,
    column_diameter: float,
    particle_size: float
) -> float:
    """
    Estimate column back pressure
    
    Args:
        flow_rate: Flow rate (mL/min)
        viscosity: Mobile phase viscosity (cP)
        column_length: Length (cm)
        column_diameter: Diameter (mm)
        particle_size: Particle size (μm)
        
    Returns:
        Estimated pressure (bar)
        
    Formula (Darcy's law):
        ΔP ∝ (η × u × L) / dp²
        
    Educational Note:
        Back pressure increases with:
        - Flow rate (linear)
        - Viscosity (higher for organic solvents)
        - Column length (linear)
        - Smaller particles (inverse square)
        
        Pressure limits:
        - Traditional HPLC: 400 bar
        - UHPLC: 1000-1500 bar
    """
    if any(x <= 0 for x in [flow_rate, viscosity, column_length, column_diameter, particle_size]):
        raise ValueError("All parameters must be positive")
        
    # Convert units
    radius_cm = column_diameter / 20
    area = math.pi * (radius_cm ** 2)
    particle_cm = particle_size / 10000
    
    # Darcy's law approximation
    # Pressure ∝ (viscosity × velocity × length) / (permeability)
    # Permeability ∝ particle_size²
    
    linear_velocity = flow_rate / (area * 60)  # cm/s
    
    # Kozeny-Carman equation (simplified)
    k_constant = 180  # Kozeny constant for spherical particles
    porosity = 0.4  # Interparticle porosity
    
    pressure_pa = (k_constant * viscosity * 0.001 * linear_velocity * column_length * 
                   (1 - porosity) ** 2) / (porosity ** 3 * particle_cm ** 2)
    
    # Convert Pa to bar
    pressure_bar = pressure_pa / 100000
    
    return pressure_bar


def calculate_resolution_per_time(
    resolution: float,
    analysis_time: float
) -> float:
    """
    Calculate separation power metric
    
    Args:
        resolution: Resolution Rs
        analysis_time: Total analysis time (minutes)
        
    Returns:
        Resolution per unit time (Rs/min)
        
    Educational Note:
        Separation power balances resolution and speed:
        - Higher Rs/t = more efficient method
        - Useful for comparing different methods
        - Helps optimize gradient vs isocratic choice
    """
    if resolution < 0 or analysis_time <= 0:
        raise ValueError("Resolution must be non-negative, time positive")
        
    return resolution / analysis_time
