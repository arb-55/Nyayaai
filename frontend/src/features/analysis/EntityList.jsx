/**
 * EntityList — Renders Phase 3A extracted legal entities grouped by entity type.
 */
import { useState } from 'react';
import ConfidenceBar from '../../shared/ConfidenceBar';
import SourceCitation from '../../shared/SourceCitation';

const TYPE_CONFIG = {
  PERSON:         { label: 'Person / Individual', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
  LEGAL_SECTION:  { label: 'Legal Section / Statute', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' },
  CASE_NUMBER:    { label: 'Case / FIR Number', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' },
  COURT:          { label: 'Court / Tribunal', color: 'bg-amber-500/20 text-amber-300 border-amber-500/30' },
  POLICE_STATION: { label: 'Police Station', color: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30' },
  DATE:           { label: 'Date', color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' },
  LOCATION:       { label: 'Location / Address', color: 'bg-rose-500/20 text-rose-300 border-rose-500/30' },
  ORGANIZATION:   { label: 'Organization', color: 'bg-violet-500/20 text-violet-300 border-violet-500/30' },
  JUDGE:          { label: 'Judge / Magistrate', color: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30' },
  ADVOCATE:       { label: 'Advocate / Counsel', color: 'bg-teal-500/20 text-teal-300 border-teal-500/30' },
  MONEY_AMOUNT:   { label: 'Monetary Amount', color: 'bg-green-500/20 text-green-300 border-green-500/30' },
};

export default function EntityList({ entities = [], documents = [] }) {
  const [activeFilter, setActiveFilter] = useState('ALL');

  if (!entities || entities.length === 0) {
    return (
      <div className="text-center py-8 border border-dashed border-surface-700/60 rounded-xl">
        <p className="text-sm text-surface-400">No entities extracted yet.</p>
        <p className="text-xs text-surface-500 mt-1">Click &ldquo;Extract Entities&rdquo; above to analyze document text with AI.</p>
      </div>
    );
  }

  // Create document lookup map by ID
  const docMap = {};
  documents.forEach((d) => {
    docMap[d.id] = d.filename;
  });

  // Group entities by entity_type
  const grouped = {};
  entities.forEach((ent) => {
    const type = ent.entity_type || 'OTHER';
    if (!grouped[type]) grouped[type] = [];
    grouped[type].push(ent);
  });

  const availableTypes = Object.keys(grouped);

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
          All Categories ({entities.length})
        </button>
        {availableTypes.map((type) => {
          const cfg = TYPE_CONFIG[type] || { label: type, color: 'bg-surface-700 text-surface-300' };
          const count = grouped[type].length;
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

      {/* Render Entity Groups */}
      <div className="space-y-6">
        {Object.entries(displayedGroups).map(([type, items]) => {
          if (!items || items.length === 0) return null;
          const cfg = TYPE_CONFIG[type] || { label: type, color: 'bg-surface-700 text-surface-300 border-surface-600' };

          return (
            <div key={type} className="glass-card p-5 border border-surface-700/40">
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-surface-700/40">
                <div className="flex items-center gap-2">
                  <span className={`badge ${cfg.color} border px-2.5 py-1 text-xs font-semibold uppercase tracking-wider`}>
                    {cfg.label}
                  </span>
                  <span className="text-xs text-surface-400">({items.length} found)</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className="p-3.5 bg-surface-900/60 border border-surface-800 rounded-xl hover:border-surface-700 transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <p className="text-sm font-semibold text-surface-100">{item.entity_text}</p>
                        {item.confidence !== null && item.confidence !== undefined && (
                          <div className="w-20">
                            <ConfidenceBar score={item.confidence} showLabel={true} />
                          </div>
                        )}
                      </div>

                      {item.normalized_value && item.normalized_value !== item.entity_text && (
                        <p className="text-xs text-brand-300 mb-2">
                          Standardized: <span className="font-mono">{item.normalized_value}</span>
                        </p>
                      )}

                      {item.source_sentence && (
                        <p className="text-xs text-surface-400 italic bg-surface-950/40 p-2 rounded-lg border border-surface-800/50 mb-2 line-clamp-2">
                          &ldquo;{item.source_sentence}&rdquo;
                        </p>
                      )}
                    </div>

                    {/* Source Citation */}
                    {item.document_id && (
                      <SourceCitation
                        reference={{
                          document_name: docMap[item.document_id] || 'Source Document',
                          page_number: item.page_number,
                          excerpt: null,
                        }}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
