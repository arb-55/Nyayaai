/**
 * ConsensusView — Renders Phase 4 Consensus Engine synthesized report.
 */
import ConfidenceBar from '../../shared/ConfidenceBar';

export default function ConsensusView({ consensusReport, documents = [] }) {
  if (!consensusReport || !consensusReport.report_data) {
    return (
      <div className="text-center py-8 border border-dashed border-surface-700/60 rounded-xl">
        <p className="text-sm text-surface-400">No consensus report generated yet.</p>
        <p className="text-xs text-surface-500 mt-1">Run AI analysis above to synthesize multi-agent findings into a consensus report.</p>
      </div>
    );
  }

  const data = consensusReport.report_data || {};
  const overallConf = consensusReport.overall_confidence ?? data.overall_confidence ?? 0.8;
  const summary = consensusReport.summary || data.summary || 'Consensus synthesis completed.';
  const keyFindings = data.key_findings || [];
  const supportingEvidence = data.supporting_evidence || [];
  const materialContradictions = data.material_contradictions || [];
  const legalContext = data.legal_context || [];
  const uncertainties = data.uncertainties || [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Human Legal Review Banner */}
      <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-start gap-3">
        <svg className="w-6 h-6 text-amber-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.008v.008H12v-.008z" />
        </svg>
        <div>
          <h4 className="text-sm font-semibold text-amber-200 uppercase tracking-wider">AI-Assisted Legal Analysis — Human Review Required</h4>
          <p className="text-xs text-amber-300/80 mt-1 leading-relaxed">
            This consensus report synthesizes evidence, contradictions, and legal research using AI. NyayaAI does not make judicial determinations, declare guilt/innocence, or provide legal advice. All conclusions require independent verification by qualified legal professionals.
          </p>
        </div>
      </div>

      {/* Overview & Confidence Card */}
      <div className="glass-card p-6 border border-surface-700/50 space-y-4">
        <div className="flex items-center justify-between border-b border-surface-700/40 pb-4 flex-wrap gap-4">
          <div>
            <h3 className="section-heading text-lg">Synthesized Case Summary</h3>
            <p className="text-xs text-surface-400 mt-0.5">Multi-agent factual consensus and analysis summary</p>
          </div>

          <div className="flex items-center gap-3 bg-surface-900/60 p-3 rounded-xl border border-surface-800">
            <span className="text-xs text-surface-400 uppercase font-semibold">Overall Analysis Confidence:</span>
            <div className="w-32">
              <ConfidenceBar score={overallConf} showLabel={true} />
            </div>
          </div>
        </div>

        <p className="text-sm text-surface-200 leading-relaxed bg-surface-900/40 p-4 rounded-xl border border-surface-800/60">
          {summary}
        </p>
      </div>

      {/* Key Findings Section */}
      {keyFindings.length > 0 && (
        <div className="glass-card p-6 border border-surface-700/50 space-y-4">
          <h3 className="section-heading text-md flex items-center gap-2">
            <svg className="w-5 h-5 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Key Synthesized Findings ({keyFindings.length})
          </h3>

          <div className="space-y-3">
            {keyFindings.map((item, idx) => (
              <div key={idx} className="p-4 bg-surface-900/60 border border-surface-800 rounded-xl space-y-2">
                <p className="text-sm font-semibold text-surface-100">{item.finding}</p>

                <div className="flex items-center gap-2 pt-1 flex-wrap">
                  {item.supporting_finding_ids?.length > 0 && (
                    <span className="badge bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[10px]">
                      Supported by {item.supporting_finding_ids.length} item(s)
                    </span>
                  )}
                  {item.contradicting_finding_ids?.length > 0 && (
                    <span className="badge bg-red-500/10 text-red-300 border border-red-500/20 text-[10px]">
                      Affected by {item.contradicting_finding_ids.length} contradiction(s)
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Material Contradictions Impact Section */}
      {materialContradictions.length > 0 && (
        <div className="glass-card p-6 border border-amber-500/30 bg-amber-500/5 space-y-4">
          <h3 className="section-heading text-md text-amber-200 flex items-center gap-2">
            <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3.75m0 3.75h.008v.008H12v-.008z" />
            </svg>
            Material Contradictions ({materialContradictions.length})
          </h3>

          <div className="space-y-3">
            {materialContradictions.map((c, idx) => (
              <div key={idx} className="p-3.5 bg-surface-900/80 border border-amber-500/20 rounded-xl">
                <p className="text-xs text-amber-300 font-medium">{c.impact || 'Inconsistency detected between document statements.'}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Identified Uncertainties Section */}
      {uncertainties.length > 0 && (
        <div className="glass-card p-6 border border-surface-700/50 space-y-3">
          <h3 className="section-heading text-md flex items-center gap-2 text-surface-200">
            <svg className="w-5 h-5 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M12 18h.008v.008H12V18z" />
            </svg>
            Identified Uncertainties & Gaps ({uncertainties.length})
          </h3>

          <ul className="space-y-2">
            {uncertainties.map((unc, idx) => (
              <li key={idx} className="text-xs text-surface-300 bg-surface-900/60 p-3 rounded-lg border border-surface-800 flex items-start gap-2">
                <span className="text-brand-400 font-bold">•</span>
                <span>{unc}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
