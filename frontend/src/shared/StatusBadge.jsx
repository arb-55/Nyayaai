/**
 * StatusBadge — Displays case/analysis status with color coding.
 */

const STATUS_STYLES = {
  CREATED:             'bg-surface-700 text-surface-300',
  DOCUMENTS_UPLOADED:  'bg-blue-500/20 text-blue-300 border border-blue-500/30',
  EXTRACTING:          'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30',
  EXTRACTING_ENTITIES: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30',
  ANALYZING:           'bg-purple-500/20 text-purple-300 border border-purple-500/30',
  RUNNING_AGENTS:      'bg-purple-500/20 text-purple-300 border border-purple-500/30',
  BUILDING_CONSENSUS:  'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30',
  COMPLETED:           'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30',
  FAILED:              'bg-red-500/20 text-red-300 border border-red-500/30',
  PENDING:             'bg-surface-600/50 text-surface-300 border border-surface-500/30',
};

const STATUS_LABELS = {
  CREATED: 'Created',
  DOCUMENTS_UPLOADED: 'Docs Uploaded',
  EXTRACTING: 'Extracting',
  EXTRACTING_ENTITIES: 'Extracting Entities',
  ANALYZING: 'Analyzing',
  RUNNING_AGENTS: 'Running Agents',
  BUILDING_CONSENSUS: 'Building Consensus',
  COMPLETED: 'Completed',
  FAILED: 'Failed',
  PENDING: 'Pending',
};

export default function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.CREATED;
  const label = STATUS_LABELS[status] || status;
  const isAnimating = ['ANALYZING', 'EXTRACTING', 'RUNNING_AGENTS', 'BUILDING_CONSENSUS', 'EXTRACTING_ENTITIES'].includes(status);

  return (
    <span className={`badge ${style}`}>
      {isAnimating && (
        <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse-subtle" />
      )}
      {label}
    </span>
  );
}
