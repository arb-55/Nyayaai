/**
 * DocumentTextModal — Modal panel for inspecting extracted and cleaned text of a document.
 */
import { useState, useEffect } from 'react';
import { documentsApi } from '../../api/documents';
import LoadingSpinner from '../../shared/LoadingSpinner';

export default function DocumentTextModal({ documentId, isOpen, onClose }) {
  const [docDetail, setDocDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('cleaned'); // 'cleaned' | 'raw'
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isOpen && documentId) {
      loadDocumentDetails();
    }
  }, [isOpen, documentId]);

  async function loadDocumentDetails() {
    setLoading(true);
    setError(null);
    try {
      const res = await documentsApi.getById(documentId);
      setDocDetail(res.data.data);
    } catch (err) {
      console.error('Failed to load document details:', err);
      setError('Failed to fetch extracted text for this document.');
    } finally {
      setLoading(false);
    }
  }

  function handleCopy() {
    const textToCopy = activeTab === 'cleaned'
      ? (docDetail?.cleaned_text || docDetail?.extracted_text || '')
      : (docDetail?.extracted_text || '');

    if (textToCopy) {
      navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="glass-card w-full max-w-4xl max-h-[85vh] flex flex-col relative animate-slide-up overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-surface-700/50 flex items-start justify-between bg-surface-900/40">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="badge bg-brand-600/20 text-brand-300 border border-brand-500/20">
                {docDetail?.document_type || 'DOCUMENT'}
              </span>
              <span className="text-xs text-surface-400">
                {docDetail?.page_count ? `${docDetail.page_count} Page${docDetail.page_count !== 1 ? 's' : ''}` : 'Pages N/A'}
              </span>
            </div>
            <h3 className="text-xl font-display font-semibold text-surface-50">
              {docDetail?.filename || 'Document Preview'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-surface-400 hover:text-surface-200 p-1.5 rounded-lg hover:bg-surface-800"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading ? (
            <LoadingSpinner message="Retrieving document text..." />
          ) : error ? (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-center">
              <p className="text-sm text-red-300">{error}</p>
            </div>
          ) : docDetail?.extraction_status === 'FAILED' ? (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
              <h4 className="text-sm font-semibold text-red-300 mb-1">Text Extraction Failed</h4>
              <p className="text-xs text-red-400 leading-relaxed">
                {docDetail.extraction_error || 'pdfplumber could not extract text from this PDF file.'}
              </p>
            </div>
          ) : (
            <div>
              {/* Toolbar & Tabs */}
              <div className="flex items-center justify-between mb-4 border-b border-surface-700/50 pb-3">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setActiveTab('cleaned')}
                    className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                      activeTab === 'cleaned'
                        ? 'bg-brand-600 text-white'
                        : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800'
                    }`}
                  >
                    Cleaned Text
                  </button>
                  <button
                    onClick={() => setActiveTab('raw')}
                    className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                      activeTab === 'raw'
                        ? 'bg-brand-600 text-white'
                        : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800'
                    }`}
                  >
                    Raw Extracted Text
                  </button>
                </div>

                <button
                  onClick={handleCopy}
                  className="btn-ghost text-xs flex items-center gap-1.5"
                >
                  {copied ? (
                    <>
                      <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-emerald-400">Copied!</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75" />
                      </svg>
                      Copy Text
                    </>
                  )}
                </button>
              </div>

              {/* Text Container */}
              <div className="bg-surface-950 p-5 rounded-xl border border-surface-800 font-mono text-xs text-surface-200 leading-relaxed whitespace-pre-wrap max-h-[50vh] overflow-y-auto">
                {activeTab === 'cleaned'
                  ? (docDetail?.cleaned_text || docDetail?.extracted_text || 'No text extracted from this document.')
                  : (docDetail?.extracted_text || 'No text extracted from this document.')}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-surface-700/50 bg-surface-900/40 flex justify-end">
          <button onClick={onClose} className="btn-secondary">
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
}
