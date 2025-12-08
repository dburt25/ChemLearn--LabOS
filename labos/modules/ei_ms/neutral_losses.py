"""Neutral loss detection for EI-MS fragment analysis.

Identifies common neutral losses in mass spectra and provides
structural interpretation hints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


# Common neutral losses in EI-MS
COMMON_LOSSES = {
    1: {"formula": "H", "name": "H", "interpretation": "Radical loss"},
    15: {"formula": "CH3", "name": "CH3", "interpretation": "Methyl group loss"},
    17: {"formula": "NH3", "name": "NH3", "interpretation": "Amine functionality"},
    18: {"formula": "H2O", "name": "H2O", "interpretation": "Alcohol/phenol/carboxylic acid"},
    28: {"formula": "CO", "name": "CO", "interpretation": "Aldehyde/ketone/aromatic"},
    29: {"formula": "CHO", "name": "CHO", "interpretation": "Aldehyde functionality"},
    31: {"formula": "OCH3", "name": "OCH3", "interpretation": "Methyl ester"},
    35: {"formula": "Cl", "name": "Cl", "interpretation": "Chlorinated compound"},
    36: {"formula": "HCl", "name": "HCl", "interpretation": "Alkyl chloride"},
    42: {"formula": "C2H2O", "name": "C2H2O", "interpretation": "Acetyl group"},
    43: {"formula": "CH3CO", "name": "CH3CO", "interpretation": "Methyl ketone/acetate"},
    44: {"formula": "CO2", "name": "CO2", "interpretation": "Carboxylic acid/ester"},
    45: {"formula": "C2H5O", "name": "C2H5O", "interpretation": "Ethyl ester"},
    46: {"formula": "NO2", "name": "NO2", "interpretation": "Nitro compound"},
    54: {"formula": "C4H6", "name": "C4H6", "interpretation": "Aromatic rearrangement"},
    57: {"formula": "C4H9", "name": "C4H9", "interpretation": "Butyl group"},
    59: {"formula": "CH3COO", "name": "CH3COO", "interpretation": "Acetate ester"},
    77: {"formula": "C6H5", "name": "C6H5", "interpretation": "Aromatic ring"},
    79: {"formula": "Br", "name": "Br", "interpretation": "Brominated compound"},
    80: {"formula": "HBr", "name": "HBr", "interpretation": "Alkyl bromide"},
}


@dataclass
class NeutralLoss:
    """Represents a detected neutral loss."""
    
    precursor_mz: float
    fragment_mz: float
    loss_mass: float
    loss_name: str
    loss_formula: str = ""
    interpretation: str | None = None
    
    def __repr__(self) -> str:
        return f"NeutralLoss({self.precursor_mz:.1f} → {self.fragment_mz:.1f}, -{self.loss_name})"
    
    def to_dict(self) -> Dict[str, object]:
        """Serialize to dictionary."""
        return {
            "precursor_mz": self.precursor_mz,
            "fragment_mz": self.fragment_mz,
            "loss_mass": self.loss_mass,
            "loss_name": self.loss_name,
            "loss_formula": self.loss_formula,
            "interpretation": self.interpretation,
        }


def detect_neutral_losses(
    precursor_mz: float,
    fragment_peaks: List[Tuple[float, float]],
    mass_tolerance: float = 0.5,
) -> List[NeutralLoss]:
    """Detect common neutral losses from precursor to fragments.
    
    Args:
        precursor_mz: Precursor ion m/z
        fragment_peaks: List of (m/z, intensity) tuples for fragments
        mass_tolerance: Mass tolerance in Da for loss matching
        
    Returns:
        List of detected neutral losses
        
    Example:
        >>> losses = detect_neutral_losses(180.0, [(162.0, 50.0), (152.0, 30.0)])
        >>> # 180 - 162 = 18 (water loss)
        >>> # 180 - 152 = 28 (CO loss)
    """
    detected_losses = []
    
    for fragment_mz, fragment_intensity in fragment_peaks:
        if fragment_mz >= precursor_mz:
            continue
        
        loss_mass = precursor_mz - fragment_mz
        
        # Check against common losses
        for common_loss_mass, loss_data in COMMON_LOSSES.items():
            if abs(loss_mass - common_loss_mass) <= mass_tolerance:
                detected_losses.append(
                    NeutralLoss(
                        precursor_mz=precursor_mz,
                        fragment_mz=fragment_mz,
                        loss_mass=common_loss_mass,
                        loss_name=loss_data["name"],
                        loss_formula=loss_data["formula"],
                        interpretation=loss_data["interpretation"],
                    )
                )
                break  # Only match once per fragment
    
    return detected_losses


def annotate_spectrum(
    precursor_mz: float,
    fragment_peaks: List[Tuple[float, float]],
    mass_tolerance: float = 0.5,
) -> List[Dict[str, object]]:
    """Annotate mass spectrum with neutral loss assignments.
    
    Args:
        precursor_mz: Precursor ion m/z
        fragment_peaks: List of (m/z, intensity) tuples for fragments
        mass_tolerance: Mass tolerance for matching
        
    Returns:
        List of annotated peaks with assignments
    """
    if not fragment_peaks:
        return []
    
    # Sort peaks by m/z
    sorted_peaks = sorted(fragment_peaks, key=lambda x: x[0])
    
    # Detect neutral losses
    neutral_losses = detect_neutral_losses(precursor_mz, sorted_peaks, mass_tolerance)
    
    # Create annotated peak list
    annotated_peaks = []
    for mz, intensity in sorted_peaks:
        peak_annotation = {"mz": mz, "intensity": intensity, "annotations": []}
        
        # Check if this is a known neutral loss fragment
        for loss in neutral_losses:
            if abs(mz - loss.fragment_mz) < 0.01:
                # Format: "Loss: H2O (18 Da) - Alcohol/phenol/carboxylic acid"
                interpretation = loss.interpretation if loss.interpretation else "Unknown"
                annotation_text = f"Loss: {loss.loss_formula} ({loss.loss_mass:.0f} Da) - {interpretation}"
                peak_annotation["annotations"].append(annotation_text)
        
        # Mark precursor peak
        if abs(mz - precursor_mz) < 0.01:
            peak_annotation["annotations"].append("M+")
        
        annotated_peaks.append(peak_annotation)
    
    return annotated_peaks


def _generate_interpretation(losses: List[NeutralLoss]) -> str:
    """Generate human-readable interpretation from detected losses."""
    if not losses:
        return "No common neutral losses detected."
    
    interpretations = set()
    for loss in losses:
        interpretations.add(loss.interpretation)
    
    summary = f"Detected {len(losses)} neutral loss(es): "
    loss_names = [f"{loss.loss_name} (-{loss.loss_mass:.0f})" for loss in losses]
    summary += ", ".join(loss_names)
    summary += ". Suggests: " + "; ".join(interpretations) + "."
    
    return summary


def find_sequential_losses(
    precursor_mz: float,
    fragment_peaks: List[Tuple[float, float]],
    mass_tolerance: float = 0.5,
) -> List[List[NeutralLoss]]:
    """Find sequential neutral loss chains (cascading fragmentation).
    
    Args:
        precursor_mz: Precursor ion m/z
        fragment_peaks: List of (m/z, intensity) tuples for fragments
        mass_tolerance: Mass tolerance for matching
        
    Returns:
        List of neutral loss chains (each chain is a list of NeutralLoss objects)
        
    Example:
        >>> # M+ → (M-H2O)+ → (M-H2O-CO)+
        >>> chains = find_sequential_losses(100.0, [(82.0, 60), (64.0, 30)])
    """
    if not fragment_peaks:
        return []
    
    all_peaks = [(precursor_mz, 100.0)] + fragment_peaks
    sorted_peaks = sorted(all_peaks, key=lambda x: x[0], reverse=True)
    chains = []
    
    def build_chain(current_mz: float, current_chain: List[NeutralLoss], depth: int) -> None:
        if depth >= 3:  # Maximum chain length
            return
        
        for candidate_mz, candidate_intensity in sorted_peaks:
            if candidate_mz >= current_mz:
                continue
            
            loss_mass = current_mz - candidate_mz
            
            for common_loss_mass, loss_data in COMMON_LOSSES.items():
                if abs(loss_mass - common_loss_mass) <= mass_tolerance:
                    new_loss = NeutralLoss(
                        precursor_mz=current_mz,
                        fragment_mz=candidate_mz,
                        loss_mass=common_loss_mass,
                        loss_formula=loss_data["formula"],
                        loss_name=loss_data["name"],
                        interpretation=loss_data["interpretation"],
                    )
                    
                    new_chain = current_chain + [new_loss]
                    chains.append(new_chain)
                    
                    # Recursively search for further losses
                    build_chain(candidate_mz, new_chain, depth + 1)
                    break
    
    # Start from highest m/z peak
    if sorted_peaks:
        build_chain(sorted_peaks[0][0], [], 0)
    
    # Filter to only chains of length 2+
    return [chain for chain in chains if len(chain) >= 2]


# Module registration
MODULE_KEY = "ei_ms.neutral_losses"
MODULE_VERSION = "1.0.0"


def analyze_neutral_losses(
    precursor_mz: float,
    fragment_peaks: List[Tuple[float, float]],
    detect_chains: bool = False,
    mass_tolerance: float = 0.5,
) -> Dict[str, object]:
    """Analyze neutral losses in EI-MS spectrum.
    
    Main entry point for module operation.
    
    Args:
        precursor_mz: Precursor ion m/z
        fragment_peaks: List of (m/z, intensity) tuples
        detect_chains: Whether to detect sequential loss chains
        mass_tolerance: Mass tolerance in Da
        
    Returns:
        Analysis results including detected losses and interpretations
    """
    annotated_peaks = annotate_spectrum(precursor_mz, fragment_peaks, mass_tolerance)
    
    # Extract detected losses from annotated peaks
    detected_losses = detect_neutral_losses(precursor_mz, fragment_peaks, mass_tolerance)
    
    result = {
        "precursor_mz": precursor_mz,
        "annotated_spectrum": annotated_peaks,
        "peaks": annotated_peaks,
        "neutral_losses": [loss.to_dict() for loss in detected_losses],
        "detected_losses": [loss.to_dict() for loss in detected_losses],
    }
    
    # Add sequential loss chains if requested
    if detect_chains:
        chains = find_sequential_losses(precursor_mz, fragment_peaks, mass_tolerance)
        result["sequential_losses"] = chains
    
    # Add summary of common losses
    loss_formulas = [loss.loss_formula for loss in detected_losses]
    if loss_formulas:
        result["summary"] = f"Detected {len(loss_formulas)} neutral loss(es): {', '.join(loss_formulas)}"
    else:
        result["summary"] = "No common neutral losses detected"
    
    return result


def _register() -> None:
    """Register neutral loss detection with module system."""
    from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor
    
    descriptor = ModuleDescriptor(
        module_id=MODULE_KEY,
        version=MODULE_VERSION,
        description="Detect and interpret neutral losses in EI-MS spectra",
    )
    
    descriptor.register_operation(
        ModuleOperation(
            name="analyze",
            description="Detect neutral losses and fragmentation patterns",
            handler=lambda params: analyze_neutral_losses(**params),
        )
    )
    
    register_descriptor(descriptor)


# Auto-register on import
_register()
