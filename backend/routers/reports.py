"""
PDF report generation router.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER

from app.database import get_db
from app.models.database_models import (
    User, FertilizationProgram, Plot, Project, SoilAnalysis, FertilizerApplication, FoliarAnalysis
)
from app.core.auth import get_current_active_user
from app.services.pdf_service import pdf_service
from app.services.excel_service import excel_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/fertilization-program/{program_id}/pdf")
async def generate_fertilization_pdf(
    program_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate PDF report for a fertilization program."""
    
    program = db.query(FertilizationProgram).join(Plot).join(Project).filter(
        FertilizationProgram.id == program_id,
        Project.user_id == current_user.id
    ).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    plot = program.plot
    project = plot.project
    
    soil_analysis = None
    if program.soil_analysis_id is not None:
        soil_analysis_obj = db.query(SoilAnalysis).filter(
            SoilAnalysis.id == program.soil_analysis_id
        ).first()
        
        if soil_analysis_obj is not None:
            soil_analysis = {
                'n_kg_ha': soil_analysis_obj.n_kg_ha,
                'p_ppm': soil_analysis_obj.p_ppm,
                'k_ppm': soil_analysis_obj.k_ppm,
                'ph': soil_analysis_obj.ph,
                'organic_matter_pct': soil_analysis_obj.organic_matter_pct,
                'analysis_date': soil_analysis_obj.analysis_date.strftime('%d/%m/%Y')
            }
    
    applications = db.query(FertilizerApplication).filter(
        FertilizerApplication.program_id == program_id
    ).all()
    
    applications_data = []
    for app in applications:
        applications_data.append({
            'planned_date': app.planned_date.strftime('%d/%m/%Y') if app.planned_date is not None else 'N/A',
            'phenological_stage': app.phenological_stage if app.phenological_stage is not None else '-',
            'application_type': app.application_type,
            'n_applied_kg_ha': app.n_applied_kg_ha if app.n_applied_kg_ha is not None else 0,
            'p2o5_applied_kg_ha': app.p2o5_applied_kg_ha if app.p2o5_applied_kg_ha is not None else 0,
            'k2o_applied_kg_ha': app.k2o_applied_kg_ha if app.k2o_applied_kg_ha is not None else 0
        })
    
    program_data = {
        'crop_slug': program.crop_slug,
        'crop_variety': program.crop_variety,
        'yield_target_t_ha': program.yield_target_t_ha,
        'planting_date': program.planting_date.strftime('%d/%m/%Y') if program.planting_date is not None else 'N/A',
        'harvest_date': program.harvest_date.strftime('%d/%m/%Y') if program.harvest_date is not None else 'N/A',
        'calculation_method': program.calculation_method,
        'calculation_results': program.calculation_results
    }
    
    plot_data = {
        'name': plot.name,
        'area_ha': plot.area_ha,
        'soil_texture': plot.soil_texture or 'N/A',
        'irrigation_type': plot.irrigation_type or 'N/A'
    }
    
    project_data = {
        'name': project.name,
        'location': project.location or 'N/A'
    }
    
    pdf_buffer = pdf_service.generate_fertilization_report(
        program_data=program_data,
        plot_data=plot_data,
        project_data=project_data,
        soil_analysis=soil_analysis,
        applications=applications_data
    )
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=fertilization_program_{program_id}.pdf"
        }
    )


