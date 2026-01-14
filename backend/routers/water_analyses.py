"""API Router for Water Analyses - allows users to save and reuse water analysis data."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from app.database import get_db
from app.models.database_models import WaterAnalysis, User
from app.schemas.water_analysis_schemas import (
    WaterAnalysisCreate,
    WaterAnalysisUpdate,
    WaterAnalysisResponse,
    WaterAnalysisList
)
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/water-analyses", tags=["Water Analyses"])


@router.get("", response_model=WaterAnalysisList)
async def list_water_analyses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all water analyses for the current user."""
    analyses = db.query(WaterAnalysis).filter(
        WaterAnalysis.user_id == current_user.id
    ).order_by(desc(WaterAnalysis.created_at)).all()
    
    return WaterAnalysisList(items=analyses, total=len(analyses))


@router.get("/{analysis_id}", response_model=WaterAnalysisResponse)
async def get_water_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific water analysis by ID."""
    analysis = db.query(WaterAnalysis).filter(
        WaterAnalysis.id == analysis_id,
        WaterAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Análisis de agua no encontrado"
        )
    
    return analysis


@router.post("", response_model=WaterAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_water_analysis(
    data: WaterAnalysisCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new water analysis."""
    analysis = WaterAnalysis(
        user_id=current_user.id,
        **data.model_dump()
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    return analysis


@router.put("/{analysis_id}", response_model=WaterAnalysisResponse)
async def update_water_analysis(
    analysis_id: int,
    data: WaterAnalysisUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing water analysis."""
    analysis = db.query(WaterAnalysis).filter(
        WaterAnalysis.id == analysis_id,
        WaterAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Análisis de agua no encontrado"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(analysis, field, value)
    
    db.commit()
    db.refresh(analysis)
    
    return analysis


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_water_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a water analysis."""
    analysis = db.query(WaterAnalysis).filter(
        WaterAnalysis.id == analysis_id,
        WaterAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Análisis de agua no encontrado"
        )
    
    db.delete(analysis)
    db.commit()
    
    return None
