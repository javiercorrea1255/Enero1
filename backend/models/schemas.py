"""
Pydantic models for AgriDose API.
Defines request/response schemas with validation.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.models.database_models import ModuleType


class SoilInput(BaseModel):
    """Input model for soil fertilization calculation with comprehensive NOM-021 parameters."""
    
    # Required basic parameters
    crop_slug: str = Field(..., description="Crop identifier (e.g., 'maiz', 'trigo')")
    yield_target_t_ha: float = Field(..., gt=0, description="Target yield in t/ha")
    soil_n_ppm: float = Field(..., ge=0, description="Soil nitrogen in ppm (NO3-N available)")
    soil_p_ppm: float = Field(..., ge=0, description="Soil phosphorus in ppm")
    soil_k_ppm: float = Field(..., ge=0, description="Soil potassium in ppm")
    
    # Calculation parameters
    method: str = Field(
        default="extraccion_balance",
        description="Calculation method: 'extraccion_balance', 'suficiencia_critico', 'mantenimiento'"
    )
    p_method: str = Field(
        default="olsen",
        description="P analysis method: 'olsen', 'bray', 'mehlich3'"
    )
    depth_cm: float = Field(default=20.0, gt=0, description="Sampling depth in cm")
    bulk_density_g_cm3: float = Field(default=1.3, gt=0, description="Bulk density in g/cm³")
    nue_n: float = Field(default=0.6, gt=0, le=1, description="Nitrogen use efficiency")
    nue_p2o5: float = Field(default=0.5, gt=0, le=1, description="P₂O₅ use efficiency")
    nue_k2o: float = Field(default=0.6, gt=0, le=1, description="K₂O use efficiency")
    build_up_factor: float = Field(default=1.0, ge=0, description="Build-up intensity factor")
    suggest_granular_blend: bool = Field(default=True, description="Suggest granular fertilizer blend")
    
    # Basic soil properties
    ph: float = Field(default=6.5, ge=3, le=10, description="Soil pH")
    texture: Optional[str] = Field(default="franca", description="Soil texture")
    irrigation: Optional[str] = Field(default="riego", description="Irrigation type: 'riego', 'temporal'")
    organic_matter: Optional[float] = Field(default=None, ge=0, le=100, description="Organic matter percentage")
    
    # Physical parameters (saturated extract)
    soil_ec_ms_cm: Optional[float] = Field(default=None, ge=0, description="Electrical conductivity in mS/cm")
    sar: Optional[float] = Field(default=None, ge=0, description="Sodium Absorption Ratio")
    psi: Optional[float] = Field(default=None, ge=0, le=100, description="Percent Sodium Interchangeable")
    saturation_pct: Optional[float] = Field(default=None, ge=0, le=100, description="Saturation percentage")
    field_capacity: Optional[float] = Field(default=None, ge=0, le=100, description="Field capacity percentage")
    wilting_point: Optional[float] = Field(default=None, ge=0, le=100, description="Permanent wilting point percentage")
    cec: Optional[float] = Field(default=None, ge=0, description="Cation Exchange Capacity in meq/100g")
    
    # Texture breakdown (percentages)
    sand_pct: Optional[float] = Field(default=None, ge=0, le=100, description="Sand percentage")
    silt_pct: Optional[float] = Field(default=None, ge=0, le=100, description="Silt percentage")
    clay_pct: Optional[float] = Field(default=None, ge=0, le=100, description="Clay percentage")
    
    # Secondary nutrients (ppm or mg/kg)
    soil_ca_ppm: Optional[float] = Field(default=None, ge=0, description="Calcium in ppm")
    soil_mg_ppm: Optional[float] = Field(default=None, ge=0, description="Magnesium in ppm")
    soil_s_ppm: Optional[float] = Field(default=None, ge=0, description="Sulfur in ppm")
    soil_na_ppm: Optional[float] = Field(default=None, ge=0, description="Sodium in ppm")
    
    # Micronutrients (ppm or mg/kg)
    soil_fe_ppm: Optional[float] = Field(default=None, ge=0, description="Iron in ppm")
    soil_zn_ppm: Optional[float] = Field(default=None, ge=0, description="Zinc in ppm")
    soil_cu_ppm: Optional[float] = Field(default=None, ge=0, description="Copper in ppm")
    soil_mn_ppm: Optional[float] = Field(default=None, ge=0, description="Manganese in ppm")
    soil_b_ppm: Optional[float] = Field(default=None, ge=0, description="Boron in ppm")
    
    # Anions (meq/L for saturated extract)
    soil_no3_meq_l: Optional[float] = Field(default=None, ge=0, description="Nitrates in meq/L")
    soil_so4_meq_l: Optional[float] = Field(default=None, ge=0, description="Sulfates in meq/L")
    soil_cl_meq_l: Optional[float] = Field(default=None, ge=0, description="Chlorides in meq/L")
    soil_hco3_meq_l: Optional[float] = Field(default=None, ge=0, description="Bicarbonates in meq/L")
    soil_co3_meq_l: Optional[float] = Field(default=None, ge=0, description="Carbonates in meq/L")
    
    # Cations (meq/L for saturated extract)
    soil_ca_meq_l: Optional[float] = Field(default=None, ge=0, description="Calcium in meq/L")
    soil_mg_meq_l: Optional[float] = Field(default=None, ge=0, description="Magnesium in meq/L")
    soil_k_meq_l: Optional[float] = Field(default=None, ge=0, description="Potassium in meq/L")
    soil_na_meq_l: Optional[float] = Field(default=None, ge=0, description="Sodium in meq/L")


class SoilOutput(BaseModel):
    """Output model for soil fertilization calculation."""
    method: str
    inputs: Dict[str, Any]
    requirements_kg_ha: Dict[str, float]
    build_up_kg_ha: Dict[str, float]
    soil_credit_kg_ha: Dict[str, float]
    fertilizer_kg_ha: Dict[str, float]
    blend: Optional[Dict[str, float]] = None
    warnings: Optional[List[str]] = None


class CustomBlendInput(BaseModel):
    """Input for custom product blend calculation."""
    n_required: float = Field(..., ge=0, description="N requirement in kg/ha")
    p2o5_required: float = Field(..., ge=0, description="P2O5 requirement in kg/ha")
    k2o_required: float = Field(..., ge=0, description="K2O requirement in kg/ha")
    n_product_slug: Optional[str] = Field(None, description="Nitrogen product slug")
    p_product_slug: Optional[str] = Field(None, description="Phosphorus product slug")
    k_product_slug: Optional[str] = Field(None, description="Potassium product slug")
    application_type: str = Field(default="soil", description="Application type")


class CustomBlendOutput(BaseModel):
    """Output for custom product blend calculation."""
    products: List[Dict[str, Any]]
    coverage: Dict[str, float]
    requirements: Dict[str, float]
    warnings: List[str]


class FoliarProduct(BaseModel):
    """Foliar fertilizer product composition."""
    name: str
    n_pct: float = Field(default=0, ge=0, le=100)
    p2o5_pct: float = Field(default=0, ge=0, le=100)
    k2o_pct: float = Field(default=0, ge=0, le=100)
    micros: Optional[Dict[str, float]] = Field(default_factory=dict)


class FoliarInput(BaseModel):
    """Input model for foliar fertilization program."""
    crop_slug: str
    stage: str = Field(..., description="Phenological stage (e.g., 'V6-V8', 'VT-R1')")
    objective: str = Field(
        default="prevencion",
        description="Objective: 'prevencion', 'correccion', 'estimulacion'"
    )
    volume_l_ha: float = Field(..., gt=0, description="Spray volume in L/ha")
    product: FoliarProduct
    water_ph: float = Field(default=7.0, ge=0, le=14, description="Water pH")
    water_ec_dS_m: float = Field(default=0.5, ge=0, description="Water EC in dS/m")
    temp_c: float = Field(default=25.0, description="Application temperature in °C")
    rh_pct: float = Field(default=50.0, ge=0, le=100, description="Relative humidity %")


class FoliarOutput(BaseModel):
    """Output model for foliar fertilization program."""
    stage: str
    volume_l_ha: float
    target_pct: Dict[str, float]
    product_dose_l_ha: float
    delivered_nutrients_kg_ha: Dict[str, float]
    warnings: List[str]
    compatibility: List[str]


class AIInput(BaseModel):
    """Input for AI interpretation service."""
    language: str = Field(default="es", description="Response language")
    crop_name: str
    soil_result: Optional[Dict[str, Any]] = None
    foliar_result: Optional[Dict[str, Any]] = None
    custom_blend: Optional[Dict[str, Any]] = None
    user_notes: Optional[str] = Field(default="", description="Additional user context")


class AIOutput(BaseModel):
    """Output from AI interpretation service."""
    message: str


class CropConfig(BaseModel):
    """Crop configuration with extraction coefficients."""
    slug: str
    name: str
    name_es: str
    n_per_t: float = Field(..., description="N extraction kg/t")
    p2o5_per_t: float = Field(..., description="P₂O₅ extraction kg/t")
    k2o_per_t: float = Field(..., description="K₂O extraction kg/t")
    description: Optional[str] = None


class ThresholdConfig(BaseModel):
    """Critical threshold configuration."""
    nutrient: str
    method: str
    critical_ppm: float
    low_ppm: float
    medium_ppm: float
    high_ppm: float
    unit: str = "ppm"


class FoliarRangeConfig(BaseModel):
    """Safe foliar concentration ranges."""
    crop_slug: str
    stage: str
    n_pct_min: float
    n_pct_max: float
    p2o5_pct_min: float
    p2o5_pct_max: float
    k2o_pct_min: float
    k2o_pct_max: float
    volume_l_ha_min: float
    volume_l_ha_max: float


class SettingsConfig(BaseModel):
    """Default settings configuration."""
    default_depth_cm: float = 20.0
    default_bulk_density_g_cm3: float = 1.3
    default_nue_n: float = 0.6
    default_nue_p2o5: float = 0.5
    default_nue_k2o: float = 0.6
    default_build_up_factor: float = 1.0


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str = "1.0.0"
    message: Optional[str] = None


# Report Schemas
class ReportCreate(BaseModel):
    """Schema for creating a new report."""
    project_id: int
    report_type: str = Field(..., description="Type: 'project_complete', 'soil_analysis', 'fertilization_plan', etc.")
    file_path: str
    file_size_bytes: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    report_metadata: Optional[Dict[str, Any]] = None


class ProjectReportPayload(BaseModel):
    """Payload for generating a project report with optional calculation results."""
    calculation_results: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    """Schema for report response."""
    id: int
    project_id: int
    report_type: str
    file_path: str
    file_size_bytes: Optional[int]
    title: Optional[str]
    description: Optional[str]
    report_metadata: Optional[Dict[str, Any]]
    generated_at: datetime
    
    class Config:
        from_attributes = True


# Project Schema Updates
class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    name: str = Field(..., min_length=1, max_length=200)
    location: Optional[str] = None
    total_area_ha: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None  # GeoJSON polygon
    module_type: ModuleType = Field(default=ModuleType.SOIL, description="Project module type: soil or hydroponics")


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    location: Optional[str] = None
    total_area_ha: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None
    module_type: Optional[ModuleType] = Field(None, description="Project module type: soil or hydroponics")


class ProjectResponse(BaseModel):
    """Schema for project response."""
    id: int
    user_id: int
    name: str
    location: Optional[str]
    total_area_ha: Optional[float]
    description: Optional[str]
    geometry: Optional[Dict[str, Any]]
    module_type: ModuleType
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
