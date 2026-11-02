import type { components } from './contract.gen';
export type ForecastabilityStudy = components['schemas']['ForecastabilityStudy'];

/** A missing, partial or internally inconsistent corpus is never a replacement for the case study. */
export function admitForecastability(value: unknown): ForecastabilityStudy {
  const d = value as ForecastabilityStudy;
  if (!d || d.schema !== 'chronoscope.forecastability/v1' || d.complete !== true || d.source_n !== 4227 ||
      !Array.isArray(d.series) || d.included_n !== d.series.length || d.included_n < 3000 ||
      !Array.isArray(d.excluded) || d.included_n+d.excluded.length !== d.source_n ||
      !Array.isArray(d.model_names) || d.model_names.length !== 8 || !d.summary ||
      d.summary.discovery_n+d.summary.confirmation_n !== d.included_n) throw new Error('Incomplete forecastability study');
  const ids = new Set<string>(); const hashes = new Set<string>(); let discovery = 0;
  for (const r of d.series) {
    if (ids.has(r.id) || hashes.has(r.sequence_sha256) || !['discovery','confirmation'].includes(r.partition) ||
        !r.features || !r.mase || !Array.isArray(r.origins) || r.origins.length !== 3 ||
        d.model_names.some(n => !Number.isFinite(r.mase[n]) || r.mase[n] < 0) ||
        (r.partition === 'confirmation' && !d.model_names.includes(r.selected_method ?? ''))) throw new Error('Invalid corpus series');
    ids.add(r.id); hashes.add(r.sequence_sha256); if (r.partition === 'discovery') discovery += 1;
  }
  if (discovery !== d.summary.discovery_n) throw new Error('Corpus partition counts differ');
  return d;
}
