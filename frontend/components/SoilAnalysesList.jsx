import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { analysesService } from '../services/analyses';
import { projectService } from '../services/projects';
import { plotService } from '../services/plots';
import { FlaskConical, MapPin, Calendar, Eye } from 'lucide-react';

export default function SoilAnalysesList() {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadAllAnalyses();
  }, []);

  const loadAllAnalyses = async () => {
    try {
      const projects = await projectService.getAll();
      
      const allAnalyses = [];
      for (const project of projects) {
        if (project.module_type === 'soil' || !project.module_type) {
          try {
            const plots = await plotService.getByProject(project.id);
            
            for (const plot of plots) {
              try {
                const soilAnalyses = await analysesService.getSoilAnalyses(plot.id);
                soilAnalyses.forEach(analysis => {
                  allAnalyses.push({
                    ...analysis,
                    project_name: project.name,
                    plot_name: plot.name,
                    project_id: project.id
                  });
                });
              } catch (err) {
                console.warn(`Failed to load analyses for plot ${plot.id}:`, err);
              }
            }
          } catch (err) {
            console.warn(`Failed to load plots for project ${project.id}:`, err);
          }
        }
      }
      
      allAnalyses.sort((a, b) => new Date(b.analysis_date) - new Date(a.analysis_date));
      setAnalyses(allAnalyses);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="card">Cargando análisis de suelo...</div>;

  if (error) {
    return (
      <div className="card" style={{background: '#fee', color: '#c00'}}>
        Error: {error}
      </div>
    );
  }

  return (
    <div>
      <div style={{marginBottom: '24px'}}>
        <h2 style={{fontSize: '1.75rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '12px'}}>
          <FlaskConical size={32} style={{color: 'var(--primary)'}} />
          Análisis de Suelo
        </h2>
        <p style={{color: 'var(--text-secondary)', margin: 0}}>
          Vista consolidada de todos tus análisis de suelo
        </p>
      </div>

      {analyses.length === 0 ? (
        <div className="card" style={{textAlign: 'center', padding: '60px 20px'}}>
          <FlaskConical size={64} style={{color: 'var(--border-color)', marginBottom: '16px'}} />
          <h3>No hay análisis de suelo</h3>
          <p style={{color: 'var(--text-secondary)', marginBottom: '24px'}}>
            Crea un proyecto y agrega parcelas para comenzar a registrar análisis de suelo
          </p>
          <Link
            to="/app/wizard"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 24px',
              background: 'var(--primary)',
              color: 'white',
              textDecoration: 'none',
              borderRadius: 'var(--radius-md)',
              fontWeight: '600'
            }}
          >
            Crear Proyecto
          </Link>
        </div>
      ) : (
        <div style={{display: 'grid', gap: '16px'}}>
          {analyses.map(analysis => (
            <div key={analysis.id} className="card">
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px'}}>
                <div>
                  <h3 style={{margin: '0 0 8px 0', fontSize: '1.25rem'}}>
                    {analysis.project_name} - {analysis.plot_name}
                  </h3>
                  <div style={{display: 'flex', flexWrap: 'wrap', gap: '16px', fontSize: '0.9rem', color: 'var(--text-secondary)'}}>
                    <span style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
                      <Calendar size={16} />
                      {new Date(analysis.analysis_date).toLocaleDateString('es-MX', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </span>
                    {analysis.laboratory_name && (
                      <span style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
                        <FlaskConical size={16} />
                        {analysis.laboratory_name}
                      </span>
                    )}
                  </div>
                </div>
                <Link
                  to={`/app/projects/${analysis.project_id}/plots`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 16px',
                    background: 'var(--primary)',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.9rem',
                    fontWeight: '600'
                  }}
                >
                  <Eye size={16} />
                  Ver Detalles
                </Link>
              </div>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '12px',
                padding: '16px',
                background: 'var(--background)',
                borderRadius: 'var(--radius-md)',
                marginTop: '12px'
              }}>
                <div>
                  <div style={{fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px'}}>pH</div>
                  <div style={{fontSize: '1.1rem', fontWeight: '600'}}>{analysis.ph || 'N/A'}</div>
                </div>
                <div>
                  <div style={{fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px'}}>M.O. (%)</div>
                  <div style={{fontSize: '1.1rem', fontWeight: '600'}}>{analysis.organic_matter || 'N/A'}</div>
                </div>
                <div>
                  <div style={{fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px'}}>N (ppm)</div>
                  <div style={{fontSize: '1.1rem', fontWeight: '600'}}>{analysis.nitrogen_ppm || 'N/A'}</div>
                </div>
                <div>
                  <div style={{fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px'}}>P (ppm)</div>
                  <div style={{fontSize: '1.1rem', fontWeight: '600'}}>{analysis.phosphorus_ppm || 'N/A'}</div>
                </div>
                <div>
                  <div style={{fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px'}}>K (ppm)</div>
                  <div style={{fontSize: '1.1rem', fontWeight: '600'}}>{analysis.potassium_ppm || 'N/A'}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
