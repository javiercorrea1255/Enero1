"""
API endpoints for user custom fertilizers.
Enables users to create, manage and use custom fertilizers in Hydroponics and Fertirrigation modules.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.core.auth import get_current_active_user
from app.models.database_models import User
from app.models.hydro_ions_models import UserCustomFertilizer

router = APIRouter(prefix="/api/custom-fertilizers", tags=["Custom Fertilizers"])


class CustomFertilizerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    form: str = Field(default="solid", pattern="^(solid|liquid)$")
    
    no3_meq: float = Field(default=0.0, ge=0)
    nh4_meq: float = Field(default=0.0, ge=0)
    h2po4_meq: float = Field(default=0.0, ge=0)
    k_meq: float = Field(default=0.0, ge=0)
    ca_meq: float = Field(default=0.0, ge=0)
    mg_meq: float = Field(default=0.0, ge=0)
    so4_meq: float = Field(default=0.0, ge=0)
    
    fe_ppm: float = Field(default=0.0, ge=0)
    mn_ppm: float = Field(default=0.0, ge=0)
    zn_ppm: float = Field(default=0.0, ge=0)
    cu_ppm: float = Field(default=0.0, ge=0)
    b_ppm: float = Field(default=0.0, ge=0)
    mo_ppm: float = Field(default=0.0, ge=0)
    
    density_g_ml: Optional[float] = Field(default=None, ge=0)
    price_per_unit: Optional[float] = Field(default=None, ge=0)
    currency: str = Field(default="MXN", max_length=3)
    stock_tank: Optional[str] = Field(default=None, pattern="^[AB]$")


class CustomFertilizerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    form: Optional[str] = Field(default=None, pattern="^(solid|liquid)$")
    
    no3_meq: Optional[float] = Field(default=None, ge=0)
    nh4_meq: Optional[float] = Field(default=None, ge=0)
    h2po4_meq: Optional[float] = Field(default=None, ge=0)
    k_meq: Optional[float] = Field(default=None, ge=0)
    ca_meq: Optional[float] = Field(default=None, ge=0)
    mg_meq: Optional[float] = Field(default=None, ge=0)
    so4_meq: Optional[float] = Field(default=None, ge=0)
    
    fe_ppm: Optional[float] = Field(default=None, ge=0)
    mn_ppm: Optional[float] = Field(default=None, ge=0)
    zn_ppm: Optional[float] = Field(default=None, ge=0)
    cu_ppm: Optional[float] = Field(default=None, ge=0)
    b_ppm: Optional[float] = Field(default=None, ge=0)
    mo_ppm: Optional[float] = Field(default=None, ge=0)
    
    density_g_ml: Optional[float] = Field(default=None, ge=0)
    price_per_unit: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, max_length=3)
    stock_tank: Optional[str] = Field(default=None, pattern="^[AB]$")
    is_active: Optional[bool] = None


class CustomFertilizerResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    form: str
    
    no3_meq: float
    nh4_meq: float
    h2po4_meq: float
    k_meq: float
    ca_meq: float
    mg_meq: float
    so4_meq: float
    
    fe_ppm: float
    mn_ppm: float
    zn_ppm: float
    cu_ppm: float
    b_ppm: float
    mo_ppm: float
    
    density_g_ml: Optional[float]
    price_per_unit: Optional[float]
    currency: str
    stock_tank: Optional[str]
    is_active: bool
    
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


def fertilizer_to_response(fert: UserCustomFertilizer) -> CustomFertilizerResponse:
    return CustomFertilizerResponse(
        id=fert.id,
        name=fert.name,
        description=fert.description,
        form=fert.form,
        no3_meq=fert.no3_meq or 0.0,
        nh4_meq=fert.nh4_meq or 0.0,
        h2po4_meq=fert.h2po4_meq or 0.0,
        k_meq=fert.k_meq or 0.0,
        ca_meq=fert.ca_meq or 0.0,
        mg_meq=fert.mg_meq or 0.0,
        so4_meq=fert.so4_meq or 0.0,
        fe_ppm=fert.fe_ppm or 0.0,
        mn_ppm=fert.mn_ppm or 0.0,
        zn_ppm=fert.zn_ppm or 0.0,
        cu_ppm=fert.cu_ppm or 0.0,
        b_ppm=fert.b_ppm or 0.0,
        mo_ppm=fert.mo_ppm or 0.0,
        density_g_ml=fert.density_g_ml,
        price_per_unit=fert.price_per_unit,
        currency=fert.currency or "MXN",
        stock_tank=fert.stock_tank,
        is_active=fert.is_active if fert.is_active is not None else True,
        created_at=fert.created_at,
        updated_at=fert.updated_at
    )


@router.get("", response_model=List[CustomFertilizerResponse])
async def get_custom_fertilizers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all custom fertilizers for the current user."""
    fertilizers = db.query(UserCustomFertilizer).filter(
        UserCustomFertilizer.user_id == current_user.id,
        UserCustomFertilizer.is_active == True
    ).order_by(UserCustomFertilizer.name).all()
    
    return [fertilizer_to_response(f) for f in fertilizers]


