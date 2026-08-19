/**
 * Documents API — Functions for document upload and retrieval.
 */
import apiClient from './client';

export const documentsApi = {
  upload: (caseId, file, documentType = 'OTHER') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    return apiClient.post(`/cases/${caseId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  listByCase: (caseId) => apiClient.get(`/cases/${caseId}/documents`),
  getById: (docId) => apiClient.get(`/documents/${docId}`),
  delete: (docId) => apiClient.delete(`/documents/${docId}`),
};
