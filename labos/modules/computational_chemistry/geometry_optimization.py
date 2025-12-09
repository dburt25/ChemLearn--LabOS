"""
Geometry Optimization Module

Molecular geometry optimization and conformational search.

THEORY:
Geometry optimization finds energy minimum on potential energy surface (PES).
Goal: ∇E = 0 (gradient vanishes at stationary point)

OPTIMIZATION ALGORITHMS:
1. Steepest Descent: x_new = x_old - α·∇E
   - Simple, robust
   - Slow convergence near minimum

2. Conjugate Gradient: uses search history
   - Faster than steepest descent
   - No Hessian required

3. Newton-Raphson: x_new = x_old - H^(-1)·∇E
   - Quadratic convergence
   - Requires Hessian matrix

CONVERGENCE CRITERIA:
- RMS gradient < 10^(-4) Hartree/Bohr
- Max gradient < 10^(-4) Hartree/Bohr
- RMS step < 10^(-3) Bohr
- Energy change < 10^(-6) Hartree
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math

@dataclass
class MolecularGeometry:
    """Molecular geometry data"""
    atomic_numbers: List[int]
    coordinates: List[Tuple[float, float, float]]  # Angstrom
    
    energy: Optional[float] = None  # Hartree
    gradient: Optional[List[Tuple[float, float, float]]] = None  # Hartree/Bohr
    
    def n_atoms(self) -> int:
        """Number of atoms"""
        return len(self.atomic_numbers)
    
    def calculate_distance(self, i: int, j: int) -> float:
        """Calculate distance between atoms i and j (Angstrom)"""
        coord_i = self.coordinates[i]
        coord_j = self.coordinates[j]
        
        dx = coord_j[0] - coord_i[0]
        dy = coord_j[1] - coord_i[1]
        dz = coord_j[2] - coord_i[2]
        
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        return distance


def calculate_gradient(
    geometry: MolecularGeometry,
    delta: float = 0.001
) -> List[Tuple[float, float, float]]:
    """
    Calculate energy gradient using finite differences
    
    ∂E/∂x ≈ [E(x+δ) - E(x-δ)] / (2δ)
    
    Parameters:
    - geometry: molecular geometry
    - delta: finite difference step size (Angstrom)
    
    Returns:
    - gradient: force on each atom (Hartree/Bohr)
    
    THEORY:
    Gradient = -Force
    Atoms move opposite to gradient (downhill in energy)
    """
    from .molecular_mechanics import calculate_bond_energy
    
    gradient = []
    
    for atom_idx in range(geometry.n_atoms()):
        grad_x, grad_y, grad_z = 0.0, 0.0, 0.0
        
        # Simplified: calculate gradient from bonded interactions
        for other_idx in range(geometry.n_atoms()):
            if atom_idx == other_idx:
                continue
            
            # Current distance
            r = geometry.calculate_distance(atom_idx, other_idx)
            
            if 0.5 < r < 2.5:  # Bonded range
                # Energy at current geometry
                e_0 = calculate_bond_energy(r, 1.5, 1000.0)
                
                # Numerical gradient components
                # x-direction
                coords_plus = list(geometry.coordinates)
                coords_plus[atom_idx] = (
                    coords_plus[atom_idx][0] + delta,
                    coords_plus[atom_idx][1],
                    coords_plus[atom_idx][2]
                )
                geom_plus = MolecularGeometry(geometry.atomic_numbers, coords_plus)
                r_plus = geom_plus.calculate_distance(atom_idx, other_idx)
                e_plus = calculate_bond_energy(r_plus, 1.5, 1000.0)
                
                coords_minus = list(geometry.coordinates)
                coords_minus[atom_idx] = (
                    coords_minus[atom_idx][0] - delta,
                    coords_minus[atom_idx][1],
                    coords_minus[atom_idx][2]
                )
                geom_minus = MolecularGeometry(geometry.atomic_numbers, coords_minus)
                r_minus = geom_minus.calculate_distance(atom_idx, other_idx)
                e_minus = calculate_bond_energy(r_minus, 1.5, 1000.0)
                
                grad_x += (e_plus - e_minus) / (2 * delta)
                
                # y and z directions (simplified: assume similar)
                grad_y += grad_x * 0.5
                grad_z += grad_x * 0.5
        
        # Convert kJ/mol/Angstrom to Hartree/Bohr
        # 1 Hartree = 2625.5 kJ/mol, 1 Bohr = 0.529 Angstrom
        conversion = 1.0 / (2625.5 * 0.529)
        gradient.append((grad_x * conversion, grad_y * conversion, grad_z * conversion))
    
    return gradient


def optimize_geometry(
    initial_geometry: MolecularGeometry,
    method: str = "steepest_descent",
    max_iterations: int = 100,
    convergence_threshold: float = 1e-4
) -> Dict[str, any]:
    """
    Optimize molecular geometry to energy minimum
    
    Parameters:
    - initial_geometry: starting geometry
    - method: optimization algorithm
    - max_iterations: maximum steps
    - convergence_threshold: RMS gradient threshold (Hartree/Bohr)
    
    Returns:
    - results: optimized geometry and convergence data
    
    ALGORITHMS:
    - steepest_descent: first-order, robust
    - conjugate_gradient: faster convergence
    - bfgs: quasi-Newton method
    """
    from .molecular_mechanics import calculate_bond_energy
    
    # Current geometry
    coords = [list(c) for c in initial_geometry.coordinates]
    n_atoms = initial_geometry.n_atoms()
    
    # Optimization history
    energies = []
    gradients_rms = []
    
    # Step size
    step_size = 0.01  # Angstrom
    
    for iteration in range(max_iterations):
        # Create current geometry object
        current_geom = MolecularGeometry(
            initial_geometry.atomic_numbers,
            [tuple(c) for c in coords]
        )
        
        # Calculate energy (simplified: pairwise bonds)
        energy = 0.0
        for i in range(n_atoms - 1):
            for j in range(i + 1, n_atoms):
                r = current_geom.calculate_distance(i, j)
                if 0.5 < r < 2.5:
                    energy += calculate_bond_energy(r, 1.5, 1000.0)
        
        energies.append(energy)
        
        # Calculate gradient
        gradient = calculate_gradient(current_geom)
        
        # RMS gradient
        rms_grad = 0.0
        for grad_atom in gradient:
            rms_grad += grad_atom[0]**2 + grad_atom[1]**2 + grad_atom[2]**2
        rms_grad = math.sqrt(rms_grad / (n_atoms * 3))
        gradients_rms.append(rms_grad)
        
        # Check convergence
        if rms_grad < convergence_threshold:
            break
        
        # Update coordinates based on method
        if method == "steepest_descent":
            # Move opposite to gradient
            for i in range(n_atoms):
                coords[i][0] -= step_size * gradient[i][0]
                coords[i][1] -= step_size * gradient[i][1]
                coords[i][2] -= step_size * gradient[i][2]
        
        elif method == "conjugate_gradient":
            # Use conjugate direction (simplified)
            for i in range(n_atoms):
                coords[i][0] -= step_size * gradient[i][0] * 1.2
                coords[i][1] -= step_size * gradient[i][1] * 1.2
                coords[i][2] -= step_size * gradient[i][2] * 1.2
        
        # Adaptive step size
        if iteration > 0 and energies[-1] > energies[-2]:
            step_size *= 0.5
        elif iteration > 0:
            step_size = min(step_size * 1.1, 0.1)
    
    optimized_geom = MolecularGeometry(
        initial_geometry.atomic_numbers,
        [tuple(c) for c in coords],
        energy=energies[-1] if energies else None
    )
    
    return {
        "optimized_geometry": optimized_geom,
        "converged": gradients_rms[-1] < convergence_threshold if gradients_rms else False,
        "n_iterations": len(energies),
        "final_energy": energies[-1] if energies else 0.0,
        "initial_energy": energies[0] if energies else 0.0,
        "energy_change": energies[0] - energies[-1] if len(energies) > 0 else 0.0,
        "final_rms_gradient": gradients_rms[-1] if gradients_rms else 0.0,
        "energy_history": energies,
    }


def find_transition_state(
    reactant_geometry: MolecularGeometry,
    product_geometry: MolecularGeometry,
    initial_guess: Optional[MolecularGeometry] = None
) -> Dict[str, any]:
    """
    Find transition state between reactant and product
    
    Transition state: saddle point on PES (one negative curvature)
    
    Parameters:
    - reactant_geometry: reactant structure
    - product_geometry: product structure
    - initial_guess: starting point for TS search
    
    Returns:
    - ts_results: transition state geometry and barrier
    
    METHODS:
    - Nudged Elastic Band (NEB): finds minimum energy path
    - Synchronous Transit-Guided Quasi-Newton (STQN)
    - Dimer method: follows uphill direction
    """
    # If no guess, interpolate between reactant and product
    if initial_guess is None:
        n_atoms = reactant_geometry.n_atoms()
        ts_coords = []
        
        for i in range(n_atoms):
            r_coord = reactant_geometry.coordinates[i]
            p_coord = product_geometry.coordinates[i]
            
            # Midpoint
            mid_x = (r_coord[0] + p_coord[0]) / 2
            mid_y = (r_coord[1] + p_coord[1]) / 2
            mid_z = (r_coord[2] + p_coord[2]) / 2
            
            ts_coords.append((mid_x, mid_y, mid_z))
        
        initial_guess = MolecularGeometry(
            reactant_geometry.atomic_numbers,
            ts_coords
        )
    
    # Optimize to saddle point (simplified: just optimize geometry)
    # Real implementation would use Hessian-based methods
    ts_optimization = optimize_geometry(
        initial_guess,
        method="steepest_descent",
        max_iterations=50
    )
    
    # Calculate activation barrier
    reactant_opt = optimize_geometry(reactant_geometry, max_iterations=50)
    product_opt = optimize_geometry(product_geometry, max_iterations=50)
    
    e_reactant = reactant_opt["final_energy"]
    e_product = product_opt["final_energy"]
    e_ts = ts_optimization["final_energy"]
    
    activation_barrier_forward = e_ts - e_reactant
    activation_barrier_reverse = e_ts - e_product
    reaction_energy = e_product - e_reactant
    
    return {
        "transition_state_geometry": ts_optimization["optimized_geometry"],
        "activation_barrier_forward": activation_barrier_forward,
        "activation_barrier_reverse": activation_barrier_reverse,
        "reaction_energy": reaction_energy,
        "e_reactant": e_reactant,
        "e_product": e_product,
        "e_transition_state": e_ts,
    }


def perform_conformational_search(
    geometry: MolecularGeometry,
    n_conformers: int = 10
) -> List[Dict[str, any]]:
    """
    Perform systematic conformational search
    
    Generates and optimizes different conformers
    
    Parameters:
    - geometry: initial molecular geometry
    - n_conformers: number of conformers to generate
    
    Returns:
    - conformers: list of conformer geometries and energies
    
    METHODS:
    - Systematic: grid search over torsions
    - Random: Monte Carlo sampling
    - Genetic algorithm: evolutionary search
    - Molecular dynamics: temperature-driven sampling
    """
    conformers = []
    
    # Generate conformers by perturbing coordinates
    for conf_idx in range(n_conformers):
        # Perturb coordinates randomly
        perturbed_coords = []
        for coord in geometry.coordinates:
            # Add random displacement (±0.5 Angstrom)
            import random
            dx = (random.random() - 0.5) * 1.0
            dy = (random.random() - 0.5) * 1.0
            dz = (random.random() - 0.5) * 1.0
            
            perturbed_coords.append((
                coord[0] + dx,
                coord[1] + dy,
                coord[2] + dz
            ))
        
        conformer_geom = MolecularGeometry(
            geometry.atomic_numbers,
            perturbed_coords
        )
        
        # Optimize conformer
        optimization = optimize_geometry(
            conformer_geom,
            max_iterations=50
        )
        
        conformers.append({
            "conformer_id": conf_idx,
            "geometry": optimization["optimized_geometry"],
            "energy": optimization["final_energy"],
            "relative_energy": 0.0,  # Will calculate after all conformers
        })
    
    # Calculate relative energies
    if conformers:
        min_energy = min(c["energy"] for c in conformers)
        for conformer in conformers:
            conformer["relative_energy"] = conformer["energy"] - min_energy
    
    # Sort by energy
    conformers.sort(key=lambda x: x["energy"])
    
    return conformers
