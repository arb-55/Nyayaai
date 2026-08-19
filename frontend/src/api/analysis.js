/**
 * Analysis API — Functions for triggering and retrieving analysis.
 */
import apiClient from './client';

export const analysisApi = {
  trigger: (caseId) => apiClient.post(`/cases/${caseId}/analyze`),
  getForCase: (caseId) => apiClient.get(`/cases/${caseId}/analysis`),
  getFindings: (analysisId, agentType = null) => {
    const params = agentType ? { agent: agentType } : {};
    return apiClient.get(`/analyses/${analysisId}/findings`, { params });
  },
  getReport: (analysisId) => apiClient.get(`/analyses/${analysisId}/report`),
  downloadReportPdf: (analysisId) =>
    apiClient.get(`/analyses/${analysisId}/report/pdf`, { responseType: 'blob' }),
};
