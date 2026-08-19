/**
 * EvidenceList — Renders Phase 3B extracted evidence findings grouped by category.
 */
import { useState } from 'react';
import ConfidenceBar from '../../shared/ConfidenceBar';
import SourceCitation from '../../shared/SourceCitation';

const CATEGORY_CONFIG = {
  FACT:        { label: 'Fact', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' },
  TESTIMONY:   { label: 'Testimony', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
  DOCUMENTARY: { label: 'Documentary', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' },
  PHYSICAL:    { label: 'Physical Evidence', color: 'bg-amber-500/20 text-amber-300 border-amber-500/30' },
  DIGITAL:     { label: 'Digital Evidence', color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' },
  FINANCIAL:   { label: 'Financial Evidence', color: 'bg-green-500/20 text-green-300 border-green-500/30' },
  MEDICAL:     { label: 'Medical Evidence', color: 'bg-rose-500/20 text-rose-300 border-rose-500/30' },
  OTHER:       { label: 'Other Evidence', color: 'bg-surface-700 text-surface-300 border-surface-600' },
};

const STRENGTH_STYLES = {
  HIGH:   'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  MEDIUM: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  LOW:    'bg-orange-500/20 text-orange-300 border-orange-500/30',
};

export default function EvidenceList({ findings = [], documents = [] }) {
  const [activeFilter, setActiveFilter] = useState('ALL');

  if (!findings || findings.length === 0) {
    return (
      <div className="text-center py-8 border border-dashed border-surface-700/60 rounded-xl">
        <p className="text-sm text-surface-400">No evidence findings extracted yet.</p>
        <p className="text-xs text-surface-500 mt-1">Run AI analysis above to extract supported legal evidence statements.</p>
      </div>
    );
  }

  // Create document lookup map by ID
  const docMap = {};
  documents.forEach((d) => {
    docMap[d.id] = d.filename;
  });

  // Group findings by category
  const grouped = {};
  findings.forEach((f) => {
    const refs = f.source_references || {};
    const cat = refs.category || 'FACT';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(f);
  });

  const availableCategories = Object.keys(grouped);

  const displayedGroups = activeFilter === 'ALL'
    ? grouped
    : { [activeFilter]: grouped[activeFilter] || [] };

  return (
    <div className="space-y-6">
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
          All Categories ({findings.length})
        </button>
        {availableCategories.map((cat) => {
          const cfg = CATEGORY_CONFIG[cat] || { label: cat, color: 'bg-surface-700 text-surface-300' };
          const count = grouped[cat].length;
          return (
            <button
              key={cat}
              onClick={() => setActiveFilter(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeFilter === cat
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

      {/* Render Evidence Groups */}
      <div className="space-y-6">
        {Object.entries(displayedGroups).map(([cat, items]) => {
          if (!items || items.length === 0) return null;
          const cfg = CATEGORY_CONFIG[cat] || { label: cat, color: 'bg-surface-700 text-surface-300 border-surface-600' };

          return (
            <div key={cat} className="glass-card p-5 border border-surface-700/40">
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-surface-700/40">
                <div className="flex items-center gap-2">
                  <span className={`badge ${cfg.color} border px-2.5 py-1 text-xs font-semibold uppercase tracking-wider`}>
                    {cfg.label}
                  </span>
                  <span className="text-xs text-surface-400">({items.length} statement{items.length !== 1 ? 's' : ''})</span>
                </div>
              </div>

              <div className="space-y-3">
                {items.map((item) => {
                  const refs = item.source_references || {};
                  const strength = refs.evidence_strength || 'HIGH';
                  const docId = refs.document_id;
                  const docName = refs.document_name || docMap[docId] || 'Source Document';
                  const pageNum = refs.page_number;
                  const excerpt = refs.excerpt;

                  return (
                    <div
                      key={item.id}
                      className="p-4 bg-surface-900/60 border border-surface-800 rounded-xl hover:border-surface-700 transition-all space-y-2.5"
                    >
                      {/* Top Bar: Strength & Confidence */}
                      <div className="flex items-center justify-between">
                        <span className={`badge ${STRENGTH_STYLES[strength] || STRENGTH_STYLES.HIGH} border text-[10px] uppercase font-bold tracking-wider`}>
                          Strength: {strength}
                        </span>

                        {item.confidence_score !== undefined && item.confidence_score !== null && (
                          <div className="w-28">
                            <ConfidenceBar score={item.confidence_score} showLabel={true} />
                          </div>
                        )}
                      </div>

                      {/* Statement */}
                      <p className="text-sm font-medium text-surface-100 leading-relaxed">
                        {item.finding_text}
                      </p>

                      {/* Quoted Excerpt */}
                      {excerpt && (
                        <div className="bg-surface-950/60 p-2.5 rounded-lg border border-surface-800/80">
                          <p className="text-xs text-surface-400 italic leading-relaxed">
                            &ldquo;{excerpt}&rdquo;
                          </p>
                        </div>
                      )}

                      {/* Source Citation */}
                      <SourceCitation
                        reference={{
                          document_name: docName,
                          page_number: pageNum,
                          excerpt: null,
                        }}
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
