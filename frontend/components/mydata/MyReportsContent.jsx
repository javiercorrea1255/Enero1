import { useState, useEffect } from 'react';
import { FileText, Download, Calendar, Search, Filter, Leaf, Beaker, TrendingUp, Sprout, Droplets } from 'lucide-react';
import { authService } from '../../services/auth';
import useIsMobile from '../../hooks/useIsMobile';

const REPORT_TYPES = [
  { id: 'all', label: 'Todos', icon: FileText },
  { id: 'soil', label: 'Suelo', icon: Leaf },
  { id: 'foliar', label: 'Foliar', icon: Leaf },
  { id: 'roi', label: 'Rentabilidad', icon: TrendingUp },
  { id: 'hydro_ions', label: 'Hidroponía', icon: Beaker },
  { id: 'fertiirrigation', label: 'FertiRiego', icon: Sprout },
];

export default function MyReportsContent() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [downloading, setDownloading] = useState(null);
  const isMobile = useIsMobile(768);

  useEffect(() => {
    loadAllReports();
  }, []);

  const loadAllReports = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/reports', {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });
      
      if (!response.ok) throw new Error('Error al cargar informes');
      
      const data = await response.json();
      setReports(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getReportCategory = (report) => {
    const type = report.report_type?.toLowerCase() || '';
    const title = report.title?.toLowerCase() || '';
    
    if (type.includes('hydro_ions') || type.includes('ion') || title.includes('nutritiva') || title.includes('iones')) return 'hydro_ions';
    if (type.includes('hydroponics') || type.includes('hydro_calculation') || type.includes('nutrient_formulation') || type === 'hydro' || title.includes('hidroponia') || title.includes('hidropon')) return 'hydro_ions';
    if (type.includes('fertiirrigation') || title.includes('fertirriego') || title.includes('fertiriego') || title.includes('fertiirrig')) return 'fertiirrigation';
    if (type.includes('roi') || title.includes('roi') || title.includes('rentabilidad') || title.includes('simulación')) return 'roi';
    if (type.includes('foliar') || title.includes('foliar')) return 'foliar';
    if (type.includes('soil') || type.includes('fertilization') || type.includes('project_summary') || title.includes('suelo') || title.includes('nom-021')) return 'soil';
    
    return 'soil';
  };

  const getCategoryInfo = (category) => {
    const info = {
      soil: { label: 'Suelo', color: '#22c55e', bg: '#dcfce7', icon: Leaf },
      foliar: { label: 'Foliar', color: '#10b981', bg: '#d1fae5', icon: Droplets },
      roi: { label: 'Rentabilidad', color: '#f59e0b', bg: '#fef3c7', icon: TrendingUp },
      hydro_ions: { label: 'Hidroponía', color: '#1e40af', bg: '#dbeafe', icon: Beaker },
      fertiirrigation: { label: 'FertiRiego', color: '#7c3aed', bg: '#ede9fe', icon: Sprout },
    };
    return info[category] || info.soil;
  };

  const filteredReports = reports.filter(report => {
    const matchesSearch = report.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         report.description?.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (filterType === 'all') return matchesSearch;
    
    const category = getReportCategory(report);
    return matchesSearch && category === filterType;
  });

  const handleDownload = async (reportId, reportTitle) => {
    try {
      setDownloading(reportId);
      const response = await fetch(`/api/reports/${reportId}/download`, {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });
      
      if (!response.ok) throw new Error('Error al descargar');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportTitle || 'informe'}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert('Error al descargar: ' + err.message);
    } finally {
      setDownloading(null);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Sin fecha';
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: isMobile ? '40px 16px' : '60px 20px' }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '3px solid #e5e7eb',
          borderTop: '3px solid #1e40af',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 16px'
        }}></div>
        <p style={{ color: '#6b7280', fontSize: '14px' }}>Cargando informes...</p>
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        background: '#fee2e2', 
        color: '#991b1b', 
        textAlign: 'center', 
        padding: '24px',
        borderRadius: '8px',
        margin: '16px'
      }}>
        <p>Error: {error}</p>
      </div>
    );
  }

  return (
    <div style={{ padding: isMobile ? '12px' : '20px' }}>
      <div style={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        gap: '12px',
        marginBottom: '20px'
      }}>
        <div style={{ 
          flex: 1, 
          position: 'relative',
          minWidth: 0
        }}>
          <Search 
            size={18} 
            style={{ 
              position: 'absolute', 
              left: '12px', 
              top: '50%', 
              transform: 'translateY(-50%)',
              color: '#9ca3af'
            }} 
          />
          <input
            type="text"
            placeholder="Buscar informes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px 10px 40px',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '14px',
              boxSizing: 'border-box'
            }}
          />
        </div>
        
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px',
          flexWrap: 'wrap'
        }}>
          <Filter size={16} color="#6b7280" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            style={{
              padding: '10px 12px',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '14px',
              background: 'white',
              minWidth: isMobile ? '100%' : '160px',
              flex: isMobile ? 1 : 'none'
            }}
          >
            {REPORT_TYPES.map(type => (
              <option key={type.id} value={type.id}>{type.label}</option>
            ))}
          </select>
        </div>
      </div>

      {isMobile && (
        <div style={{
          display: 'flex',
          gap: '6px',
          overflowX: 'auto',
          paddingBottom: '8px',
          marginBottom: '16px',
          WebkitOverflowScrolling: 'touch'
        }}>
          {REPORT_TYPES.map(type => {
            const Icon = type.icon;
            const isActive = filterType === type.id;
            return (
              <button
                key={type.id}
                onClick={() => setFilterType(type.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '6px 12px',
                  border: 'none',
                  borderRadius: '20px',
                  fontSize: '12px',
                  fontWeight: '500',
                  background: isActive ? '#1e40af' : '#f3f4f6',
                  color: isActive ? 'white' : '#6b7280',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  flexShrink: 0
                }}
              >
                <Icon size={14} />
                {type.label}
              </button>
            );
          })}
        </div>
      )}

      <div style={{ 
        fontSize: '13px', 
        color: '#6b7280', 
        marginBottom: '12px' 
      }}>
        {filteredReports.length} informe{filteredReports.length !== 1 ? 's' : ''} encontrado{filteredReports.length !== 1 ? 's' : ''}
      </div>

      {filteredReports.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: isMobile ? '32px 16px' : '48px 24px',
          background: '#f9fafb',
          borderRadius: '12px'
        }}>
          <FileText size={48} color="#d1d5db" style={{ marginBottom: '12px' }} />
          <p style={{ color: '#6b7280', fontSize: '15px', marginBottom: '8px' }}>
            {searchTerm || filterType !== 'all' ? 'No se encontraron informes' : 'No tienes informes generados'}
          </p>
          <p style={{ color: '#9ca3af', fontSize: '13px' }}>
            Los informes aparecerán aquí cuando los generes desde las calculadoras.
          </p>
        </div>
      ) : (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '10px'
        }}>
          {filteredReports.map(report => {
            const category = getReportCategory(report);
            const categoryInfo = getCategoryInfo(category);
            const CategoryIcon = categoryInfo.icon;
            
            return (
              <div
                key={report.id}
                style={{
                  display: 'flex',
                  flexDirection: isMobile ? 'column' : 'row',
                  alignItems: isMobile ? 'stretch' : 'center',
                  gap: isMobile ? '10px' : '16px',
                  padding: isMobile ? '14px' : '16px',
                  background: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '10px',
                  transition: 'box-shadow 0.2s'
                }}
              >
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '12px',
                  flex: 1,
                  minWidth: 0
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '10px',
                    background: categoryInfo.bg,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    <CategoryIcon size={20} color={categoryInfo.color} />
                  </div>
                  
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontWeight: '600',
                      fontSize: '14px',
                      color: '#1f2937',
                      marginBottom: '4px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: isMobile ? 'normal' : 'nowrap'
                    }}>
                      {report.title || 'Informe sin título'}
                    </div>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      flexWrap: 'wrap'
                    }}>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '11px',
                        fontWeight: '500',
                        background: categoryInfo.bg,
                        color: categoryInfo.color
                      }}>
                        {categoryInfo.label}
                      </span>
                      <span style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '12px',
                        color: '#9ca3af'
                      }}>
                        <Calendar size={12} />
                        {formatDate(report.created_at)}
                      </span>
                    </div>
                  </div>
                </div>
                
                <button
                  onClick={() => handleDownload(report.id, report.title)}
                  disabled={downloading === report.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    padding: isMobile ? '10px 16px' : '8px 16px',
                    background: downloading === report.id ? '#9ca3af' : '#1e40af',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '13px',
                    fontWeight: '600',
                    cursor: downloading === report.id ? 'wait' : 'pointer',
                    transition: 'background 0.2s',
                    flexShrink: 0,
                    width: isMobile ? '100%' : 'auto'
                  }}
                  onMouseEnter={(e) => {
                    if (downloading !== report.id) e.currentTarget.style.background = '#1e3a8a';
                  }}
                  onMouseLeave={(e) => {
                    if (downloading !== report.id) e.currentTarget.style.background = '#1e40af';
                  }}
                >
                  <Download size={16} />
                  {downloading === report.id ? 'Descargando...' : 'Descargar'}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
