import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { X, CheckCircle, AlertCircle, Edit2, Check, Droplet } from 'lucide-react';
import Button from './Button';
import Input from './Input';

/**
 * WaterAnalysisPreviewModal Component
 * 
 * Displays extracted water analysis data with edit capability before accepting
 */
function WaterAnalysisPreviewModal({ 
  extractedData, 
  confidence, 
  validationWarnings, 
  notes,
  onAccept, 
  onCancel 
}) {
  const [editableData, setEditableData] = useState({ ...extractedData });
  const [editingField, setEditingField] = useState(null);

  const handleFieldChange = (field, value) => {
    setEditableData(prev => ({
      ...prev,
      [field]: value === '' ? null : parseFloat(value)
    }));
  };

  const toggleEdit = (field) => {
    setEditingField(editingField === field ? null : field);
  };

  const handleAccept = () => {
    onAccept(editableData);
  };

  // Organize fields for water analysis
  const waterFields = [
    { 
      key: 'current_ph', 
      label: 'pH', 
      description: 'Potencial de hidrógeno'
    },
    { 
      key: 'source_water_ec', 
      label: 'EC (mS/cm)', 
      description: 'Conductividad eléctrica'
    },
    { 
      key: 'source_water_ca_ppm', 
      label: 'Calcio (ppm)', 
      description: 'Ca²⁺'
    },
    { 
      key: 'source_water_mg_ppm', 
      label: 'Magnesio (ppm)', 
      description: 'Mg²⁺'
    },
    { 
      key: 'alkalinity_ppm_caco3', 
      label: 'Alcalinidad (ppm CaCO₃)', 
      description: 'Bicarbonatos HCO₃⁻'
    },
    { 
      key: 'source_water_tds', 
      label: 'TDS (ppm)', 
      description: 'Sólidos disueltos totales'
    },
    { 
      key: 'hardness', 
      label: 'Dureza (ppm CaCO₃)', 
      description: 'Dureza total'
    }
  ];

  const renderField = (fieldConfig) => {
    const { key, label, description } = fieldConfig;
    const value = editableData[key];
    const isEditing = editingField === key;
    const hasValue = value !== null && value !== undefined;

    if (!hasValue) return null;

    return (
      <div key={key} style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-3)',
        padding: 'var(--space-4)',
        background: 'var(--color-bg-secondary)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--hydro-200)',
        transition: 'all 0.2s',
        boxShadow: isEditing ? '0 0 0 3px var(--hydro-100)' : 'none'
      }}>
        <div style={{ 
          width: '40px', 
          height: '40px', 
          borderRadius: 'var(--radius-md)',
          background: 'linear-gradient(135deg, var(--hydro-500), var(--hydro-600))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0
        }}>
          <Droplet size={20} color="#fff" />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--color-text-secondary)',
            marginBottom: 'var(--space-1)',
            fontWeight: 'var(--font-medium)'
          }}>
            {description}
          </div>
          {isEditing ? (
            <Input
              type="number"
              value={value || ''}
              onChange={(e) => handleFieldChange(key, e.target.value)}
              step="0.01"
              style={{ 
                width: '100%',
                fontSize: 'var(--text-base)',
                padding: 'var(--space-2)'
              }}
            />
          ) : (
            <div style={{
              fontSize: 'var(--text-lg)',
              fontWeight: 'var(--font-bold)',
              color: 'var(--color-text-primary)'
            }}>
              {typeof value === 'number' ? value.toFixed(2) : value}
              <span style={{ 
                fontSize: 'var(--text-xs)', 
                color: 'var(--color-text-secondary)',
                marginLeft: 'var(--space-2)',
                fontWeight: 'var(--font-normal)'
              }}>
                {label}
              </span>
            </div>
          )}
        </div>
        <button
          onClick={() => toggleEdit(key)}
          style={{
            background: isEditing ? 'var(--success-100)' : 'var(--gray-100)',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-2)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s'
          }}
          title={isEditing ? 'Guardar' : 'Editar'}
        >
          {isEditing ? (
            <Check size={16} color="var(--success-600)" />
          ) : (
            <Edit2 size={16} color="var(--gray-600)" />
          )}
        </button>
      </div>
    );
  };

  const confidenceColor = confidence === 'high' ? 'var(--success-600)' : 
                         confidence === 'medium' ? 'var(--warning-600)' : 
                         'var(--error-600)';

  const confidenceText = confidence === 'high' ? 'Alta ✓' : 
                        confidence === 'medium' ? 'Media' : 
                        'Baja';

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: 'var(--space-4)'
    }}>
      <div style={{
        background: 'var(--color-bg-primary)',
        borderRadius: 'var(--radius-xl)',
        maxWidth: '700px',
        width: '100%',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)'
      }}>
        {/* Header */}
        <div style={{
          padding: 'var(--space-6)',
          borderBottom: '1px solid var(--gray-200)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'linear-gradient(135deg, var(--hydro-50), var(--hydro-100))'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <CheckCircle size={28} color="var(--hydro-600)" />
              <h3 style={{
                fontSize: 'var(--text-xl)',
                fontWeight: 'var(--font-bold)',
                color: 'var(--color-text-primary)',
                margin: 0
              }}>
                Datos Extraídos del Análisis de Agua
              </h3>
            </div>
            <p style={{
              fontSize: 'var(--text-sm)',
              color: 'var(--color-text-secondary)',
              margin: 'var(--space-2) 0 0 0'
            }}>
              <span style={{ fontWeight: 'var(--font-semibold)' }}>Confianza: </span>
              <span style={{ color: confidenceColor, fontWeight: 'var(--font-bold)' }}>
                {confidenceText}
              </span>
              {notes && <span> • {notes}</span>}
            </p>
          </div>
          <button
            onClick={onCancel}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: 'var(--space-2)',
              color: 'var(--gray-500)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={24} />
          </button>
        </div>

        {/* Validation Warnings */}
        {validationWarnings && (
          <div style={{
            padding: 'var(--space-4) var(--space-6)',
            background: 'var(--warning-50)',
            borderBottom: '1px solid var(--warning-200)'
          }}>
            <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
              <AlertCircle size={20} color="var(--warning-600)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <p style={{
                  fontSize: 'var(--text-sm)',
                  fontWeight: 'var(--font-semibold)',
                  color: 'var(--warning-800)',
                  margin: '0 0 var(--space-1) 0'
                }}>
                  Advertencias de Validación:
                </p>
                <p style={{
                  fontSize: 'var(--text-sm)',
                  color: 'var(--warning-700)',
                  margin: 0
                }}>
                  {validationWarnings}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Data Fields */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          padding: 'var(--space-6)'
        }}>
          <p style={{
            fontSize: 'var(--text-sm)',
            color: 'var(--color-text-secondary)',
            marginBottom: 'var(--space-6)',
            fontStyle: 'italic',
            background: 'var(--hydro-50)',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-md)',
            borderLeft: '4px solid var(--hydro-500)'
          }}>
            💡 Revisa los datos extraídos y haz clic en <Edit2 size={14} style={{ display: 'inline', verticalAlign: 'middle' }} /> para editar cualquier valor antes de aceptar.
          </p>

          <div style={{
            display: 'grid',
            gap: 'var(--space-3)'
          }}>
            {waterFields.map(field => renderField(field))}
          </div>
        </div>

        {/* Footer Actions */}
        <div style={{
          padding: 'var(--space-6)',
          borderTop: '1px solid var(--gray-200)',
          display: 'flex',
          gap: 'var(--space-3)',
          justifyContent: 'flex-end',
          background: 'var(--color-bg-secondary)'
        }}>
          <Button
            variant="secondary"
            onClick={onCancel}
          >
            Cancelar
          </Button>
          <Button
            variant="primary"
            onClick={handleAccept}
            style={{
              background: 'linear-gradient(135deg, var(--hydro-500), var(--hydro-600))',
              color: '#fff'
            }}
          >
            Aceptar y Continuar
          </Button>
        </div>
      </div>
    </div>
  );
}

WaterAnalysisPreviewModal.propTypes = {
  extractedData: PropTypes.object.isRequired,
  confidence: PropTypes.oneOf(['high', 'medium', 'low']),
  validationWarnings: PropTypes.string,
  notes: PropTypes.string,
  onAccept: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired
};

export default WaterAnalysisPreviewModal;
