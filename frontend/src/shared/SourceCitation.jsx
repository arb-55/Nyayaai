/**
 * SourceCitation — Links an AI finding back to its source document.
 *
 * Renders a clickable reference showing the document name, page number,
 * and a snippet of the source text.
 */
export default function SourceCitation({ reference }) {
  if (!reference) return null;

  const { document_name, page_number, excerpt } = reference;

  return (
    <div className="mt-2 p-2.5 bg-surface-800/60 border border-surface-700/40 rounded-lg">
      <div className="flex items-center gap-2 mb-1">
        <svg className="w-3.5 h-3.5 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
        <span className="text-xs font-medium text-brand-300">
          {document_name || 'Source Document'}
        </span>
        {page_number && (
          <span className="text-[10px] text-surface-500">p. {page_number}</span>
        )}
      </div>
      {excerpt && (
        <p className="text-xs text-surface-400 italic leading-relaxed line-clamp-2">
          &ldquo;{excerpt}&rdquo;
        </p>
      )}
    </div>
  );
}