@router.get("/fertilization-program/{program_id}/excel")
async def export_fertilization_excel(
    program_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export fertilization program to Excel format."""
    
    program = db.query(FertilizationProgram).join(Plot).join(Project).filter(
        FertilizationProgram.id == program_id,
        Project.user_id == current_user.id
    ).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    plot = program.plot
    project = plot.project
    
    soil_analysis = None
    if program.soil_analysis_id is not None:
        soil_analysis_obj = db.query(SoilAnalysis).filter(
            SoilAnalysis.id == program.soil_analysis_id
        ).first()
        
        if soil_analysis_obj is not None:
            soil_analysis = {
                'n_kg_ha': soil_analysis_obj.n_kg_ha,
                'p_ppm': soil_analysis_obj.p_ppm,
                'k_ppm': soil_analysis_obj.k_ppm,
                'ph': soil_analysis_obj.ph,
                'organic_matter_pct': soil_analysis_obj.organic_matter_pct,
                'analysis_date': soil_analysis_obj.analysis_date.strftime('%d/%m/%Y')
            }
    
    applications = db.query(FertilizerApplication).filter(
        FertilizerApplication.program_id == program_id
    ).all()
    
    applications_data = []
    for app in applications:
        applications_data.append({
            'planned_date': app.planned_date.strftime('%d/%m/%Y') if app.planned_date is not None else 'N/A',
            'phenological_stage': app.phenological_stage if app.phenological_stage is not None else '-',
            'application_type': app.application_type,
            'n_applied_kg_ha': app.n_applied_kg_ha if app.n_applied_kg_ha is not None else 0,
            'p2o5_applied_kg_ha': app.p2o5_applied_kg_ha if app.p2o5_applied_kg_ha is not None else 0,
            'k2o_applied_kg_ha': app.k2o_applied_kg_ha if app.k2o_applied_kg_ha is not None else 0
        })
    
    program_data = {
        'crop_slug': program.crop_slug,
        'crop_variety': program.crop_variety,
        'yield_target_t_ha': program.yield_target_t_ha,
        'planting_date': program.planting_date.strftime('%d/%m/%Y') if program.planting_date is not None else 'N/A',
        'harvest_date': program.harvest_date.strftime('%d/%m/%Y') if program.harvest_date is not None else 'N/A',
        'calculation_method': program.calculation_method,
        'calculation_results': program.calculation_results
    }
    
    plot_data = {
        'name': plot.name,
        'area_ha': plot.area_ha,
        'soil_texture': plot.soil_texture or 'N/A',
        'irrigation_type': plot.irrigation_type or 'N/A'
    }
    
    project_data = {
        'name': project.name,
        'location': project.location or 'N/A'
    }
    
    excel_buffer = excel_service.generate_fertilization_report(
        program_data=program_data,
        plot_data=plot_data,
        project_data=project_data,
        soil_analysis=soil_analysis,
        applications=applications_data
    )
    
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=fertilization_program_{program_id}.xlsx"
        }
    )


@router.get("/report/{report_id}/excel")
async def export_report_excel(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export report to Excel format (for wizard-generated reports without program_id)."""
    from app.models.database_models import Report
    
    report = db.query(Report).join(Project).filter(
        Report.id == report_id,
        Project.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    project = report.project
    
    # Extract calculation results from report metadata if available
    # Since wizard doesn't create FertilizationProgram, we need to extract from report metadata
    calc_results = {}
    soil_result = {}
    
    # Try to get data from report metadata if available
    if report.report_metadata:
        calc_results = report.report_metadata.get('calculation_results', {})
        soil_result = calc_results.get('soilResult', {})
    
    # Build data structures for Excel (with safe defaults for old reports without calc_results)
    program_data = {
        'crop_slug': soil_result.get('inputs', {}).get('crop_slug') if soil_result.get('inputs') else 'No especificado',
        'crop_variety': 'N/A',
        'yield_target_t_ha': soil_result.get('inputs', {}).get('yield_target_t_ha', 0) if soil_result.get('inputs') else 0,
        'planting_date': 'N/A',
        'harvest_date': 'N/A',
        'calculation_method': soil_result.get('inputs', {}).get('method') if soil_result.get('inputs') else 'No especificado',
        'calculation_results': calc_results if calc_results else {
            'note': 'Este reporte fue generado antes de la implementación de exportación a Excel. Genera un nuevo reporte desde el wizard para obtener datos completos.'
        }
    }
    
    plot_data = {
        'name': project.name,
        'area_ha': project.total_area_ha or 0,
        'soil_texture': 'N/A',
        'irrigation_type': 'N/A'
    }
    
    project_data = {
        'name': project.name,
        'location': project.location or 'N/A'
    }
    
    # Get soil analysis if exists
    soil_analysis = None
    if soil_result and soil_result.get('soil_analysis'):
        sa = soil_result['soil_analysis']
        soil_analysis = {
            'n_kg_ha': sa.get('n_kg_ha'),
            'p_ppm': sa.get('p_ppm'),
            'k_ppm': sa.get('k_ppm'),
            'ph': sa.get('ph'),
            'organic_matter_pct': sa.get('organic_matter_pct'),
            'analysis_date': 'N/A'
        }
    
    # Build applications from calculation results
    applications_data = []
    if soil_result and soil_result.get('fertilizer_kg_ha'):
        fert = soil_result['fertilizer_kg_ha']
        applications_data.append({
            'planned_date': 'N/A',
            'phenological_stage': 'General',
            'application_type': 'soil',
            'n_applied_kg_ha': fert.get('N', 0),
            'p2o5_applied_kg_ha': fert.get('P2O5', 0),
            'k2o_applied_kg_ha': fert.get('K2O', 0)
        })
    
    excel_buffer = excel_service.generate_fertilization_report(
        program_data=program_data,
        plot_data=plot_data,
        project_data=project_data,
        soil_analysis=soil_analysis,
        applications=applications_data
    )
    
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=report_{report_id}.xlsx"
        }
    )


