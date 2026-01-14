"""Pydantic schemas for Water Analysis endpoints."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WaterAnalysisBase(BaseModel):
    """Base schema for water analysis data."""
    name: str = Field(..., min_length=1, max_length=100, description="Name for this water analysis")
    source_type: Optional[str] = Field(default="otro", max_length=50, description="Water source type")
    saved_units: Optional[str] = Field(default="meq", max_length=10, description="Units used when saving (meq, ppm, mmol)")
    
    anion_no3: float = Field(default=0.0, ge=0, description="Nitrate (NO3-) in meq/L")
    anion_h2po4: float = Field(default=0.0, ge=0, description="Phosphate (H2PO4-) in meq/L")
    anion_so42: float = Field(default=0.0, ge=0, description="Sulfate (SO42-) in meq/L")
    anion_hco3: float = Field(default=0.0, ge=0, description="Bicarbonate (HCO3-) in meq/L")
    anion_cl: float = Field(default=0.0, ge=0, description="Chloride (Cl-) in meq/L")
    
    cation_nh4: float = Field(default=0.0, ge=0, description="Ammonium (NH4+) in meq/L")
    cation_k: float = Field(default=0.0, ge=0, description="Potassium (K+) in meq/L")
    cation_ca: float = Field(default=0.0, ge=0, description="Calcium (Ca2+) in meq/L")
    cation_mg: float = Field(default=0.0, ge=0, description="Magnesium (Mg2+) in meq/L")
    cation_na: float = Field(default=0.0, ge=0, description="Sodium (Na+) in meq/L")
    
    micro_fe: float = Field(default=0.0, ge=0, description="Iron (Fe) in ppm")
    micro_mn: float = Field(default=0.0, ge=0, description="Manganese (Mn) in ppm")
    micro_zn: float = Field(default=0.0, ge=0, description="Zinc (Zn) in ppm")
    micro_cu: float = Field(default=0.0, ge=0, description="Copper (Cu) in ppm")
    micro_b: float = Field(default=0.0, ge=0, description="Boron (B) in ppm")
    micro_mo: float = Field(default=0.0, ge=0, description="Molybdenum (Mo) in ppm")
    
    ec: float = Field(default=0.0, ge=0, description="Electrical Conductivity in mS/cm")
    ph: Optional[float] = Field(default=None, ge=0, le=14, description="pH value")
    source_description: Optional[str] = Field(default=None, max_length=255, description="Water source description")


class WaterAnalysisCreate(WaterAnalysisBase):
    """Schema for creating a new water analysis."""
    pass


class WaterAnalysisUpdate(BaseModel):
    """Schema for updating an existing water analysis."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    source_type: Optional[str] = Field(None, max_length=50)
    saved_units: Optional[str] = Field(None, max_length=10)
    
    anion_no3: Optional[float] = Field(None, ge=0)
    anion_h2po4: Optional[float] = Field(None, ge=0)
    anion_so42: Optional[float] = Field(None, ge=0)
    anion_hco3: Optional[float] = Field(None, ge=0)
    anion_cl: Optional[float] = Field(None, ge=0)
    
    cation_nh4: Optional[float] = Field(None, ge=0)
    cation_k: Optional[float] = Field(None, ge=0)
    cation_ca: Optional[float] = Field(None, ge=0)
    cation_mg: Optional[float] = Field(None, ge=0)
    cation_na: Optional[float] = Field(None, ge=0)
    
    micro_fe: Optional[float] = Field(None, ge=0)
    micro_mn: Optional[float] = Field(None, ge=0)
    micro_zn: Optional[float] = Field(None, ge=0)
    micro_cu: Optional[float] = Field(None, ge=0)
    micro_b: Optional[float] = Field(None, ge=0)
    micro_mo: Optional[float] = Field(None, ge=0)
    
    ec: Optional[float] = Field(None, ge=0)
    ph: Optional[float] = Field(None, ge=0, le=14)
    source_description: Optional[str] = Field(None, max_length=255)


class WaterAnalysisResponse(WaterAnalysisBase):
    """Schema for water analysis response."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WaterAnalysisList(BaseModel):
    """Schema for list of water analyses."""
    items: list[WaterAnalysisResponse]
    total: int
