# Numerical methods and product tooling

ChronoScope consumes the separately published `forecastscope` distribution. The
exact dependency version is pinned in the runtime requirements. The product root
`pyproject.toml` contains tooling configuration and declares no Python project or
build backend. Run the product-specific pipeline by path with
`python data-pipeline/run.py`; there is no local distribution to install.

The `data-pipeline/engine` tree owns case selection, source-data provenance,
checkpoint and runtime policy, stage orchestration, artifact schemas and export.
Fourteen compatibility modules resolve directly to installed ForecastScope
modules: the finite-prefix forecasters, fixed contextual combination, temporally
validated combinations, and eleven diagnostic families. They contain no copied
numerical implementations. A caller can import the published numerical API
directly; existing product orchestration uses the compatibility imports so its
schema and workflow responsibilities remain local.

The authoritative provider receipt records the distribution version and every
provider module SHA-256. `python scripts/method_inventory.py` verifies that the
installed distribution matches those bytes and that each numerical procedure
resolves to its declared provider. `python scripts/check_numerical_provider.py`
compares full-precision forecasts, allocation weights and completed historical
origins with independent original kernels on all fifteen shipped histories.
The reference code executes only inside that verification command, under a
separate namespace. It never supplies the application's current method calls.

Historical studies retain their original recorded implementation identities.
`docs/research/provider-migration-source-archive.json` binds an immutable ZIP of
original source bytes and lists complete, known historical binding maps. Admission
resolves only those maps through the verified archive. An unknown or modified map
must match current source files; adding a new file to an old experiment cannot
inherit its archive binding. The earlier fresh-fit experiment has its own
source-bound archive. Neither archive is imported by product admission.

The retained case inventory, combination results, corpus study and browser
calibration outputs remain historical results. Carrying and independently scoring
those payloads during release does not mean that today's installed methods fitted
them again. To create genuinely new forecasts, set `CHRONOSCOPE_DERIVED_DIR` to an
external output directory before invoking the path pipeline, retain the actual
provider and checkpoint revisions, and admit the new result as a separate study.
The shipped canonical data must never be overwritten by a reduced-runtime bake.

Unit corrections use explicit degeneracy policies. A constant prefix supplies no
normalized-loss training example; without eligible examples the combination uses
equal experts. A constant observable has no cross-correlation. Exactly constant
observations form one PELT regime, and non-l2 costs require an explicit penalty in
that cost's units. Result paths keep their computed floating-point precision.
These policies have independent dimensional tests; they do not retroactively
change the numerical identities or conclusions of archived experiments.
