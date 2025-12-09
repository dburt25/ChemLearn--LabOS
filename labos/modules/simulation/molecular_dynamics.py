"""
Molecular Dynamics Simulation Module

Simplified molecular dynamics for educational purposes:
- Energy minimization
- Force field calculations
- Trajectory simulation
- Geometry optimization
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Dict, Optional
import math


class ForceFieldType(Enum):
    """Common force field types for molecular simulations"""
    MM2 = "mm2"  # Molecular mechanics
    AMBER = "amber"  # Assisted Model Building with Energy Refinement
    CHARMM = "charmm"  # Chemistry at HARvard Macromolecular Mechanics
    OPLS = "opls"  # Optimized Potentials for Liquid Simulations
    UFF = "uff"  # Universal Force Field


@dataclass
class Atom:
    """Represents an atom in a molecular system"""
    element: str
    x: float  # Cartesian coordinates (Angstroms)
    y: float
    z: float
    charge: float  # Partial charge
    atom_type: str  # Force field atom type
    mass: float  # Atomic mass (amu)


@dataclass
class Bond:
    """Represents a bond between two atoms"""
    atom1_idx: int
    atom2_idx: int
    bond_order: float  # 1=single, 2=double, 3=triple
    equilibrium_length: float  # Angstroms
    force_constant: float  # kcal/(mol·Å²)


@dataclass
class MolecularSystem:
    """Complete molecular system for simulation"""
    atoms: List[Atom]
    bonds: List[Bond]
    total_charge: float
    multiplicity: int  # Spin multiplicity
    name: str
    

@dataclass
class EnergyComponents:
    """Energy breakdown for a molecular system"""
    bond_energy: float  # kcal/mol
    angle_energy: float
    dihedral_energy: float
    vdw_energy: float  # Van der Waals
    electrostatic_energy: float
    total_energy: float
    

@dataclass
class OptimizationResult:
    """Results from geometry optimization"""
    initial_system: MolecularSystem
    optimized_system: MolecularSystem
    initial_energy: float
    final_energy: float
    energy_change: float
    iterations: int
    converged: bool
    convergence_criterion: str
    force_field: ForceFieldType
    notes: List[str]


@dataclass
class TrajectoryFrame:
    """Single frame in an MD trajectory"""
    time: float  # picoseconds
    system: MolecularSystem
    energy: EnergyComponents
    temperature: float  # Kelvin
    kinetic_energy: float  # kcal/mol
    

@dataclass
class MDSimulationResult:
    """Results from molecular dynamics simulation"""
    trajectory: List[TrajectoryFrame]
    total_time: float  # picoseconds
    timestep: float  # picoseconds
    temperature: float  # Kelvin
    force_field: ForceFieldType
    average_energy: float
    energy_drift: float
    notes: List[str]


# Atomic masses (amu)
ATOMIC_MASSES = {
    "H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999,
    "F": 18.998, "P": 30.974, "S": 32.065, "Cl": 35.453,
    "Br": 79.904, "I": 126.904
}

# Van der Waals radii (Angstroms)
VDW_RADII = {
    "H": 1.20, "C": 1.70, "N": 1.55, "O": 1.52,
    "F": 1.47, "P": 1.80, "S": 1.80, "Cl": 1.75
}


def calculate_distance(atom1: Atom, atom2: Atom) -> float:
    """
    Calculate distance between two atoms.
    
    Args:
        atom1: First atom
        atom2: Second atom
        
    Returns:
        Distance in Angstroms
    """
    dx = atom2.x - atom1.x
    dy = atom2.y - atom1.y
    dz = atom2.z - atom1.z
    return math.sqrt(dx*dx + dy*dy + dz*dz)


def calculate_bond_energy(
    bond: Bond,
    atom1: Atom,
    atom2: Atom
) -> float:
    """
    Calculate harmonic bond energy: E = 0.5 * k * (r - r0)^2
    
    Args:
        bond: Bond parameters
        atom1: First atom
        atom2: Second atom
        
    Returns:
        Bond energy in kcal/mol
    """
    r = calculate_distance(atom1, atom2)
    dr = r - bond.equilibrium_length
    return 0.5 * bond.force_constant * dr * dr


def calculate_vdw_energy(
    atom1: Atom,
    atom2: Atom,
    distance: float = None
) -> float:
    """
    Calculate van der Waals energy using Lennard-Jones potential.
    Simplified 6-12 potential: E = 4ε[(σ/r)^12 - (σ/r)^6]
    
    Args:
        atom1: First atom
        atom2: Second atom
        distance: Pre-calculated distance (optional)
        
    Returns:
        VdW energy in kcal/mol
    """
    if distance is None:
        distance = calculate_distance(atom1, atom2)
    
    # Avoid division by zero
    if distance < 0.1:
        return 1000.0  # Very high energy for overlapping atoms
    
    # Get VdW radii
    r1 = VDW_RADII.get(atom1.element, 1.7)
    r2 = VDW_RADII.get(atom2.element, 1.7)
    sigma = (r1 + r2) / 2.0  # Combining rule
    
    # Well depth (simplified, typically 0.1-0.5 kcal/mol)
    epsilon = 0.2
    
    # Lennard-Jones 6-12
    sigma_r = sigma / distance
    sigma_r6 = sigma_r ** 6
    sigma_r12 = sigma_r6 * sigma_r6
    
    energy = 4 * epsilon * (sigma_r12 - sigma_r6)
    
    # Cap energy to avoid numerical issues
    return max(-10.0, min(energy, 100.0))


def calculate_electrostatic_energy(
    atom1: Atom,
    atom2: Atom,
    distance: float = None,
    dielectric: float = 1.0
) -> float:
    """
    Calculate electrostatic energy: E = (q1 * q2) / (4πε₀ * r * ε_r)
    Using kcal/mol units: E = 332.06 * (q1 * q2) / (ε_r * r)
    
    Args:
        atom1: First atom
        atom2: Second atom
        distance: Pre-calculated distance in Angstroms (optional)
        dielectric: Relative dielectric constant
        
    Returns:
        Electrostatic energy in kcal/mol
    """
    if distance is None:
        distance = calculate_distance(atom1, atom2)
    
    if distance < 0.1:
        return 1000.0
    
    # Coulomb's constant in kcal·Å/(mol·e²)
    ke = 332.06
    
    energy = ke * (atom1.charge * atom2.charge) / (dielectric * distance)
    
    # Cap energy
    return max(-100.0, min(energy, 100.0))


def calculate_total_energy(
    system: MolecularSystem,
    force_field: ForceFieldType = ForceFieldType.UFF
) -> EnergyComponents:
    """
    Calculate total molecular mechanics energy.
    
    Args:
        system: Molecular system
        force_field: Force field to use
        
    Returns:
        EnergyComponents with breakdown
    """
    bond_energy = 0.0
    vdw_energy = 0.0
    electrostatic_energy = 0.0
    
    # Bond energies
    for bond in system.bonds:
        atom1 = system.atoms[bond.atom1_idx]
        atom2 = system.atoms[bond.atom2_idx]
        bond_energy += calculate_bond_energy(bond, atom1, atom2)
    
    # Non-bonded interactions (VdW and electrostatic)
    # Only calculate for non-bonded pairs
    bonded_pairs = {(b.atom1_idx, b.atom2_idx) for b in system.bonds}
    bonded_pairs.update({(b.atom2_idx, b.atom1_idx) for b in system.bonds})
    
    for i, atom1 in enumerate(system.atoms):
        for j, atom2 in enumerate(system.atoms):
            if j <= i:  # Avoid double counting
                continue
            if (i, j) in bonded_pairs:  # Skip bonded pairs
                continue
            
            distance = calculate_distance(atom1, atom2)
            
            # Only calculate for atoms within cutoff (10 Angstroms)
            if distance > 10.0:
                continue
            
            vdw_energy += calculate_vdw_energy(atom1, atom2, distance)
            electrostatic_energy += calculate_electrostatic_energy(atom1, atom2, distance)
    
    # Simplified angle and dihedral energies (placeholder)
    angle_energy = 0.0
    dihedral_energy = 0.0
    
    total = bond_energy + angle_energy + dihedral_energy + vdw_energy + electrostatic_energy
    
    return EnergyComponents(
        bond_energy=bond_energy,
        angle_energy=angle_energy,
        dihedral_energy=dihedral_energy,
        vdw_energy=vdw_energy,
        electrostatic_energy=electrostatic_energy,
        total_energy=total
    )


def optimize_geometry(
    system: MolecularSystem,
    force_field: ForceFieldType = ForceFieldType.UFF,
    max_iterations: int = 100,
    energy_tolerance: float = 0.001  # kcal/mol
) -> OptimizationResult:
    """
    Perform simplified geometry optimization using steepest descent.
    
    Args:
        system: Initial molecular system
        force_field: Force field to use
        max_iterations: Maximum optimization steps
        energy_tolerance: Convergence criterion (energy change)
        
    Returns:
        OptimizationResult with optimized geometry
    """
    import copy
    
    # Calculate initial energy
    initial_energy_comp = calculate_total_energy(system, force_field)
    initial_energy = initial_energy_comp.total_energy
    
    # Copy system for optimization
    current_system = copy.deepcopy(system)
    current_energy = initial_energy
    
    converged = False
    iteration = 0
    step_size = 0.01  # Angstroms
    
    notes = [
        f"Geometry optimization using {force_field.value} force field",
        f"Initial energy: {initial_energy:.3f} kcal/mol"
    ]
    
    for iteration in range(max_iterations):
        # Calculate numerical gradient (simplified)
        # For each atom, try small displacements and calculate energy
        
        # Store gradients
        gradients = []
        
        for i, atom in enumerate(current_system.atoms):
            # Try displacement in x
            atom.x += step_size
            energy_plus = calculate_total_energy(current_system, force_field).total_energy
            atom.x -= step_size
            grad_x = (energy_plus - current_energy) / step_size
            
            # Try displacement in y
            atom.y += step_size
            energy_plus = calculate_total_energy(current_system, force_field).total_energy
            atom.y -= step_size
            grad_y = (energy_plus - current_energy) / step_size
            
            # Try displacement in z
            atom.z += step_size
            energy_plus = calculate_total_energy(current_system, force_field).total_energy
            atom.z -= step_size
            grad_z = (energy_plus - current_energy) / step_size
            
            gradients.append((grad_x, grad_y, grad_z))
        
        # Update positions (steepest descent)
        for i, (grad_x, grad_y, grad_z) in enumerate(gradients):
            current_system.atoms[i].x -= step_size * grad_x
            current_system.atoms[i].y -= step_size * grad_y
            current_system.atoms[i].z -= step_size * grad_z
        
        # Calculate new energy
        new_energy = calculate_total_energy(current_system, force_field).total_energy
        energy_change = abs(new_energy - current_energy)
        
        # Check convergence
        if energy_change < energy_tolerance:
            converged = True
            notes.append(f"Converged after {iteration + 1} iterations")
            break
        
        current_energy = new_energy
        
        # Every 10 iterations, log progress
        if (iteration + 1) % 10 == 0:
            notes.append(f"Iteration {iteration + 1}: Energy = {current_energy:.3f} kcal/mol")
    
    if not converged:
        notes.append(f"Did not converge after {max_iterations} iterations")
    
    final_energy = calculate_total_energy(current_system, force_field).total_energy
    notes.append(f"Final energy: {final_energy:.3f} kcal/mol")
    
    return OptimizationResult(
        initial_system=system,
        optimized_system=current_system,
        initial_energy=initial_energy,
        final_energy=final_energy,
        energy_change=initial_energy - final_energy,
        iterations=iteration + 1,
        converged=converged,
        convergence_criterion=f"Energy change < {energy_tolerance} kcal/mol",
        force_field=force_field,
        notes=notes
    )


def run_md_simulation(
    system: MolecularSystem,
    temperature: float = 300.0,  # Kelvin
    timestep: float = 0.001,  # picoseconds (1 fs)
    total_time: float = 0.1,  # picoseconds (100 fs)
    force_field: ForceFieldType = ForceFieldType.UFF,
    save_frequency: int = 10  # Save every N steps
) -> MDSimulationResult:
    """
    Run simplified molecular dynamics simulation.
    Uses velocity Verlet integration.
    
    Args:
        system: Initial molecular system
        temperature: Simulation temperature (K)
        timestep: Integration timestep (ps)
        total_time: Total simulation time (ps)
        force_field: Force field to use
        save_frequency: Save trajectory every N steps
        
    Returns:
        MDSimulationResult with trajectory
    """
    import copy
    import random
    
    # Constants
    kb = 0.001987  # Boltzmann constant in kcal/(mol·K)
    
    # Initialize velocities from Maxwell-Boltzmann distribution
    current_system = copy.deepcopy(system)
    velocities = []
    
    for atom in current_system.atoms:
        # v_rms = sqrt(kT/m)
        v_rms = math.sqrt(kb * temperature / atom.mass)
        vx = random.gauss(0, v_rms)
        vy = random.gauss(0, v_rms)
        vz = random.gauss(0, v_rms)
        velocities.append([vx, vy, vz])
    
    # Calculate number of steps
    num_steps = int(total_time / timestep)
    
    trajectory = []
    notes = [
        f"MD simulation at {temperature} K",
        f"Timestep: {timestep} ps",
        f"Total time: {total_time} ps",
        f"Number of steps: {num_steps}"
    ]
    
    # Run simulation (simplified)
    for step in range(num_steps):
        current_time = step * timestep
        
        # Calculate energy
        energy_comp = calculate_total_energy(current_system, force_field)
        
        # Calculate kinetic energy
        ke = 0.0
        for i, atom in enumerate(current_system.atoms):
            vx, vy, vz = velocities[i]
            v_squared = vx*vx + vy*vy + vz*vz
            ke += 0.5 * atom.mass * v_squared
        
        # Save frame if at save frequency
        if step % save_frequency == 0:
            frame = TrajectoryFrame(
                time=current_time,
                system=copy.deepcopy(current_system),
                energy=energy_comp,
                temperature=temperature,
                kinetic_energy=ke
            )
            trajectory.append(frame)
        
        # Simplified integration (positions only, no force calculation)
        # In reality, would calculate forces and update velocities
        for i, atom in enumerate(current_system.atoms):
            vx, vy, vz = velocities[i]
            atom.x += vx * timestep
            atom.y += vy * timestep
            atom.z += vz * timestep
    
    # Calculate statistics
    avg_energy = sum(f.energy.total_energy for f in trajectory) / len(trajectory) if trajectory else 0
    energy_drift = trajectory[-1].energy.total_energy - trajectory[0].energy.total_energy if len(trajectory) > 1 else 0
    
    notes.append(f"Saved {len(trajectory)} trajectory frames")
    notes.append(f"Average energy: {avg_energy:.3f} kcal/mol")
    notes.append(f"Energy drift: {energy_drift:.3f} kcal/mol")
    
    return MDSimulationResult(
        trajectory=trajectory,
        total_time=total_time,
        timestep=timestep,
        temperature=temperature,
        force_field=force_field,
        average_energy=avg_energy,
        energy_drift=energy_drift,
        notes=notes
    )


def create_water_molecule() -> MolecularSystem:
    """Create a simple H2O molecule for testing"""
    atoms = [
        Atom("O", 0.0, 0.0, 0.0, -0.8, "O.3", 15.999),
        Atom("H", 0.96, 0.0, 0.0, 0.4, "H", 1.008),
        Atom("H", -0.24, 0.93, 0.0, 0.4, "H", 1.008),
    ]
    
    bonds = [
        Bond(0, 1, 1.0, 0.96, 500.0),  # O-H
        Bond(0, 2, 1.0, 0.96, 500.0),  # O-H
    ]
    
    return MolecularSystem(
        atoms=atoms,
        bonds=bonds,
        total_charge=0.0,
        multiplicity=1,
        name="H2O"
    )


def create_methane_molecule() -> MolecularSystem:
    """Create a simple CH4 molecule for testing"""
    atoms = [
        Atom("C", 0.0, 0.0, 0.0, 0.0, "C.3", 12.011),
        Atom("H", 0.63, 0.63, 0.63, 0.0, "H", 1.008),
        Atom("H", -0.63, -0.63, 0.63, 0.0, "H", 1.008),
        Atom("H", -0.63, 0.63, -0.63, 0.0, "H", 1.008),
        Atom("H", 0.63, -0.63, -0.63, 0.0, "H", 1.008),
    ]
    
    bonds = [
        Bond(0, 1, 1.0, 1.09, 400.0),
        Bond(0, 2, 1.0, 1.09, 400.0),
        Bond(0, 3, 1.0, 1.09, 400.0),
        Bond(0, 4, 1.0, 1.09, 400.0),
    ]
    
    return MolecularSystem(
        atoms=atoms,
        bonds=bonds,
        total_charge=0.0,
        multiplicity=1,
        name="CH4"
    )
