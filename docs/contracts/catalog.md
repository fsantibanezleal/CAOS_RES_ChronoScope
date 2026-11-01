# Contract catalog

The catalog records the pipeline-to-browser artifact boundary and the browser model asset. Schema references
point to the implementation that validates or serializes each shape; JSON Schemas are not claimed where none
exists. Producers and consumers remain covered by executable tests.

| id | version | owner | schema file | example | producer test | consumer test | missing-data behavior | provider | swap test | model io | documents |
|---|---|---|---|---|---|---|---|---|---|---|---|
| trace | 1.0.0 | pipeline and web | data-pipeline/chronoscopelab/core/trace.py | data/derived/REAL_m4_daily/trace.json | tests/test_pipeline_smoke.py | frontend/src/test/contract.test.ts | Invalid or absent trace is rejected with a case-specific error. | baseline:data/derived/REAL_m4_daily/trace.json | tests/test_pipeline_smoke.py | - | data/derived/*/trace.json |
| manifest | 1.0.0 | pipeline and web | data-pipeline/chronoscopelab/core/manifest.py | data/derived/manifests/REAL_m4_daily.json | tests/test_manifest.py | frontend/src/test/contract.test.ts | Invalid or absent manifest is rejected before rendering. | baseline:data/derived/manifests/REAL_m4_daily.json | tests/test_manifest.py | - | data/derived/manifests/*.json |
| streaming | 1.0.0 | pipeline and web | data-pipeline/chronoscopelab/stages/streaming.py | data/derived/REAL_m4_daily/streaming.json | tests/test_stage_streaming.py | frontend/src/test/contract.test.ts | Missing streaming output is shown as unavailable; it is not synthesized in the browser. | baseline:data/derived/REAL_m4_daily/streaming.json | tests/test_stage_streaming.py | - | data/derived/*/streaming.json |
| analysis | 1.0.0 | pipeline and web | data-pipeline/chronoscopelab/stages/analyze.py | data/derived/REAL_m4_daily/analysis.json | tests/test_stage_analyze.py | frontend/src/test/contract.test.ts | Missing analysis is shown as unavailable; browser diagnostics remain independently available. | baseline:data/derived/REAL_m4_daily/analysis.json | tests/test_stage_analyze.py | - | data/derived/*/analysis.json |
| nlinear-model | 1.0.0 | browser forecast panel | frontend/public/models/nlinear.json | frontend/public/models/nlinear.json | tests/test_pipeline_smoke.py | frontend/src/test/parity.test.ts | Missing or unloadable model is omitted from the live method list. | baseline:frontend/public/models/nlinear.onnx | frontend/src/test/parity.test.ts | ONNX float32 input [1,48], output [1,12]; metadata in nlinear.json | frontend/public/models/nlinear.json, frontend/public/models/nlinear.onnx |
| reevaluation | 1.0.0 | pipeline and web | docs/contracts/schemas/reevaluation.schema.json | data/derived/reevaluation.json | tests/test_reevaluation.py | frontend/src/test/reevaluation.test.ts | Missing comparison is reported as unavailable; historical scores are not silently substituted. | baseline:data/derived/reevaluation.json | tests/test_reevaluation.py | - | data/derived/reevaluation.json |

## History

| contract | version | date | change | kind |
|---|---|---|---|---|
| trace | 1.0.0 | 2026-11-01 | Initial catalog record for the existing trace serializer and consumer. | initial |
| manifest | 1.0.0 | 2026-11-01 | Initial catalog record for the existing case manifest. | initial |
| streaming | 1.0.0 | 2026-11-01 | Initial catalog record for the prequential artifact boundary. | initial |
| analysis | 1.0.0 | 2026-11-01 | Initial catalog record for the committed diagnostics artifact and browser consumer. | initial |
| nlinear-model | 1.0.0 | 2026-11-01 | Initial catalog record for the browser ONNX asset and metadata. | initial |
| reevaluation | 1.0.0 | 2026-11-01 | Common final-holdout scores, forecast paths, provenance and source hashes. | initial |
