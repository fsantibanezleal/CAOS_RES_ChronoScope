/** Reader-facing translations; stored identifiers and numerical inputs stay unchanged. */
const families: Record<string, { en: string; es: string }> = {
  classical: { en: 'Rules and smoothing', es: 'Reglas y suavizado' },
  statistical: { en: 'Automatic statistical fits', es: 'Ajustes estadísticos automáticos' },
  ml: { en: 'Lagged trees', es: 'Árboles con rezagos' },
  deep: { en: 'Per-series neural models', es: 'Redes ajustadas por serie' },
  'deep (live)': { en: 'Browser neural inference', es: 'Inferencia neuronal local' },
  'linear (live)': { en: 'Browser linear inference', es: 'Inferencia lineal local' },
  foundation: { en: 'Pretrained sequence models', es: 'Modelos preentrenados' },
  'adaptive ensemble': { en: 'Adaptive combinations', es: 'Combinaciones adaptativas' },
};

export function methodFamilyLabel(value: string, es: boolean): string {
  return families[value]?.[es ? 'es' : 'en'] ?? value;
}

export function sourceClassLabel(value: string | null | undefined, es: boolean): string {
  if (value === 'synthetic') return es ? 'sintética' : 'synthetic';
  if (value === 'real') return 'real';
  return value ?? '';
}

const stationarityVerdicts: Record<string, string> = {
  'difference-stationary (ADF stationary, KPSS rejects: likely needs differencing)': 'estacionaria tras diferenciar (ADF indica estacionariedad; KPSS rechaza: probablemente requiere diferenciación)',
  'non-stationary (both tests agree)': 'no estacionaria (ambas pruebas coinciden)',
  'stationary (both tests agree)': 'estacionaria (ambas pruebas coinciden)',
  'trend-stationary (KPSS stationary, ADF unit root: detrend rather than difference)': 'estacionaria en torno a una tendencia (KPSS indica estacionariedad; ADF no rechaza la raíz unitaria: eliminar la tendencia en vez de diferenciar)',
};

export function stationarityVerdictLabel(value: string | null | undefined, es: boolean): string {
  if (!value) return es ? 'Sin resumen registrado' : 'No recorded summary';
  return es ? stationarityVerdicts[value] ?? `Diagnóstico de origen: ${value}` : value;
}
