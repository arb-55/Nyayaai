/**
 * DashboardPage — Main landing page showing all cases.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../shared/Header';
import StatusBadge from '../../shared/StatusBadge';
import LoadingSpinner from '../../shared/LoadingSpinner';
import { casesApi } from '../../api/cases';

export default function DashboardPage() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCase, setNewCase] = useState({ title: '', description: '' });
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadCases();
  }, []);

  async function loadCases() {
    try {
      const res = await casesApi.list();
      setCases(res.data.data || []);
    } catch (err) {
      console.error('Failed to load cases:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateCase(e) {
    e.preventDefault();
    if (!newCase.title.trim()) return;
    setCreating(true);
    try {
      const res = await casesApi.create(newCase);
      setShowCreateModal(false);
      setNewCase({ title: '', description: '' });
      navigate(`/case/${res.data.data.id}`);
    } catch (err) {
      console.error('Failed to create case:', err);
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="animate-fade-in">
      <Header
        title="Dashboard"
        subtitle={`${cases.length} case${cases.length !== 1 ? 's' : ''}`}
        actions={
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
            id="btn-create-case"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            New Case
          </button>
        }
      />

      <div className="p-8">
        {/* Hero section */}
        <div className="glass-card p-8 mb-8 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-brand-600/10 to-purple-600/10" />
          <div className="relative z-10">
            <h1 className="text-3xl font-display font-bold text-surface-50 mb-2">
              Welcome to <span className="text-gradient">NyayaAI</span>
            </h1>
            <p className="text-surface-400 max-w-2xl">
              AI-assisted multi-agent legal document analysis system for Indian court cases.
              Upload case documents, run AI-powered analysis, and generate structured reports.
            </p>
          </div>
        </div>

        {/* Cases Grid */}
        {loading ? (
          <LoadingSpinner message="Loading cases..." />
        ) : cases.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <div className="w-16 h-16 rounded-2xl bg-brand-600/20 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M12 10.5v6m3-3H9m4.06-7.19l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
              </svg>
            </div>
            <h3 className="text-lg font-display font-semibold text-surface-200 mb-2">No cases yet</h3>
            <p className="text-sm text-surface-400 mb-6">Create your first case to get started with document analysis.</p>
            <button onClick={() => setShowCreateModal(true)} className="btn-primary">
              Create First Case
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cases.map((c) => (
              <button
                key={c.id}
                onClick={() => navigate(`/case/${c.id}`)}
                className="glass-card-hover p-5 text-left group"
                id={`case-card-${c.id}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-display font-semibold text-surface-100 group-hover:text-brand-300 transition-colors line-clamp-1">
                    {c.title}
                  </h3>
                  <StatusBadge status={c.status} />
                </div>
                {c.description && (
                  <p className="text-sm text-surface-400 mb-3 line-clamp-2">{c.description}</p>
                )}
                <div className="flex items-center gap-4 text-xs text-surface-500">
                  <span className="flex items-center gap-1">
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                    {c.document_count} doc{c.document_count !== 1 ? 's' : ''}
                  </span>
                  <span>
                    {new Date(c.created_at).toLocaleDateString('en-IN', {
                      day: 'numeric', month: 'short', year: 'numeric'
                    })}
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Create Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
          <div className="glass-card p-6 w-full max-w-md mx-4 animate-slide-up">
            <h3 className="text-lg font-display font-semibold text-surface-50 mb-4">Create New Case</h3>
            <form onSubmit={handleCreateCase}>
              <div className="mb-4">
                <label htmlFor="case-title" className="block text-sm font-medium text-surface-300 mb-1.5">
                  Case Title *
                </label>
                <input
                  id="case-title"
                  type="text"
                  className="input-field"
                  placeholder="e.g. State vs. Sharma"
                  value={newCase.title}
                  onChange={(e) => setNewCase({ ...newCase, title: e.target.value })}
                  autoFocus
                  required
                />
              </div>
              <div className="mb-6">
                <label htmlFor="case-description" className="block text-sm font-medium text-surface-300 mb-1.5">
                  Description
                </label>
                <textarea
                  id="case-description"
                  className="input-field h-24 resize-none"
                  placeholder="Brief description of the case..."
                  value={newCase.description}
                  onChange={(e) => setNewCase({ ...newCase, description: e.target.value })}
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !newCase.title.trim()}
                  className="btn-primary disabled:opacity-50"
                  id="btn-submit-case"
                >
                  {creating ? 'Creating...' : 'Create Case'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