@router.get("/all", response_model=List[CustomFertilizerResponse])
async def get_all_custom_fertilizers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all custom fertilizers including inactive ones."""
    fertilizers = db.query(UserCustomFertilizer).filter(
        UserCustomFertilizer.user_id == current_user.id
    ).order_by(UserCustomFertilizer.name).all()
    
    return [fertilizer_to_response(f) for f in fertilizers]


@router.get("/format/hydro-catalog", response_model=List[dict])
async def get_custom_fertilizers_hydro_format(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get custom fertilizers formatted for the hydroponics calculator catalog.
    Returns fertilizers in the same format as hydro_fertilizers.json.
    """
    fertilizers = db.query(UserCustomFertilizer).filter(
        UserCustomFertilizer.user_id == current_user.id,
        UserCustomFertilizer.is_active == True
    ).all()
    
    result = []
    for fert in fertilizers:
        meq_per_gram = {}
        if fert.no3_meq and fert.no3_meq > 0:
            meq_per_gram["NO3"] = fert.no3_meq
        if fert.nh4_meq and fert.nh4_meq > 0:
            meq_per_gram["NH4"] = fert.nh4_meq
        if fert.h2po4_meq and fert.h2po4_meq > 0:
            meq_per_gram["H2PO4"] = fert.h2po4_meq
        if fert.k_meq and fert.k_meq > 0:
            meq_per_gram["K"] = fert.k_meq
        if fert.ca_meq and fert.ca_meq > 0:
            meq_per_gram["Ca"] = fert.ca_meq
        if fert.mg_meq and fert.mg_meq > 0:
            meq_per_gram["Mg"] = fert.mg_meq
        if fert.so4_meq and fert.so4_meq > 0:
            meq_per_gram["SO42"] = fert.so4_meq
        
        catalog_entry = {
            "id": f"custom_{fert.id}",
            "name": fert.name,
            "type": "salt",
            "form": fert.form,
            "is_custom": True,
            "custom_id": fert.id,
            "meq_per_gram": meq_per_gram,
            "typical_cost_mxn_per_kg": fert.price_per_unit if fert.form == "solid" else None,
            "typical_cost_mxn_per_liter": fert.price_per_unit if fert.form == "liquid" else None,
            "density_g_ml": fert.density_g_ml,
            "stock_tank": fert.stock_tank
        }
        
        if any([fert.fe_ppm, fert.mn_ppm, fert.zn_ppm, fert.cu_ppm, fert.b_ppm, fert.mo_ppm]):
            catalog_entry["micronutrients"] = {
                "Fe": fert.fe_ppm or 0,
                "Mn": fert.mn_ppm or 0,
                "Zn": fert.zn_ppm or 0,
                "Cu": fert.cu_ppm or 0,
                "B": fert.b_ppm or 0,
                "Mo": fert.mo_ppm or 0
            }
        
        result.append(catalog_entry)
    
    return result


@router.get("/format/fertiirrigation-catalog")
async def get_custom_fertilizers_fertiirrigation_format(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get custom fertilizers formatted for the fertirrigation calculator.
    Returns fertilizers in the same format as fertiirrigation fertilizers.
    """
    fertilizers = db.query(UserCustomFertilizer).filter(
        UserCustomFertilizer.user_id == current_user.id,
        UserCustomFertilizer.is_active == True
    ).all()
    
    result = []
    for fert in fertilizers:
        slug = f"custom_{fert.id}"
        
        ions = {}
        if fert.no3_meq and fert.no3_meq > 0:
            ions["NO3"] = fert.no3_meq
        if fert.nh4_meq and fert.nh4_meq > 0:
            ions["NH4"] = fert.nh4_meq
        if fert.h2po4_meq and fert.h2po4_meq > 0:
            ions["H2PO4"] = fert.h2po4_meq
        if fert.k_meq and fert.k_meq > 0:
            ions["K"] = fert.k_meq
        if fert.ca_meq and fert.ca_meq > 0:
            ions["Ca"] = fert.ca_meq
        if fert.mg_meq and fert.mg_meq > 0:
            ions["Mg"] = fert.mg_meq
        if fert.so4_meq and fert.so4_meq > 0:
            ions["SO42"] = fert.so4_meq
        
        catalog_entry = {
            "slug": slug,
            "name": fert.name,
            "formula": fert.description or fert.name,
            "type": "custom",
            "form": fert.form,
            "is_custom": True,
            "custom_id": fert.id,
            "ions_meq_per_g": ions,
            "solubility_g_per_l": None,
            "typical_price_per_kg": fert.price_per_unit if fert.form == "solid" else None,
            "typical_price_per_l": fert.price_per_unit if fert.form == "liquid" else None,
            "stock_tank": fert.stock_tank,
            "tank": fert.stock_tank
        }
        
        if any([fert.fe_ppm, fert.mn_ppm, fert.zn_ppm, fert.cu_ppm, fert.b_ppm, fert.mo_ppm]):
            catalog_entry["micronutrients"] = {
                "Fe": fert.fe_ppm or 0,
                "Mn": fert.mn_ppm or 0,
                "Zn": fert.zn_ppm or 0,
                "Cu": fert.cu_ppm or 0,
                "B": fert.b_ppm or 0,
                "Mo": fert.mo_ppm or 0
            }
        
        result.append(catalog_entry)
    
    return {"fertilizers": result}


@router.get("/{fertilizer_id}", response_model=CustomFertilizerResponse)
async def get_custom_fertilizer(
    fertilizer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific custom fertilizer by ID."""
    fertilizer = db.query(UserCustomFertilizer).filter(
        UserCustomFertilizer.id == fertilizer_id,
        UserCustomFertilizer.user_id == current_user.id
    ).first()
    
    if not fertilizer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fertilizante no encontrado"
        )
    
    return fertilizer_to_response(fertilizer)


