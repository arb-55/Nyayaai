/**
 * CaseOverviewPage — Shows case details, document pipeline, and analysis status.
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../../shared/Header';
import StatusBadge from '../../shared/StatusBadge';
import LoadingSpinner from '../../shared/LoadingSpinner';
import UploadDocumentModal from '../documents/UploadDocumentModal';
import DocumentTextModal from '../documents/DocumentTextModal';
import { casesApi } from '../../api/cases';
import { documentsApi } from '../../api/documents';

export default function CaseOverviewPage() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modal states
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [deletingDocId, setDeletingDocId] = useState(null);

  useEffect(() => {
    loadCaseData();
  }, [caseId]);

  async function loadCaseData() {
    try {
      const [caseRes, docsRes] = await Promise.all([
        casesApi.getById(caseId),
        documentsApi.listByCase(caseId),
      ]);
      setCaseData(caseRes.data.data);
      setDocuments(docsRes.data.data || []);
    } catch (err) {
      console.error('Failed to load case:', err);
    } finally {
      setLoading(false);
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-surface-800/40 rounded-lg">
              <p className="text-xs text-surface-500 uppercase tracking-wider mb-1">Status</p>
              <StatusBadge status={caseData.status} />
            </div>
            <div className="p-4 bg-surface-800/40 rounded-lg">
              <p className="text-xs text-surface-500 uppercase tracking-wider mb-1">Documents Uploaded</p>
              <p className="text-2xl font-display font-bold text-surface-100">{documents.length}</p>
            </div>
            <div className="p-4 bg-surface-800/40 rounded-lg">
              <p className="text-xs text-surface-500 uppercase tracking-wider mb-1">Created Date</p>
              <p className="text-sm text-surface-200">
                {new Date(caseData.created_at).toLocaleDateString('en-IN', {
                  day: 'numeric', month: 'long', year: 'numeric'
                })}
              </p>
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
                    {/* Status Badge */}
                    <span className={`badge ${
                      doc.extraction_status === 'COMPLETED'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : doc.extraction_status === 'FAILED'
                        ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                        : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
                    }`}>
                      {doc.extraction_status}
                    </span>

                    {/* View Text Button */}
                    <button
                      onClick={() => setSelectedDocId(doc.id)}
                      className="btn-secondary text-xs px-3 py-1.5"
                    >
                      View Text
                    </button>

                    {/* Delete Button */}
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

        {/* Analysis Section Placeholder */}
        <div className="glass-card p-6">
          <h3 className="section-heading mb-4">Analysis</h3>
          <div className="text-center py-8">
            <p className="text-sm text-surface-400">
              AI multi-agent analysis will be available after documents are uploaded and processed.
            </p>
          </div>
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
