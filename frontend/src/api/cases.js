/**
 * Cases API — Functions for case CRUD operations.
 */
import apiClient from './client';

export const casesApi = {
  create: (data) => apiClient.post('/cases', data),
  list: () => apiClient.get('/cases'),
  getById: (caseId) => apiClient.get(`/cases/${caseId}`),
  delete: (caseId) => apiClient.delete(`/cases/${caseId}`),
};
