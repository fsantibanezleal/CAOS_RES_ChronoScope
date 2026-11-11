# Reproduce the released manuscript

The exact DOI-bearing PDF and every local LaTeX input are bound by
[publication.json](publication.json). From the product root, run
`python scripts/check_publication_bindings.py` to verify those files.

Use pdfTeX and latexmk with the packages declared in [tex/main.tex](tex/main.tex).
Build outside the source tree to preserve the archived PDF.

```text
latexmk -cd -pdf -recorder -interaction=nonstopmode -halt-on-error -outdir=<external-build-folder> manuscripts/context-memory/tex/main.tex
```

The [numerical reproduction guide](next/REPRODUCING.md) documents source-prefix checks, archived paths, paired-series scoring and figure generation.
It names the independent numerical inputs and working-draft build. A different
TeX installation or build date can change the PDF digest.
