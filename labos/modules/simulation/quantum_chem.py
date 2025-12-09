"""
Simplified Quantum Chemistry Module

Educational quantum chemistry calculations:
- Molecular orbital theory
- Electron configuration
- Orbital energies
- Electronic transitions
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Tuple
import math


class OrbitalType(Enum):
    """Types of molecular orbitals"""
    SIGMA = "σ"
    SIGMA_STAR = "σ*"
    PI = "π"
    PI_STAR = "π*"
    N = "n"  # Non-bonding


@dataclass
class MolecularOrbital:
    """Molecular orbital with energy and occupancy"""
    name: str
    orbital_type: OrbitalType
    energy: float  # eV
    occupancy: int  # Number of electrons (0, 1, or 2)
    is_homo: bool  # Highest Occupied Molecular Orbital
    is_lumo: bool  # Lowest Unoccupied Molecular Orbital


@dataclass
class ElectronicTransition:
    """Electronic transition between orbitals"""
    initial_orbital: str
    final_orbital: str
    energy_difference: float  # eV
    wavelength: float  # nm
    oscillator_strength: float  # Dimensionless (0-1)
    transition_type: str  # e.g., "π → π*", "n → π*"


@dataclass
class QuantumChemResult:
    """Results from quantum chemistry calculation"""
    molecule_name: str
    total_electrons: int
    orbitals: List[MolecularOrbital]
    homo_energy: float
    lumo_energy: float
    homo_lumo_gap: float  # eV
    ionization_energy: float  # eV (≈ -HOMO)
    electron_affinity: float  # eV (≈ -LUMO)
    transitions: List[ElectronicTransition]
    notes: List[str]


# Constants
PLANCK = 4.135667696e-15  # eV·s
SPEED_OF_LIGHT = 2.998e17  # nm/s


def ev_to_wavelength(energy_ev: float) -> float:
    """Convert energy in eV to wavelength in nm"""
    if energy_ev <= 0:
        return float('inf')
    # E = hc/λ, so λ = hc/E
    wavelength = (PLANCK * SPEED_OF_LIGHT) / energy_ev
    return wavelength


def wavelength_to_ev(wavelength_nm: float) -> float:
    """Convert wavelength in nm to energy in eV"""
    if wavelength_nm <= 0:
        return 0.0
    return (PLANCK * SPEED_OF_LIGHT) / wavelength_nm


def huckel_benzene() -> QuantumChemResult:
    """
    Hückel molecular orbital calculation for benzene (C6H6).
    Educational simplified calculation.
    """
    # Benzene has 6 π electrons in 6 π orbitals
    # Energies: α ± β, α ± β, α ± 2β (where α = 0, β = -2.4 eV typically)
    
    alpha = 0.0  # Reference energy
    beta = -2.4  # Resonance integral (eV)
    
    orbitals = [
        MolecularOrbital("π₁", OrbitalType.PI, alpha + 2*beta, 2, False, False),
        MolecularOrbital("π₂", OrbitalType.PI, alpha + beta, 2, False, False),
        MolecularOrbital("π₃", OrbitalType.PI, alpha + beta, 2, True, False),  # HOMO (degenerate)
        MolecularOrbital("π₄*", OrbitalType.PI_STAR, alpha - beta, 0, False, True),  # LUMO (degenerate)
        MolecularOrbital("π₅*", OrbitalType.PI_STAR, alpha - beta, 0, False, False),
        MolecularOrbital("π₆*", OrbitalType.PI_STAR, alpha - 2*beta, 0, False, False),
    ]
    
    homo_energy = alpha + beta
    lumo_energy = alpha - beta
    homo_lumo_gap = lumo_energy - homo_energy  # Should be 2β = -4.8 eV in absolute terms
    
    # Transitions
    transitions = [
        ElectronicTransition(
            "π₃ (HOMO)", "π₄* (LUMO)",
            abs(homo_lumo_gap),
            ev_to_wavelength(abs(homo_lumo_gap)),
            0.8,
            "π → π*"
        )
    ]
    
    notes = [
        "Hückel MO theory for benzene",
        "6 π electrons in 6 π orbitals",
        "Aromatic: 4n+2 rule satisfied (n=1)",
        f"HOMO energy: {homo_energy:.2f} eV",
        f"LUMO energy: {lumo_energy:.2f} eV",
        f"HOMO-LUMO gap: {abs(homo_lumo_gap):.2f} eV",
        f"UV absorption: ~{ev_to_wavelength(abs(homo_lumo_gap)):.0f} nm"
    ]
    
    return QuantumChemResult(
        molecule_name="Benzene (C₆H₆)",
        total_electrons=6,  # π electrons only
        orbitals=orbitals,
        homo_energy=homo_energy,
        lumo_energy=lumo_energy,
        homo_lumo_gap=abs(homo_lumo_gap),
        ionization_energy=-homo_energy,
        electron_affinity=-lumo_energy,
        transitions=transitions,
        notes=notes
    )


def huckel_ethylene() -> QuantumChemResult:
    """Hückel MO for ethylene (C2H4)"""
    alpha = 0.0
    beta = -2.4
    
    orbitals = [
        MolecularOrbital("π", OrbitalType.PI, alpha + beta, 2, True, False),  # HOMO
        MolecularOrbital("π*", OrbitalType.PI_STAR, alpha - beta, 0, False, True),  # LUMO
    ]
    
    homo_energy = alpha + beta
    lumo_energy = alpha - beta
    gap = abs(lumo_energy - homo_energy)
    
    transitions = [
        ElectronicTransition(
            "π (HOMO)", "π* (LUMO)",
            gap,
            ev_to_wavelength(gap),
            1.0,
            "π → π*"
        )
    ]
    
    notes = [
        "Hückel MO theory for ethylene",
        "2 π electrons in 2 π orbitals",
        f"HOMO-LUMO gap: {gap:.2f} eV",
        f"UV absorption: ~{ev_to_wavelength(gap):.0f} nm"
    ]
    
    return QuantumChemResult(
        molecule_name="Ethylene (C₂H₄)",
        total_electrons=2,
        orbitals=orbitals,
        homo_energy=homo_energy,
        lumo_energy=lumo_energy,
        homo_lumo_gap=gap,
        ionization_energy=-homo_energy,
        electron_affinity=-lumo_energy,
        transitions=transitions,
        notes=notes
    )


def huckel_butadiene() -> QuantumChemResult:
    """Hückel MO for 1,3-butadiene (C4H6)"""
    alpha = 0.0
    beta = -2.4
    
    # 4 π orbitals with energies at α ± 0.618β and α ± 1.618β
    sqrt5 = math.sqrt(5)
    phi = (1 + sqrt5) / 2  # Golden ratio ≈ 1.618
    
    orbitals = [
        MolecularOrbital("π₁", OrbitalType.PI, alpha + phi*beta, 2, False, False),
        MolecularOrbital("π₂", OrbitalType.PI, alpha + (2-phi)*beta, 2, True, False),  # HOMO
        MolecularOrbital("π₃*", OrbitalType.PI_STAR, alpha - (2-phi)*beta, 0, False, True),  # LUMO
        MolecularOrbital("π₄*", OrbitalType.PI_STAR, alpha - phi*beta, 0, False, False),
    ]
    
    homo_energy = alpha + (2-phi)*beta
    lumo_energy = alpha - (2-phi)*beta
    gap = abs(lumo_energy - homo_energy)
    
    transitions = [
        ElectronicTransition(
            "π₂ (HOMO)", "π₃* (LUMO)",
            gap,
            ev_to_wavelength(gap),
            0.9,
            "π → π*"
        )
    ]
    
    notes = [
        "Hückel MO theory for 1,3-butadiene",
        "4 π electrons in 4 π orbitals",
        "Conjugated diene system",
        f"HOMO-LUMO gap: {gap:.2f} eV",
        f"UV absorption: ~{ev_to_wavelength(gap):.0f} nm"
    ]
    
    return QuantumChemResult(
        molecule_name="1,3-Butadiene (C₄H₆)",
        total_electrons=4,
        orbitals=orbitals,
        homo_energy=homo_energy,
        lumo_energy=lumo_energy,
        homo_lumo_gap=gap,
        ionization_energy=-homo_energy,
        electron_affinity=-lumo_energy,
        transitions=transitions,
        notes=notes
    )


def calculate_mo_system(
    num_carbons: int,
    cyclic: bool = False
) -> QuantumChemResult:
    """
    General Hückel calculation for linear or cyclic π systems.
    
    Args:
        num_carbons: Number of carbon atoms
        cyclic: Whether system is cyclic (like benzene)
        
    Returns:
        QuantumChemResult
    """
    if num_carbons == 2:
        return huckel_ethylene()
    elif num_carbons == 4 and not cyclic:
        return huckel_butadiene()
    elif num_carbons == 6 and cyclic:
        return huckel_benzene()
    
    # Generic calculation
    alpha = 0.0
    beta = -2.4
    
    orbitals = []
    for k in range(num_carbons):
        if cyclic:
            # Cyclic: E_k = α + 2β cos(2πk/n)
            energy = alpha + 2 * beta * math.cos(2 * math.pi * k / num_carbons)
        else:
            # Linear: E_k = α + 2β cos(πk/(n+1))
            energy = alpha + 2 * beta * math.cos(math.pi * (k+1) / (num_carbons + 1))
        
        # Determine occupancy (fill lowest orbitals first)
        occupancy = 2 if k < num_carbons // 2 else 0
        
        orb_type = OrbitalType.PI if energy > alpha else OrbitalType.PI_STAR
        is_homo = (k == num_carbons // 2 - 1)
        is_lumo = (k == num_carbons // 2)
        
        orbitals.append(MolecularOrbital(
            f"{'π' if orb_type == OrbitalType.PI else 'π*'}_{k+1}",
            orb_type,
            energy,
            occupancy,
            is_homo,
            is_lumo
        ))
    
    # Find HOMO and LUMO
    occupied = [o for o in orbitals if o.occupancy > 0]
    unoccupied = [o for o in orbitals if o.occupancy == 0]
    
    homo = max(occupied, key=lambda o: o.energy) if occupied else orbitals[0]
    lumo = min(unoccupied, key=lambda o: o.energy) if unoccupied else orbitals[-1]
    
    gap = abs(lumo.energy - homo.energy)
    
    transitions = [
        ElectronicTransition(
            f"{homo.name} (HOMO)",
            f"{lumo.name} (LUMO)",
            gap,
            ev_to_wavelength(gap),
            0.8,
            "π → π*"
        )
    ]
    
    system_type = "cyclic" if cyclic else "linear"
    notes = [
        f"Hückel MO for {system_type} C{num_carbons} π system",
        f"{num_carbons} π electrons",
        f"HOMO-LUMO gap: {gap:.2f} eV"
    ]
    
    return QuantumChemResult(
        molecule_name=f"C{num_carbons} {'cyclic' if cyclic else 'linear'}",
        total_electrons=num_carbons,
        orbitals=orbitals,
        homo_energy=homo.energy,
        lumo_energy=lumo.energy,
        homo_lumo_gap=gap,
        ionization_energy=-homo.energy,
        electron_affinity=-lumo.energy,
        transitions=transitions,
        notes=notes
    )
