/**
 * ContradictionList — Renders Phase 3C detected potential contradictions.
 */
import { useState } from 'react';
import ConfidenceBar from '../../shared/ConfidenceBar';
import SourceCitation from '../../shared/SourceCitation';

const TYPE_CONFIG = {
  TIME_CONFLICT:             { label: 'Time Conflict', color: 'bg-amber-500/20 text-amber-300 border-amber-500/30' },
  DATE_CONFLICT:             { label: 'Date Conflict', color: 'bg-rose-500/20 text-rose-300 border-rose-500/30' },
  LOCATION_CONFLICT:         { label: 'Location Conflict', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' },
  PERSON_PRESENCE_CONFLICT: { label: 'Presence / Absence Conflict', color: 'bg-red-500/20 text-red-300 border-red-500/30' },
  IDENTITY_CONFLICT:        { label: 'Identity Conflict', color: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30' },
  AMOUNT_CONFLICT:          { label: 'Monetary Amount Conflict', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' },
  EVENT_DESCRIPTION_CONFLICT:{ label: 'Event Description Conflict', color: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30' },
  OBJECT_ATTRIBUTE_CONFLICT: { label: 'Physical Attribute Conflict', color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' },
  OTHER:                    { label: 'Potential Inconsistency', color: 'bg-surface-700 text-surface-300 border-surface-600' },
};

export default function ContradictionList({ findings = [], documents = [] }) {
  const [activeFilter, setActiveFilter] = useState('ALL');

  if (!findings || findings.length === 0) {
    return (
      <div className="text-center py-8 border border-dashed border-surface-700/60 rounded-xl">
        <p className="text-sm text-surface-400">No factual contradictions detected between documents.</p>
        <p className="text-xs text-surface-500 mt-1">Run AI analysis above to evaluate statement consistency across uploaded case documents.</p>
      </div>
    );
  }

  // Create document lookup map by ID
  const docMap = {};
  documents.forEach((d) => {
    docMap[d.id] = d.filename;
  });

  // Filter valid contradiction items
  const validFindings = findings.filter(
    (f) => f.agent_type === 'CONTRADICTION' || (f.source_references && f.source_references.classification === 'CONTRADICTION')
  );

  // Group findings by contradiction_type
  const grouped = {};
  validFindings.forEach((f) => {
    const refs = f.source_references || {};
    const ctype = refs.contradiction_type || 'OTHER';
    if (!grouped[ctype]) grouped[ctype] = [];
    grouped[ctype].push(f);
  });

  const availableTypes = Object.keys(grouped);

  const displayedGroups = activeFilter === 'ALL'
    ? grouped
    : { [activeFilter]: grouped[activeFilter] || [] };

  return (
    <div className="space-y-6">
      {/* Human Review Banner */}
      <div className="p-3 bg-amber-500/10 border border-amber-500/25 rounded-xl flex items-start gap-3">
        <svg className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.008v.008H12v-.008z" />
        </svg>
        <div>
          <p className="text-xs font-semibold text-amber-200 uppercase tracking-wider">Human Legal Review Required</p>
          <p className="text-xs text-amber-300/80 mt-0.5">
            Findings indicate potential factual inconsistencies between document excerpts. The system does not determine credibility, truthfulness, or legal liability.
          </p>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex flex-wrap items-center gap-2 pb-2 border-b border-surface-700/40">
        <button
          onClick={() => setActiveFilter('ALL')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeFilter === 'ALL'
              ? 'bg-brand-600 text-white'
              : 'bg-surface-800 text-surface-400 hover:text-surface-200'
          }`}
        >
          All Inconsistencies ({validFindings.length})
        </button>
        {availableTypes.map((ctype) => {
          const cfg = TYPE_CONFIG[ctype] || { label: ctype, color: 'bg-surface-700 text-surface-300' };
          const count = grouped[ctype].length;
          return (
            <button
              key={ctype}
              onClick={() => setActiveFilter(ctype)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeFilter === ctype
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

      {/* Render Contradiction Groups */}
      <div className="space-y-6">
        {Object.entries(displayedGroups).map(([ctype, items]) => {
          if (!items || items.length === 0) return null;
          const cfg = TYPE_CONFIG[ctype] || { label: ctype, color: 'bg-surface-700 text-surface-300 border-surface-600' };

          return (
            <div key={ctype} className="space-y-4">
              {items.map((item) => {
                const refs = item.source_references || {};
                const sourceA = refs.source_a || {};
                const sourceB = refs.source_b || {};
                const explanation = refs.explanation || item.finding_text;

                const nameA = sourceA.document_name || docMap[sourceA.document_id] || 'Document A';
                const nameB = sourceB.document_name || docMap[sourceB.document_id] || 'Document B';

                return (
                  <div
                    key={item.id}
                    className="glass-card p-5 border border-surface-700/50 space-y-4 hover:border-surface-600 transition-all"
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between border-b border-surface-700/40 pb-3">
                      <div className="flex items-center gap-2">
                        <span className={`badge ${cfg.color} border px-2.5 py-1 text-xs font-semibold uppercase tracking-wider`}>
                          {cfg.label}
                        </span>
                        <span className="badge bg-amber-500/10 text-amber-300 border border-amber-500/20 text-[10px]">
                          Requires Review
                        </span>
                      </div>

                      {item.confidence_score !== undefined && (
                        <div className="w-28">
                          <ConfidenceBar score={item.confidence_score} showLabel={true} />
                        </div>
                      )}
                    </div>

                    {/* VS Comparison Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Statement A */}
                      <div className="p-4 bg-surface-900/80 border border-surface-800 rounded-xl space-y-2 relative">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] uppercase font-bold text-surface-400 tracking-wider">Statement A</span>
                        </div>
                        <p className="text-sm font-medium text-surface-100">&ldquo;{sourceA.statement}&rdquo;</p>
                        {sourceA.excerpt && sourceA.excerpt !== sourceA.statement && (
                          <p className="text-xs text-surface-400 italic bg-surface-950/60 p-2 rounded-lg border border-surface-800/60">
                            Excerpt: &ldquo;{sourceA.excerpt}&rdquo;
                          </p>
                        )}
                        <SourceCitation
                          reference={{
                            document_name: nameA,
                            page_number: sourceA.page_number,
                            excerpt: null,
                          }}
                        />
                      </div>

                      {/* Statement B */}
                      <div className="p-4 bg-surface-900/80 border border-surface-800 rounded-xl space-y-2 relative">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] uppercase font-bold text-surface-400 tracking-wider">Statement B</span>
                        </div>
                        <p className="text-sm font-medium text-surface-100">&ldquo;{sourceB.statement}&rdquo;</p>
                        {sourceB.excerpt && sourceB.excerpt !== sourceB.statement && (
                          <p className="text-xs text-surface-400 italic bg-surface-950/60 p-2 rounded-lg border border-surface-800/60">
                            Excerpt: &ldquo;{sourceB.excerpt}&rdquo;
                          </p>
                        )}
                        <SourceCitation
                          reference={{
                            document_name: nameB,
                            page_number: sourceB.page_number,
                            excerpt: null,
                          }}
                        />
                      </div>
                    </div>

                    {/* Factual Inconsistency Assessment */}
                    <div className="p-3 bg-surface-800/30 border border-surface-700/30 rounded-xl">
                      <p className="text-xs font-semibold text-surface-300 uppercase tracking-wider mb-1">Factual Assessment</p>
                      <p className="text-xs text-surface-200 leading-relaxed">{explanation}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}