@router.get("/project/{project_id}/pdf")
async def generate_project_report(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate comprehensive PDF report for a project with all analyses and programs."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    plots = db.query(Plot).filter(Plot.project_id == project_id).all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#2d5016'), spaceAfter=30, alignment=TA_CENTER)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor('#2d5016'), spaceAfter=12, spaceBefore=12)
    
    story.append(Paragraph(f"Reporte del Proyecto: {project.name}", title_style))
    story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    info_data = [
        ['Proyecto:', project.name],
        ['Ubicación:', project.location or 'No especificada'],
        ['Propietario:', current_user.full_name],
        ['Total de parcelas:', str(len(plots))],
        ['Fecha de creación:', project.created_at.strftime('%d/%m/%Y')]
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f5e9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))
    
    if project.notes:
        story.append(Paragraph("Notas del Proyecto:", heading_style))
        story.append(Paragraph(project.notes, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    for plot in plots:
        story.append(PageBreak())
        story.append(Paragraph(f"Parcela: {plot.name}", heading_style))
        
        plot_data = [
            ['Superficie:', f"{plot.area_ha} ha"],
            ['Cultivo:', plot.crop or 'No especificado'],
        ]
        
        if plot.gps_coordinates:
            plot_data.append(['GPS:', plot.gps_coordinates])
        
        plot_table = Table(plot_data, colWidths=[2*inch, 4*inch])
        plot_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(plot_table)
        story.append(Spacer(1, 0.2*inch))
        
        soil_analyses = db.query(SoilAnalysis).filter(SoilAnalysis.plot_id == plot.id).all()
        if soil_analyses:
            story.append(Paragraph(f"Análisis de Suelo ({len(soil_analyses)})", heading_style))
            
            for sa in soil_analyses:
                fecha = sa.analysis_date.strftime('%d/%m/%Y') if sa.analysis_date else 'N/A'
                story.append(Paragraph(f"Fecha: {fecha}", styles['Normal']))
                
                sa_data = [
                    ['Parámetro', 'Valor'],
                    ['N (kg/ha)', str(sa.n_kg_ha) if sa.n_kg_ha else 'N/A'],
                    ['P (ppm)', str(sa.p_ppm) if sa.p_ppm else 'N/A'],
                    ['K (ppm)', str(sa.k_ppm) if sa.k_ppm else 'N/A'],
                    ['pH', str(sa.ph) if sa.ph else 'N/A'],
                    ['MO (%)', str(sa.organic_matter_pct) if sa.organic_matter_pct else 'N/A'],
                    ['Textura', sa.texture or 'N/A'],
                ]
                
                sa_table = Table(sa_data, colWidths=[2.5*inch, 2.5*inch])
                sa_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5016')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ]))
                
                story.append(sa_table)
                story.append(Spacer(1, 0.15*inch))
        
        foliar_analyses = db.query(FoliarAnalysis).filter(FoliarAnalysis.plot_id == plot.id).all()
        if foliar_analyses:
            story.append(Paragraph(f"Análisis Foliar ({len(foliar_analyses)})", heading_style))
            
            for fa in foliar_analyses:
                fecha = fa.analysis_date.strftime('%d/%m/%Y') if fa.analysis_date else 'N/A'
                etapa = fa.phenological_stage or 'N/A'
                story.append(Paragraph(f"Fecha: {fecha} - Etapa: {etapa}", styles['Normal']))
                
                fa_data = [
                    ['Nutriente', 'Valor'],
                    ['N (%)', str(fa.n_pct) if fa.n_pct else 'N/A'],
                    ['P (%)', str(fa.p_pct) if fa.p_pct else 'N/A'],
                    ['K (%)', str(fa.k_pct) if fa.k_pct else 'N/A'],
                    ['Ca (%)', str(fa.ca_pct) if fa.ca_pct else 'N/A'],
                    ['Mg (%)', str(fa.mg_pct) if fa.mg_pct else 'N/A'],
                ]
                
                fa_table = Table(fa_data, colWidths=[2.5*inch, 2.5*inch])
                fa_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a7c59')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ]))
                
                story.append(fa_table)
                story.append(Spacer(1, 0.15*inch))
        
        programs = db.query(FertilizationProgram).filter(FertilizationProgram.plot_id == plot.id).all()
        if programs:
            story.append(Paragraph(f"Programas de Fertilización ({len(programs)})", heading_style))
            
            for prog in programs:
                story.append(Paragraph(f"Cultivo: {prog.crop_slug} - Rendimiento objetivo: {prog.yield_target_t_ha} t/ha", styles['Normal']))
                story.append(Paragraph(f"Método: {prog.calculation_method}", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
    
    footer_text = "Reporte generado por AgriDose - Directo al Campo | NOM-021-RECNAT-2000, INIFAP/SADER, FAO"
    story.append(PageBreak())
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))
    
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=proyecto_{project.name.replace(' ', '_')}.pdf"}
    )
