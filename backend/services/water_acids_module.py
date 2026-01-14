"""
Water + Acids Module for IA Grower v3.0

This module handles:
1. Water analysis processing
2. Alkalinity calculation and target setting
3. Acid selection with N-P-S constraints (candados)
4. Ion contribution from water + acids
5. Deficit calculation after water/acid adjustments

The output feeds into the fertilizer optimizer with real deficits.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AcidType(Enum):
    NITRIC = "nitric_acid_70"
    PHOSPHORIC = "phosphoric_acid_75"
    SULFURIC = "sulfuric_acid_98"


@dataclass
class AcidProperties:
    """Properties of an acid for alkalinity neutralization."""
    id: str
    name: str
    ion_contributed: str
    meq_h_per_ml: float
    meq_ion_per_ml: float
    cost_per_liter: float = 0.0
    safety_level: str = "high"


ACID_CATALOG = {
    AcidType.NITRIC: AcidProperties(
        id="nitric_acid_70",
        name="Ácido Nítrico 70%",
        ion_contributed="NO3",
        meq_h_per_ml=15.9,
        meq_ion_per_ml=15.9,
        cost_per_liter=56.8,
        safety_level="very_high"
    ),
    AcidType.PHOSPHORIC: AcidProperties(
        id="phosphoric_acid_75",
        name="Ácido Fosfórico 75%",
        ion_contributed="H2PO4",
        meq_h_per_ml=10.2,
        meq_ion_per_ml=10.2,
        cost_per_liter=56.0,
        safety_level="high"
    ),
    AcidType.SULFURIC: AcidProperties(
        id="sulfuric_acid_98",
        name="Ácido Sulfúrico 98%",
        ion_contributed="SO42",
        meq_h_per_ml=20.4,
        meq_ion_per_ml=20.4,
        cost_per_liter=46.25,
        safety_level="very_high"
    ),
}


@dataclass
class WaterAnalysis:
    """Water analysis data from user input."""
    ec: float = 0.0
    ph: float = 7.0
    NO3: float = 0.0
    H2PO4: float = 0.0
    SO42: float = 0.0
    HCO3: float = 0.0
    Cl: float = 0.0
    K: float = 0.0
    Ca: float = 0.0
    Mg: float = 0.0
    Na: float = 0.0
    NH4: float = 0.0
    Fe: float = 0.0
    Mn: float = 0.0
    Zn: float = 0.0
    Cu: float = 0.0
    B: float = 0.0
    Mo: float = 0.0
    
    def get_ion_concentrations(self) -> Dict[str, float]:
        """Return all ion concentrations as dict."""
        return {
            "NO3": self.NO3,
            "H2PO4": self.H2PO4,
            "SO42": self.SO42,
            "HCO3": self.HCO3,
            "Cl": self.Cl,
            "K": self.K,
            "Ca": self.Ca,
            "Mg": self.Mg,
            "Na": self.Na,
            "NH4": self.NH4,
        }


@dataclass
class AcidConstraints:
    """N-P-S constraints for acid selection (candados)."""
    max_no3_from_acid: float = 3.0
    max_h2po4_from_acid: float = 1.5
    max_so42_from_acid: float = 2.0
    
    def get_limit(self, ion: str) -> float:
        """Get the maximum ion contribution allowed from acid."""
        limits = {
            "NO3": self.max_no3_from_acid,
            "H2PO4": self.max_h2po4_from_acid,
            "SO42": self.max_so42_from_acid,
        }
        return limits.get(ion, float('inf'))


@dataclass
class AcidDose:
    """Calculated dose for an acid."""
    acid_type: AcidType
    acid_id: str
    acid_name: str
    ml_per_m3: float
    ml_per_liter: float
    hco3_neutralized: float
    ion_contributed: str
    ion_meq_added: float
    cost_per_m3: float = 0.0


@dataclass
class WaterAcidResult:
    """Result of water + acid calculation."""
    original_hco3: float
    target_hco3_range: Tuple[float, float]
    final_hco3: float
    acid_doses: List[AcidDose]
    total_ion_contributions: Dict[str, float]
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class WaterAcidsModule:
    """
    Module for water analysis and acid selection.
    
    Workflow:
    1. Receive water analysis
    2. Calculate alkalinity and target HCO3
    3. Select acid(s) respecting N-P-S constraints
    4. Calculate ion contributions from water + acids
    5. Return adjusted ion levels for deficit calculation
    """
    
    def __init__(self, 
                 water_analysis: WaterAnalysis,
                 target_hco3_range: Tuple[float, float] = (0.3, 0.8),
                 constraints: Optional[AcidConstraints] = None,
                 available_acids: Optional[List[AcidType]] = None,
                 target_ions: Optional[Dict[str, float]] = None):
        """
        Initialize the module.
        
        Args:
            water_analysis: Water analysis data
            target_hco3_range: (min, max) HCO3 after neutralization in meq/L
            constraints: N-P-S limits for acid ion contribution
            available_acids: List of acids available to use
            target_ions: Ion objectives to consider for acid selection
        """
        self.water = water_analysis
        self.target_hco3_range = target_hco3_range
        self.constraints = constraints or AcidConstraints()
        self.available_acids = available_acids or list(AcidType)
        self.target_ions = target_ions or {}
        
    def calculate_hco3_to_neutralize(self) -> float:
        """
        Calculate how much HCO3 needs to be neutralized.
        
        Returns meq/L of HCO3 to remove.
        """
        current_hco3 = self.water.HCO3
        target_max = self.target_hco3_range[1]
        
        if current_hco3 <= target_max:
            return 0.0
        
        return current_hco3 - target_max
    
    def select_acids(self) -> List[Tuple[AcidType, float]]:
        """
        Select which acid(s) to use and how much HCO3 each should neutralize.
        
        Returns list of (AcidType, hco3_to_neutralize_meq_l).
        """
        hco3_needed = self.calculate_hco3_to_neutralize()
        
        if hco3_needed <= 0:
            return []
        
        selections = []
        remaining_hco3 = hco3_needed
        
        acid_priority = self._prioritize_acids()
        
        for acid_type in acid_priority:
            if remaining_hco3 <= 0:
                break
            
            props = ACID_CATALOG[acid_type]
            ion = props.ion_contributed
            
            ion_limit = self.constraints.get_limit(ion)
            
            current_ion = getattr(self.water, ion, 0) if hasattr(self.water, ion) else 0
            if ion == "SO42":
                current_ion = self.water.SO42
            
            available_ion_space = max(0, ion_limit - current_ion)
            
            max_hco3_by_constraint = available_ion_space
            
            can_neutralize = min(remaining_hco3, max_hco3_by_constraint)
            
            if can_neutralize > 0.05:
                selections.append((acid_type, can_neutralize))
                remaining_hco3 -= can_neutralize
        
        if remaining_hco3 > 0.1:
            logger.warning(f"Could not fully neutralize HCO3. Remaining: {remaining_hco3:.2f} meq/L")
        
        return selections
    
    def _prioritize_acids(self) -> List[AcidType]:
        """
        Prioritize acids based on ion needs and constraints.
        
        Logic:
        1. If NO3 target is high and room available -> prioritize HNO3
        2. If H2PO4 target is high and room available -> prioritize H3PO4
        3. If SO4 target is high and room available -> prioritize H2SO4
        4. Default: use the cheapest available
        """
        scores = {}
        
        for acid_type in self.available_acids:
            props = ACID_CATALOG[acid_type]
            ion = props.ion_contributed
            
            target = self.target_ions.get(ion, 0)
            current = self._get_water_ion(ion)
            deficit = max(0, target - current)
            
            ion_limit = self.constraints.get_limit(ion)
            available_space = max(0, ion_limit - current)
            
            score = 0
            if deficit > 0 and available_space > 0:
                useful_contribution = min(deficit, available_space)
                score = useful_contribution * 10
            
            score -= props.cost_per_liter / 100
            
            scores[acid_type] = score
        
        return sorted(self.available_acids, key=lambda a: scores.get(a, 0), reverse=True)
    
    def _get_water_ion(self, ion: str) -> float:
        """Get ion concentration from water analysis."""
        if ion == "SO42":
            return self.water.SO42
        return getattr(self.water, ion, 0)
    
    def calculate_acid_doses(self) -> List[AcidDose]:
        """
        Calculate specific doses for selected acids.
        
        Returns list of AcidDose with ml/m³ and ion contributions.
        """
        selections = self.select_acids()
        doses = []
        
        for acid_type, hco3_amount in selections:
            props = ACID_CATALOG[acid_type]
            
            ml_per_m3 = (hco3_amount * 1000) / props.meq_h_per_ml
            
            ion_added = (ml_per_m3 * props.meq_ion_per_ml) / 1000
            
            cost = (ml_per_m3 / 1000) * props.cost_per_liter
            
            doses.append(AcidDose(
                acid_type=acid_type,
                acid_id=props.id,
                acid_name=props.name,
                ml_per_m3=round(ml_per_m3, 1),
                ml_per_liter=round(ml_per_m3 / 1000, 4),
                hco3_neutralized=round(hco3_amount, 2),
                ion_contributed=props.ion_contributed,
                ion_meq_added=round(ion_added, 3),
                cost_per_m3=round(cost, 2)
            ))
        
        return doses
    
    def calculate_total_contributions(self) -> Dict[str, float]:
        """
        Calculate total ion contributions from water + acids.
        
        Returns dict of ion -> meq/L contributed.
        """
        contributions = self.water.get_ion_concentrations().copy()
        
        acid_doses = self.calculate_acid_doses()
        for dose in acid_doses:
            ion = dose.ion_contributed
            contributions[ion] = contributions.get(ion, 0) + dose.ion_meq_added
        
        total_neutralized = sum(d.hco3_neutralized for d in acid_doses)
        contributions["HCO3"] = max(0, self.water.HCO3 - total_neutralized)
        
        return contributions
    
    def calculate_deficits(self, targets: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate real deficits after accounting for water + acids.
        
        Args:
            targets: Ion objectives in meq/L
            
        Returns:
            Dict of ion -> deficit (positive = need to add, negative = excess)
        """
        contributions = self.calculate_total_contributions()
        
        deficits = {}
        for ion, target in targets.items():
            contribution = contributions.get(ion, 0)
            deficits[ion] = target - contribution
        
        return deficits
    
    def process(self) -> WaterAcidResult:
        """
        Run the complete water + acid calculation.
        
        Returns WaterAcidResult with all calculations.
        """
        acid_doses = self.calculate_acid_doses()
        contributions = self.calculate_total_contributions()
        
        total_neutralized = sum(d.hco3_neutralized for d in acid_doses)
        final_hco3 = max(0, self.water.HCO3 - total_neutralized)
        
        warnings = []
        notes = []
        
        if self.water.Na > 2.0:
            warnings.append(f"Agua con Na elevado ({self.water.Na:.1f} meq/L). Puede afectar el cultivo.")
        
        if self.water.Cl > 3.0:
            warnings.append(f"Agua con Cl elevado ({self.water.Cl:.1f} meq/L). Riesgo de toxicidad.")
        
        if final_hco3 > self.target_hco3_range[1]:
            warnings.append(
                f"No se pudo neutralizar todo el HCO3. Final: {final_hco3:.1f} meq/L "
                f"(objetivo: {self.target_hco3_range[1]:.1f})"
            )
        
        if acid_doses:
            acids_used = [d.acid_name for d in acid_doses]
            notes.append(f"Ácidos utilizados: {', '.join(acids_used)}")
            
            for dose in acid_doses:
                notes.append(
                    f"{dose.acid_name}: {dose.ml_per_m3:.1f} mL/m³ "
                    f"(aporta {dose.ion_meq_added:.2f} meq/L de {dose.ion_contributed})"
                )
        
        return WaterAcidResult(
            original_hco3=self.water.HCO3,
            target_hco3_range=self.target_hco3_range,
            final_hco3=final_hco3,
            acid_doses=acid_doses,
            total_ion_contributions=contributions,
            warnings=warnings,
            notes=notes
        )


