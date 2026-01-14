import { useState, useEffect } from 'react';
import { analysesService } from '../services/analyses';

export default function AnalysesManager({ plotId, plotName }) {
  const [soilAnalyses, setSoilAnalyses] = useState([]);
  const [foliarAnalyses, setFoliarAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('soil');

  useEffect(() => {
    loadAnalyses();
  }, [plotId]);

  const loadAnalyses = async () => {
    try {
      const [soil, foliar] = await Promise.all([
        analysesService.getSoilAnalyses(plotId),
        analysesService.getFoliarAnalyses(plotId)
      ]);
      setSoilAnalyses(soil);
      setFoliarAnalyses(foliar);
    } catch (err) {
      console.error('Error loading analyses:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Cargando análisis...</div>;

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Análisis de {plotName}</h3>
      
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', borderBottom: '2px solid #e0e0e0' }}>
        <button
          onClick={() => setActiveTab('soil')}
          style={{
            padding: '10px 20px',
            background: activeTab === 'soil' ? '#2d5016' : 'transparent',
            color: activeTab === 'soil' ? 'white' : '#2d5016',
            border: 'none',
            borderBottom: activeTab === 'soil' ? '3px solid #2d5016' : 'none',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          Análisis de Suelo ({soilAnalyses.length})
        </button>
        <button
          onClick={() => setActiveTab('foliar')}
          style={{
            padding: '10px 20px',
            background: activeTab === 'foliar' ? '#2d5016' : 'transparent',
            color: activeTab === 'foliar' ? 'white' : '#2d5016',
            border: 'none',
            borderBottom: activeTab === 'foliar' ? '3px solid #2d5016' : 'none',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          Análisis Foliar ({foliarAnalyses.length})
        </button>
      </div>

      {activeTab === 'soil' && (
        <div>
          {soilAnalyses.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>
              <p>No hay análisis de suelo para esta parcela</p>
              <button
                style={{
                  padding: '8px 16px',
                  background: '#4a7c59',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Agregar Análisis de Suelo
              </button>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '15px' }}>
              {soilAnalyses.map(analysis => (
                <div
                  key={analysis.id}
                  style={{
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    padding: '15px',
                    background: '#f9f9f9'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <strong>Fecha: {new Date(analysis.analysis_date).toLocaleDateString()}</strong>
                    {analysis.laboratory && <span style={{ color: '#7f8c8d' }}>{analysis.laboratory}</span>}
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                    <div>
                      <strong>N:</strong> {analysis.n_kg_ha ? `${analysis.n_kg_ha} kg/ha` : 'N/A'}
                    </div>
                    <div>
                      <strong>P:</strong> {analysis.p_ppm ? `${analysis.p_ppm} ppm` : 'N/A'}
                    </div>
                    <div>
                      <strong>K:</strong> {analysis.k_ppm ? `${analysis.k_ppm} ppm` : 'N/A'}
                    </div>
                    <div>
                      <strong>pH:</strong> {analysis.ph || 'N/A'}
                    </div>
                    <div>
                      <strong>MO:</strong> {analysis.organic_matter_pct ? `${analysis.organic_matter_pct}%` : 'N/A'}
                    </div>
                    <div>
                      <strong>Textura:</strong> {analysis.texture || 'N/A'}
                    </div>
                  </div>

                  {analysis.notes && (
                    <div style={{ marginTop: '10px', padding: '10px', background: '#fff', borderRadius: '4px', fontSize: '0.9rem' }}>
                      <strong>Notas:</strong> {analysis.notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'foliar' && (
        <div>
          {foliarAnalyses.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>
              <p>No hay análisis foliar para esta parcela</p>
              <button
                style={{
                  padding: '8px 16px',
                  background: '#4a7c59',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Agregar Análisis Foliar
              </button>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '15px' }}>
              {foliarAnalyses.map(analysis => (
                <div
                  key={analysis.id}
                  style={{
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    padding: '15px',
                    background: '#f9f9f9'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <strong>Fecha: {new Date(analysis.sampling_date).toLocaleDateString()}</strong>
                    <span style={{ color: '#4a7c59', fontWeight: 'bold' }}>
                      {analysis.phenological_stage}
                    </span>
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                    <div>
                      <strong>N:</strong> {analysis.n_pct ? `${analysis.n_pct}%` : 'N/A'}
                    </div>
                    <div>
                      <strong>P:</strong> {analysis.p_pct ? `${analysis.p_pct}%` : 'N/A'}
                    </div>
                    <div>
                      <strong>K:</strong> {analysis.k_pct ? `${analysis.k_pct}%` : 'N/A'}
                    </div>
                    <div>
                      <strong>Ca:</strong> {analysis.ca_pct ? `${analysis.ca_pct}%` : 'N/A'}
                    </div>
                    <div>
                      <strong>Mg:</strong> {analysis.mg_pct ? `${analysis.mg_pct}%` : 'N/A'}
                    </div>
                    <div>
                      <strong>S:</strong> {analysis.s_pct ? `${analysis.s_pct}%` : 'N/A'}
                    </div>
                  </div>

                  {analysis.notes && (
                    <div style={{ marginTop: '10px', padding: '10px', background: '#fff', borderRadius: '4px', fontSize: '0.9rem' }}>
                      <strong>Notas:</strong> {analysis.notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
