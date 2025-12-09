"""
DFT Calculations Module

Density Functional Theory orbital calculations and electronic structure.

THEORY:
DFT uses electron density ρ(r) rather than wavefunction Ψ to describe electronic structure.
Key equation: E[ρ] = T[ρ] + V_ne[ρ] + V_ee[ρ] + E_xc[ρ]

ORBITAL ENERGIES:
- Kohn-Sham orbitals: approximate single-particle states
- HOMO (Highest Occupied Molecular Orbital): electron donor capability
- LUMO (Lowest Unoccupied Molecular Orbital): electron acceptor capability
- HOMO-LUMO gap: approximates excitation energy

BASIS SETS:
- STO-3G: minimal basis, 3 Gaussians per Slater orbital
- 6-31G: split valence, 6 and 3+1 Gaussians
- 6-31G**: adds polarization functions
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math

@dataclass
class OrbitalData:
    """DFT orbital calculation results"""
    orbital_index: int
    energy: float  # Hartree
    occupancy: float  # electrons
    orbital_type: str  # 's', 'p', 'd'
    symmetry: Optional[str] = None
    
    # Auto-calculated
    energy_ev: float = field(init=False)
    is_occupied: bool = field(init=False)
    
    def __post_init__(self):
        """Calculate derived properties"""
        # Convert Hartree to eV (1 Hartree = 27.2114 eV)
        self.energy_ev = self.energy * 27.2114
        
        # Occupied if has electrons
        self.is_occupied = self.occupancy > 0.0
    
    def interpretation(self) -> str:
        """Interpret orbital properties"""
        status = "occupied" if self.is_occupied else "virtual"
        return f"{self.orbital_type} orbital ({status}): {self.energy_ev:.2f} eV"


def calculate_orbital_energy(
    nuclear_charge: int,
    principal_quantum_number: int,
    basis_set: str = "STO-3G"
) -> float:
    """
    Calculate approximate orbital energy using Slater's rules
    
    Simplified model for orbital energies in atoms
    
    Parameters:
    - nuclear_charge: atomic number Z
    - principal_quantum_number: n value
    - basis_set: basis set quality factor
    
    Returns:
    - energy: orbital energy in Hartree
    
    THEORY:
    E_n = -Z_eff²/(2n²) where Z_eff accounts for electron shielding
    """
    # Basis set correction factor
    basis_factors = {
        "STO-3G": 0.9,
        "6-31G": 0.95,
        "6-31G*": 0.98,
        "6-311G**": 0.99,
    }
    
    correction = basis_factors.get(basis_set, 1.0)
    
    # Simplified Slater effective nuclear charge
    # Real calculation requires detailed shielding
    z_eff = nuclear_charge * 0.7  # Approximate shielding
    
    # Orbital energy (Hartree)
    energy = -z_eff**2 / (2 * principal_quantum_number**2) * correction
    
    return energy


def calculate_homo_lumo_gap(
    homo_energy: float,
    lumo_energy: float,
    unit: str = "eV"
) -> Dict[str, float]:
    """
    Calculate HOMO-LUMO gap
    
    The gap approximates:
    - First excitation energy
    - Chemical reactivity
    - Band gap for materials
    
    Parameters:
    - homo_energy: HOMO energy (Hartree)
    - lumo_energy: LUMO energy (Hartree)
    - unit: output unit ("eV" or "Hartree")
    
    Returns:
    - gap_data: gap energy and interpretation
    
    INTERPRETATION:
    - Large gap (>5 eV): chemically stable, insulator
    - Medium gap (2-5 eV): semiconductor
    - Small gap (<2 eV): conductive, reactive
    """
    gap_hartree = lumo_energy - homo_energy
    gap_ev = gap_hartree * 27.2114
    
    # Classify reactivity
    if gap_ev > 5.0:
        classification = "stable/unreactive"
    elif gap_ev > 2.0:
        classification = "moderate reactivity"
    else:
        classification = "highly reactive"
    
    result = {
        "gap_hartree": gap_hartree,
        "gap_ev": gap_ev,
        "classification": classification,
        "is_semiconductor": 1.0 < gap_ev < 4.0,
    }
    
    if unit == "eV":
        result["gap"] = gap_ev
    else:
        result["gap"] = gap_hartree
    
    return result


def predict_electronic_transitions(
    occupied_orbitals: List[float],
    virtual_orbitals: List[float],
    max_transitions: int = 5
) -> List[Dict[str, float]]:
    """
    Predict electronic transitions from occupied to virtual orbitals
    
    Uses orbital energy differences to approximate absorption spectrum
    
    Parameters:
    - occupied_orbitals: list of occupied orbital energies (Hartree)
    - virtual_orbitals: list of virtual orbital energies (Hartree)
    - max_transitions: maximum number of transitions to return
    
    Returns:
    - transitions: list of transition data (energy, wavelength, oscillator strength)
    
    THEORY:
    ΔE = E_virtual - E_occupied
    λ = hc/ΔE where h=6.626×10⁻³⁴ J·s, c=2.998×10⁸ m/s
    """
    transitions = []
    
    # Consider all possible transitions
    for i, occ_energy in enumerate(occupied_orbitals):
        for j, virt_energy in enumerate(virtual_orbitals):
            delta_e_hartree = virt_energy - occ_energy
            delta_e_ev = delta_e_hartree * 27.2114
            
            # Convert to wavelength (nm)
            # 1 Hartree = 4.35974×10⁻¹⁸ J
            delta_e_joules = delta_e_hartree * 4.35974e-18
            
            # Skip if energy difference is too small
            if abs(delta_e_joules) < 1e-20:
                continue
            
            wavelength_m = 6.626e-34 * 2.998e8 / delta_e_joules
            wavelength_nm = wavelength_m * 1e9
            
            # Approximate oscillator strength (simplified)
            # Real calculation requires transition dipole moments
            oscillator_strength = 1.0 / (1.0 + abs(j - len(occupied_orbitals) + i))
            
            transitions.append({
                "from_orbital": i,
                "to_orbital": j + len(occupied_orbitals),
                "energy_ev": delta_e_ev,
                "wavelength_nm": wavelength_nm,
                "oscillator_strength": oscillator_strength,
            })
    
    # Sort by oscillator strength (most intense first)
    transitions.sort(key=lambda x: x["oscillator_strength"], reverse=True)
    
    return transitions[:max_transitions]


def perform_dft_calculation(
    atomic_numbers: List[int],
    basis_set: str = "6-31G",
    functional: str = "B3LYP"
) -> Dict[str, any]:
    """
    Perform simplified DFT calculation
    
    Simulates key steps of a DFT calculation:
    1. Build basis set
    2. Calculate orbital energies
    3. Identify HOMO/LUMO
    4. Predict transitions
    
    Parameters:
    - atomic_numbers: list of atomic numbers in molecule
    - basis_set: basis set choice
    - functional: DFT functional (B3LYP, PBE, etc.)
    
    Returns:
    - results: complete DFT calculation results
    
    FUNCTIONALS:
    - B3LYP: hybrid functional, good for organic molecules
    - PBE: GGA functional, good for solids
    - M06-2X: meta-GGA, good for non-covalent interactions
    """
    # Build orbitals for each atom
    all_orbitals = []
    for atom_idx, z in enumerate(atomic_numbers):
        # 1s orbital
        if z >= 1:
            energy_1s = calculate_orbital_energy(z, 1, basis_set)
            all_orbitals.append(OrbitalData(
                orbital_index=len(all_orbitals),
                energy=energy_1s,
                occupancy=2.0 if z >= 1 else 0.0,
                orbital_type="s"
            ))
        
        # 2s orbital
        if z >= 3:
            energy_2s = calculate_orbital_energy(z, 2, basis_set)
            all_orbitals.append(OrbitalData(
                orbital_index=len(all_orbitals),
                energy=energy_2s,
                occupancy=2.0 if z >= 3 else 0.0,
                orbital_type="s"
            ))
        
        # 2p orbitals
        if z >= 5:
            energy_2p = calculate_orbital_energy(z, 2, basis_set) * 1.1  # p slightly higher
            electrons_2p = min(6.0, max(0.0, z - 4))
            for p_idx in range(3):
                all_orbitals.append(OrbitalData(
                    orbital_index=len(all_orbitals),
                    energy=energy_2p,
                    occupancy=min(2.0, electrons_2p - p_idx * 2.0) if electrons_2p > p_idx * 2.0 else 0.0,
                    orbital_type="p"
                ))
    
    # Identify HOMO and LUMO
    occupied = [orb for orb in all_orbitals if orb.is_occupied]
    virtual = [orb for orb in all_orbitals if not orb.is_occupied]
    
    homo = max(occupied, key=lambda x: x.energy) if occupied else None
    lumo = min(virtual, key=lambda x: x.energy) if virtual else None
    
    results = {
        "basis_set": basis_set,
        "functional": functional,
        "total_orbitals": len(all_orbitals),
        "orbitals": all_orbitals,
        "homo": homo,
        "lumo": lumo,
    }
    
    # Calculate HOMO-LUMO gap if both exist
    if homo and lumo:
        gap_data = calculate_homo_lumo_gap(homo.energy, lumo.energy)
        results["homo_lumo_gap"] = gap_data
        
        # Predict transitions
        occ_energies = [orb.energy for orb in occupied[-3:]]  # Top 3 occupied
        virt_energies = [orb.energy for orb in virtual[:3]]  # Bottom 3 virtual
        transitions = predict_electronic_transitions(occ_energies, virt_energies)
        results["electronic_transitions"] = transitions
    
    return results


def interpret_dft_results(results: Dict[str, any]) -> str:
    """
    Interpret DFT calculation results
    
    Provides chemical insights from orbital energies
    """
    interpretation = []
    
    interpretation.append(f"DFT Calculation ({results['functional']}/{results['basis_set']})")
    interpretation.append(f"Total orbitals: {results['total_orbitals']}")
    
    if results.get("homo"):
        homo = results["homo"]
        interpretation.append(f"\nHOMO: {homo.energy_ev:.2f} eV")
        interpretation.append("  (electron-donating ability)")
    
    if results.get("lumo"):
        lumo = results["lumo"]
        interpretation.append(f"\nLUMO: {lumo.energy_ev:.2f} eV")
        interpretation.append("  (electron-accepting ability)")
    
    if results.get("homo_lumo_gap"):
        gap = results["homo_lumo_gap"]
        interpretation.append(f"\nHOMO-LUMO Gap: {gap['gap_ev']:.2f} eV")
        interpretation.append(f"  Classification: {gap['classification']}")
    
    if results.get("electronic_transitions"):
        interpretation.append("\nPredicted Electronic Transitions:")
        for i, trans in enumerate(results["electronic_transitions"][:3], 1):
            interpretation.append(
                f"  {i}. λ={trans['wavelength_nm']:.1f} nm "
                f"(ΔE={trans['energy_ev']:.2f} eV, f={trans['oscillator_strength']:.3f})"
            )
    
    return "\n".join(interpretation)
