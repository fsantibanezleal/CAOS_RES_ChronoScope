import { validateExecutive } from '@fasl-work/caos-app-shell';
import { describe, expect, it } from 'vitest';
import executive from '../../../content/executive.json';

describe('Demand-planning executive brief', () => {
  it('validates the sourced bilingual brief', () => {
    expect(validateExecutive(executive)).toEqual([]);
  });

  it('adversarial: rejects cause weights that exceed the whole', () => {
    const planted = structuredClone(executive);
    planted.pain.causes[0].weight = 100;
    expect(validateExecutive(planted).length).toBeGreaterThan(0);
  });
});
