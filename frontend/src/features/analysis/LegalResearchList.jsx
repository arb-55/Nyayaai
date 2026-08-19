/**
 * LegalResearchList — Renders Phase 3D AI-assisted legal research findings.
 */
import { useState } from 'react';
import ConfidenceBar from '../../shared/ConfidenceBar';

const AUTHORITY_CONFIG = {
  STATUTE:                 { label: 'Statute / Legislation', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' },
  CASE_LAW:                { label: 'Case Law / Judicial Precedent', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' },
  RULE:                    { label: 'Rule / Procedural Rule', color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' },
  REGULATION:              { label: 'Regulation', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
  CONSTITUTIONAL_PROVISION:{ label: 'Constitutional Provision', color: 'bg-amber-500/20 text-amber-300 border-amber-500/30' },
  OTHER:                   { label: 'Legal Authority', color: 'bg-surface-700 text-surface-300 border-surface-600' },
};

export default function LegalResearchList({ findings = [] }) {
  const [activeFilter, setActiveFilter] = useState('ALL');

  const researchFindings = findings.filter(
    (f) => f.agent_type === 'LEGAL_RESEARCH' || (f.source_references && f.source_references.research_question)
  );

  if (!researchFindings || researchFindings.length === 0) {
    return (
      <div className="text-center py-8 border border-dashed border-surface-700/60 rounded-xl">
        <p className="text-sm text-surface-400">No legal research findings generated yet.</p>
        <p className="text-xs text-surface-500 mt-1">Run AI analysis above to identify relevant research questions and legal authorities.</p>
      </div>
    );
  }

  // Filter items
  const displayed = activeFilter === 'ALL'
    ? researchFindings
    : researchFindings.filter((item) => {
        const refs = item.source_references || {};
        return refs.authority_type === activeFilter;
      });

  const authorityTypes = Array.from(
    new Set(researchFindings.map((f) => (f.source_references || {}).authority_type || 'STATUTE'))
  );

  return (
    <div className="space-y-6">
      {/* Disclaimer Banner */}
      <div className="p-3 bg-blue-500/10 border border-blue-500/25 rounded-xl flex items-start gap-3">
        <svg className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12v-.008z" />
        </svg>
        <div>
          <p className="text-xs font-semibold text-blue-200 uppercase tracking-wider">AI-Assisted Legal Research</p>
          <p className="text-xs text-blue-300/80 mt-0.5">
            Legal authorities are retrieved for human reference. Verified authorities have passed 2-level domain and content checks against official repositories.
          </p>
        </div>
      </div>

      {/* Authority Type Filter Pills */}
      <div className="flex flex-wrap items-center gap-2 pb-2 border-b border-surface-700/40">
        <button
          onClick={() => setActiveFilter('ALL')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeFilter === 'ALL'
              ? 'bg-brand-600 text-white'
              : 'bg-surface-800 text-surface-400 hover:text-surface-200'
          }`}
        >
          All Authorities ({researchFindings.length})
        </button>
        {authorityTypes.map((type) => {
          const cfg = AUTHORITY_CONFIG[type] || { label: type, color: 'bg-surface-700 text-surface-300' };
          const count = researchFindings.filter((f) => (f.source_references || {}).authority_type === type).length;
          return (
            <button
              key={type}
              onClick={() => setActiveFilter(type)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeFilter === type
                  ? 'bg-brand-600 text-white'
                  : 'bg-surface-800 text-surface-300 hover:text-white'
              }`}
            >
              <span>{cfg.label}</span>
              <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-black/30 font-semibold">{count}</span>
            </button>
          );
        })}
      </div>

      {/* Render Legal Research Items */}
      <div className="space-y-4">
        {displayed.map((item) => {
          const refs = item.source_references || {};
          const atype = refs.authority_type || 'STATUTE';
          const cfg = AUTHORITY_CONFIG[atype] || { label: atype, color: 'bg-surface-700 text-surface-300 border-surface-600' };
          const isVerified = refs.verification_status === 'VERIFIED';
          const url = refs.source_url;

          return (
            <div
              key={item.id}
              className="glass-card p-5 border border-surface-700/50 space-y-4 hover:border-surface-600 transition-all"
            >
              {/* Header: Authority Type & Verification Badge */}
              <div className="flex items-center justify-between border-b border-surface-700/40 pb-3 flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <span className={`badge ${cfg.color} border px-2.5 py-1 text-xs font-semibold uppercase tracking-wider`}>
                    {cfg.label}
                  </span>

                  {isVerified ? (
                    <span className="badge bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] flex items-center gap-1">
                      <svg className="w-3 h-3 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                      Source Verified (2-Level)
                    </span>
                  ) : (
                    <span className="badge bg-amber-500/10 text-amber-300 border border-amber-500/20 text-[10px] flex items-center gap-1">
                      <svg className="w-3 h-3 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.008v.008H12v-.008z" />
                      </svg>
                      Source Unverified
                    </span>
                  )}
                </div>

                {item.confidence_score !== undefined && (
                  <div className="w-28">
                    <ConfidenceBar score={item.confidence_score} showLabel={true} />
                  </div>
                )}
              </div>

              {/* Research Question */}
              <div>
                <p className="text-[10px] uppercase font-bold text-surface-400 tracking-wider mb-1">Research Question</p>
                <p className="text-sm font-semibold text-surface-100">{refs.research_question || item.finding_text}</p>
              </div>

              {/* Authority Title & Citation */}
              <div className="p-3.5 bg-surface-900/80 border border-surface-800 rounded-xl space-y-1.5">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-bold text-brand-300">{refs.title || 'Legal Authority'}</p>
                  <p className="text-xs font-mono text-surface-400">{refs.citation}</p>
                </div>
                <p className="text-xs text-surface-200 leading-relaxed">{refs.legal_proposition}</p>
              </div>

              {/* Source Link / Information */}
              <div className="flex items-center justify-between pt-1 text-xs text-surface-400">
                <div className="flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-surface-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918" />
                  </svg>
                  <span>{refs.source_name || 'Official Source'}</span>
                </div>

                {isVerified && url ? (
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1 hover:underline"
                  >
                    <span>View Official Source</span>
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                    </svg>
                  </a>
                ) : (
                  <span className="text-surface-500 italic text-[11px]">No verified link</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
