"""Recompute all case diagnostics twice and export only a byte-identical candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("NUMBA_NUM_THREADS", "2")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'data-pipeline'))
from chronoscopelab import registry  # noqa: E402
from chronoscopelab.io.formats import _sanitize, write_json  # noqa: E402
from chronoscopelab.stages import analyze  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(ROOT):
        parser.error('Candidate diagnostics must be external')
    index = json.loads((ROOT/'data/derived/manifests/index.json').read_text())
    receipt = {"ok": False, "cases": [], "code_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted((ROOT/'data-pipeline/chronoscopelab').rglob('*.py'))}}
    for case in index['cases']:
        identifier = case['case_id']
        spec = registry.build_series(registry.get_case(identifier), seed=42)
        first = analyze.run(spec, seed=42)
        # A second computation, rather than two serializations of one in-memory object.
        second = analyze.run(spec, seed=42)
        def canonical(obj):
            return json.dumps(_sanitize(obj), sort_keys=True, allow_nan=False)
        if canonical(first) != canonical(second):
            changed = [k for k in first if canonical(first[k]) != canonical(second[k])]
            raise ValueError(f'Non-deterministic case {identifier}: {changed}')
        if 'error' in first['sequence'] or not first['sequence']['matrix_profile'].get('available'):
            raise ValueError(f'Missing sequence diagnostic for {identifier}')
        destination = args.output/identifier/'analysis.json'
        count = write_json(destination, first)
        manifest = json.loads((ROOT/f'data/derived/manifests/{identifier}.json').read_text())
        manifest['analysis_artifact']['bytes'] = count
        write_json(args.output/'manifests'/f'{identifier}.json', manifest)
        receipt['cases'].append({"id": identifier, "bytes": count, "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                                 "n": len(spec.y), "identical_independent_runs": 2})
        print(f'Diagnostics: {identifier}, {len(spec.y)} original observations; two identical runs', flush=True)
    receipt['ok'] = True
    write_json(args.output/'diagnostic-reproduction.json', receipt)


if __name__ == '__main__':
    main()