@router.post("", response_model=CustomFertilizerResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_fertilizer(
    data: CustomFertilizerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new custom fertilizer."""
    existing = db.query(UserCustomFertilizer).filter(
        UserCustomFertilizer.user_id == current_user.id,
        UserCustomFertilizer.name == data.name,
        UserCustomFertilizer.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un fertilizante con el nombre '{data.name}'"
        )
    
    fertilizer = UserCustomFertilizer(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        form=data.form,
        no3_meq=data.no3_meq,
        nh4_meq=data.nh4_meq,
        h2po4_meq=data.h2po4_meq,
        k_meq=data.k_meq,
        ca_meq=data.ca_meq,
        mg_meq=data.mg_meq,
        so4_meq=data.so4_meq,
        fe_ppm=data.fe_ppm,
        mn_ppm=data.mn_ppm,
        zn_ppm=data.zn_ppm,
        cu_ppm=data.cu_ppm,
        b_ppm=data.b_ppm,
        mo_ppm=data.mo_ppm,
        density_g_ml=data.density_g_ml,
        price_per_unit=data.price_per_unit,
        currency=data.currency,
        stock_tank=data.stock_tank,
        is_active=True
    )
    
    db.add(fertilizer)
    db.commit()
    db.refresh(fertilizer)
    
    return fertilizer_to_response(fertilizer)


@router.put("/{fertilizer_id}", response_model=CustomFertilizerResponse)
async def update_custom_fertilizer(
    fertilizer_id: int,
    data: CustomFertilizerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing custom fertilizer."""
    fertilizer = db.query(UserCustomFertilizer).filter(
        UserCustomFertilizer.id == fertilizer_id,
        UserCustomFertilizer.user_id == current_user.id
    ).first()
    
    if not fertilizer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fertilizante no encontrado"
        )
    
    if data.name and data.name != fertilizer.name:
        existing = db.query(UserCustomFertilizer).filter(
            UserCustomFertilizer.user_id == current_user.id,
            UserCustomFertilizer.name == data.name,
            UserCustomFertilizer.is_active == True,
            UserCustomFertilizer.id != fertilizer_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un fertilizante con el nombre '{data.name}'"
            )
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(fertilizer, field, value)
    
    db.commit()
    db.refresh(fertilizer)
    
    return fertilizer_to_response(fertilizer)


@router.delete("/{fertilizer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_fertilizer(
    fertilizer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a custom fertilizer (soft delete by setting is_active=False)."""
    fertilizer = db.query(UserCustomFertilizer).filter(
        UserCustomFertilizer.id == fertilizer_id,
        UserCustomFertilizer.user_id == current_user.id
    ).first()
    
    if not fertilizer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fertilizante no encontrado"
        )
    
    fertilizer.is_active = False
    db.commit()
    
    return None


@router.post("/{fertilizer_id}/restore", response_model=CustomFertilizerResponse)
async def restore_custom_fertilizer(
    fertilizer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Restore a deleted custom fertilizer."""
    fertilizer = db.query(UserCustomFertilizer).filter(
        UserCustomFertilizer.id == fertilizer_id,
        UserCustomFertilizer.user_id == current_user.id
    ).first()
    
    if not fertilizer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fertilizante no encontrado"
        )
    
    fertilizer.is_active = True
    db.commit()
    db.refresh(fertilizer)
    
    return fertilizer_to_response(fertilizer)
