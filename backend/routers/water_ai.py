"""
HidroponIA Vision - Water Analysis AI Router
API endpoints for AI-powered water analysis and fertilization recommendations.
"""
import os
import json
import base64
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.auth import get_current_user
from app.models.database_models import User
from app.models.water_ai_models import WaterAIAnalysis, WaterAIRecommendation, WaterAIReport, AnalysisStatus
from app.schemas.water_ai_schemas import (
    WaterAnalysisUploadResponse,
    WaterParametersExtracted,
    CropSelectionRequest,
    RecommendationRequest,
    AIRecommendationResponse,
    ReportGenerationRequest,
    ReportResponse,
    WaterAnalysisListItem,
    RecommendationListItem,
    CropCatalogResponse,
    CropCatalogItem
)
from app.services.agronomic_ai_service import AgronomicAIService
from app.utils.stripe_helpers import is_premium_user

router = APIRouter(prefix="/api/hydroponia-vision", tags=["HidroponIA Vision"])

# Initialize AI service
ai_service = AgronomicAIService()


@router.post("/upload", response_model=WaterAnalysisUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_water_analysis(
    file: UploadFile = File(...),
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload water analysis document (PDF/image) and extract parameters using AI.
    Premium feature only.
    """
    # Verify Premium access
    if not is_premium_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HidroponIA Vision es una funcionalidad Premium. Actualiza tu plan para acceder."
        )
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no soportado. Use: JPG, PNG o PDF"
        )
    
    # Validate file size (max 10MB)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo excede el tamaño máximo de 10MB"
        )
    
    # Convert PDF to image if necessary, track MIME type
    if file.content_type == "application/pdf":
        import fitz  # PyMuPDF
        
        pdf_document = None
        try:
            # Open PDF and convert first page to image
            pdf_document = fitz.open(stream=file_content, filetype="pdf")
            first_page = pdf_document[0]
            
            # Render page to image (300 DPI for better OCR)
            pix = first_page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            
            # Convert to PNG bytes
            img_bytes = pix.tobytes("png")
            
            # Convert to base64
            base64_content = base64.b64encode(img_bytes).decode('utf-8')
            image_mime_type = "image/png"
        finally:
            if pdf_document:
                pdf_document.close()
    else:
        # For images, use directly
        base64_content = base64.b64encode(file_content).decode('utf-8')
        # Preserve original MIME type
        image_mime_type = file.content_type
    
    # Create database record
    water_analysis = WaterAIAnalysis(
        user_id=current_user.id,
        project_id=project_id,
        original_filename=file.filename,
        status=AnalysisStatus.EXTRACTING.value
    )
    db.add(water_analysis)
    db.commit()
    db.refresh(water_analysis)
    
    try:
        # Extract parameters using AI
        extracted_data = ai_service.extract_water_parameters_from_image(base64_content, image_mime_type)
        
        # Update database with extracted parameters
        water_analysis.ph = extracted_data.get('ph')
        water_analysis.ec_ms_cm = extracted_data.get('ec_ms_cm')
        water_analysis.tds_ppm = extracted_data.get('tds_ppm')
        water_analysis.alkalinity_ppm_caco3 = extracted_data.get('alkalinity_ppm_caco3')
        water_analysis.hardness_ppm = extracted_data.get('hardness_ppm')
        water_analysis.temperature_c = extracted_data.get('temperature_c')
        
        water_analysis.calcium_ppm = extracted_data.get('calcium_ppm')
        water_analysis.magnesium_ppm = extracted_data.get('magnesium_ppm')
        water_analysis.potassium_ppm = extracted_data.get('potassium_ppm')
        water_analysis.sodium_ppm = extracted_data.get('sodium_ppm')
        
        water_analysis.nitrate_ppm = extracted_data.get('nitrate_ppm')
        water_analysis.sulfate_ppm = extracted_data.get('sulfate_ppm')
        water_analysis.chloride_ppm = extracted_data.get('chloride_ppm')
        water_analysis.bicarbonate_ppm = extracted_data.get('bicarbonate_ppm')
        water_analysis.phosphate_ppm = extracted_data.get('phosphate_ppm')
        
        water_analysis.iron_ppm = extracted_data.get('iron_ppm')
        water_analysis.manganese_ppm = extracted_data.get('manganese_ppm')
        water_analysis.zinc_ppm = extracted_data.get('zinc_ppm')
        water_analysis.copper_ppm = extracted_data.get('copper_ppm')
        water_analysis.boron_ppm = extracted_data.get('boron_ppm')
        
        water_analysis.lab_name = extracted_data.get('lab_name')
        water_analysis.source_type = extracted_data.get('source_type')
        
        # Parse analysis date if present
        if extracted_data.get('analysis_date'):
            try:
                water_analysis.analysis_date = datetime.fromisoformat(extracted_data['analysis_date'])
            except:
                pass
        
        water_analysis.ai_extracted = True
        water_analysis.ai_confidence_score = extracted_data.get('confidence_score', 0.0)
        water_analysis.ai_extraction_notes = extracted_data.get('extraction_notes')
        water_analysis.status = AnalysisStatus.REVIEW.value
        
        db.commit()
        db.refresh(water_analysis)
        
        # Build response
        return WaterAnalysisUploadResponse(
            analysis_id=water_analysis.id,
            status="success",
            message="Parámetros extraídos correctamente. Revise y ajuste si es necesario.",
            extracted_parameters=WaterParametersExtracted(**extracted_data)
        )
        
    except Exception as e:
        water_analysis.status = AnalysisStatus.ERROR.value
        water_analysis.ai_extraction_notes = f"Error en extracción: {str(e)}"
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el análisis: {str(e)}"
        )


@router.patch("/analyses/{analysis_id}/parameters")
@router.put("/analyses/{analysis_id}/parameters")
async def update_water_parameters(
    analysis_id: int,
    parameters: WaterParametersExtracted,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update/edit extracted water parameters manually.
    Supports both PATCH and PUT methods for compatibility.
    """
    water_analysis = db.query(WaterAIAnalysis).filter(
        WaterAIAnalysis.id == analysis_id,
        WaterAIAnalysis.user_id == current_user.id
    ).first()
    
    if not water_analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Análisis no encontrado")
    
    # Update all parameters
    for field, value in parameters.dict(exclude_none=True).items():
        if hasattr(water_analysis, field):
            setattr(water_analysis, field, value)
    
    water_analysis.manually_edited = True
    water_analysis.status = AnalysisStatus.REVIEW.value
    db.commit()
    
    return {"message": "Parámetros actualizados correctamente"}


@router.get("/crops", response_model=CropCatalogResponse)
async def get_crop_catalog(
    current_user: User = Depends(get_current_user)
):
    """
    Get catalog of supported crops with nutrient requirements by phenological stage.
    """
    # Load catalog from JSON
    catalog_path = os.path.join(os.path.dirname(__file__), "..", "config", "hydroponic_crops_catalog.json")
    
    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog_data = json.load(f)
        
        crops = [CropCatalogItem(**crop) for crop in catalog_data['crops']]
        
        return CropCatalogResponse(
            crops=crops,
            total_crops=len(crops)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar catálogo de cultivos: {str(e)}"
        )


@router.post("/recommendation", response_model=AIRecommendationResponse, status_code=status.HTTP_201_CREATED)
async def generate_recommendation(
    request: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered fertilization recommendation based on water analysis and crop selection.
    Premium feature only.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🚀 INICIO generación de recomendación - Usuario: {current_user.email}, Análisis ID: {request.water_analysis_id}")
    
    # Verify Premium access
    logger.info("✓ Verificando acceso Premium...")
    if not is_premium_user(current_user):
        logger.warning(f"❌ Usuario {current_user.email} no tiene acceso Premium")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HidroponIA Vision es una funcionalidad Premium"
        )
    logger.info("✓ Acceso Premium verificado")
    
    # Get water analysis
    logger.info(f"✓ Buscando análisis de agua ID: {request.water_analysis_id}...")
    water_analysis = db.query(WaterAIAnalysis).filter(
        WaterAIAnalysis.id == request.water_analysis_id,
        WaterAIAnalysis.user_id == current_user.id
    ).first()
    
    if not water_analysis:
        logger.error(f"❌ Análisis de agua no encontrado - ID: {request.water_analysis_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Análisis de agua no encontrado")
    logger.info(f"✓ Análisis encontrado: pH={water_analysis.ph}, EC={water_analysis.ec_ms_cm}")
    
    # Load crop catalog to get nutrient requirements
    logger.info(f"✓ Cargando catálogo de cultivos...")
    catalog_path = os.path.join(os.path.dirname(__file__), "..", "config", "hydroponic_crops_catalog.json")
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog_data = json.load(f)
    
    # Find crop and stage
    logger.info(f"✓ Buscando cultivo: {request.crop_selection.crop_key} - Etapa: {request.crop_selection.growth_stage.value}")
    crop_info = next((c for c in catalog_data['crops'] if c['key'] == request.crop_selection.crop_key), None)
    if not crop_info:
        logger.error(f"❌ Cultivo no encontrado: {request.crop_selection.crop_key}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cultivo no encontrado en catálogo")
    
    stage_info = next((s for s in crop_info['stages'] if s['stage'] == request.crop_selection.growth_stage.value), None)
    if not stage_info:
        logger.error(f"❌ Etapa no encontrada: {request.crop_selection.growth_stage.value}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Etapa fenológica no encontrada")
    logger.info(f"✓ Cultivo y etapa encontrados. Targets: pH={stage_info['target_ph_min']}-{stage_info['target_ph_max']}, EC={stage_info['target_ec_min']}-{stage_info['target_ec_max']}")
    
    # Prepare water parameters for AI
    water_params = {
        'ph': water_analysis.ph,
        'ec_ms_cm': water_analysis.ec_ms_cm,
        'calcium_ppm': water_analysis.calcium_ppm,
        'magnesium_ppm': water_analysis.magnesium_ppm,
        'potassium_ppm': water_analysis.potassium_ppm,
        'sodium_ppm': water_analysis.sodium_ppm,
        'nitrate_ppm': water_analysis.nitrate_ppm,
        'sulfate_ppm': water_analysis.sulfate_ppm,
        'chloride_ppm': water_analysis.chloride_ppm,
        'alkalinity_ppm_caco3': water_analysis.alkalinity_ppm_caco3,
        'hardness_ppm': water_analysis.hardness_ppm,
    }
    
    # Prepare crop data for AI
    crop_data = {
        'crop_name': request.crop_selection.crop_name,
        'growth_stage': request.crop_selection.growth_stage.value,
        'target_ph_min': stage_info['target_ph_min'],
        'target_ph_max': stage_info['target_ph_max'],
        'target_ec_min': stage_info['target_ec_min'],
        'target_ec_max': stage_info['target_ec_max'],
        'n_ppm_min': stage_info['n_ppm_min'],
        'n_ppm_max': stage_info['n_ppm_max'],
        'p_ppm_min': stage_info['p_ppm_min'],
        'p_ppm_max': stage_info['p_ppm_max'],
        'k_ppm_min': stage_info['k_ppm_min'],
        'k_ppm_max': stage_info['k_ppm_max'],
        'ca_ppm_min': stage_info['ca_ppm_min'],
        'ca_ppm_max': stage_info['ca_ppm_max'],
        'mg_ppm_min': stage_info['mg_ppm_min'],
        'mg_ppm_max': stage_info['mg_ppm_max'],
    }
    
    # Generate AI recommendation (with fallback if OpenAI unavailable)
    logger.info("🤖 INICIANDO llamada a OpenAI GPT-5 para generar recomendación agronómica...")
    logger.info(f"   - Cultivo: {crop_data['crop_name']} ({crop_data['growth_stage']})")
    logger.info(f"   - Agua: pH={water_params.get('ph')}, EC={water_params.get('ec_ms_cm')}")
    logger.info(f"   - Metodología preferida: {request.prefer_methodology or 'auto'}")
    
    start_time = datetime.now()
    ai_result = ai_service.generate_hydro_recommendation(
        water_params,
        crop_data,
        methodology_preference=request.prefer_methodology or "auto"
    )
    generation_time = (datetime.now() - start_time).total_seconds()
    
    # Check if AI or fallback was used
    if ai_result.get('ai_summary') and 'Configure OpenAI API' in ai_result.get('ai_summary', ''):
        logger.warning("⚠️  Usando modo fallback - OpenAI no disponible")
        logger.info("   - Recomendación básica generada sin IA")
    else:
        logger.info(f"✅ OpenAI respondió exitosamente en {generation_time:.2f} segundos")
        logger.info(f"   - Diagnóstico: {ai_result.get('water_quality_diagnosis', {}).get('overall_suitability', 'N/A')}")
        logger.info(f"   - Fertilizantes recomendados: {len(ai_result.get('fertilizer_recommendations', []))}")
    
    # Save recommendation to database
    logger.info("💾 Guardando recomendación en base de datos...")
    recommendation = WaterAIRecommendation(
        water_analysis_id=water_analysis.id,
        user_id=current_user.id,
        crop_name=request.crop_selection.crop_name,
        crop_key=request.crop_selection.crop_key,
        growth_stage=request.crop_selection.growth_stage.value,
        hydroponic_system=request.crop_selection.hydroponic_system.value if request.crop_selection.hydroponic_system else None,
        cultivation_area_m2=request.crop_selection.cultivation_area_m2,
        estimated_plants=request.crop_selection.estimated_plants,
        target_ph=ai_result.get('target_ph'),
        target_ec=ai_result.get('target_ec'),
        target_n_ppm=ai_result.get('target_n_ppm'),
        target_p_ppm=ai_result.get('target_p_ppm'),
        target_k_ppm=ai_result.get('target_k_ppm'),
        target_ca_ppm=ai_result.get('target_ca_ppm'),
        target_mg_ppm=ai_result.get('target_mg_ppm'),
        water_quality_diagnosis=ai_result.get('water_quality_diagnosis'),
        fertilizer_formula=ai_result.get('fertilizer_recommendations'),
        adjustment_instructions=ai_result.get('adjustment_instructions'),
        methodology_applied=ai_result.get('methodology_applied'),
        ai_summary=ai_result.get('ai_summary'),
        ai_detailed_analysis=ai_result.get('ai_detailed_analysis'),
        warnings_and_alerts=ai_result.get('warnings_and_alerts'),
        ai_model_used="gpt-5",
        generation_time_seconds=generation_time
    )
    
    db.add(recommendation)
    water_analysis.status = AnalysisStatus.COMPLETED.value
    db.commit()
    db.refresh(recommendation)
    logger.info(f"✅ Recomendación guardada exitosamente - ID: {recommendation.id}")
    
    # Build response
    return AIRecommendationResponse(
        recommendation_id=recommendation.id,
        water_analysis_id=water_analysis.id,
        crop_name=recommendation.crop_name,
        growth_stage=recommendation.growth_stage,
        target_ph=recommendation.target_ph,
        target_ec=recommendation.target_ec,
        target_n_ppm=recommendation.target_n_ppm,
        target_p_ppm=recommendation.target_p_ppm,
        target_k_ppm=recommendation.target_k_ppm,
        target_ca_ppm=recommendation.target_ca_ppm,
        target_mg_ppm=recommendation.target_mg_ppm,
        water_quality_diagnosis=ai_result['water_quality_diagnosis'],
        fertilizer_recommendations=ai_result['fertilizer_recommendations'],
        adjustment_instructions=ai_result['adjustment_instructions'],
        methodology_applied=ai_result['methodology_applied'],
        ai_summary=ai_result['ai_summary'],
        ai_detailed_analysis=ai_result['ai_detailed_analysis'],
        warnings_and_alerts=ai_result.get('warnings_and_alerts', []),
        estimated_cost_per_m3=recommendation.estimated_cost_per_m3,
        estimated_monthly_cost=recommendation.estimated_monthly_cost,
        created_at=recommendation.created_at,
        ai_model_used=recommendation.ai_model_used
    )


@router.get("/analyses", response_model=list[WaterAnalysisListItem])
async def list_water_analyses(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List water analyses for current user.
    """
    analyses = db.query(WaterAIAnalysis).filter(
        WaterAIAnalysis.user_id == current_user.id
    ).order_by(WaterAIAnalysis.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for analysis in analyses:
        recommendation_count = db.query(WaterAIRecommendation).filter(
            WaterAIRecommendation.water_analysis_id == analysis.id
        ).count()
        
        result.append(WaterAnalysisListItem(
            id=analysis.id,
            source_type=analysis.source_type,
            ph=analysis.ph,
            ec_ms_cm=analysis.ec_ms_cm,
            status=analysis.status,
            created_at=analysis.created_at,
            has_recommendations=recommendation_count > 0,
            recommendation_count=recommendation_count
        ))
    
    return result


@router.get("/recommendations", response_model=list[RecommendationListItem])
async def list_recommendations(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List recommendations for current user.
    """
    recommendations = db.query(WaterAIRecommendation).filter(
        WaterAIRecommendation.user_id == current_user.id
    ).order_by(WaterAIRecommendation.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for rec in recommendations:
        has_report = db.query(WaterAIReport).filter(
            WaterAIReport.recommendation_id == rec.id
        ).first() is not None
        
        result.append(RecommendationListItem(
            id=rec.id,
            crop_name=rec.crop_name,
            growth_stage=rec.growth_stage,
            target_ph=rec.target_ph,
            target_ec=rec.target_ec,
            created_at=rec.created_at,
            has_report=has_report
        ))
    
    return result


@router.post("/generate-report", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_pdf_report(
    request: ReportGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate professional PDF report for a recommendation.
    """
    # Get recommendation
    recommendation = db.query(WaterAIRecommendation).filter(
        WaterAIRecommendation.id == request.recommendation_id,
        WaterAIRecommendation.user_id == current_user.id
    ).first()
    
    if not recommendation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recomendación no encontrada")
    
    # Check if report already exists
    existing_report = db.query(WaterAIReport).filter(
        WaterAIReport.recommendation_id == recommendation.id
    ).first()
    
    if existing_report:
        return ReportResponse(
            report_id=existing_report.id,
            folio=existing_report.folio,
            filename=existing_report.filename,
            file_path=existing_report.file_path,
            download_url=f"/api/hydroponia-vision/reports/{existing_report.id}/download",
            created_at=existing_report.created_at
        )
    
    # Generate folio
    year = datetime.now().year
    report_count = db.query(WaterAIReport).filter(
        WaterAIReport.user_id == current_user.id
    ).count()
    folio = f"AGRI-VISION-{year}-{str(report_count + 1).zfill(4)}"
    
    # Generate title and filename with defensive defaults
    crop_name = recommendation.crop_name or "Cultivo"
    growth_stage = (recommendation.growth_stage or "").capitalize() or "General"
    title = f"Reporte HidroponIA Vision - {crop_name} {growth_stage}"
    filename = f"vision_{folio}.pdf"
    
    # Create report record
    report = WaterAIReport(
        recommendation_id=recommendation.id,
        water_analysis_id=recommendation.water_analysis_id,
        user_id=current_user.id,
        title=title,
        folio=folio,
        filename=filename,
        file_path=f"reports/{filename}"
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return ReportResponse(
        report_id=report.id,
        folio=report.folio,
        filename=report.filename,
        file_path=report.file_path,
        download_url=f"/api/hydroponia-vision/reports/{report.id}/download",
        created_at=report.created_at
    )


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download PDF report for HidroponIA Vision.
    """
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from fastapi.responses import StreamingResponse
    
    # Get report
    report = db.query(WaterAIReport).filter(
        WaterAIReport.id == report_id,
        WaterAIReport.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporte no encontrado")
    
    # Get recommendation
    recommendation = db.query(WaterAIRecommendation).filter(
        WaterAIRecommendation.id == report.recommendation_id
    ).first()
    
    if not recommendation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recomendación no encontrada")
    
    # Get water analysis
    water_analysis = db.query(WaterAIAnalysis).filter(
        WaterAIAnalysis.id == recommendation.water_analysis_id
    ).first()
    
    # Generate PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CustomTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#4a7c59'), alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle(name='SectionTitle', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#4a7c59'), spaceAfter=10, spaceBefore=15))
    
    story = []
    
    # Title
    story.append(Paragraph("AGRIDOSER", styles['CustomTitle']))
    story.append(Paragraph(report.title or "Reporte HidroponIA Vision", styles['CustomTitle']))
    story.append(Paragraph(f"Folio: {report.folio}", styles['Normal']))
    story.append(Paragraph(f"Fecha: {report.created_at.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Crop info
    story.append(Paragraph("INFORMACIÓN DEL CULTIVO", styles['SectionTitle']))
    crop_data = [
        ['Cultivo:', recommendation.crop_name or 'N/A'],
        ['Etapa Fenológica:', (recommendation.growth_stage or 'N/A').capitalize()],
        ['Sistema:', recommendation.hydroponic_system or 'N/A']
    ]
    crop_table = Table(crop_data, colWidths=[2*inch, 4*inch])
    crop_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (0,-1), colors.lightgrey)]))
    story.append(crop_table)
    story.append(Spacer(1, 0.2 * inch))
    
    # Water analysis
    if water_analysis:
        story.append(Paragraph("PARÁMETROS DEL AGUA", styles['SectionTitle']))
        water_data = [
            ['Parámetro', 'Valor', 'Unidad'],
            ['pH', f"{water_analysis.ph:.2f}" if water_analysis.ph else 'N/A', ''],
            ['CE', f"{water_analysis.ec_ms_cm:.2f}" if water_analysis.ec_ms_cm else 'N/A', 'mS/cm'],
            ['Calcio (Ca)', f"{water_analysis.calcium_ppm:.1f}" if water_analysis.calcium_ppm else 'N/A', 'ppm'],
            ['Magnesio (Mg)', f"{water_analysis.magnesium_ppm:.1f}" if water_analysis.magnesium_ppm else 'N/A', 'ppm'],
            ['Sodio (Na)', f"{water_analysis.sodium_ppm:.1f}" if water_analysis.sodium_ppm else 'N/A', 'ppm'],
            ['Potasio (K)', f"{water_analysis.potassium_ppm:.1f}" if water_analysis.potassium_ppm else 'N/A', 'ppm']
        ]
        water_table = Table(water_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
        water_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4a7c59')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
        ]))
        story.append(water_table)
        story.append(Spacer(1, 0.2 * inch))
    
    # Recommendation
    story.append(Paragraph("RECOMENDACIÓN", styles['SectionTitle']))
    rec_data = [
        ['pH Objetivo:', f"{recommendation.target_ph:.1f}" if recommendation.target_ph else 'N/A'],
        ['EC Objetivo:', f"{recommendation.target_ec:.2f} mS/cm" if recommendation.target_ec else 'N/A']
    ]
    rec_table = Table(rec_data, colWidths=[2*inch, 4*inch])
    rec_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (0,-1), colors.lightgrey)]))
    story.append(rec_table)
    story.append(Spacer(1, 0.2 * inch))
    
    # AI Summary
    if recommendation.ai_summary:
        story.append(Paragraph("ANÁLISIS AGRONÓMICO", styles['SectionTitle']))
        story.append(Paragraph(recommendation.ai_summary, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={report.filename}"}
    )
