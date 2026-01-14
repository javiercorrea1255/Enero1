"""
User Extraction Curves CRUD router.
Allows users to create and manage custom extraction curves for fertirrigation calculations.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.database_models import User, UserExtractionCurve
from app.schemas.fertiirrigation_schemas import (
    UserExtractionCurveCreate,
    UserExtractionCurveUpdate,
    UserExtractionCurveResponse,
    UserExtractionCurveList,
    UserExtractionCurveSummary
)
from app.core.auth import get_current_active_user

router = APIRouter(prefix="/api/user-extraction-curves", tags=["user-extraction-curves"])


@router.post("", response_model=UserExtractionCurveResponse, status_code=status.HTTP_201_CREATED)
async def create_extraction_curve(
    data: UserExtractionCurveCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new custom extraction curve for the current user."""
    stages_data = [stage.model_dump() for stage in data.stages]
    
    new_curve = UserExtractionCurve(
        user_id=current_user.id,
        name=data.name,
        scientific_name=data.scientific_name,
        description=data.description,
        cycle_days_min=data.cycle_days_min,
        cycle_days_max=data.cycle_days_max,
        yield_reference_ton_ha=data.yield_reference_ton_ha,
        total_n_kg_ha=data.total_n_kg_ha,
        total_p2o5_kg_ha=data.total_p2o5_kg_ha,
        total_k2o_kg_ha=data.total_k2o_kg_ha,
        total_ca_kg_ha=data.total_ca_kg_ha,
        total_mg_kg_ha=data.total_mg_kg_ha,
        total_s_kg_ha=data.total_s_kg_ha,
        stages=stages_data,
        sensitivity_notes=data.sensitivity_notes,
        is_active=True
    )
    
    db.add(new_curve)
    db.commit()
    db.refresh(new_curve)
    
    return _curve_to_response(new_curve)


@router.get("", response_model=UserExtractionCurveList)
async def list_extraction_curves(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all custom extraction curves for the current user."""
    curves = db.query(UserExtractionCurve).filter(
        UserExtractionCurve.user_id == current_user.id,
        UserExtractionCurve.is_active == True
    ).order_by(desc(UserExtractionCurve.created_at)).all()
    
    return UserExtractionCurveList(
        items=[_curve_to_response(c) for c in curves],
        total=len(curves)
    )


@router.get("/{curve_id}", response_model=UserExtractionCurveResponse)
async def get_extraction_curve(
    curve_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific extraction curve by ID."""
    curve = db.query(UserExtractionCurve).filter(
        UserExtractionCurve.id == curve_id,
        UserExtractionCurve.user_id == current_user.id
    ).first()
    
    if not curve:
        raise HTTPException(status_code=404, detail="Extraction curve not found")
    
    return _curve_to_response(curve)


@router.put("/{curve_id}", response_model=UserExtractionCurveResponse)
async def update_extraction_curve(
    curve_id: int,
    data: UserExtractionCurveUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing extraction curve."""
    curve = db.query(UserExtractionCurve).filter(
        UserExtractionCurve.id == curve_id,
        UserExtractionCurve.user_id == current_user.id
    ).first()
    
    if not curve:
        raise HTTPException(status_code=404, detail="Extraction curve not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    if 'stages' in update_data and update_data['stages'] is not None:
        update_data['stages'] = [s.model_dump() if hasattr(s, 'model_dump') else s for s in update_data['stages']]
    
    for field, value in update_data.items():
        setattr(curve, field, value)
    
    db.commit()
    db.refresh(curve)
    
    return _curve_to_response(curve)


@router.delete("/{curve_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_extraction_curve(
    curve_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete (soft-delete) an extraction curve."""
    curve = db.query(UserExtractionCurve).filter(
        UserExtractionCurve.id == curve_id,
        UserExtractionCurve.user_id == current_user.id
    ).first()
    
    if not curve:
        raise HTTPException(status_code=404, detail="Extraction curve not found")
    
    curve.is_active = False
    db.commit()
    
    return None


@router.post("/{curve_id}/duplicate", response_model=UserExtractionCurveResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_extraction_curve(
    curve_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Duplicate an existing extraction curve."""
    original = db.query(UserExtractionCurve).filter(
        UserExtractionCurve.id == curve_id,
        UserExtractionCurve.user_id == current_user.id
    ).first()
    
    if not original:
        raise HTTPException(status_code=404, detail="Extraction curve not found")
    
    new_curve = UserExtractionCurve(
        user_id=current_user.id,
        name=f"{original.name} (Copia)",
        scientific_name=original.scientific_name,
        description=original.description,
        cycle_days_min=original.cycle_days_min,
        cycle_days_max=original.cycle_days_max,
        yield_reference_ton_ha=original.yield_reference_ton_ha,
        total_n_kg_ha=original.total_n_kg_ha,
        total_p2o5_kg_ha=original.total_p2o5_kg_ha,
        total_k2o_kg_ha=original.total_k2o_kg_ha,
        total_ca_kg_ha=original.total_ca_kg_ha,
        total_mg_kg_ha=original.total_mg_kg_ha,
        total_s_kg_ha=original.total_s_kg_ha,
        stages=original.stages,
        sensitivity_notes=original.sensitivity_notes,
        is_active=True
    )
    
    db.add(new_curve)
    db.commit()
    db.refresh(new_curve)
    
    return _curve_to_response(new_curve)


def _curve_to_response(curve: UserExtractionCurve) -> UserExtractionCurveResponse:
    """Convert database model to response schema."""
    return UserExtractionCurveResponse(
        id=curve.id,
        name=curve.name,
        scientific_name=curve.scientific_name,
        description=curve.description,
        cycle_days_min=curve.cycle_days_min,
        cycle_days_max=curve.cycle_days_max,
        yield_reference_ton_ha=curve.yield_reference_ton_ha,
        total_n_kg_ha=curve.total_n_kg_ha,
        total_p2o5_kg_ha=curve.total_p2o5_kg_ha,
        total_k2o_kg_ha=curve.total_k2o_kg_ha,
        total_ca_kg_ha=curve.total_ca_kg_ha,
        total_mg_kg_ha=curve.total_mg_kg_ha,
        total_s_kg_ha=curve.total_s_kg_ha,
        stages=curve.stages,
        sensitivity_notes=curve.sensitivity_notes,
        is_active=curve.is_active,
        created_at=curve.created_at,
        updated_at=curve.updated_at
    )
