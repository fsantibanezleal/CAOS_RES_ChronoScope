# Manuscript review set

These are local review candidates. No new Zenodo record or manuscript version has been
published in this refactor. The strict manuscript gate remains a release requirement;
an unpublished candidate is never entered as a published record in `product.json`.

| Candidate | Canonical PDF | Source | Status |
|---|---|---|---|
| Detailed product report | [Product report](product-report/main.pdf) | [LaTeX](product-report/tex/main.tex) | Local draft; separate concept and version DOIs required |
| ContextMemory and matching ablations | [Proposal manuscript](context-memory/main.pdf) | [LaTeX](context-memory/tex/main.tex) | Local draft; separate record required; retains the negative result |
| Streaming evaluation revision | [Streaming manuscript](prequential-streaming-conformal/main.pdf) | [LaTeX](prequential-streaming-conformal/tex/main.tex) | Local revision 2.4; existing published version remains 2.3 |

The published companion streaming study has concept DOI
[10.5281/zenodo.21508920](https://doi.org/10.5281/zenodo.21508920) and version 2.3 record
[22825217](https://zenodo.org/records/22825217). It does not report the newly implemented
contextual forecasting proposal, and is not used to cover that proposal in the registry.

The product report separates the archived-path comparison from fresh final-block
executions. The streaming manuscript retains the original streaming measurements and
identifies its historical smoothing-plus-drift adapter separately from the corrected
finite-history Theta implementation. Revising prose does not rerun that old experiment.

To reproduce numerical figures and tables, run the report's evidence generator from the
repository root in the notebook environment. Compile each source from its `tex` folder
with `latexmk -pdf main.tex`, then copy the resulting PDF to its canonical manuscript
root. Render every page for visual review and run the scientific-voice and content gates.
Exact package and checkpoint identities belong to the numerical artifacts, not to a DOI
reservation or a successful PDF build.

Publication requires review of these concrete PDFs, actual DOI assignment, updated DOI
headers, recompilation and verification of the published records before updating the
strict product registry. Remote promotion and live deployment remain separate gates.
