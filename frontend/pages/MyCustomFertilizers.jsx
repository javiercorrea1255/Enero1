import { useState, useEffect } from 'react';
import { FlaskConical, Plus, Edit2, Trash2, Save, X, AlertCircle, Check, ChevronDown, ChevronUp, Droplets, Layers } from 'lucide-react';
import api from '../services/api';
import useIsMobile from '../hooks/useIsMobile';
import '../styles/custom-fertilizers.css';

const ionLabels = {
  no3_meq: 'NO₃⁻',
  nh4_meq: 'NH₄⁺',
  h2po4_meq: 'H₂PO₄⁻',
  k_meq: 'K⁺',
  ca_meq: 'Ca²⁺',
  mg_meq: 'Mg²⁺',
  so4_meq: 'SO₄²⁻'
};

const microLabels = {
  fe_ppm: 'Fe',
  mn_ppm: 'Mn',
  zn_ppm: 'Zn',
  cu_ppm: 'Cu',
  b_ppm: 'B',
  mo_ppm: 'Mo'
};

const formOptions = [
  { value: 'solid', label: 'Sólido (g)' },
  { value: 'liquid', label: 'Líquido (mL)' }
];

const tankOptions = [
  { value: '', label: 'Sin asignar' },
  { value: 'A', label: 'Tanque A' },
  { value: 'B', label: 'Tanque B' }
];

const defaultFertilizer = {
  name: '',
  description: '',
  form: 'solid',
  no3_meq: 0, nh4_meq: 0, h2po4_meq: 0, k_meq: 0, ca_meq: 0, mg_meq: 0, so4_meq: 0,
  fe_ppm: 0, mn_ppm: 0, zn_ppm: 0, cu_ppm: 0, b_ppm: 0, mo_ppm: 0,
  density_g_ml: '',
  price_per_unit: '',
  currency: 'MXN',
  stock_tank: ''
};

const ionFields = ['no3_meq', 'nh4_meq', 'h2po4_meq', 'k_meq', 'ca_meq', 'mg_meq', 'so4_meq'];
const microFields = ['fe_ppm', 'mn_ppm', 'zn_ppm', 'cu_ppm', 'b_ppm', 'mo_ppm'];

