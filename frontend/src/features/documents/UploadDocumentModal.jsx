/**
 * UploadDocumentModal — Modal dialog for selecting document type and uploading PDF.
 */
import { useState } from 'react';
import { documentsApi } from '../../api/documents';

const DOCUMENT_TYPES = [
  { value: 'FIR', label: 'FIR (First Information Report)' },
  { value: 'WITNESS_STATEMENT', label: 'Witness Statement' },
  { value: 'EVIDENCE', label: 'Evidence / Forensic Report' },
  { value: 'ARGUMENT', label: 'Written Argument' },
  { value: 'JUDGMENT', label: 'Previous Order / Judgment' },
  { value: 'OTHER', label: 'Other Document' },
];

export default function UploadDocumentModal({ caseId, isOpen, onClose, onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [documentType, setDocumentType] = useState('OTHER');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  function handleFileChange(e) {
    const file = e.target.files[0];
    setError(null);

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Please select a valid PDF file (.pdf).');
      setSelectedFile(null);
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      setError('File size exceeds the maximum limit of 20 MB.');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a PDF document to upload.');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      await documentsApi.upload(caseId, selectedFile, documentType);
      setSelectedFile(null);
      setDocumentType('OTHER');
      onUploadSuccess();
      onClose();
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail?.message || 'Failed to upload document.';
      setError(msg);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="glass-card w-full max-w-lg p-6 relative animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between mb-5 border-b border-surface-700/50 pb-4">
          <div>
            <h3 className="text-lg font-display font-semibold text-surface-50">Upload Case Document</h3>
            <p className="text-xs text-surface-400">Select document type and upload a PDF file for text extraction.</p>
          </div>
          <button
            onClick={onClose}
            disabled={uploading}
            className="text-surface-400 hover:text-surface-200 p-1"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-2">
            <svg className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <p className="text-xs text-red-300">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Document Type Dropdown */}
          <div>
            <label className="block text-xs font-medium text-surface-300 uppercase tracking-wider mb-1.5">
              Document Type *
            </label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              disabled={uploading}
              className="input-field cursor-pointer"
            >
              {DOCUMENT_TYPES.map((dt) => (
                <option key={dt.value} value={dt.value} className="bg-surface-800 text-surface-100">
                  {dt.label}
                </option>
              ))}
            </select>
          </div>

          {/* File Selector */}
          <div>
            <label className="block text-xs font-medium text-surface-300 uppercase tracking-wider mb-1.5">
              PDF Document *
            </label>
            <div className="relative border-2 border-dashed border-surface-600 hover:border-brand-500/50 rounded-xl p-6 text-center transition-all bg-surface-900/40">
              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileChange}
                disabled={uploading}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
              />
              <div className="flex flex-col items-center">
                <svg className="w-10 h-10 text-brand-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                {selectedFile ? (
                  <div>
                    <p className="text-sm font-medium text-brand-300">{selectedFile.name}</p>
                    <p className="text-xs text-surface-400 mt-0.5">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm text-surface-200 font-medium">Click or drag PDF file to upload</p>
                    <p className="text-xs text-surface-500 mt-1">Maximum file size: 20 MB</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-surface-700/50">
            <button
              type="button"
              onClick={onClose}
              disabled={uploading}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading || !selectedFile}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? (
                <span className="flex items-center gap-2">
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Uploading & Extracting...
                </span>
              ) : (
                'Upload & Extract'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
