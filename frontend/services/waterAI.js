import { apiFetch } from './api';
import { authService } from './auth';

/**
 * Service for HidroponIA Vision - AI-powered water analysis and fertilization recommendations
 * Handles communication with /api/hydroponia-vision endpoints
 */
export const waterAIService = {
  
  // ==================== WATER ANALYSIS UPLOAD ====================
  
  /**
   * Upload water analysis document (PDF/JPG/PNG) and extract parameters using AI
   * @param {File} file - Document file
   * @param {number|null} projectId - Optional project ID
   * @returns {Promise<Object>} Analysis data with extracted parameters
   */
  async uploadAnalysis(file, projectId = null) {
    const formData = new FormData();
    formData.append('file', file);
    if (projectId) {
      formData.append('project_id', projectId.toString());
    }
    
    const token = authService.getToken();
    const response = await fetch('/api/hydroponia-vision/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });
    
    if (response.status === 401) {
      authService.clearAuth();
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al subir el análisis');
    }
    
    return response.json();
  },

  /**
   * Update extracted parameters manually
   * @param {number} analysisId - Analysis ID
   * @param {Object} parameters - Updated parameters
   * @returns {Promise<Object>} Updated analysis
   */
  async updateParameters(analysisId, parameters) {
    const response = await apiFetch(`/api/hydroponia-vision/analyses/${analysisId}/parameters`, {
      method: 'PUT',
      body: JSON.stringify(parameters)
    });
    return response.json();
  },

  // ==================== CROP CATALOG ====================
  
  /**
   * Get all available hydroponic crops with phenological stages and NPK requirements
   * @returns {Promise<Array>} List of crops
   */
  async getCropsCatalog() {
    const response = await apiFetch('/api/hydroponia-vision/crops');
    const data = await response.json();
    return data.crops || [];
  },

  // ==================== AI RECOMMENDATIONS ====================
  
  /**
   * Generate AI-powered fertilization recommendation
   * @param {Object} requestData - { analysis_id, crop_name, growth_stage, methodology }
   * @returns {Promise<Object>} Recommendation with dosages and insights
   */
  async generateRecommendation(requestData) {
    console.log('🔵 waterAIService.generateRecommendation - INICIO');
    console.log('🔵 Request Data:', JSON.stringify(requestData, null, 2));
    
    // Timeout de 120 segundos para OpenAI
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.error('⏰ TIMEOUT: La petición tardó más de 120 segundos');
      controller.abort();
    }, 120000);
    
    try {
      console.log('🔵 Enviando POST a /api/hydroponia-vision/recommendation...');
      const response = await apiFetch('/api/hydroponia-vision/recommendation', {
        method: 'POST',
        body: JSON.stringify(requestData),
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      console.log('🔵 Respuesta recibida, parseando JSON...');
      const data = await response.json();
      console.log('✅ Recomendación generada exitosamente');
      return data;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        console.error('❌ ERROR: Timeout - OpenAI tardó demasiado');
        throw new Error('La generación de la recomendación está tardando más de lo esperado. Esto puede deberse a que OpenAI está procesando el análisis. Por favor intenta nuevamente en unos momentos.');
      }
      console.error('❌ ERROR en generateRecommendation:', error);
      throw error;
    }
  },

  /**
   * Get recommendation details
   * @param {number} recommendationId - Recommendation ID
   * @returns {Promise<Object>} Recommendation details
   */
  async getRecommendation(recommendationId) {
    const response = await apiFetch(`/api/hydroponia-vision/recommendations/${recommendationId}`);
    return response.json();
  },

  // ==================== PDF REPORTS ====================
  
  /**
   * Generate professional PDF report
   * @param {number} recommendationId - Recommendation ID
   * @param {Object} options - Report options
   * @returns {Promise<Object>} Report metadata
   */
  async generateReport(recommendationId, options = {}) {
    const response = await apiFetch('/api/hydroponia-vision/generate-report', {
      method: 'POST',
      body: JSON.stringify({
        recommendation_id: recommendationId,
        ...options
      })
    });
    return response.json();
  },

  /**
   * Download report PDF
   * @param {number} reportId - Report ID
   * @returns {Promise<Blob>} PDF file
   */
  async downloadReport(reportId) {
    const token = authService.getToken();
    const response = await fetch(`/api/hydroponia-vision/reports/${reportId}/download`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Error al descargar el reporte');
    }
    
    return response.blob();
  },

  // ==================== USER HISTORY ====================
  
  /**
   * Get user's water analyses history
   * @param {Object} params - Query parameters { limit, offset, status }
   * @returns {Promise<Object>} Analyses list with pagination
   */
  async getUserAnalyses(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = `/api/hydroponia-vision/analyses${queryString ? `?${queryString}` : ''}`;
    const response = await apiFetch(url);
    return response.json();
  },

  /**
   * Get user's recommendations history
   * @param {Object} params - Query parameters { limit, offset }
   * @returns {Promise<Object>} Recommendations list with pagination
   */
  async getUserRecommendations(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = `/api/hydroponia-vision/recommendations${queryString ? `?${queryString}` : ''}`;
    const response = await apiFetch(url);
    return response.json();
  },

  /**
   * Get analysis details
   * @param {number} analysisId - Analysis ID
   * @returns {Promise<Object>} Analysis details
   */
  async getAnalysis(analysisId) {
    const response = await apiFetch(`/api/hydroponia-vision/analyses/${analysisId}`);
    return response.json();
  },

  /**
   * Delete analysis
   * @param {number} analysisId - Analysis ID
   * @returns {Promise<void>}
   */
  async deleteAnalysis(analysisId) {
    await apiFetch(`/api/hydroponia-vision/analyses/${analysisId}`, {
      method: 'DELETE'
    });
  },

  // ==================== HELPER METHODS ====================
  
  /**
   * Format parameter value for display
   * @param {number|null} value - Parameter value
   * @param {string} unit - Unit of measurement
   * @returns {string} Formatted value
   */
  formatParameter(value, unit = '') {
    if (value === null || value === undefined) {
      return 'N/A';
    }
    return `${value.toFixed(2)} ${unit}`;
  },

  /**
   * Get quality assessment for water parameter
   * @param {string} parameter - Parameter name
   * @param {number} value - Parameter value
   * @returns {Object} { status: 'good'|'warning'|'alert', message: string }
   */
  getParameterQuality(parameter, value) {
    const ranges = {
      ph: { min: 5.5, max: 6.5, optimal: [5.8, 6.2] },
      ec_ms_cm: { min: 0.5, max: 3.0, optimal: [1.5, 2.5] },
      calcium_ppm: { min: 40, max: 200, optimal: [100, 150] },
      magnesium_ppm: { min: 20, max: 80, optimal: [40, 60] }
    };
    
    const range = ranges[parameter];
    if (!range || value === null || value === undefined) {
      return { status: 'neutral', message: 'Sin datos suficientes' };
    }
    
    if (value >= range.optimal[0] && value <= range.optimal[1]) {
      return { status: 'good', message: 'Valor óptimo' };
    } else if (value >= range.min && value <= range.max) {
      return { status: 'warning', message: 'Valor aceptable' };
    } else {
      return { status: 'alert', message: 'Requiere ajuste' };
    }
  }
};
