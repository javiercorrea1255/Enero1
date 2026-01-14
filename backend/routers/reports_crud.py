"""
Reports CRUD router for managing generated PDF reports.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os
from datetime import datetime
import logging
from app.database import get_db
from app.models.database_models import User, Project, Report
from app.models.schemas import ReportCreate, ReportResponse, ProjectReportPayload
from app.core.auth import get_current_active_user
from app.services.enhanced_pdf_service import EnhancedPDFService
from app.services.email_service import email_service

router = APIRouter(prefix="/api/reports", tags=["reports"])
logger = logging.getLogger(__name__)

# Ensure reports directory exists
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


# Background task helper for sending emails
async def send_report_email_background(
    to_email: str,
    user_name: str,
    module_name: str,
    report_title: str,
    pdf_bytes: bytes,
    pdf_filename: str,
    report_id: int
):
    """Background task to send PDF report via email without blocking the response."""
    try:
        email_sent = await email_service.send_pdf_report_email(
            to_email=to_email,
            user_name=user_name,
            module_name=module_name,
            report_title=report_title,
            pdf_bytes=pdf_bytes,
            pdf_filename=pdf_filename
        )
        
        if email_sent:
            logger.info(f"Email sent successfully to {to_email} for report {report_id}")
        else:
            logger.warning(f"Failed to send email to {to_email} for report {report_id}")
    except Exception as email_error:
        logger.error(f"Error sending email for report {report_id}: {email_error}", exc_info=True)


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new report entry (PDF must be generated separately)."""
    # Verify user owns the project
    project = db.query(Project).filter(
        Project.id == report_data.project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    new_report = Report(
        project_id=report_data.project_id,
        report_type=report_data.report_type,
        file_path=report_data.file_path,
        file_size_bytes=report_data.file_size_bytes,
        title=report_data.title,
        description=report_data.description,
        report_metadata=report_data.report_metadata
    )
    
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    
    return ReportResponse.model_validate(new_report)


@router.get("", response_model=List[ReportResponse])
async def get_user_reports(
    project_id: Optional[int] = None,
    report_type: Optional[str] = None,
    module: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all reports for the current user with optional filtering by module (soil/hydro/hydro_ions)."""
    # Validate module parameter (accept legacy 'hydroponics' for backward compatibility)
    if module and module not in ["soil", "hydro", "hydroponics", "hydro_ions", "fertiirrigation"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid module parameter. Must be 'soil', 'hydro', 'hydro_ions', or 'fertiirrigation', got '{module}'"
        )
    
    # Normalize legacy 'hydroponics' to 'hydro' for internal processing
    if module == "hydroponics":
        module = "hydro"
    
    # Module-to-report_type authoritative mapping
    SOIL_REPORT_TYPES = {
        "fertilization_program",  # NOM-021 calculations
        "soil_analysis",           # Soil analysis reports
        "foliar_analysis",         # Foliar analysis reports
        "roi_simulation",          # ROI simulator reports
        "project_summary"          # Legacy project summaries (soil-based)
    }
    
    HYDRO_REPORT_TYPES = {
        "hydroponics",             # Hydroponics calculator reports (legacy)
        "hydro_calculation",       # Alternative hydro report type
        "nutrient_formulation"     # Nutrient formulation reports
    }
    
    HYDRO_IONS_REPORT_TYPES = {
        "hydro_ions",              # Ion-based hydroponics (Meq/L methodology)
        "ion_balance_calculation"  # Ion balance calculation reports
    }
    
    FERTIIRRIGATION_REPORT_TYPES = {
        "fertiirrigation",         # Fertigation calculator reports
        "fertiirrigation_pdf",     # PDF reports from fertigation module
        "fertiirrigation_excel"    # Excel reports from fertigation module
    }
    
    # Get user's project IDs
    user_project_ids = [p.id for p in db.query(Project.id).filter(
        Project.user_id == current_user.id
    ).all()]
    
    query = db.query(Report).filter(Report.project_id.in_(user_project_ids))
    
    if project_id:
        query = query.filter(Report.project_id == project_id)
    
    if report_type:
        query = query.filter(Report.report_type == report_type)
    
    reports = query.order_by(Report.generated_at.desc()).all()
    
    # Filter by module using ONLY authoritative report_type mapping (no keyword fallbacks)
    if module:
        filtered_reports = []
        
        for report in reports:
            report_type_val = report.report_type or ""
            
            # Strict filtering: ONLY use authoritative mappings, NO keyword heuristics
            if module == "soil" and report_type_val in SOIL_REPORT_TYPES:
                filtered_reports.append(report)
            elif module == "hydro" and report_type_val in HYDRO_REPORT_TYPES:
                filtered_reports.append(report)
            elif module == "hydro_ions" and report_type_val in HYDRO_IONS_REPORT_TYPES:
                filtered_reports.append(report)
            elif module == "fertiirrigation" and report_type_val in FERTIIRRIGATION_REPORT_TYPES:
                filtered_reports.append(report)
            # If report_type is unmapped, it won't appear in ANY module (prevents bleed)
        
        reports = filtered_reports
    
    return [ReportResponse.model_validate(r) for r in reports]


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Verify user owns the project
    project = db.query(Project).filter(
        Project.id == report.project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ReportResponse.model_validate(report)


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download the PDF file for a specific report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Verify user owns the project
    project = db.query(Project).filter(
        Project.id == report.project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if file exists
    file_path = Path(report.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    
    # Return file with proper headers for download
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"{report.title.replace(' ', '_')}.pdf"
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a report entry (does not delete the PDF file)."""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Verify user owns the project
    project = db.query(Project).filter(
        Project.id == report.project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(report)
    db.commit()


@router.post("/project/{project_id}/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_project_report(
    project_id: int,
    background_tasks: BackgroundTasks,
    payload: Optional[ProjectReportPayload] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Orchestrated endpoint: Generate PDF report for a project and create report entry.
    This endpoint generates the actual PDF file, saves it to disk, and creates the database record.
    Accepts optional calculation_results in the request body.
    """
    # 1. Verify user owns the project
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    file_path = None
    try:
        # 2. Generate PDF using EnhancedPDFService
        pdf_service = EnhancedPDFService()
        
        # Create a simple project summary for the PDF
        project_data = {
            "name": project.name,
            "location": project.location or "No especificada",
            "area": project.total_area_ha,
            "description": project.description or "Sin descripción",
            "geometry": project.geometry  # CRITICAL: Pass geometry for map generation
        }
        
        # Add calculation results if provided
        if payload and payload.calculation_results:
            calc_results = payload.calculation_results
            
            # CRITICAL FIX: Sanitize AI recommendations to remove Unicode subscripts
            # that were generated with old code and appear as black boxes in PDFs
            if calc_results.get("ai_recommendations"):
                ai_recs = calc_results["ai_recommendations"]
                
                # Replace Unicode subscripts with ASCII equivalents
                def sanitize_text(text: str) -> str:
                    """Remove Unicode subscripts that cause black boxes in PDFs."""
                    if not text:
                        return text
                    # Replace Unicode subscripts with plain ASCII
                    replacements = {
                        '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
                        '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
                        'P₂O₅': 'P2O5', 'K₂O': 'K2O',  # Common formulas
                    }
                    result = text
                    for old, new in replacements.items():
                        result = result.replace(old, new)
                    return result
                
                # Sanitize interpretation text
                if ai_recs.get("interpretation"):
                    ai_recs["interpretation"] = sanitize_text(ai_recs["interpretation"])
                
                # Sanitize plan_4r text
                if ai_recs.get("plan_4r"):
                    ai_recs["plan_4r"] = sanitize_text(ai_recs["plan_4r"])
            
            project_data["calculation_results"] = calc_results
        
        pdf_bytes = pdf_service.generate_formal_fertilization_report(project_data)
        
        # 3. Save PDF to disk
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"project_{project_id}_{timestamp}.pdf"
        file_path = REPORTS_DIR / filename
        
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
        
        file_size_bytes = os.path.getsize(file_path)
        
        # 4. Create report entry in database
        metadata = {
            "project_name": project.name,
            "generated_by": current_user.full_name,
            "area_ha": project.total_area_ha
        }
        
        # Add calculation_results to metadata if provided (for Excel export)
        if payload and payload.calculation_results:
            metadata["calculation_results"] = payload.calculation_results
        
        new_report = Report(
            project_id=project_id,
            report_type="project_complete",
            file_path=str(file_path),
            file_size_bytes=file_size_bytes,
            title=f"Reporte: {project.name}",
            description=f"Reporte completo del proyecto {project.name}",
            report_metadata=metadata
        )
        
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        # 5. Schedule email sending in background (non-blocking)
        user_name = current_user.full_name or current_user.email.split('@')[0]
        background_tasks.add_task(
            send_report_email_background,
            to_email=current_user.email,
            user_name=user_name,
            module_name="Suelo",
            report_title=f"Reporte: {project.name}",
            pdf_bytes=pdf_bytes,
            pdf_filename=filename,
            report_id=new_report.id
        )
        
        return ReportResponse.model_validate(new_report)
        
    except Exception as e:
        db.rollback()
        # Clean up PDF file if it was created
        if file_path and Path(file_path).exists():
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )
