import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { X, CheckCircle, AlertCircle, Edit2, Check } from 'lucide-react';
import Button from './Button';
import Input from './Input';

/**
 * AnalysisDataPreviewModal Component
 * 
 * Displays extracted soil analysis data in organized categories
 * with edit capability before accepting
 */
function AnalysisDataPreviewModal({ 
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
    // Handle string fields vs numeric fields based on original data type
    const originalValue = extractedData[field];
    const isStringField = typeof originalValue === 'string' && isNaN(parseFloat(originalValue));
    
    setEditableData(prev => ({
      ...prev,
      [field]: value === '' ? null : (isStringField ? value : parseFloat(value))
    }));
  };

  const toggleEdit = (field) => {
    setEditingField(editingField === field ? null : field);
  };

  const handleAccept = () => {
    onAccept(editableData);
  };

  // Organize fields by category
  const categories = {
    'Propiedades Básicas': {
      fields: ['ph', 'soil_ec_ms_cm', 'texture', 'organic_matter', 'cec'],
      labels: {
        ph: 'pH',
        soil_ec_ms_cm: 'EC (mS/cm)',
        texture: 'Textura',
        organic_matter: 'Materia Orgánica (%)',
        cec: 'CEC (meq/100g)'
      }
    },
    'Nutrientes Primarios (N-P-K)': {
      fields: ['soil_n_ppm', 'soil_p_ppm', 'soil_k_ppm'],
      labels: {
        soil_n_ppm: 'Nitrógeno (ppm)',
        soil_p_ppm: 'Fósforo (ppm)',
        soil_k_ppm: 'Potasio (ppm)'
      }
    },
    'Nutrientes Secundarios': {
      fields: ['soil_ca_ppm', 'soil_mg_ppm', 'soil_s_ppm', 'soil_na_ppm'],
      labels: {
        soil_ca_ppm: 'Calcio (ppm)',
        soil_mg_ppm: 'Magnesio (ppm)',
        soil_s_ppm: 'Azufre (ppm)',
        soil_na_ppm: 'Sodio (ppm)'
      }
    },
    'Micronutrientes': {
      fields: ['soil_fe_ppm', 'soil_zn_ppm', 'soil_cu_ppm', 'soil_mn_ppm', 'soil_b_ppm'],
      labels: {
        soil_fe_ppm: 'Fierro (ppm)',
        soil_zn_ppm: 'Zinc (ppm)',
        soil_cu_ppm: 'Cobre (ppm)',
        soil_mn_ppm: 'Manganeso (ppm)',
        soil_b_ppm: 'Boro (ppm)'
      }
    },
    'Propiedades Físicas': {
      fields: ['sar', 'psi', 'saturation_pct', 'field_capacity', 'wilting_point', 'sand_pct', 'silt_pct', 'clay_pct'],
      labels: {
        sar: 'SAR',
        psi: 'PSI (%)',
        saturation_pct: 'Saturación (%)',
        field_capacity: 'Capacidad de Campo (%)',
        wilting_point: 'Punto de Marchitez (%)',
        sand_pct: 'Arena (%)',
        silt_pct: 'Limo (%)',
        clay_pct: 'Arcilla (%)'
      }
    },
    'Extracto Saturado - Aniones (meq/L)': {
      fields: ['soil_no3_meq_l', 'soil_so4_meq_l', 'soil_cl_meq_l', 'soil_hco3_meq_l', 'soil_co3_meq_l'],
      labels: {
        soil_no3_meq_l: 'NO₃⁻',
        soil_so4_meq_l: 'SO₄²⁻',
        soil_cl_meq_l: 'Cl⁻',
        soil_hco3_meq_l: 'HCO₃⁻',
        soil_co3_meq_l: 'CO₃²⁻'
      }
    },
    'Extracto Saturado - Cationes (meq/L)': {
      fields: ['soil_ca_meq_l', 'soil_mg_meq_l', 'soil_k_meq_l', 'soil_na_meq_l'],
      labels: {
        soil_ca_meq_l: 'Ca²⁺',
        soil_mg_meq_l: 'Mg²⁺',
        soil_k_meq_l: 'K⁺',
        soil_na_meq_l: 'Na⁺'
      }
    }
  };

  const renderField = (field, label) => {
    const value = editableData[field];
    const isEditing = editingField === field;
    const hasValue = value !== null && value !== undefined;

    if (!hasValue) return null;

    // Determine input type based on original data type
    const originalValue = extractedData[field];
    const isStringField = typeof originalValue === 'string' && isNaN(parseFloat(originalValue));

    return (
      <div key={field} style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-3)',
        padding: 'var(--space-3)',
        background: 'var(--color-bg-secondary)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--gray-200)'
      }}>
        <div style={{ flex: 1 }}>
          <div style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--color-text-secondary)',
            marginBottom: 'var(--space-1)',
            fontWeight: 'var(--font-medium)'
          }}>
            {label}
          </div>
          {isEditing ? (
            <Input
              name={field}
              type={isStringField ? 'text' : 'number'}
              value={value !== null && value !== undefined ? String(value) : ''}
              onChange={(e) => handleFieldChange(field, e.target.value)}
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
              {value}
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={() => toggleEdit(field)}
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

  const renderCategory = (categoryName, categoryData) => {
    const { fields, labels } = categoryData;
    const visibleFields = fields.filter(field => 
      editableData[field] !== null && editableData[field] !== undefined
    );

    if (visibleFields.length === 0) return null;

    return (
      <div key={categoryName} style={{ marginBottom: 'var(--space-6)' }}>
        <h4 style={{
          fontSize: 'var(--text-base)',
          fontWeight: 'var(--font-bold)',
          color: 'var(--color-text-primary)',
          marginBottom: 'var(--space-3)',
          paddingBottom: 'var(--space-2)',
          borderBottom: '2px solid var(--soil-primary)'
        }}>
          {categoryName}
        </h4>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
          gap: 'var(--space-3)'
        }}>
          {visibleFields.map(field => renderField(field, labels[field]))}
        </div>
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
        maxWidth: '900px',
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
          justifyContent: 'space-between'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <CheckCircle size={28} color="var(--success-600)" />
              <h3 style={{
                fontSize: 'var(--text-xl)',
                fontWeight: 'var(--font-bold)',
                color: 'var(--color-text-primary)',
                margin: 0
              }}>
                Datos Extraídos del Análisis
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
            type="button"
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

        {/* Data Categories */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          padding: 'var(--space-6)'
        }}>
          <p style={{
            fontSize: 'var(--text-sm)',
            color: 'var(--color-text-secondary)',
            marginBottom: 'var(--space-6)',
            fontStyle: 'italic'
          }}>
            Revisa los datos extraídos y haz clic en <Edit2 size={14} style={{ display: 'inline', verticalAlign: 'middle' }} /> para editar cualquier valor antes de aceptar.
          </p>

          {Object.entries(categories).map(([categoryName, categoryData]) => 
            renderCategory(categoryName, categoryData)
          )}
        </div>

        {/* Footer Actions */}
        <div style={{
          padding: 'var(--space-6)',
          borderTop: '1px solid var(--gray-200)',
          display: 'flex',
          gap: 'var(--space-3)',
          justifyContent: 'flex-end'
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
          >
            Aceptar y Continuar
          </Button>
        </div>
      </div>
    </div>
  );
}

AnalysisDataPreviewModal.propTypes = {
  extractedData: PropTypes.object.isRequired,
  confidence: PropTypes.oneOf(['high', 'medium', 'low']),
  validationWarnings: PropTypes.string,
  notes: PropTypes.string,
  onAccept: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired
};

export default AnalysisDataPreviewModal;
