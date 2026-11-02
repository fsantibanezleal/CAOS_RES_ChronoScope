"""Admit complete sequence diagnostics and the executed, source-bound M4 study."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
METHODS = {'Naive', 'SeasonalNaive', 'SES', 'Holt', 'HoltWinters', 'Theta', 'AutoETS', 'AutoTheta'}
STUDY_CODE = {'scripts/run_forecastability_study.py', 'data-pipeline/chronoscopelab/analysis/atlas.py',
              'data-pipeline/chronoscopelab/analysis/sequence.py', 'data-pipeline/chronoscopelab/model/forecasters.py'}


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)


def adjusted(p):
    n = len(p)
    harmonic = sum(1/i for i in range(1,n+1))
    result = [1.] * n
    best = 1.
    order = sorted(range(n), key=p.__getitem__)
    for rank in range(n,0,-1):
        i = order[rank-1]
        best = min(best, p[i]*n*harmonic/rank)
        result[i] = best
    return result


def validate_study(d: dict, root: Path = ROOT, statistics_check: bool = False):
    if d.get('schema') != 'chronoscope.forecastability/v1' or d.get('complete') is not True or d.get('source_n') != 4227:
        raise ValueError('A partial/trial corpus cannot be admitted')
    rows = d['series']
    if len(rows) < 3000 or d['included_n'] != len(rows) or len(rows)+len(d['excluded']) != 4227:
        raise ValueError('Corpus inventory is incomplete')
    ids = [r['id'] for r in rows]+[r['id'] for r in d['excluded']]
    if len(set(ids)) != len(ids) or len({r['sequence_sha256'] for r in rows}) != len(rows):
        raise ValueError('Duplicate source identity or sequence')
    if set(d['model_names']) != METHODS or len(d['model_names']) != len(METHODS):
        raise ValueError('Changed model roster')
    expected_protocol = {'horizon':14, 'origins':3, 'context_cap':1024, 'seasonality':1, 'minimum_prefix':32,
                         'q':.05, 'discovery_percent':70, 'seed':42}
    if any(d['protocol'].get(k) != v for k,v in expected_protocol.items()):
        raise ValueError('Changed preregistered protocol')
    if set(d['code_sha256']) != STUDY_CODE:
        raise ValueError('Incomplete implementation identity')
    for relative, digest in d['code_sha256'].items():
        if hashlib.sha256((root/relative).read_bytes().replace(b'\r\n',b'\n')).hexdigest() != digest:
            raise ValueError('Stale corpus implementation: '+relative)
    feature_names = set(d['summary']['selector_features'])
    if len(feature_names) < 40:
        raise ValueError('Feature inventory is incomplete')
    for row in rows:
        expected = 'discovery' if int(hashlib.sha256(('chronoscope-atlas-v1:'+row['sequence_sha256']).encode()).hexdigest()[:8],16)%100 < 70 else 'confirmation'
        if row['partition'] != expected or set(row['features']) != feature_names or set(row['mase']) != METHODS:
            raise ValueError('Series partition or feature/model inventory differs')
        if row['origins'] != [row['source_n']-42, row['source_n']-28, row['source_n']-14]:
            raise ValueError('Temporal origin schedule differs')
        if any(not math.isfinite(v) or v < 0 for v in row['mase'].values()):
            raise ValueError('Invalid corpus error')
    discovery = [r for r in rows if r['partition']=='discovery']
    confirmation = [r for r in rows if r['partition']=='confirmation']
    summary = d['summary']
    medians = [statistics.median(r['features'][f] for r in discovery if r['features'][f] is not None)
               if any(r['features'][f] is not None for r in discovery) else 0. for f in summary['selector_features']]
    if len(medians) != len(summary['discovery_medians']) or any(not close(a,b) for a,b in zip(medians,summary['discovery_medians'],strict=True)):
        raise ValueError('Imputation was not fitted on discovery alone')
    if summary['discovery_n'] != len(discovery) or summary['confirmation_n'] != len(confirmation):
        raise ValueError('Partition counts differ')
    constant = min(d['model_names'], key=lambda n: statistics.mean(r['mase'][n] for r in discovery))
    if constant != summary['constant_method']:
        raise ValueError('Constant comparator was not chosen from discovery')
    expected_scores = {'selected':statistics.mean(r['mase'][r['selected_method']] for r in confirmation),
                       'oracle':statistics.mean(min(r['mase'].values()) for r in confirmation),
                       'discovery_constant':statistics.mean(r['mase'][constant] for r in confirmation)}
    if any(not close(v,summary['selection_mean_mase'][k]) for k,v in expected_scores.items()):
        raise ValueError('Held-out selection summary differs from individual rows')
    if any(not close(statistics.mean(r['mase'][n] for r in confirmation),summary['model_mean_mase'][n]) for n in METHODS):
        raise ValueError('Method summary differs')
    associations = summary['associations']
    if {a['feature'] for a in associations} != feature_names or len(associations) != len(feature_names):
        raise ValueError('Hypothesis inventory differs')
    for group, selected in (('discovery',discovery),('confirmation',confirmation)):
        ps = [a[group]['p'] for a in associations]
        if any(not math.isfinite(p) or not 0<=p<=1 for p in ps):
            raise ValueError('Invalid probability')
        for a,q in zip(associations,adjusted(ps),strict=True):
            result = a[group]
            if not close(q,result['q']) or result['rejected'] != (q <= .05):
                raise ValueError('BY correction differs')
            if statistics_check:
                from scipy.stats import kendalltau
                pairs = [(r['features'][a['feature']],math.log1p(min(r['mase'].values()))) for r in selected if r['features'][a['feature']] is not None]
                x,y = zip(*pairs,strict=True) if pairs else ((),())
                tau,p = kendalltau(x,y) if len(pairs)>=20 and len(set(x))>1 else (0.,1.)
                if not close(float(p),result['p']) or not close(float(tau),result['tau']) or len(pairs)!=result['n']:
                    raise ValueError('Independent Kendall statistic differs')
    for a in associations:
        expected = a['discovery']['rejected'] and a['confirmation']['rejected'] and a['discovery']['tau']*a['confirmation']['tau']>0
        if a['confirmed'] != expected:
            raise ValueError('Confirmation rule differs')
    if d['audit']['verified_origin_scores'] != len(rows)*3*len(METHODS):
        raise ValueError('Incomplete independently scored path inventory')


def validate_diagnostics(root: Path = ROOT):
    index = json.loads((root/'data/derived/manifests/index.json').read_text())
    if len(index['cases']) != 15 or len({r['case_id'] for r in index['cases']}) != 15:
        raise ValueError('The diagnostic case inventory is incomplete')
    for entry in index['cases']:
        d = json.loads((root/f"data/derived/{entry['case_id']}/analysis.json").read_text())
        sequence = d.get('sequence',{})
        if sequence.get('n') != d['n'] or sequence.get('observation_indices') != list(range(d['n'])) or len(sequence.get('values',[])) != d['n']:
            raise ValueError('Original sequence is missing or decimated')
        profile = sequence['matrix_profile']
        if not profile.get('available') or len(profile['profile']) != d['n']-profile['window']+1:
            raise ValueError('Incomplete Matrix Profile')
        for i,j in enumerate(profile['nearest_neighbor']):
            if j < 0 or j >= len(profile['profile']) or abs(i-j) <= profile['exclusion_zone']:
                raise ValueError('Invalid or trivial nearest-neighbor match')
        for motif in profile['motifs']:
            if abs(motif['start']-motif['match']) < profile['window']:
                raise ValueError('Overlapping motif pair')
        tolerances = [r['tolerance'] for r in sequence['multiscale_entropy']['scales']]
        if len(set(tolerances)) != 1:
            raise ValueError('Entropy tolerance changed with scale')
    return len(index['cases'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--statistics',action='store_true',help='Recompute Kendall statistics (local release gate; needs SciPy)')
    parser.add_argument('--study',type=Path,default=ROOT/'data/derived/forecastability.json')
    args = parser.parse_args()
    n = validate_diagnostics()
    d = json.loads(args.study.read_text())
    validate_study(d, statistics_check=args.statistics)
    print(f'Research extensions: {n} complete sequence diagnostics; {d["included_n"]} admitted corpus series and disjoint confirmation passed')


if __name__ == '__main__':
    main()