def process_water_analysis(
    water_data: Dict[str, float],
    target_ions: Dict[str, float],
    target_hco3_range: Tuple[float, float] = (0.3, 0.8),
    acid_constraints: Optional[Dict[str, float]] = None,
    available_acids: Optional[List[str]] = None
) -> WaterAcidResult:
    """
    Convenience function to process water analysis.
    
    Args:
        water_data: Dict with water analysis values
        target_ions: Dict with ion targets in meq/L
        target_hco3_range: (min, max) HCO3 target after neutralization
        acid_constraints: Dict with max_no3, max_h2po4, max_so42 from acids
        available_acids: List of acid IDs available
        
    Returns:
        WaterAcidResult with complete analysis
    """
    water = WaterAnalysis(
        ec=water_data.get("ec", 0),
        ph=water_data.get("ph", 7.0),
        NO3=water_data.get("NO3", 0),
        H2PO4=water_data.get("H2PO4", 0),
        SO42=water_data.get("SO42", 0),
        HCO3=water_data.get("HCO3", 0),
        Cl=water_data.get("Cl", 0),
        K=water_data.get("K", 0),
        Ca=water_data.get("Ca", 0),
        Mg=water_data.get("Mg", 0),
        Na=water_data.get("Na", 0),
        NH4=water_data.get("NH4", 0),
    )
    
    constraints = None
    if acid_constraints:
        constraints = AcidConstraints(
            max_no3_from_acid=acid_constraints.get("max_no3", 3.0),
            max_h2po4_from_acid=acid_constraints.get("max_h2po4", 1.5),
            max_so42_from_acid=acid_constraints.get("max_so42", 2.0),
        )
    
    acids = None
    if available_acids:
        acid_map = {
            "nitric_acid_70": AcidType.NITRIC,
            "phosphoric_acid_75": AcidType.PHOSPHORIC,
            "sulfuric_acid_98": AcidType.SULFURIC,
        }
        acids = [acid_map[a] for a in available_acids if a in acid_map]
    
    module = WaterAcidsModule(
        water_analysis=water,
        target_hco3_range=target_hco3_range,
        constraints=constraints,
        available_acids=acids,
        target_ions=target_ions
    )
    
    return module.process()
