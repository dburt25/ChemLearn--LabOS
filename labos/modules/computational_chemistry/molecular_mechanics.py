"""
Molecular Mechanics Module

Force field calculations and energy minimization.

THEORY:
Molecular mechanics uses classical physics to model molecular systems.
Total energy = E_bonds + E_angles + E_torsions + E_vdw + E_electrostatic

FORCE FIELDS:
- AMBER: Assisted Model Building with Energy Refinement (biomolecules)
- CHARMM: Chemistry at HARvard Macromolecular Mechanics (proteins)
- OPLS: Optimized Potentials for Liquid Simulations (organic molecules)

ENERGY TERMS:
1. Bond stretching: E_bond = k_b(r - r₀)²
2. Angle bending: E_angle = k_θ(θ - θ₀)²
3. Torsion: E_torsion = Σ V_n/2[1 + cos(nφ - γ)]
4. Van der Waals: E_vdw = ε[(r_min/r)¹² - 2(r_min/r)⁶]
5. Electrostatic: E_elec = q₁q₂/(4πε₀r)
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import math

@dataclass
class ForceFieldParameters:
    """Force field parameter set"""
    name: str  # AMBER, CHARMM, OPLS
    
    # Bond parameters
    bond_force_constants: Dict[str, float]  # kJ/(mol·Å²)
    bond_equilibrium_lengths: Dict[str, float]  # Å
    
    # Angle parameters
    angle_force_constants: Dict[str, float]  # kJ/(mol·rad²)
    angle_equilibrium_angles: Dict[str, float]  # degrees
    
    # Torsion parameters
    torsion_barriers: Dict[str, List[float]]  # kJ/mol
    torsion_phases: Dict[str, List[float]]  # degrees
    torsion_periodicities: Dict[str, List[int]]
    
    # Non-bonded parameters
    vdw_epsilon: Dict[str, float]  # kJ/mol
    vdw_radius: Dict[str, float]  # Å
    partial_charges: Dict[str, float]  # elementary charge


def get_amber_ff99() -> ForceFieldParameters:
    """Get AMBER ff99 force field parameters (simplified subset)"""
    return ForceFieldParameters(
        name="AMBER-ff99",
        bond_force_constants={
            "C-C": 1340.0,  # kJ/(mol·Å²)
            "C-H": 1460.0,
            "C-N": 1680.0,
            "C-O": 2510.0,
            "N-H": 1840.0,
            "O-H": 2300.0,
        },
        bond_equilibrium_lengths={
            "C-C": 1.53,  # Å
            "C-H": 1.09,
            "C-N": 1.47,
            "C-O": 1.43,
            "N-H": 1.01,
            "O-H": 0.96,
        },
        angle_force_constants={
            "C-C-C": 260.0,  # kJ/(mol·rad²)
            "C-C-H": 195.0,
            "H-C-H": 147.0,
            "C-N-H": 188.0,
            "C-O-H": 230.0,
        },
        angle_equilibrium_angles={
            "C-C-C": 109.5,  # degrees (tetrahedral)
            "C-C-H": 109.5,
            "H-C-H": 109.5,
            "C-N-H": 109.5,
            "C-O-H": 108.5,
        },
        torsion_barriers={
            "C-C-C-C": [5.4, 1.2, 0.5],  # kJ/mol for n=1,2,3
            "H-C-C-H": [0.6, 0.0, 0.3],
        },
        torsion_phases={
            "C-C-C-C": [0.0, 180.0, 0.0],  # degrees
            "H-C-C-H": [0.0, 0.0, 0.0],
        },
        torsion_periodicities={
            "C-C-C-C": [1, 2, 3],
            "H-C-C-H": [1, 2, 3],
        },
        vdw_epsilon={
            "C": 0.36,  # kJ/mol
            "H": 0.07,
            "N": 0.71,
            "O": 0.88,
        },
        vdw_radius={
            "C": 1.70,  # Å
            "H": 1.20,
            "N": 1.55,
            "O": 1.52,
        },
        partial_charges={
            "C": 0.0,  # neutral carbon
            "H": 0.0,
            "N": -0.5,
            "O": -0.5,
        }
    )


def calculate_bond_energy(
    current_length: float,
    equilibrium_length: float,
    force_constant: float
) -> float:
    """
    Calculate bond stretching energy
    
    Harmonic oscillator approximation:
    E = k_b(r - r₀)²
    
    Parameters:
    - current_length: current bond length (Å)
    - equilibrium_length: equilibrium bond length (Å)
    - force_constant: force constant (kJ/(mol·Å²))
    
    Returns:
    - energy: bond energy (kJ/mol)
    """
    displacement = current_length - equilibrium_length
    energy = force_constant * displacement**2
    return energy


def calculate_angle_energy(
    current_angle: float,
    equilibrium_angle: float,
    force_constant: float
) -> float:
    """
    Calculate angle bending energy
    
    Harmonic oscillator for angles:
    E = k_θ(θ - θ₀)²
    
    Parameters:
    - current_angle: current angle (degrees)
    - equilibrium_angle: equilibrium angle (degrees)
    - force_constant: force constant (kJ/(mol·rad²))
    
    Returns:
    - energy: angle energy (kJ/mol)
    """
    # Convert to radians
    current_rad = math.radians(current_angle)
    equilibrium_rad = math.radians(equilibrium_angle)
    
    displacement = current_rad - equilibrium_rad
    energy = force_constant * displacement**2
    return energy


def calculate_torsion_energy(
    dihedral_angle: float,
    barriers: List[float],
    phases: List[float],
    periodicities: List[int]
) -> float:
    """
    Calculate torsional energy
    
    Fourier series expansion:
    E = Σ_n V_n/2 [1 + cos(n·φ - γ_n)]
    
    Parameters:
    - dihedral_angle: current dihedral angle (degrees)
    - barriers: torsional barriers for each periodicity (kJ/mol)
    - phases: phase shifts for each term (degrees)
    - periodicities: periodicities (n values)
    
    Returns:
    - energy: torsional energy (kJ/mol)
    
    THEORY:
    - n=1: overall rotation barrier
    - n=2: eclipsing interactions
    - n=3: 3-fold symmetry (e.g., methyl rotation)
    """
    phi_rad = math.radians(dihedral_angle)
    
    energy = 0.0
    for v_n, gamma, n in zip(barriers, phases, periodicities):
        gamma_rad = math.radians(gamma)
        energy += (v_n / 2.0) * (1 + math.cos(n * phi_rad - gamma_rad))
    
    return energy


def calculate_vdw_energy(
    distance: float,
    epsilon_i: float,
    epsilon_j: float,
    radius_i: float,
    radius_j: float
) -> float:
    """
    Calculate van der Waals energy using Lennard-Jones potential
    
    12-6 Lennard-Jones potential:
    E = ε[(r_min/r)¹² - 2(r_min/r)⁶]
    
    Parameters:
    - distance: interatomic distance (Å)
    - epsilon_i, epsilon_j: well depths for atoms i,j (kJ/mol)
    - radius_i, radius_j: VDW radii for atoms i,j (Å)
    
    Returns:
    - energy: VDW energy (kJ/mol)
    
    THEORY:
    - r⁻¹² term: Pauli repulsion (very short range)
    - r⁻⁶ term: London dispersion attraction
    - Minimum at r = r_min = r_i + r_j
    """
    # Combining rules (Lorentz-Berthelot)
    epsilon = math.sqrt(epsilon_i * epsilon_j)
    r_min = radius_i + radius_j
    
    # Avoid division by zero
    if distance < 0.1:
        return 1e6  # Very high energy for overlap
    
    # Lennard-Jones potential
    ratio = r_min / distance
    energy = epsilon * (ratio**12 - 2 * ratio**6)
    
    return energy


def calculate_electrostatic_energy(
    distance: float,
    charge_i: float,
    charge_j: float,
    dielectric_constant: float = 1.0
) -> float:
    """
    Calculate electrostatic energy using Coulomb's law
    
    E = q₁q₂/(4πε₀εᵣr)
    
    In practical units:
    E = 1389 · q₁q₂/(εᵣr)  [kJ/mol, with q in e, r in Å]
    
    Parameters:
    - distance: interatomic distance (Å)
    - charge_i, charge_j: partial charges (elementary charge units)
    - dielectric_constant: relative permittivity (1 for vacuum, ~80 for water)
    
    Returns:
    - energy: electrostatic energy (kJ/mol)
    """
    # Coulomb constant in kJ·Å/(mol·e²)
    k_coulomb = 1389.0
    
    # Avoid division by zero
    if distance < 0.1:
        return 1e6 if charge_i * charge_j > 0 else -1e6
    
    energy = k_coulomb * charge_i * charge_j / (dielectric_constant * distance)
    
    return energy


def minimize_energy(
    initial_coordinates: List[Tuple[float, float, float]],
    force_field: ForceFieldParameters,
    max_iterations: int = 100,
    convergence_threshold: float = 0.01
) -> Dict[str, any]:
    """
    Minimize molecular energy using steepest descent
    
    Iteratively move atoms down energy gradient until convergence
    
    Parameters:
    - initial_coordinates: list of (x,y,z) coordinates (Å)
    - force_field: force field parameters
    - max_iterations: maximum optimization steps
    - convergence_threshold: RMS gradient threshold (kJ/(mol·Å))
    
    Returns:
    - results: optimized coordinates and energies
    
    ALGORITHM:
    1. Calculate energy and gradient
    2. Move atoms in direction of -gradient
    3. Repeat until gradient < threshold
    
    STEP SIZE:
    Adaptive step size to prevent oscillation
    """
    coordinates = [list(coord) for coord in initial_coordinates]
    n_atoms = len(coordinates)
    
    step_size = 0.01  # Å
    energies = []
    
    for iteration in range(max_iterations):
        # Simplified energy calculation (bond stretching only for demo)
        # Real implementation would calculate all terms
        
        total_energy = 0.0
        gradient = [[0.0, 0.0, 0.0] for _ in range(n_atoms)]
        
        # Calculate pairwise interactions (simplified)
        for i in range(n_atoms - 1):
            for j in range(i + 1, n_atoms):
                # Calculate distance
                dx = coordinates[j][0] - coordinates[i][0]
                dy = coordinates[j][1] - coordinates[i][1]
                dz = coordinates[j][2] - coordinates[i][2]
                
                distance = math.sqrt(dx**2 + dy**2 + dz**2)
                
                # Simplified: assume C-C bond
                if 1.0 < distance < 2.0:
                    bond_energy = calculate_bond_energy(distance, 1.53, 1340.0)
                    total_energy += bond_energy
                    
                    # Gradient (force = -dE/dr)
                    force_magnitude = -2 * 1340.0 * (distance - 1.53) / distance
                    
                    gradient[i][0] -= force_magnitude * dx
                    gradient[i][1] -= force_magnitude * dy
                    gradient[i][2] -= force_magnitude * dz
                    
                    gradient[j][0] += force_magnitude * dx
                    gradient[j][1] += force_magnitude * dy
                    gradient[j][2] += force_magnitude * dz
        
        energies.append(total_energy)
        
        # Calculate RMS gradient
        rms_gradient = 0.0
        for grad in gradient:
            rms_gradient += grad[0]**2 + grad[1]**2 + grad[2]**2
        rms_gradient = math.sqrt(rms_gradient / (n_atoms * 3))
        
        # Check convergence
        if rms_gradient < convergence_threshold:
            break
        
        # Update coordinates (steepest descent)
        for i in range(n_atoms):
            coordinates[i][0] -= step_size * gradient[i][0]
            coordinates[i][1] -= step_size * gradient[i][1]
            coordinates[i][2] -= step_size * gradient[i][2]
        
        # Adaptive step size
        if iteration > 0 and energies[-1] > energies[-2]:
            step_size *= 0.5  # Reduce step if energy increased
        elif iteration > 0 and energies[-1] < energies[-2]:
            step_size *= 1.2  # Increase step if energy decreased
    
    return {
        "optimized_coordinates": [tuple(coord) for coord in coordinates],
        "final_energy": energies[-1] if energies else 0.0,
        "initial_energy": energies[0] if energies else 0.0,
        "iterations": len(energies),
        "converged": rms_gradient < convergence_threshold if 'rms_gradient' in locals() else False,
        "energy_history": energies,
    }
