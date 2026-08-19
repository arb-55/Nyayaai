/**
 * Header — Top bar showing current page title and actions.
 */
export default function Header({ title, subtitle, actions }) {
  return (
    <header className="h-16 flex items-center justify-between px-8 border-b border-surface-700/50 bg-surface-900/60 backdrop-blur-md">
      <div>
        <h2 className="text-lg font-display font-semibold text-surface-50">{title}</h2>
        {subtitle && (
          <p className="text-sm text-surface-400">{subtitle}</p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-3">
          {actions}
        </div>
      )}
    </header>
  );
}
