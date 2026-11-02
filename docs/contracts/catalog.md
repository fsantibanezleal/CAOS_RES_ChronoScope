# Contract catalog

JSON Schema files define the static artifact boundaries. Python contract tests validate against the same files that generate the browser types. Cross-field temporal, licensing, quantile and metric invariants remain executable producer/consumer tests. The OpenAPI component inventory supports generation and does not activate an HTTP inference API.

| id | version | owner | schema file | example | documents | producer test | consumer test | missing-data behavior | provider | model io | swap test | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| trace | 2.0.0 | pipeline and web | docs/contracts/schemas/trace.schema.json | data/derived/REAL_m4_daily/trace.json | data/derived/*/trace.json | tests/test_pipeline_smoke.py | frontend/src/test/contract.test.ts | Invalid or absent trace is rejected with a case-specific error. | baseline:data/derived/REAL_m4_daily/trace.json | - | tests/test_pipeline_smoke.py | real |
| manifest | 2.0.0 | pipeline and web | docs/contracts/schemas/manifest.schema.json | data/derived/manifests/REAL_m4_daily.json | data/derived/manifests/*.json, !data/derived/manifests/index.json | tests/test_manifest.py | frontend/src/test/contract.test.ts | Invalid or absent manifest is rejected before rendering. | baseline:data/derived/manifests/REAL_m4_daily.json | - | tests/test_manifest.py | real |
| streaming | 2.0.0 | pipeline and web | docs/contracts/schemas/streaming.schema.json | data/derived/REAL_m4_daily/streaming.json | data/derived/*/streaming.json | tests/test_stage_streaming.py | frontend/src/test/contract.test.ts | Missing streaming output is shown as unavailable; it is not synthesized in the browser. | baseline:data/derived/REAL_m4_daily/streaming.json | - | tests/test_stage_streaming.py | real |
| analysis | 2.0.0 | pipeline and web | docs/contracts/schemas/analysis.schema.json | data/derived/REAL_m4_daily/analysis.json | data/derived/*/analysis.json | tests/test_stage_analyze.py | frontend/src/test/contract.test.ts | Missing analysis is shown as unavailable; browser diagnostics remain independently available. | baseline:data/derived/REAL_m4_daily/analysis.json | - | tests/test_stage_analyze.py | real |
| nlinear-model | 2.0.0 | browser forecast panel | docs/contracts/schemas/nlinear-model.schema.json | frontend/public/models/nlinear.json | frontend/public/models/nlinear.json, frontend/public/models/nlinear.onnx | tests/test_pipeline_smoke.py | frontend/src/test/parity.test.ts | Missing or unloadable model is omitted from the live method list. | baseline:frontend/public/models/nlinear.onnx | ONNX float32 input [1,48], output [1,12]; metadata in nlinear.json | frontend/src/test/parity.test.ts | real |
| reevaluation | 2.0.0 | pipeline and web | docs/contracts/schemas/reevaluation.schema.json | data/derived/reevaluation.json | data/derived/reevaluation.json | tests/test_reevaluation.py | frontend/src/test/reevaluation.test.ts | Missing comparison is reported as unavailable; historical scores are not silently substituted. | baseline:data/derived/reevaluation.json | - | tests/test_reevaluation.py | real |
| index | 1.0.0 | pipeline inventory | docs/contracts/schemas/index.schema.json | data/derived/manifests/index.json | data/derived/manifests/index.json | tests/test_contract_documents.py | frontend/src/test/contract.test.ts | missing: no case inventory; the browser reports a loading error and does not invent cases. | baseline:data/derived/manifests/index.json | - | tests/test_contract_documents.py | real |
| selector | 1.0.0 | offline classical training metadata | docs/contracts/schemas/selector.schema.json | models/selector.json | models/selector.json | tests/test_contract_documents.py | tests/test_contract_documents.py | Missing legacy selector does not change the browser comparison; offline training regenerates it only when explicitly requested. | baseline:models/selector.json | Historical classical method ranking; not used to select common-holdout winners. | tests/test_contract_documents.py | real |

## History

| contract | version | date | change | kind |
|---|---|---|---|---|
| trace | 1.0.0 | 2026-11-01 | Initial catalog record for the existing trace serializer and consumer. | initial |
| manifest | 1.0.0 | 2026-11-01 | Initial catalog record for the existing case manifest. | initial |
| streaming | 1.0.0 | 2026-11-01 | Initial catalog record for the prequential artifact boundary. | initial |
| analysis | 1.0.0 | 2026-11-01 | Initial catalog record for the committed diagnostics artifact and browser consumer. | initial |
| nlinear-model | 1.0.0 | 2026-11-01 | Initial catalog record for the browser ONNX asset and metadata. | initial |
| reevaluation | 1.0.0 | 2026-11-01 | Common final-holdout scores, forecast paths, provenance and source hashes. | initial |
| reevaluation | 2.0.0 | 2026-11-01 | Full contiguous histories reconstructed and source-verified; rejects decimated replay input; common scales and light fits corrected. | major |
| trace | 2.0.0 | 2026-11-01 | Normative JSON Schema replaces partial structural validation; generated consumers use this schema. | major |
| manifest | 2.0.0 | 2026-11-01 | Normative JSON Schema replaces partial structural validation; generated consumers use this schema. | major |
| streaming | 2.0.0 | 2026-11-01 | Normative JSON Schema replaces partial structural validation; generated consumers use this schema. | major |
| analysis | 2.0.0 | 2026-11-01 | Normative JSON Schema replaces partial structural validation; generated consumers use this schema. | major |
| nlinear-model | 2.0.0 | 2026-11-01 | Normative JSON Schema replaces partial structural validation; generated consumers use this schema. | major |
| index | 1.0.0 | 2026-11-01 | Explicit schema and catalog coverage for the existing index artifact. | initial |
| selector | 1.0.0 | 2026-11-01 | Explicit schema and catalog coverage for the existing selector artifact. | initial |