export default function MyCustomFertilizers({ embedded = false }) {
  const [fertilizers, setFertilizers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState(defaultFertilizer);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [expandedSections, setExpandedSections] = useState({ macro: true, micro: false });
  const isMobile = useIsMobile(768);

  useEffect(() => {
    fetchFertilizers();
  }, []);

  const fetchFertilizers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/custom-fertilizers');
      setFertilizers(response || []);
    } catch (err) {
      setError('Error al cargar los fertilizantes');
      console.error('Error fetching fertilizers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError('El nombre es requerido');
      return;
    }

    const hasIons = ionFields.some(f => parseFloat(formData[f]) > 0);
    const hasMicros = microFields.some(f => parseFloat(formData[f]) > 0);
    if (!hasIons && !hasMicros) {
      setError('Debe ingresar al menos un valor de composición iónica o micronutrientes');
      return;
    }

    setSaving(true);
    setError(null);

    const numericFields = [...ionFields, ...microFields];
    const normalizedData = { ...formData };
    
    numericFields.forEach(field => {
      const val = normalizedData[field];
      normalizedData[field] = parseFloat(val) || 0;
    });
    
    if (normalizedData.density_g_ml === '' || normalizedData.density_g_ml === null) {
      normalizedData.density_g_ml = null;
    } else {
      normalizedData.density_g_ml = parseFloat(normalizedData.density_g_ml) || null;
    }
    
    if (normalizedData.price_per_unit === '' || normalizedData.price_per_unit === null) {
      normalizedData.price_per_unit = null;
    } else {
      normalizedData.price_per_unit = parseFloat(normalizedData.price_per_unit) || null;
    }

    if (!normalizedData.stock_tank) {
      normalizedData.stock_tank = null;
    }

    try {
      if (editingId) {
        await api.put(`/api/custom-fertilizers/${editingId}`, normalizedData);
        setSuccessMessage('Fertilizante actualizado correctamente');
      } else {
        await api.post('/api/custom-fertilizers', normalizedData);
        setSuccessMessage('Fertilizante guardado correctamente');
      }
      
      await fetchFertilizers();
      setShowForm(false);
      setEditingId(null);
      setFormData(defaultFertilizer);
      
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Error al guardar el fertilizante';
      setError(errMsg);
      console.error('Error saving fertilizer:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (fertilizer) => {
    setFormData({
      name: fertilizer.name || '',
      description: fertilizer.description || '',
      form: fertilizer.form || 'solid',
      no3_meq: fertilizer.no3_meq || 0,
      nh4_meq: fertilizer.nh4_meq || 0,
      h2po4_meq: fertilizer.h2po4_meq || 0,
      k_meq: fertilizer.k_meq || 0,
      ca_meq: fertilizer.ca_meq || 0,
      mg_meq: fertilizer.mg_meq || 0,
      so4_meq: fertilizer.so4_meq || 0,
      fe_ppm: fertilizer.fe_ppm || 0,
      mn_ppm: fertilizer.mn_ppm || 0,
      zn_ppm: fertilizer.zn_ppm || 0,
      cu_ppm: fertilizer.cu_ppm || 0,
      b_ppm: fertilizer.b_ppm || 0,
      mo_ppm: fertilizer.mo_ppm || 0,
      density_g_ml: fertilizer.density_g_ml || '',
      price_per_unit: fertilizer.price_per_unit || '',
      currency: fertilizer.currency || 'MXN',
      stock_tank: fertilizer.stock_tank || ''
    });
    setEditingId(fertilizer.id);
    setShowForm(true);
    setError(null);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Estás seguro de eliminar este fertilizante?')) return;
    
    try {
      await api.delete(`/api/custom-fertilizers/${id}`);
      setSuccessMessage('Fertilizante eliminado correctamente');
      await fetchFertilizers();
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      setError('Error al eliminar el fertilizante');
      console.error('Error deleting fertilizer:', err);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingId(null);
    setFormData(defaultFertilizer);
    setError(null);
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const getFormattedIons = (fertilizer) => {
    const ions = [];
    ionFields.forEach(field => {
      const val = fertilizer[field];
      if (val && val > 0) {
        ions.push(`${ionLabels[field]}: ${val.toFixed(2)}`);
      }
    });
    return ions.length > 0 ? ions.join(', ') : 'Sin composición';
  };

  const containerClass = embedded ? '' : 'data-module-container';

  return (
    <div className={containerClass}>
      {!embedded && (
        <div className="data-module-header">
          <div className="data-module-title-row">
            <FlaskConical size={28} className="data-module-icon" />
            <div>
              <h1 className="data-module-title">Mis Fertilizantes</h1>
              <p className="data-module-subtitle">
                Crea fertilizantes personalizados con su composición iónica para usar en Hidroponía y Fertirriego
              </p>
            </div>
          </div>
          <button
            className="data-module-add-btn"
            onClick={() => {
              setFormData(defaultFertilizer);
              setEditingId(null);
              setShowForm(true);
              setError(null);
            }}
          >
            <Plus size={18} />
            Nuevo Fertilizante
          </button>
        </div>
      )}

      {successMessage && (
        <div className="data-module-success">
          <Check size={18} />
          {successMessage}
        </div>
      )}

      {error && (
        <div className="data-module-error">
          <AlertCircle size={18} />
          {error}
          <button onClick={() => setError(null)} className="data-module-error-close">
            <X size={16} />
          </button>
        </div>
      )}

      {showForm && (
        <div className="data-module-form-card">
          <h3 className="data-module-form-title">
            {editingId ? 'Editar Fertilizante' : 'Nuevo Fertilizante'}
          </h3>
          
          <form onSubmit={handleSubmit}>
            <div className="data-module-form-grid">
              <div className="data-module-form-group data-module-form-full">
                <label className="data-module-label">Nombre *</label>
                <input
                  type="text"
                  className="data-module-input"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="Ej: Mi fertilizante especial"
                  required
                />
              </div>
              
              <div className="data-module-form-group data-module-form-full">
                <label className="data-module-label">Descripción (opcional)</label>
                <input
                  type="text"
                  className="data-module-input"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Descripción o notas"
                />
              </div>

              <div className="data-module-form-group">
                <label className="data-module-label">Tipo</label>
                <select
                  className="data-module-select"
                  value={formData.form}
                  onChange={(e) => handleInputChange('form', e.target.value)}
                >
                  {formOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div className="data-module-form-group">
                <label className="data-module-label">Tanque Stock (A/B)</label>
                <select
                  className="data-module-select"
                  value={formData.stock_tank}
                  onChange={(e) => handleInputChange('stock_tank', e.target.value)}
                >
                  {tankOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {formData.form === 'liquid' && (
                <div className="data-module-form-group">
                  <label className="data-module-label">Densidad (g/mL)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    className="data-module-input"
                    value={formData.density_g_ml}
                    onChange={(e) => handleInputChange('density_g_ml', e.target.value)}
                    placeholder="1.0"
                  />
                </div>
              )}

              <div className="data-module-form-group">
                <label className="data-module-label">
                  Precio por {formData.form === 'solid' ? 'kg' : 'L'} ({formData.currency})
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  className="data-module-input"
                  value={formData.price_per_unit}
                  onChange={(e) => handleInputChange('price_per_unit', e.target.value)}
                  placeholder="0.00"
                />
              </div>
            </div>

            <div className="data-module-section">
              <button
                type="button"
                className="data-module-section-header"
                onClick={() => toggleSection('macro')}
              >
                <Layers size={18} />
                <span>Composición Iónica (meq/g o meq/mL)</span>
                {expandedSections.macro ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
              
              {expandedSections.macro && (
                <div className="data-module-section-content">
                  <p className="data-module-section-hint">
                    Ingresa los valores en miliequivalentes por gramo (sólidos) o por mL (líquidos)
                  </p>
                  <div className="data-module-ion-grid">
                    {ionFields.map(field => (
                      <div key={field} className="data-module-ion-field">
                        <label className="data-module-ion-label">{ionLabels[field]}</label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          className="data-module-ion-input"
                          value={formData[field]}
                          onChange={(e) => handleInputChange(field, e.target.value)}
                          placeholder="0.00"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="data-module-section">
              <button
                type="button"
                className="data-module-section-header"
                onClick={() => toggleSection('micro')}
              >
                <Droplets size={18} />
                <span>Micronutrientes (ppm por g o mL)</span>
                {expandedSections.micro ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
              
              {expandedSections.micro && (
                <div className="data-module-section-content">
                  <p className="data-module-section-hint">
                    Ingresa los valores en ppm por gramo (sólidos) o por mL (líquidos)
                  </p>
                  <div className="data-module-ion-grid">
                    {microFields.map(field => (
                      <div key={field} className="data-module-ion-field">
                        <label className="data-module-ion-label">{microLabels[field]}</label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          className="data-module-ion-input"
                          value={formData[field]}
                          onChange={(e) => handleInputChange(field, e.target.value)}
                          placeholder="0.00"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="data-module-form-actions">
              <button
                type="button"
                className="data-module-btn-cancel"
                onClick={handleCancel}
                disabled={saving}
              >
                <X size={18} />
                Cancelar
              </button>
              <button
                type="submit"
                className="data-module-btn-save"
                disabled={saving}
              >
                <Save size={18} />
                {saving ? 'Guardando...' : (editingId ? 'Actualizar' : 'Guardar')}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="data-module-loading">
          <div className="data-module-spinner"></div>
          <p>Cargando fertilizantes...</p>
        </div>
      ) : fertilizers.length === 0 ? (
        <div className="data-module-empty">
          <FlaskConical size={48} className="data-module-empty-icon" />
          <h3>No tienes fertilizantes personalizados</h3>
          <p>Crea tu primer fertilizante para usarlo en los calculadores de Hidroponía y Fertirriego</p>
          {!showForm && (
            <button
              className="data-module-add-btn"
              onClick={() => {
                setFormData(defaultFertilizer);
                setEditingId(null);
                setShowForm(true);
              }}
            >
              <Plus size={18} />
              Crear Primer Fertilizante
            </button>
          )}
        </div>
      ) : (
        <div className="data-module-list">
          {fertilizers.map(fertilizer => (
            <div key={fertilizer.id} className="data-module-card">
              <div className="data-module-card-header">
                <div className="data-module-card-title-row">
                  <FlaskConical size={20} className="data-module-card-icon" />
                  <div>
                    <h3 className="data-module-card-title">{fertilizer.name}</h3>
                    {fertilizer.description && (
                      <p className="data-module-card-subtitle">{fertilizer.description}</p>
                    )}
                  </div>
                </div>
                <div className="data-module-card-actions">
                  <button
                    className="data-module-action-btn data-module-action-edit"
                    onClick={() => handleEdit(fertilizer)}
                    title="Editar"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    className="data-module-action-btn data-module-action-delete"
                    onClick={() => handleDelete(fertilizer.id)}
                    title="Eliminar"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              
              <div className="data-module-card-body">
                <div className="data-module-card-badges">
                  <span className="data-module-badge data-module-badge-blue">
                    {fertilizer.form === 'solid' ? 'Sólido' : 'Líquido'}
                  </span>
                  {fertilizer.stock_tank && (
                    <span className="data-module-badge data-module-badge-green">
                      Tanque {fertilizer.stock_tank}
                    </span>
                  )}
                  {fertilizer.price_per_unit && (
                    <span className="data-module-badge data-module-badge-yellow">
                      ${fertilizer.price_per_unit.toFixed(2)}/{fertilizer.form === 'solid' ? 'kg' : 'L'}
                    </span>
                  )}
                </div>
                
                <div className="data-module-card-ions">
                  <span className="data-module-card-ions-label">Composición:</span>
                  <span className="data-module-card-ions-value">{getFormattedIons(fertilizer)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
