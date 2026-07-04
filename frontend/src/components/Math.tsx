// KaTeX math rendering (inline + block). Used by the Methodology page for term-by-term equations.
import katex from 'katex';
import 'katex/dist/katex.min.css';

export function M({ tex, block }: { tex: string; block?: boolean }) {
  const html = katex.renderToString(tex, { displayMode: !!block, throwOnError: false });
  return (
    <span
      dangerouslySetInnerHTML={{ __html: html }}
      style={block ? { display: 'block', margin: '10px 0', overflowX: 'auto' } : undefined}
    />
  );
}
