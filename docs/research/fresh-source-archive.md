# Original sources of the historical fresh-fit experiment

The 15-case, 22-variant experiment in `data/derived/fresh-reevaluation.json`
records 56 implementation hashes. Its original inventory also includes modules
that its evaluator did not execute. Keeping those bindings tied only to the
current working tree prevented even an export-only safety guard from evolving.

`fresh-source-2026-11-01.zip` preserves all 56 original byte sequences. On
November 5 each member was recovered from Git and checked against the existing
experiment hash before archiving. `fresh-source-archive.json` records the archive
digest, original artifact digest, exact binding-set fingerprint and recovery
commit. The historical execution commit was not retained; the recovery commit
must not be presented as that execution commit.

Admission selects this archive only for the exact original binding inventory
and unchanged admitted artifact. It verifies every member against the original
hash, rejects missing/duplicate members and redirected paths, and follows local
imports within those preserved sources. Archive entries are never extracted or
executed. Every input, checkpoint, forecast, metric and aggregate retains its
existing validation. A candidate with a different binding inventory must satisfy
the current-source path and cannot inherit this archive's admission.

The original method label "recomputed from current source" describes the source
at execution time. The browser and manuscripts consume a historical experiment;
neither a package extraction nor a new guard is a new execution of those models.
The current export guard separately checks its output before writing. No frozen
experiment hash was replaced to make that change pass.

Tests in `tests/test_fresh_reevaluation.py` retain all prior corrupt-candidate
controls and additionally plant altered archive bytes, changed source bytes even
after updating the outer archive checksum, missing members, path redirection,
changed experiment bytes and an unrecognized binding inventory.
