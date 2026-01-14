import { apiFetch } from './api';

export const analysesService = {
  async getSoilAnalyses(plotId) {
    const response = await apiFetch(`/api/soil-analysis/plot/${plotId}`);
    return response.json();
  },

  async createSoilAnalysis(data) {
    const response = await apiFetch('/api/soil-analysis', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    return response.json();
  },

  async updateSoilAnalysis(id, data) {
    const response = await apiFetch(`/api/soil-analysis/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
    return response.json();
  },

  async deleteSoilAnalysis(id) {
    await apiFetch(`/api/soil-analysis/${id}`, { method: 'DELETE' });
  },

  async getFoliarAnalyses(plotId) {
    const response = await apiFetch(`/api/foliar-analysis/plot/${plotId}`);
    return response.json();
  },

  async createFoliarAnalysis(data) {
    const response = await apiFetch('/api/foliar-analysis', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    return response.json();
  },

  async updateFoliarAnalysis(id, data) {
    const response = await apiFetch(`/api/foliar-analysis/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
    return response.json();
  },

  async deleteFoliarAnalysis(id) {
    await apiFetch(`/api/foliar-analysis/${id}`, { method: 'DELETE' });
  },
};
