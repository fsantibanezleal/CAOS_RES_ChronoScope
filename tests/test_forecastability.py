"""Leakage, dependent-test correction and series partition invariants."""
import numpy as np
import pytest

from chronoscopelab.analysis.atlas import MODEL_NAMES, PROTOCOL, by_adjust, partition, prefix_features, study_summary


def test_by_matches_manual_harmonic_step_up_oracle():
    p = np.array([.2, .001, .01, 1.])
    order = np.argsort(p)
    factor = len(p)*sum(1/i for i in range(1,len(p)+1))
    adjusted = p[order]*factor/np.arange(1,len(p)+1)
    expected = np.minimum(1,np.minimum.accumulate(adjusted[::-1])[::-1])
    np.testing.assert_allclose(by_adjust(p)[order], expected)
    with pytest.raises(ValueError):
        by_adjust([.01, np.nan])


def test_duplicate_identity_always_stays_in_the_same_partition():
    assert partition('ab'*32) == partition('ab'*32)
    assert {partition(f'{i:064x}') for i in range(50)} == {'discovery','confirmation'}


def test_adversarial_future_changes_do_not_change_origin_features():
    # The exact prefix consumed by the production evaluator, not a shuffled full series.
    rng = np.random.default_rng(17)
    full = rng.normal(size=160)
    end = len(full)-PROTOCOL['origins']*PROTOCOL['horizon']
    first = prefix_features(full[max(0,end-PROTOCOL['context_cap']):end])
    full[end:] = 1e9
    assert prefix_features(full[max(0,end-PROTOCOL['context_cap']):end]) == first


def test_confirmation_targets_cannot_choose_the_constant_or_fit_imputation():
    rows = []
    for i in range(100):
        rows.append({'id':str(i), 'partition':'discovery' if i<70 else 'confirmation',
                     'features':{'x':float(i), 'missing':None},
                     'mase':{n:1.+j*.1+(i%3)*.01 for j,n in enumerate(MODEL_NAMES)}})
    original, model = study_summary(rows)
    for r in rows[70:]:
        r['features']['missing'] = 1e8
        r['mase'] = {n:float(len(MODEL_NAMES)-i) for i,n in enumerate(MODEL_NAMES)}
    modified, second = study_summary(rows)
    assert original['constant_method'] == modified['constant_method'] == MODEL_NAMES[0]
    assert original['discovery_medians'] == modified['discovery_medians']
    assert model.get_params() == second.get_params()
    assert len(original['associations']) == 2
