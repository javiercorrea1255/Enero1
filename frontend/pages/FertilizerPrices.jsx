import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/auth';
import useIsMobile from '../hooks/useIsMobile';
import { 
  DollarSign, 
  Save, 
  RotateCcw, 
  AlertCircle, 
  Check,
  Filter,
  Search,
  ChevronDown,
  ChevronUp,
  Beaker,
  Droplets,
  Leaf,
  FlaskConical,
  Globe
} from 'lucide-react';
import '../styles/data-modules.css';

const API_URL = import.meta.env.VITE_API_URL || '';

const FERTILIZER_CATEGORIES = {
  acid: { label: 'Ácidos', icon: Droplets, color: '#ef4444' },
  salt: { label: 'Sales Fertilizantes', icon: Beaker, color: '#3b82f6' },
  micronutrient: { label: 'Micronutrientes', icon: Leaf, color: '#22c55e' },
  micronutrient_mix: { label: 'Mezclas de Micronutrientes', icon: FlaskConical, color: '#8b5cf6' },
  chelate: { label: 'Quelatos', icon: FlaskConical, color: '#f59e0b' }
};

let priceSyncChannel = null;

const getPriceSyncChannel = () => {
  if (typeof window === 'undefined' || typeof BroadcastChannel === 'undefined') {
    return null;
  }
  if (!priceSyncChannel) {
    priceSyncChannel = new BroadcastChannel('fertilizer-prices');
  }
  return priceSyncChannel;
};

