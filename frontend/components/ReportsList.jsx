import { useState, useEffect } from 'react';
import { reportsService } from '../services/reports';
import { FileText, Download, Trash2, FileSpreadsheet } from 'lucide-react';

export default function ReportsList() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ projectId: '', reportType: '' });

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      const data = await reportsService.getAll(
        filter.projectId || null,
        filter.reportType || null
      );
      setReports(data);
    } catch (error) {
      console.error('Error loading reports:', error);
      alert('Error al cargar informes');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar este informe?')) return;
    
    try {
      await reportsService.delete(id);
      setReports(reports.filter(r => r.id !== id));
    } catch (error) {
      console.error('Error deleting report:', error);
      alert('Error al eliminar informe');
    }
  };

  const handleDownload = async (report) => {
    try {
      const filename = `${report.title.replace(/\s+/g, '_')}.pdf`;
      await reportsService.downloadReport(report.id, filename);
    } catch (error) {
      console.error('Error downloading report:', error);
      alert('Error al descargar el informe');
    }
  };

  const handleDownloadExcel = async (report) => {
    try {
      const filename = `${report.title.replace(/\s+/g, '_')}.xlsx`;
      
      // Check if report has a program_id (created from fertilization programs)
      const programId = report.metadata?.program_id;
      
      if (programId) {
        // Use program-specific endpoint for detailed fertilization programs
        await reportsService.downloadExcel(programId, filename);
      } else {
        // Use report-based endpoint for wizard-generated reports
        await reportsService.downloadReportExcel(report.id, filename);
      }
    } catch (error) {
      console.error('Error downloading Excel:', error);
      alert('Error al descargar el archivo Excel');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatSize = (bytes) => {
    if (!bytes) return 'N/A';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  const getTypeLabel = (type) => {
    const types = {
      'project_complete': 'Proyecto Completo',
      'soil_analysis': 'Análisis de Suelo',
      'fertilization_plan': 'Plan de Fertilización',
      'foliar_analysis': 'Análisis Foliar'
    };
    return types[type] || type;
  };

  if (loading) {
    return <div style={{padding: '20px'}}>Cargando informes...</div>;
  }

  return (
    <div style={{padding: '20px'}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px'}}>
        <h1 style={{margin: 0, display: 'flex', alignItems: 'center', gap: '10px'}}>
          <FileText size={28} /> Informes Generados
        </h1>
      </div>

      {reports.length === 0 ? (
        <div className="card" style={{textAlign: 'center', padding: '40px'}}>
          <p style={{color: '#7f8c8d', marginBottom: '10px'}}>No hay informes generados aún.</p>
          <p style={{fontSize: '0.9rem', color: '#95a5a6'}}>
            Los informes se generan automáticamente al completar proyectos en el wizard.
          </p>
        </div>
      ) : (
        <div style={{display: 'grid', gap: '15px'}}>
          {reports.map(report => (
            <div key={report.id} className="card" style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{flex: 1}}>
                <h3 style={{margin: '0 0 10px 0'}}>
                  {report.title || `Informe #${report.id}`}
                </h3>
                <div style={{fontSize: '0.9rem', color: '#7f8c8d'}}>
                  <p style={{margin: '5px 0'}}>
                    <strong>Tipo:</strong> {getTypeLabel(report.report_type)}
                  </p>
                  <p style={{margin: '5px 0'}}>
                    <strong>Generado:</strong> {formatDate(report.generated_at)}
                  </p>
                  {report.file_size_bytes && (
                    <p style={{margin: '5px 0'}}>
                      <strong>Tamaño:</strong> {formatSize(report.file_size_bytes)}
                    </p>
                  )}
                  {report.description && (
                    <p style={{margin: '10px 0 0 0', color: '#555'}}>
                      {report.description}
                    </p>
                  )}
                </div>
              </div>
              
              <div style={{display: 'flex', gap: '10px', marginLeft: '20px'}}>
                <button
                  onClick={() => handleDownload(report)}
                  style={{
                    padding: '10px 20px',
                    background: '#1e40af',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    transition: 'all 0.2s',
                    boxShadow: '0 2px 6px rgba(30, 64, 175, 0.3)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#1e3a8a';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(30, 64, 175, 0.4)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#1e40af';
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 2px 6px rgba(30, 64, 175, 0.3)';
                  }}
                >
                  <Download size={16} /> PDF
                </button>
                <button
                  onClick={() => handleDownloadExcel(report)}
                  style={{
                    padding: '10px 20px',
                    background: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    transition: 'all 0.2s',
                    boxShadow: '0 2px 6px rgba(59, 130, 246, 0.3)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#2563eb';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.4)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#3b82f6';
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 2px 6px rgba(59, 130, 246, 0.3)';
                  }}
                >
                  <FileSpreadsheet size={16} /> Excel
                </button>
                <button
                  onClick={() => handleDelete(report.id)}
                  style={{
                    padding: '10px 20px',
                    background: '#e74c3c',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <Trash2 size={16} /> Eliminar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
