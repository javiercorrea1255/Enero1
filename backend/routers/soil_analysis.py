"""
Soil analysis CRUD router.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.database_models import User, Plot, Project, SoilAnalysis
from app.models.auth_schemas import SoilAnalysisCreate, SoilAnalysisResponse
from app.core.auth import get_current_active_user

router = APIRouter(prefix="/api/soil-analysis", tags=["soil-analysis"])


@router.post("", response_model=SoilAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_soil_analysis(
    data: SoilAnalysisCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new soil analysis for a plot."""
    plot = db.query(Plot).join(Project).filter(
        Plot.id == data.plot_id,
        Project.user_id == current_user.id
    ).first()
    
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    
    new_analysis = SoilAnalysis(
        plot_id=data.plot_id,
        analysis_date=data.analysis_date,
        laboratory=data.laboratory,
        n_kg_ha=data.n_kg_ha,
        p_ppm=data.p_ppm,
        k_ppm=data.k_ppm,
        ph=data.ph,
        organic_matter_pct=data.organic_matter_pct,
        texture=data.texture,
        bulk_density_g_cm3=data.bulk_density_g_cm3,
        depth_cm=data.depth_cm,
        ec_dS_m=data.ec_dS_m,
        ca_ppm=data.ca_ppm,
        mg_ppm=data.mg_ppm,
        s_ppm=data.s_ppm,
        zn_ppm=data.zn_ppm,
        fe_ppm=data.fe_ppm,
        mn_ppm=data.mn_ppm,
        cu_ppm=data.cu_ppm,
        b_ppm=data.b_ppm,
        notes=data.notes
    )
    
    db.add(new_analysis)
    db.commit()
    db.refresh(new_analysis)
    
    return SoilAnalysisResponse.model_validate(new_analysis)


@router.get("/plot/{plot_id}", response_model=List[SoilAnalysisResponse])
async def get_plot_analyses(
    plot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all soil analyses for a plot."""
    plot = db.query(Plot).join(Project).filter(
        Plot.id == plot_id,
        Project.user_id == current_user.id
    ).first()
    
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    
    analyses = db.query(SoilAnalysis).filter(
        SoilAnalysis.plot_id == plot_id
    ).order_by(SoilAnalysis.analysis_date.desc()).all()
    
    return [SoilAnalysisResponse.model_validate(a) for a in analyses]


@router.get("/{analysis_id}", response_model=SoilAnalysisResponse)
async def get_soil_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific soil analysis."""
    analysis = db.query(SoilAnalysis).join(Plot).join(Project).filter(
        SoilAnalysis.id == analysis_id,
        Project.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Soil analysis not found")
    
    return SoilAnalysisResponse.model_validate(analysis)


@router.put("/{analysis_id}", response_model=SoilAnalysisResponse)
async def update_soil_analysis(
    analysis_id: int,
    data: SoilAnalysisCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing soil analysis."""
    analysis = db.query(SoilAnalysis).join(Plot).join(Project).filter(
        SoilAnalysis.id == analysis_id,
        Project.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Soil analysis not found")
    
    analysis.analysis_date = data.analysis_date
    analysis.laboratory = data.laboratory
    analysis.n_kg_ha = data.n_kg_ha
    analysis.p_ppm = data.p_ppm
    analysis.k_ppm = data.k_ppm
    analysis.ph = data.ph
    analysis.organic_matter_pct = data.organic_matter_pct
    analysis.texture = data.texture
    analysis.bulk_density_g_cm3 = data.bulk_density_g_cm3
    analysis.depth_cm = data.depth_cm
    analysis.ec_dS_m = data.ec_dS_m
    analysis.ca_ppm = data.ca_ppm
    analysis.mg_ppm = data.mg_ppm
    analysis.s_ppm = data.s_ppm
    analysis.zn_ppm = data.zn_ppm
    analysis.fe_ppm = data.fe_ppm
    analysis.mn_ppm = data.mn_ppm
    analysis.cu_ppm = data.cu_ppm
    analysis.b_ppm = data.b_ppm
    analysis.notes = data.notes
    
    db.commit()
    db.refresh(analysis)
    
    return SoilAnalysisResponse.model_validate(analysis)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_soil_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a soil analysis."""
    analysis = db.query(SoilAnalysis).join(Plot).join(Project).filter(
        SoilAnalysis.id == analysis_id,
        Project.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Soil analysis not found")
    
    db.delete(analysis)
    db.commit()
