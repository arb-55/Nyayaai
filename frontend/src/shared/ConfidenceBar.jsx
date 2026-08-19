/**
 * ConfidenceBar — Visual bar showing AI confidence score (0-1).
 */
export default function ConfidenceBar({ score, showLabel = true }) {
  const percentage = Math.round(score * 100);

  // Color based on confidence level
  let barColor = 'bg-red-500';
  let textColor = 'text-red-400';
  if (percentage >= 80) {
    barColor = 'bg-emerald-500';
    textColor = 'text-emerald-400';
  } else if (percentage >= 60) {
    barColor = 'bg-yellow-500';
    textColor = 'text-yellow-400';
  } else if (percentage >= 40) {
    barColor = 'bg-orange-500';
    textColor = 'text-orange-400';
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-surface-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} rounded-full transition-all duration-700 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className={`text-xs font-medium ${textColor} min-w-[3ch] text-right`}>
          {percentage}%
        </span>
      )}
    </div>
  );
}
