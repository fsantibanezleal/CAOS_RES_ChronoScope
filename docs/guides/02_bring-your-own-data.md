# Bring your own series

Store private input CSVs under the configured external `CAOS_DATA_ROOT`. The ingestion contract accepts long-format `unique_id,ds,y` columns and optional covariates. `data-pipeline/engine/stages/preprocess.py` reads a CSV and returns accepted series, rejection reasons and flags. Acceptance can retain missing values under the declared threshold; choose and document their treatment before fitting.

From the product root, this example validates a user file, reserves the final block and calls the published numerical provider on the preceding observations:

```python
import json
import os
from pathlib import Path
import sys

import numpy as np
from forecastscope import forecast

sys.path.insert(0, 'data-pipeline')
from engine.stages import preprocess

source = Path(os.environ['CAOS_DATA_ROOT']) / 'my-series.csv'
report = preprocess.run(str(source))
print(report.summary(), report.flagged)
if report.rejected:
    raise ValueError(report.rejected)
seasonality, horizon = 24, 24  # choose from the observation cadence and task
results = []
for record in report.accepted:
    values = np.asarray(record.y, dtype=float)
    if len(values) < 3 * seasonality or not np.isfinite(values).all():
        raise ValueError('Need a finite fitting prefix and a separate target block')
    history, actual = values[:-horizon], values[-horizon:]
    quantiles = forecast('Theta', history, seasonality=seasonality, horizon=horizon)
    mae = float(np.mean(np.abs(actual - quantiles[:, 1])))
    results.append({'series': record.unique_id, 'quantiles': quantiles.tolist(), 'mae': mae})
output_root = Path(os.environ['CAOS_TEMP_ROOT'])
if not output_root.is_absolute() or output_root.resolve().is_relative_to(Path.cwd().resolve()):
    raise ValueError('Use an absolute external output root')
output_root.mkdir(parents=True, exist_ok=True)
(output_root / 'forecast-candidate.json').write_text(
    json.dumps(results, allow_nan=False, indent=2), encoding='utf-8')
```

The probabilities are the provider's requested 0.1/0.5/0.9 columns. Their presence does not guarantee coverage. MAE here scores one reserved block; it is not an independent population comparison. Check timestamp order, seasonal lag, measurement units and any covariate arrival policy before interpreting the output.

Adding a case to the delivered app additionally requires source/redistribution metadata, the full artifact contracts and stage admission. Generate into an external candidate and promote only after validation. The current browser does not upload this CSV or execute Python; its live TypeScript/ONNX methods and their input limits are described in [live computation](../architecture/04_live-computation.md).
