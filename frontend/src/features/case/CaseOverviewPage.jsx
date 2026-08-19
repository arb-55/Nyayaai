/**
 * CaseOverviewPage — Shows case details, document pipeline, Phase 3A Entity Extraction, Phase 3B Evidence Extraction, Phase 3C Contradictions, and Phase 3D Legal Research.
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../../shared/Header';
import StatusBadge from '../../shared/StatusBadge';
import LoadingSpinner from '../../shared/LoadingSpinner';
import AIDisclaimerBanner from '../../shared/AIDisclaimerBanner';
import UploadDocumentModal from '../documents/UploadDocumentModal';
import DocumentTextModal from '../documents/DocumentTextModal';
import EntityList from '../analysis/EntityList';
import EvidenceList from '../analysis/EvidenceList';
import ContradictionList from '../analysis/ContradictionList';
import LegalResearchList from '../analysis/LegalResearchList';
import { casesApi } from '../../api/cases';
import { documentsApi } from '../../api/documents';
import { analysisApi } from '../../api/analysis';

export default function CaseOverviewPage() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [entities, setEntities] = useState([]);
  const [evidenceFindings, setEvidenceFindings] = useState([]);
  const [contradictions, setContradictions] = useState([]);
  const [legalResearch, setLegalResearch] = useState([]);
  const [analysisInfo, setAnalysisInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);
  const [activeAnalysisTab, setActiveAnalysisTab] = useState('entities'); // 'entities' | 'evidence' | 'contradictions' | 'research'

  // Modal states
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [deletingDocId, setDeletingDocId] = useState(null);

  useEffect(() => {
    loadCaseData();
  }, [caseId]);

  async function loadCaseData() {
    try {
      const [caseRes, docsRes, analysisRes, entitiesRes, evidenceRes, contradictionsRes, researchRes] = await Promise.allSettled([
        casesApi.getById(caseId),
        documentsApi.listByCase(caseId),
        analysisApi.getForCase(caseId),
        analysisApi.getEntities(caseId),
        analysisApi.getEvidence(caseId),
        analysisApi.getContradictions(caseId),
        analysisApi.getLegalResearch(caseId),
      ]);

      if (caseRes.status === 'fulfilled') setCaseData(caseRes.value.data.data);
      if (docsRes.status === 'fulfilled') setDocuments(docsRes.value.data.data || []);
      if (analysisRes.status === 'fulfilled' && analysisRes.value.data?.data) {
        setAnalysisInfo(analysisRes.value.data.data);
      }
      if (entitiesRes.status === 'fulfilled' && entitiesRes.value.data?.data) {
        const rawGroups = entitiesRes.value.data.data || [];
        const flatEntities = [];
        rawGroups.forEach((grp) => {
          if (grp.entities) flatEntities.push(...grp.entities);
        });
        setEntities(flatEntities);
      }
      if (evidenceRes.status === 'fulfilled' && evidenceRes.value.data?.data) {
        const rawGroups = evidenceRes.value.data.data || {};
        const flatFindings = [];
        Object.values(rawGroups).forEach((arr) => {
          if (Array.isArray(arr)) flatFindings.push(...arr);
        });
        setEvidenceFindings(flatFindings);
      }
      if (contradictionsRes.status === 'fulfilled' && contradictionsRes.value.data?.data) {
        setContradictions(contradictionsRes.value.data.data || []);
      }
      if (researchRes.status === 'fulfilled' && researchRes.value.data?.data) {
        setLegalResearch(researchRes.value.data.data || []);
      }
    } catch (err) {
      console.error('Failed to load case data:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleRunAnalysis() {
    setAnalyzing(true);
    setAnalysisError(null);
    try {
      const res = await analysisApi.trigger(caseId);
      if (res.data?.entities) {
        setEntities(res.data.entities);
      }
      if (res.data?.data) {
        setAnalysisInfo(res.data.data);
      }
      await loadCaseData();
    } catch (err) {
      console.error('Analysis error:', err);
      const msg = err.response?.data?.detail?.message || err.response?.data?.error?.message || 'AI Analysis failed.';
      setAnalysisError(msg);
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleDeleteDocument(docId, filename) {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) return;

    setDeletingDocId(docId);
    try {
      await documentsApi.delete(docId);
      await loadCaseData();
    } catch (err) {
      console.error('Failed to delete document:', err);
      alert('Failed to delete document.');
    } finally {
      setDeletingDocId(null);
    }
  }

  if (loading) return <LoadingSpinner message="Loading case details..." />;
  if (!caseData) {
    return (
      <div className="p-8">
        <div className="glass-card p-8 text-center">
          <h3 className="text-lg font-semibold text-surface-200 mb-2">Case not found</h3>
          <button onClick={() => navigate('/')} className="btn-secondary mt-4">Back to Dashboard</button>
        </div>
      </div>
    );
  }

  const hasExtractableDocs = documents.some(
    (d) => d.has_extracted_text || d.has_cleaned_text || d.extraction_status === 'COMPLETED'
  );

  return (
    <div className="animate-fade-in">
      <Header
        title={caseData.title}
        subtitle={caseData.description}
        actions={
          <div className="flex items-center gap-3">
            <StatusBadge status={caseData.status} />
            <button onClick={() => navigate('/')} className="btn-ghost">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
              Back
            </button>
          </div>
        }
      />

      <div className="p-8 space-y-6">
        {/* Case Info Card */}
        <div className="glass-card p-6">
          <h3 className="section-heading mb-4">Case Information</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="p-4 bg-surface-800/40 rounded-lg">
              <p className="text-xs text-surface-500 uppercase tracking-wider mb-1">Status</p>
              <StatusBadge status={caseData.status} />
            </div>
            <div className="p-4 bg-surface-800/40 rounded-lg">
              <p className="text-xs text-surface-500 uppercase tracking-wider mb-1">Documents Uploaded</p>
              <p className="text-2xl font-display font-bold text-surface-100">{documents.length}</p>
            </div>
            <div className="p-4 bg-surface-800/40 rounded-lg">
              <p className="text-xs text-surface-500 uppercase tracking-wider mb-1">Extracted Entities</p>
              <p className="text-2xl font-display font-bold text-brand-300">{entities.length}</p>
            </div>
            <div className="p-4 bg-surface-800/40 rounded-lg">
              <p className="text-xs text-surface-500 uppercase tracking-wider mb-1">Evidence Findings</p>
              <p className="text-2xl font-display font-bold text-emerald-400">{evidenceFindings.length}</p>
            </div>
            <div className="p-4 bg-surface-800/40 rounded-lg">
              <p className="text-xs text-surface-500 uppercase tracking-wider mb-1">Legal Authorities</p>
              <p className="text-2xl font-display font-bold text-purple-400">{legalResearch.length}</p>
            </div>
          </div>
        </div>

        {/* Documents Section */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="section-heading">Case Documents</h3>
              <p className="text-xs text-surface-400 mt-0.5">Upload FIRs, witness statements, evidence, and legal filings.</p>
            </div>
            <button
              onClick={() => setIsUploadOpen(true)}
              className="btn-primary text-xs"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Upload PDF Document
            </button>
          </div>

          {documents.length === 0 ? (
            <div className="text-center py-10 border-2 border-dashed border-surface-800 rounded-xl">
              <div className="w-12 h-12 rounded-xl bg-brand-600/10 flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m.75 12l3 3m0 0l3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              </div>
              <p className="text-sm text-surface-300 font-medium mb-1">No documents uploaded yet</p>
              <p className="text-xs text-surface-500 mb-4">Upload case PDFs to extract text and prepare for AI legal analysis.</p>
              <button onClick={() => setIsUploadOpen(true)} className="btn-secondary text-xs">
                Upload First Document
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-4 bg-surface-800/40 border border-surface-700/30 rounded-xl hover:border-surface-600/50 transition-all">
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="w-9 h-9 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                          d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m.75 12l3 3m0 0l3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-surface-100 truncate">{doc.filename}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="badge bg-surface-700 text-surface-300 text-[10px]">
                          {doc.document_type}
                        </span>
                        {doc.page_count && (
                          <span className="text-xs text-surface-500">{doc.page_count} page{doc.page_count !== 1 ? 's' : ''}</span>
                        )}
                        <span className="text-xs text-surface-500">
                          {new Date(doc.uploaded_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 ml-4">
                    <span className={`badge ${
                      doc.extraction_status === 'COMPLETED'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : doc.extraction_status === 'FAILED'
                        ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                        : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
                    }`}>
                      {doc.extraction_status}
                    </span>

                    <button
                      onClick={() => setSelectedDocId(doc.id)}
                      className="btn-secondary text-xs px-3 py-1.5"
                    >
                      View Text
                    </button>

                    <button
                      onClick={() => handleDeleteDocument(doc.id, doc.filename)}
                      disabled={deletingDocId === doc.id}
                      className="text-surface-500 hover:text-red-400 p-1.5 transition-colors disabled:opacity-50"
                      title="Delete document"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Phase 3: AI Legal Analysis Section */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="section-heading">AI Case Analysis (Phase 3)</h3>
              <p className="text-xs text-surface-400 mt-0.5">
                Run AI analysis to extract legal entities (3A), evidence findings (3B), potential contradictions (3C), and legal research (3D).
              </p>
            </div>
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing || !hasExtractableDocs}
              className="btn-accent text-xs disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {analyzing ? (
                <span className="flex items-center gap-2">
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Running AI Analysis...
                </span>
              ) : (
                'Run AI Analysis'
              )}
            </button>
          </div>

          {/* AI Disclaimer */}
          {(entities.length > 0 || evidenceFindings.length > 0 || contradictions.length > 0 || legalResearch.length > 0) && <AIDisclaimerBanner />}

          {/* Error Alert */}
          {analysisError && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-2">
              <svg className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              <p className="text-xs text-red-300">{analysisError}</p>
            </div>
          )}

          {/* Analysis View Tabs */}
          <div className="flex items-center gap-3 mb-6 border-b border-surface-700/50 pb-3 flex-wrap">
            <button
              onClick={() => setActiveAnalysisTab('entities')}
              className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all flex items-center gap-2 ${
                activeAnalysisTab === 'entities'
                  ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/20'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800'
              }`}
            >
              <span>Legal Entities (3A)</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] bg-black/30">{entities.length}</span>
            </button>
            <button
              onClick={() => setActiveAnalysisTab('evidence')}
              className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all flex items-center gap-2 ${
                activeAnalysisTab === 'evidence'
                  ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/20'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800'
              }`}
            >
              <span>Evidence Findings (3B)</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] bg-black/30">{evidenceFindings.length}</span>
            </button>
            <button
              onClick={() => setActiveAnalysisTab('contradictions')}
              className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all flex items-center gap-2 ${
                activeAnalysisTab === 'contradictions'
                  ? 'bg-amber-600 text-white shadow-lg shadow-amber-600/20'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800'
              }`}
            >
              <span>Contradictions (3C)</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] bg-black/30">{contradictions.length}</span>
            </button>
            <button
              onClick={() => setActiveAnalysisTab('research')}
              className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all flex items-center gap-2 ${
                activeAnalysisTab === 'research'
                  ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800'
              }`}
            >
              <span>Legal Research (3D)</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] bg-black/30">{legalResearch.length}</span>
            </button>
          </div>

          {/* Active Tab Content */}
          {activeAnalysisTab === 'entities' && (
            <EntityList entities={entities} documents={documents} />
          )}
          {activeAnalysisTab === 'evidence' && (
            <EvidenceList findings={evidenceFindings} documents={documents} />
          )}
          {activeAnalysisTab === 'contradictions' && (
            <ContradictionList findings={contradictions} documents={documents} />
          )}
          {activeAnalysisTab === 'research' && (
            <LegalResearchList findings={legalResearch} />
          )}
        </div>
      </div>

      {/* Modals */}
      <UploadDocumentModal
        caseId={caseId}
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={loadCaseData}
      />

      <DocumentTextModal
        documentId={selectedDocId}
        isOpen={Boolean(selectedDocId)}
        onClose={() => setSelectedDocId(null)}
      />
    </div>
  );
}
