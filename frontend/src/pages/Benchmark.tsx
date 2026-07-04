import { useEffect, useState } from 'react';
import { loadIndex, loadManifest, loadTrace } from '../api/artifacts';
import { H, Lead, P } from '../components/doc';
import type { Trace } from '../lib/contract.types';

interface CaseTrace { caseId: string; category: string; trace: Trace; }
const fmt = (v: number | null) => (v == null || Number.isNaN(v) ? '-' : v.toFixed(3));

export function Benchmark() {
  const [rows, setRows] = useState<CaseTrace[]>([]);
  const [err, setErr] = useState('');

  useEffect(() => {
    loadIndex()
      .then(async (ix) => {
        const out: CaseTrace[] = [];
        for (const c of ix.cases) {
          const m = await loadManifest(c.case_id);
          const t = await loadTrace(m.artifact.path);
          out.push({ caseId: c.case_id, category: c.category, trace: t });
        }
        setRows(out);
      })
      .catch((e) => setErr(String(e)));
  }, []);

  const methods = Array.from(new Set(rows.flatMap((r) => r.trace.methods.map((m) => m.name))));
  const maseOf = (ct: CaseTrace, name: string) => ct.trace.methods.find((m) => m.name === name)?.backtest.mase ?? null;
  const winnerOf = (ct: CaseTrace) => ct.trace.summary.best_method;

  return (
    <div>
      <H>Benchmark</H>
      <Lead>
        The cross-case results, built live from the committed artifacts (never hand-typed). Each cell is a
        method's MASE on that case from the leakage-safe backtest; the winner per case is in bold. Below 1 beats
        the seasonal-naive baseline.
      </Lead>
      {err && <p style={{ color: '#f85149' }}>error: {err}</p>}

      {rows.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ borderCollapse: 'collapse', fontSize: 13, minWidth: 640 }}>
            <thead>
              <tr>
                <th style={th}>method</th>
                {rows.map((r) => (
                  <th key={r.caseId} style={th} title={r.category}>{r.caseId}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {methods.map((name) => (
                <tr key={name}>
                  <td style={{ ...td, fontWeight: 600 }}>{name}</td>
                  {rows.map((r) => {
                    const v = maseOf(r, name);
                    const win = winnerOf(r) === name;
                    return (
                      <td key={r.caseId} style={{ ...td, fontWeight: win ? 800 : 400, color: win ? '#3fb950' : undefined }}>
                        {fmt(v)}
                      </td>
                    );
                  })}
                </tr>
              ))}
              <tr>
                <td style={{ ...td, fontStyle: 'italic' }}>winner</td>
                {rows.map((r) => (
                  <td key={r.caseId} style={{ ...td, fontStyle: 'italic', color: '#3fb950' }}>{winnerOf(r)}</td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}

      <P>
        The takeaway is the no-free-lunch story: the zero-shot foundation model wins on some cases, the
        auto-tuned statistical models on others, and simple baselines on the messy real series and the noise
        controls. That is why the atlas keeps the whole ladder rather than picking one method. Heavier offline
        runs over the full public suites (GIFT-Eval, fev-bench) are surfaced through their live leaderboards.
      </P>
    </div>
  );
}

const th: React.CSSProperties = { textAlign: 'left', borderBottom: '1px solid #30363d', padding: '4px 10px', whiteSpace: 'nowrap' };
const td: React.CSSProperties = { padding: '4px 10px', borderBottom: '1px solid #21262d', whiteSpace: 'nowrap' };
