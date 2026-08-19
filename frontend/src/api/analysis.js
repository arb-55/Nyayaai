/**
 * Analysis API — Functions for triggering analysis and retrieving entities, evidence findings, and reports.
 */
import apiClient from './client';

export const analysisApi = {
  trigger: (caseId) => apiClient.post(`/cases/${caseId}/analyze`),
  getForCase: (caseId) => apiClient.get(`/cases/${caseId}/analysis`),
  getEntities: (caseId) => apiClient.get(`/cases/${caseId}/entities`),
  getEvidence: (caseId) => apiClient.get(`/cases/${caseId}/evidence`),
  getFindings: (analysisId, agentType = null) => {
    const params = agentType ? { agent: agentType } : {};
    return apiClient.get(`/analyses/${analysisId}/findings`, { params });
  },
  getReport: (analysisId) => apiClient.get(`/analyses/${analysisId}/report`),
  downloadReportPdf: (analysisId) =>
    apiClient.get(`/analyses/${analysisId}/report/pdf`, { responseType: 'blob' }),
};
