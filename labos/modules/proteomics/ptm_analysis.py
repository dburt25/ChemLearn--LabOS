"""
Post-Translational Modification (PTM) Analysis Module

Handles common post-translational modifications in proteomics,
including modification prediction, mass shifts, and site specificity.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Set, Optional, Tuple


class PTMType(Enum):
    """Common post-translational modifications"""
    # Phosphorylation
    PHOSPHORYLATION = "phosphorylation"
    
    # Acetylation
    ACETYLATION = "acetylation"
    N_TERMINAL_ACETYLATION = "n_terminal_acetylation"
    
    # Methylation
    METHYLATION = "methylation"
    DIMETHYLATION = "dimethylation"
    TRIMETHYLATION = "trimethylation"
    
    # Oxidation
    OXIDATION = "oxidation"
    
    # Ubiquitination
    UBIQUITINATION = "ubiquitination"
    
    # Glycosylation
    N_GLYCOSYLATION = "n_glycosylation"
    O_GLYCOSYLATION = "o_glycosylation"
    
    # Other common modifications
    DEAMIDATION = "deamidation"
    CARBAMIDOMETHYLATION = "carbamidomethylation"
    SULFATION = "sulfation"
    NITRATION = "nitration"
    CITRULLINATION = "citrullination"


@dataclass
class PTMDefinition:
    """Definition of a post-translational modification"""
    ptm_type: PTMType
    name: str
    mass_shift: float  # Da
    target_residues: Set[str]  # Amino acids that can be modified
    formula_change: str  # Chemical formula change
    common_sites: List[str]  # Common motifs or contexts
    biological_role: str
    detection_difficulty: str  # easy, moderate, difficult


@dataclass
class ModificationSite:
    """Represents a potential or confirmed PTM site"""
    position: int  # 0-indexed position in sequence
    residue: str
    ptm_type: PTMType
    mass_shift: float
    confidence: float  # 0-1, prediction confidence
    motif_match: bool  # Whether matches known motif
    surrounding_sequence: str  # Context window
    notes: str


@dataclass
class ModifiedPeptide:
    """Peptide with modifications"""
    sequence: str
    modifications: List[ModificationSite]
    unmodified_mass: float
    modified_mass: float
    total_mass_shift: float
    modification_string: str  # e.g., "pS7, pT9"
    is_multiply_modified: bool


@dataclass
class PTMAnalysisResult:
    """Results of PTM analysis on a peptide or protein"""
    sequence: str
    potential_sites: List[ModificationSite]
    modified_peptides: List[ModifiedPeptide]
    total_modification_sites: int
    ptm_types_found: List[PTMType]
    notes: List[str]


# PTM database with mass shifts and specificity
PTM_DATABASE: Dict[PTMType, PTMDefinition] = {
    PTMType.PHOSPHORYLATION: PTMDefinition(
        ptm_type=PTMType.PHOSPHORYLATION,
        name="Phosphorylation",
        mass_shift=79.966331,  # HPO3
        target_residues={"S", "T", "Y"},
        formula_change="H1P1O3",
        common_sites=["S-x-x-[D/E]", "K/R-x-x-S/T", "S/T-P"],
        biological_role="Signal transduction, protein activation/deactivation",
        detection_difficulty="moderate"
    ),
    
    PTMType.ACETYLATION: PTMDefinition(
        ptm_type=PTMType.ACETYLATION,
        name="Acetylation",
        mass_shift=42.010565,  # C2H2O
        target_residues={"K"},
        formula_change="C2H2O1",
        common_sites=["K-rich regions"],
        biological_role="Gene expression regulation, histone modification",
        detection_difficulty="moderate"
    ),
    
    PTMType.N_TERMINAL_ACETYLATION: PTMDefinition(
        ptm_type=PTMType.N_TERMINAL_ACETYLATION,
        name="N-terminal Acetylation",
        mass_shift=42.010565,
        target_residues={"N_TERM"},  # Special marker for N-terminus
        formula_change="C2H2O1",
        common_sites=["Protein N-terminus"],
        biological_role="Protein stability, localization",
        detection_difficulty="easy"
    ),
    
    PTMType.METHYLATION: PTMDefinition(
        ptm_type=PTMType.METHYLATION,
        name="Methylation",
        mass_shift=14.015650,  # CH2
        target_residues={"K", "R"},
        formula_change="C1H2",
        common_sites=["K/R in histones"],
        biological_role="Gene expression, chromatin remodeling",
        detection_difficulty="moderate"
    ),
    
    PTMType.DIMETHYLATION: PTMDefinition(
        ptm_type=PTMType.DIMETHYLATION,
        name="Dimethylation",
        mass_shift=28.031300,  # C2H4
        target_residues={"K", "R"},
        formula_change="C2H4",
        common_sites=["K/R in histones"],
        biological_role="Gene expression, chromatin remodeling",
        detection_difficulty="moderate"
    ),
    
    PTMType.TRIMETHYLATION: PTMDefinition(
        ptm_type=PTMType.TRIMETHYLATION,
        name="Trimethylation",
        mass_shift=42.046950,  # C3H6
        target_residues={"K"},
        formula_change="C3H6",
        common_sites=["K in histones (H3K4, H3K9, H3K27)"],
        biological_role="Gene expression, chromatin remodeling",
        detection_difficulty="moderate"
    ),
    
    PTMType.OXIDATION: PTMDefinition(
        ptm_type=PTMType.OXIDATION,
        name="Oxidation",
        mass_shift=15.994915,  # O
        target_residues={"M", "W", "P"},
        formula_change="O1",
        common_sites=["Any M, artifact or biological"],
        biological_role="Oxidative stress response, can be artifact",
        detection_difficulty="easy"
    ),
    
    PTMType.UBIQUITINATION: PTMDefinition(
        ptm_type=PTMType.UBIQUITINATION,
        name="Ubiquitination",
        mass_shift=114.042927,  # GG remnant after trypsin
        target_residues={"K"},
        formula_change="C4H6N2O2",
        common_sites=["K in various contexts"],
        biological_role="Protein degradation, signaling",
        detection_difficulty="moderate"
    ),
    
    PTMType.DEAMIDATION: PTMDefinition(
        ptm_type=PTMType.DEAMIDATION,
        name="Deamidation",
        mass_shift=0.984016,  # NH3 -> OH
        target_residues={"N", "Q"},
        formula_change="H-1N-1O1",
        common_sites=["N-G, N-S"],
        biological_role="Aging, structural change, can be artifact",
        detection_difficulty="difficult"
    ),
    
    PTMType.CARBAMIDOMETHYLATION: PTMDefinition(
        ptm_type=PTMType.CARBAMIDOMETHYLATION,
        name="Carbamidomethylation",
        mass_shift=57.021464,  # C2H3NO
        target_residues={"C"},
        formula_change="C2H3N1O1",
        common_sites=["All C (alkylation)"],
        biological_role="Chemical modification (sample prep artifact)",
        detection_difficulty="easy"
    ),
    
    PTMType.SULFATION: PTMDefinition(
        ptm_type=PTMType.SULFATION,
        name="Sulfation",
        mass_shift=79.956815,  # SO3
        target_residues={"Y"},
        formula_change="S1O3",
        common_sites=["Y in secreted proteins"],
        biological_role="Protein-protein interactions",
        detection_difficulty="difficult"
    ),
    
    PTMType.NITRATION: PTMDefinition(
        ptm_type=PTMType.NITRATION,
        name="Nitration",
        mass_shift=44.985078,  # NO2 - H
        target_residues={"Y"},
        formula_change="N1O2H-1",
        common_sites=["Y in oxidative stress"],
        biological_role="Oxidative stress marker",
        detection_difficulty="difficult"
    ),
    
    PTMType.CITRULLINATION: PTMDefinition(
        ptm_type=PTMType.CITRULLINATION,
        name="Citrullination",
        mass_shift=0.984016,  # NH -> O
        target_residues={"R"},
        formula_change="H-1N-1O1",
        common_sites=["R in various proteins"],
        biological_role="Autoimmune diseases, gene regulation",
        detection_difficulty="difficult"
    ),
}


def predict_phosphorylation_sites(
    sequence: str,
    motif_scoring: bool = True
) -> List[ModificationSite]:
    """
    Predict potential phosphorylation sites in a sequence.
    
    Args:
        sequence: Protein or peptide sequence
        motif_scoring: Use motif context for confidence scoring
        
    Returns:
        List of potential phosphorylation sites
    """
    sequence = sequence.upper()
    sites = []
    ptm_def = PTM_DATABASE[PTMType.PHOSPHORYLATION]
    
    for i, aa in enumerate(sequence):
        if aa not in ptm_def.target_residues:
            continue
        
        # Get surrounding context
        start = max(0, i - 3)
        end = min(len(sequence), i + 4)
        context = sequence[start:end]
        
        # Basic confidence
        confidence = 0.3
        motif_match = False
        notes = f"Potential phosphorylation at {aa}{i+1}"
        
        if motif_scoring and i > 0 and i < len(sequence) - 1:
            # Check for kinase motifs
            
            # Proline-directed (e.g., CDK, MAPK)
            if i < len(sequence) - 1 and sequence[i + 1] == "P":
                confidence = 0.8
                motif_match = True
                notes += " (proline-directed motif)"
            
            # Acidic motif (e.g., CK2)
            elif i >= 2:
                acidic_count = sum(1 for j in range(i - 2, i) if sequence[j] in "DE")
                if acidic_count >= 1:
                    confidence = 0.7
                    motif_match = True
                    notes += " (acidic motif)"
            
            # Basophilic motif (e.g., PKA, PKC)
            elif i >= 2:
                basic_count = sum(1 for j in range(i - 3, i) if sequence[j] in "KR")
                if basic_count >= 2:
                    confidence = 0.75
                    motif_match = True
                    notes += " (basophilic motif)"
        
        sites.append(ModificationSite(
            position=i,
            residue=aa,
            ptm_type=PTMType.PHOSPHORYLATION,
            mass_shift=ptm_def.mass_shift,
            confidence=confidence,
            motif_match=motif_match,
            surrounding_sequence=context,
            notes=notes
        ))
    
    return sites


def predict_acetylation_sites(sequence: str) -> List[ModificationSite]:
    """Predict potential lysine acetylation sites"""
    sequence = sequence.upper()
    sites = []
    ptm_def = PTM_DATABASE[PTMType.ACETYLATION]
    
    # N-terminal acetylation (common)
    if sequence:
        n_term_def = PTM_DATABASE[PTMType.N_TERMINAL_ACETYLATION]
        sites.append(ModificationSite(
            position=0,
            residue=sequence[0],
            ptm_type=PTMType.N_TERMINAL_ACETYLATION,
            mass_shift=n_term_def.mass_shift,
            confidence=0.6,  # Common but not universal
            motif_match=True,
            surrounding_sequence=sequence[:7],
            notes="N-terminal acetylation (common modification)"
        ))
    
    # Lysine acetylation
    for i, aa in enumerate(sequence):
        if aa != "K":
            continue
        
        start = max(0, i - 3)
        end = min(len(sequence), i + 4)
        context = sequence[start:end]
        
        # Higher confidence in lysine-rich regions (histones)
        confidence = 0.4
        lysine_nearby = sum(1 for j in range(max(0, i-5), min(len(sequence), i+6)) 
                           if j != i and sequence[j] == "K")
        
        if lysine_nearby >= 2:
            confidence = 0.7
            notes = f"Lysine acetylation at K{i+1} (lysine-rich region)"
        else:
            notes = f"Lysine acetylation at K{i+1}"
        
        sites.append(ModificationSite(
            position=i,
            residue=aa,
            ptm_type=PTMType.ACETYLATION,
            mass_shift=ptm_def.mass_shift,
            confidence=confidence,
            motif_match=lysine_nearby >= 2,
            surrounding_sequence=context,
            notes=notes
        ))
    
    return sites


def predict_oxidation_sites(sequence: str) -> List[ModificationSite]:
    """Predict potential oxidation sites (often artifact)"""
    sequence = sequence.upper()
    sites = []
    ptm_def = PTM_DATABASE[PTMType.OXIDATION]
    
    for i, aa in enumerate(sequence):
        if aa not in ptm_def.target_residues:
            continue
        
        start = max(0, i - 3)
        end = min(len(sequence), i + 4)
        context = sequence[start:end]
        
        # Methionine oxidation most common
        if aa == "M":
            confidence = 0.5
            notes = f"Methionine oxidation at M{i+1} (common artifact/biological)"
        elif aa == "W":
            confidence = 0.3
            notes = f"Tryptophan oxidation at W{i+1} (less common)"
        else:
            confidence = 0.2
            notes = f"Proline oxidation at P{i+1} (rare)"
        
        sites.append(ModificationSite(
            position=i,
            residue=aa,
            ptm_type=PTMType.OXIDATION,
            mass_shift=ptm_def.mass_shift,
            confidence=confidence,
            motif_match=False,
            surrounding_sequence=context,
            notes=notes
        ))
    
    return sites


def predict_all_modifications(
    sequence: str,
    include_artifacts: bool = False
) -> PTMAnalysisResult:
    """
    Comprehensive PTM prediction for a sequence.
    
    Args:
        sequence: Protein or peptide sequence
        include_artifacts: Include likely artifact modifications (oxidation, deamidation)
        
    Returns:
        PTMAnalysisResult with all predicted sites
    """
    sequence = sequence.upper().strip()
    
    all_sites = []
    
    # Phosphorylation (most common)
    all_sites.extend(predict_phosphorylation_sites(sequence))
    
    # Acetylation
    all_sites.extend(predict_acetylation_sites(sequence))
    
    # Oxidation (if requested)
    if include_artifacts:
        all_sites.extend(predict_oxidation_sites(sequence))
    
    # Sort by position
    all_sites.sort(key=lambda x: x.position)
    
    # Get unique PTM types
    ptm_types = list(set(site.ptm_type for site in all_sites))
    
    notes = [
        f"Analyzed {len(sequence)} amino acids",
        f"Found {len(all_sites)} potential modification sites",
        f"Modification types: {', '.join(ptm.value for ptm in ptm_types)}"
    ]
    
    if not include_artifacts:
        notes.append("Artifact modifications (oxidation, deamidation) excluded")
    
    return PTMAnalysisResult(
        sequence=sequence,
        potential_sites=all_sites,
        modified_peptides=[],  # Filled by generate_modified_peptides
        total_modification_sites=len(all_sites),
        ptm_types_found=ptm_types,
        notes=notes
    )


def apply_modifications_to_peptide(
    sequence: str,
    modification_sites: List[ModificationSite],
    base_mass: float
) -> ModifiedPeptide:
    """
    Apply modifications to a peptide and calculate modified mass.
    
    Args:
        sequence: Peptide sequence
        modification_sites: List of modifications to apply
        base_mass: Unmodified peptide mass
        
    Returns:
        ModifiedPeptide with calculated mass shifts
    """
    total_shift = sum(site.mass_shift for site in modification_sites)
    modified_mass = base_mass + total_shift
    
    # Generate modification string (e.g., "pS7, pT9, AcK12")
    mod_strings = []
    for site in sorted(modification_sites, key=lambda x: x.position):
        if site.ptm_type == PTMType.PHOSPHORYLATION:
            prefix = "p"
        elif site.ptm_type in [PTMType.ACETYLATION, PTMType.N_TERMINAL_ACETYLATION]:
            prefix = "Ac"
        elif site.ptm_type == PTMType.OXIDATION:
            prefix = "ox"
        elif site.ptm_type == PTMType.METHYLATION:
            prefix = "me"
        else:
            prefix = site.ptm_type.value[:2]
        
        mod_strings.append(f"{prefix}{site.residue}{site.position + 1}")
    
    mod_string = ", ".join(mod_strings)
    
    return ModifiedPeptide(
        sequence=sequence,
        modifications=modification_sites,
        unmodified_mass=base_mass,
        modified_mass=modified_mass,
        total_mass_shift=total_shift,
        modification_string=mod_string,
        is_multiply_modified=len(modification_sites) > 1
    )


def calculate_modification_stoichiometry(
    ptm_analysis: PTMAnalysisResult,
    observed_modified_mass: float,
    base_mass: float,
    tolerance_da: float = 0.1
) -> List[List[ModificationSite]]:
    """
    Determine which combination of modifications matches observed mass shift.
    
    Args:
        ptm_analysis: PTM analysis result
        observed_modified_mass: Observed mass from MS
        base_mass: Unmodified theoretical mass
        tolerance_da: Mass tolerance in Daltons
        
    Returns:
        List of possible modification combinations
    """
    observed_shift = observed_modified_mass - base_mass
    
    matches = []
    sites = ptm_analysis.potential_sites
    
    # Try single modifications
    for site in sites:
        if abs(site.mass_shift - observed_shift) <= tolerance_da:
            matches.append([site])
    
    # Try double modifications
    for i, site1 in enumerate(sites):
        for site2 in sites[i+1:]:
            combined_shift = site1.mass_shift + site2.mass_shift
            if abs(combined_shift - observed_shift) <= tolerance_da:
                matches.append([site1, site2])
    
    # Sort by confidence
    matches.sort(key=lambda combo: sum(s.confidence for s in combo), reverse=True)
    
    return matches