const FertilizerPrices = ({ embedded = false }) => {
  const { isAuthenticated } = useAuth();
  const isMobile = useIsMobile(768);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [currencies, setCurrencies] = useState([]);
  const [selectedCurrency, setSelectedCurrency] = useState('MXN');
  const [currencyInfo, setCurrencyInfo] = useState({});
  const [prices, setPrices] = useState([]);
  const [editedPrices, setEditedPrices] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [message, setMessage] = useState({ type: '', text: '' });
  const [hasChanges, setHasChanges] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState({});

  const notifyPriceSync = (payload = {}) => {
    const detail = {
      ...payload,
      timestamp: Date.now()
    };
    window.dispatchEvent(new CustomEvent('fertilizer-prices-updated', { detail }));
    try {
      localStorage.setItem('fertilizer-prices-sync', JSON.stringify(detail));
    } catch (error) {
      console.warn('[FertilizerPrices] Unable to persist price sync event', error);
    }
    const channel = getPriceSyncChannel();
    if (channel) {
      channel.postMessage(detail);
    }
  };

  const fetchCurrencies = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/fertilizer-prices/currencies`);
      if (response.ok) {
        const data = await response.json();
        setCurrencies(data.currencies || []);
      }
    } catch (error) {
      console.error('Error fetching currencies:', error);
    }
  }, []);

  const fetchPrices = useCallback(async () => {
    const token = authService.getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/fertilizer-prices/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setPrices(data.prices || []);
        setSelectedCurrency(data.currency || 'MXN');
        setCurrencyInfo(data.currency_info || {});
        setEditedPrices({});
        setHasChanges(false);
      } else if (response.status === 401) {
        setMessage({ type: 'error', text: 'Sesión expirada. Por favor, inicia sesión nuevamente.' });
      }
    } catch (error) {
      console.error('Error fetching prices:', error);
      setMessage({ type: 'error', text: 'Error al cargar los precios' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrencies();
  }, [fetchCurrencies]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchPrices();
    }
  }, [isAuthenticated, fetchPrices]);

  const handlePriceChange = (fertilizerId, field, value) => {
    const numValue = value === '' ? null : parseFloat(value);
    setEditedPrices(prev => ({
      ...prev,
      [fertilizerId]: {
        ...prev[fertilizerId],
        [field]: numValue
      }
    }));
    setHasChanges(true);
  };

  const handleCurrencyChange = async (newCurrency) => {
    const token = authService.getToken();
    
    if (!token) {
      setMessage({ type: 'error', text: 'Debes iniciar sesión para cambiar la moneda' });
      setTimeout(() => setMessage({ type: '', text: '' }), 4000);
      return;
    }
    
    setSelectedCurrency(newCurrency);
    const currInfo = currencies.find(c => c.code === newCurrency);
    setCurrencyInfo(currInfo || {});
    setEditedPrices({});
    setHasChanges(false);
    
    try {
      setLoading(true);
      
      // Update user's preferred currency in the backend first
      console.log('[FertilizerPrices] Updating currency to:', newCurrency);
      const response = await fetch(`${API_URL}/api/fertilizer-prices/settings`, {
        method: 'PUT',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          preferred_currency: newCurrency,
          show_cost_in_results: true
        })
      });
      
      console.log('[FertilizerPrices] Currency update response:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('[FertilizerPrices] Currency update failed:', errorText);
        throw new Error('Failed to update currency preference');
      }
      
      const currName = currencies.find(c => c.code === newCurrency)?.name || newCurrency;
      setMessage({ type: 'success', text: `Moneda cambiada a ${newCurrency} (${currName})` });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
      
      // Then fetch the prices for the new currency (this now uses the updated preference)
      await fetchPrices();
      notifyPriceSync({ reason: 'currency-change', currency: newCurrency });
    } catch (error) {
      console.error('[FertilizerPrices] Error updating currency:', error);
      setMessage({ type: 'error', text: 'Error al cambiar la moneda' });
      setTimeout(() => setMessage({ type: '', text: '' }), 4000);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyMarketPrices = async () => {
    try {
      const response = await fetch(`${API_URL}/api/fertilizer-prices/defaults/${selectedCurrency}`, {
        headers: { 'Authorization': `Bearer ${authService.getToken()}` }
      });
      if (response.ok) {
        const data = await response.json();
        const newEditedPrices = {};
        data.defaults.forEach(d => {
          newEditedPrices[d.fertilizer_id] = {
            price_per_kg: d.price_per_kg,
            price_per_liter: d.price_per_liter
          };
        });
        setEditedPrices(newEditedPrices);
        setHasChanges(true);
        setMessage({ type: 'success', text: `Precios de mercado en ${selectedCurrency} aplicados. Guarda para confirmar.` });
        setTimeout(() => setMessage({ type: '', text: '' }), 4000);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error al cargar precios de mercado' });
    }
  };

  const handleSave = async () => {
    const token = authService.getToken();
    if (!token) {
      setMessage({ type: 'error', text: 'Debes iniciar sesión para guardar' });
      return;
    }

    setSaving(true);
    try {
      const priceUpdates = Object.entries(editedPrices).map(([fertilizerId, priceData]) => ({
        fertilizer_id: fertilizerId,
        price_per_kg: priceData.price_per_kg,
        price_per_liter: priceData.price_per_liter
      }));

      const response = await fetch(`${API_URL}/api/fertilizer-prices/bulk`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          currency: selectedCurrency,
          prices: priceUpdates
        })
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Precios guardados correctamente' });
        await fetchPrices();
        notifyPriceSync({ reason: 'prices-saved', currency: selectedCurrency });
      } else {
        throw new Error('Failed to save');
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error al guardar los precios' });
    } finally {
      setSaving(false);
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    }
  };

  const handleResetAll = async () => {
    if (!window.confirm('¿Restaurar todos los precios a los valores por defecto?')) return;
    
    const token = authService.getToken();
    try {
      const response = await fetch(`${API_URL}/api/fertilizer-prices/reset`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        setMessage({ type: 'success', text: 'Precios restaurados' });
        await fetchPrices();
        notifyPriceSync({ reason: 'prices-reset', currency: selectedCurrency });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error al restaurar' });
    }
    setTimeout(() => setMessage({ type: '', text: '' }), 3000);
  };

  const getDisplayPrice = (price, field) => {
    if (editedPrices[price.fertilizer_id]?.[field] !== undefined) {
      return editedPrices[price.fertilizer_id][field];
    }
    return price[field];
  };

  const toggleCategory = (category) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  const filteredPrices = prices.filter(p => {
    const matchesSearch = p.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          p.fertilizer_id?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || p.type === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const groupedPrices = filteredPrices.reduce((acc, p) => {
    const category = p.type || 'salt';
    if (!acc[category]) acc[category] = [];
    acc[category].push(p);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="dm-loading" style={{ minHeight: '400px' }}>
        <div className="dm-spinner"></div>
        <p className="dm-loading-text">Cargando precios...</p>
      </div>
    );
  }

  return (
    <div className={`dm-container ${embedded ? 'embedded' : ''}`} style={{ background: embedded ? 'transparent' : '#f8fafc', minHeight: embedded ? 'auto' : '100vh' }}>
      {!embedded && (
        <div className="dm-header">
          <div className="dm-header-content">
            <div className="dm-header-title">
              <div className="dm-header-icon">
                <DollarSign size={24} color="white" />
              </div>
              <div>
                <h1>Configuración de Precios</h1>
                <p>Configura los precios de fertilizantes en tu moneda local</p>
              </div>
            </div>
            <div className="dm-header-actions">
              <button onClick={handleApplyMarketPrices} className="dm-btn dm-btn-white" disabled={saving}>
                <Globe size={18} />
                Precios de Mercado
              </button>
            </div>
          </div>
        </div>
      )}

      {message.text && (
        <div className={`dm-alert ${message.type === 'success' ? 'dm-alert-success' : 'dm-alert-error'}`}>
          {message.type === 'success' ? <Check size={20} /> : <AlertCircle size={20} />}
          <div className="dm-alert-content">{message.text}</div>
        </div>
      )}

      <div className="dm-card" style={{ marginBottom: '20px' }}>
        <div className="dm-card-body">
          <div className="dm-toolbar" style={{ flexWrap: 'wrap' }}>
            <div className="dm-form-group" style={{ minWidth: '180px' }}>
              <label className="dm-label">Moneda</label>
              <select
                value={selectedCurrency}
                onChange={(e) => handleCurrencyChange(e.target.value)}
                className="dm-select"
              >
                {currencies.map(curr => (
                  <option key={curr.code} value={curr.code}>
                    {curr.flag} {curr.code} - {curr.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="dm-form-group dm-toolbar-search">
              <label className="dm-label">Buscar</label>
              <div className="dm-input-with-icon">
                <Search size={18} className="dm-input-icon" />
                <input
                  type="text"
                  placeholder="Buscar fertilizante..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="dm-input"
                />
              </div>
            </div>

            <div className="dm-form-group" style={{ minWidth: '160px' }}>
              <label className="dm-label">Categoría</label>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="dm-select"
              >
                <option value="all">Todas</option>
                {Object.entries(FERTILIZER_CATEGORIES).map(([key, cat]) => (
                  <option key={key} value={key}>{cat.label}</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', gap: '8px', marginLeft: 'auto', alignItems: 'flex-end' }}>
              <button onClick={handleResetAll} disabled={saving} className="dm-btn dm-btn-secondary">
                <RotateCcw size={18} />
                {!isMobile && 'Restaurar'}
              </button>
              <button onClick={handleSave} disabled={saving || !hasChanges} className="dm-btn dm-btn-primary">
                <Save size={18} />
                {saving ? 'Guardando...' : (isMobile ? 'Guardar' : 'Guardar Cambios')}
              </button>
            </div>
          </div>
        </div>
      </div>

      {Object.entries(groupedPrices).map(([category, categoryPrices]) => {
        const catInfo = FERTILIZER_CATEGORIES[category] || { label: category, color: '#6b7280' };
        const CatIcon = catInfo.icon || Beaker;
        const isExpanded = expandedCategories[category] !== false;

        return (
          <div key={category} className="dm-card" style={{ marginBottom: '16px' }}>
            <div 
              className="dm-section-header" 
              onClick={() => toggleCategory(category)}
              style={{ 
                background: `linear-gradient(135deg, ${catInfo.color}15 0%, ${catInfo.color}08 100%)`,
                borderColor: `${catInfo.color}30`,
                marginBottom: 0,
                borderRadius: isExpanded ? 'var(--dm-radius-lg) var(--dm-radius-lg) 0 0' : 'var(--dm-radius-lg)'
              }}
            >
              <h3 style={{ color: 'var(--dm-gray-800)' }}>
                <CatIcon size={20} style={{ color: catInfo.color }} />
                {catInfo.label}
                <span className="dm-badge" style={{ background: catInfo.color, color: 'white', marginLeft: '12px' }}>
                  {categoryPrices.length}
                </span>
              </h3>
              {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </div>

            {isExpanded && (
              <div className="dm-card-body" style={{ padding: 0 }}>
                <div className="dm-table-container" style={{ border: 'none', borderRadius: 0 }}>
                  <table className="dm-table">
                    <thead>
                      <tr>
                        <th>Fertilizante</th>
                        <th style={{ textAlign: 'right' }}>Precio/kg</th>
                        {categoryPrices.some(p => p.form === 'liquid') && (
                          <th style={{ textAlign: 'right' }}>Precio/L</th>
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {categoryPrices.map(price => (
                        <tr key={price.fertilizer_id}>
                          <td>
                            <div style={{ fontWeight: '500' }}>{price.name}</div>
                            <div className="dm-text-sm dm-text-muted">{price.fertilizer_id}</div>
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
                              <span className="dm-text-muted">{currencyInfo.symbol || '$'}</span>
                              <input
                                type="number"
                                step="0.01"
                                min="0"
                                value={getDisplayPrice(price, 'price_per_kg') ?? ''}
                                onChange={(e) => handlePriceChange(price.fertilizer_id, 'price_per_kg', e.target.value)}
                                className="dm-input dm-input-sm"
                                style={{ width: '100px', textAlign: 'right' }}
                              />
                            </div>
                          </td>
                          {categoryPrices.some(p => p.form === 'liquid') && (
                            <td style={{ textAlign: 'right' }}>
                              {price.form === 'liquid' ? (
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
                                  <span className="dm-text-muted">{currencyInfo.symbol || '$'}</span>
                                  <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    value={getDisplayPrice(price, 'price_per_liter') ?? ''}
                                    onChange={(e) => handlePriceChange(price.fertilizer_id, 'price_per_liter', e.target.value)}
                                    className="dm-input dm-input-sm"
                                    style={{ width: '100px', textAlign: 'right' }}
                                  />
                                </div>
                              ) : (
                                <span className="dm-text-muted">—</span>
                              )}
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        );
      })}

      {filteredPrices.length === 0 && (
        <div className="dm-empty-state">
          <div className="dm-empty-state-icon">
            <Search size={32} />
          </div>
          <h3>No se encontraron fertilizantes</h3>
          <p>Intenta con otro término de búsqueda o cambia el filtro de categoría</p>
        </div>
      )}
    </div>
  );
};

export default FertilizerPrices;
