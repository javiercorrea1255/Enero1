"""
My Soil Analyses CRUD router (Independent FertiIrrigation Module).
Allows users to save and manage their soil analysis data.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.database_models import User, MySoilAnalysis
from app.schemas.fertiirrigation_schemas import (
    MySoilAnalysisCreate,
    MySoilAnalysisUpdate,
    MySoilAnalysisResponse,
    MySoilAnalysisList
)
from app.core.auth import get_current_active_user

router = APIRouter(prefix="/api/my-soil-analyses", tags=["my-soil-analyses"])


@router.post("", response_model=MySoilAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_soil_analysis(
    data: MySoilAnalysisCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new soil analysis for the current user."""
    new_analysis = MySoilAnalysis(
        user_id=current_user.id,
        name=data.name,
        laboratory=data.laboratory,
        analysis_date=data.analysis_date,
        texture=data.texture,
        bulk_density=data.bulk_density,
        depth_cm=data.depth_cm,
        ph=data.ph,
        ec_ds_m=data.ec_ds_m,
        organic_matter_pct=data.organic_matter_pct,
        n_total_pct=data.n_total_pct,
        n_no3_ppm=data.n_no3_ppm,
        n_nh4_ppm=data.n_nh4_ppm,
        p_ppm=data.p_ppm,
        k_ppm=data.k_ppm,
        ca_ppm=data.ca_ppm,
        mg_ppm=data.mg_ppm,
        s_ppm=data.s_ppm,
        na_ppm=data.na_ppm,
        cic_cmol_kg=data.cic_cmol_kg,
        ca_exch=data.ca_exch,
        mg_exch=data.mg_exch,
        k_exch=data.k_exch,
        na_exch=data.na_exch,
        fe_ppm=data.fe_ppm,
        mn_ppm=data.mn_ppm,
        zn_ppm=data.zn_ppm,
        cu_ppm=data.cu_ppm,
        b_ppm=data.b_ppm,
        caco3_pct=data.caco3_pct,
        notes=data.notes
    )
    
    db.add(new_analysis)
    db.commit()
    db.refresh(new_analysis)
    
    return MySoilAnalysisResponse.model_validate(new_analysis)


@router.get("", response_model=MySoilAnalysisList)
async def list_soil_analyses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all soil analyses for the current user."""
    analyses = db.query(MySoilAnalysis).filter(
        MySoilAnalysis.user_id == current_user.id
    ).order_by(desc(MySoilAnalysis.created_at)).all()
    
    return MySoilAnalysisList(
        items=[MySoilAnalysisResponse.model_validate(a) for a in analyses],
        total=len(analyses)
    )


@router.get("/{analysis_id}", response_model=MySoilAnalysisResponse)
async def get_soil_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific soil analysis by ID."""
    analysis = db.query(MySoilAnalysis).filter(
        MySoilAnalysis.id == analysis_id,
        MySoilAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Soil analysis not found")
    
    return MySoilAnalysisResponse.model_validate(analysis)


@router.put("/{analysis_id}", response_model=MySoilAnalysisResponse)
async def update_soil_analysis(
    analysis_id: int,
    data: MySoilAnalysisUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing soil analysis."""
    analysis = db.query(MySoilAnalysis).filter(
        MySoilAnalysis.id == analysis_id,
        MySoilAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Soil analysis not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(analysis, field, value)
    
    db.commit()
    db.refresh(analysis)
    
    return MySoilAnalysisResponse.model_validate(analysis)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_soil_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a soil analysis."""
    analysis = db.query(MySoilAnalysis).filter(
        MySoilAnalysis.id == analysis_id,
        MySoilAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Soil analysis not found")
    
    db.delete(analysis)
    db.commit()
    
    return None
