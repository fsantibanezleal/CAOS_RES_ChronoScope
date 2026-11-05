# Source-bound numerical replay and document build

Use a clean copy of the complete source snapshot accompanying this document.
`build-receipt.json` identifies every local TeX/PDF input by SHA-256. The
retrospective analysis additionally fixes the original numerical replay digest
in `evidence/analysis-plan.json`. The historical execution environment and
hardware were not fully retained; do not attribute new-machine timing to it.

Initialize the declared product environment using `scripts/setup.ps1` on Windows
or `scripts/setup.sh` on POSIX, with the repository's external environment roots.
The numerical replay uses the published `preqts==0.3.0`; exact direct numerical
and plotting dependencies are in `requirements-precompute.txt` and
`notebooks/requirements.txt`. The retained reconstruction records its numerical
settings independently of historical hardware latency. LaTeX requires `latexmk`,
pdfTeX and the packages named in `tex/main.tex`.

From the source repository root, using that product Python interpreter:

```text
python scripts/manuscript_replay.py --check
python scripts/analyze_replay_cases.py --check
python scripts/build_working_manuscripts.py --only prequential-streaming-conformal --refresh-replay-inputs --scratch <external-build-folder>
python scripts/check_working_draft_bindings.py
```

The refresh option copies the original replay, original table builder
`scripts/make_manuscript_tables.py`, and original two-figure builder
`manuscripts/prequential-streaming-conformal/figures/make_figs.py` into the
external scratch folder and runs those copies. It transfers four generated
tables with explicit labels and both computed figures into `next/`. The static
information-order diagram remains supplied as the unchanged SVG/PDF source
asset. `scripts/analyze_replay_cases.py --check --render` then regenerates the
three extension figures, paired table and case inventory from the separately
bound numerical extension. These operations preserve published source/evidence.

The builder invokes `latexmk -cd -pdf -recorder -interaction=nonstopmode
-halt-on-error` with its output under the external build folder. It refuses
unresolved references, duplicate destinations and overfull boxes, copies the
compiled PDF into `next/main.pdf`, and hashes actual local recorder inputs into
the review receipt. The receipt is an identity record; it does not certify
independent scientific review or a new publication. Exact compiled PDF bytes
may change with TeX distribution and metadata; numerical evidence is checked
separately from that identity.
