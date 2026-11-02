// All reader types derive from the same schema that validates the produced artifact.
import type { components } from './contract.gen';
export type Reevaluation = components['schemas']['Reevaluation'];
export type ReevaluatedCase = Reevaluation['cases'][number];
export type ReevaluatedMethod = ReevaluatedCase['methods'][number];
export type HoldoutMetrics = ReevaluatedMethod['metrics'];
