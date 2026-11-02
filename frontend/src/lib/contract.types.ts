// Public artifact aliases generated from the normative JSON Schemas.
import type { components } from './contract.gen';

export type MethodBacktest = components['schemas']['MethodBacktest'];
export type MethodForecast = components['schemas']['MethodForecast'];
export type TraceSummary = components['schemas']['TraceSummary'];
export type Trace = components['schemas']['Trace'];
export type ArtifactRef = components['schemas']['ArtifactRef'];
export type GateVerdict = components['schemas']['GateVerdict'];
export type SeriesDescriptors = components['schemas']['SeriesDescriptors'];
export type CaseManifest = components['schemas']['CaseManifest'];
export type CaseIndexEntry = components['schemas']['CaseIndexEntry'];
export type CaseIndex = components['schemas']['CaseIndex'];
export type CombinationIndex = components['schemas']['CombinationIndex'];
export type CombinationCase = components['schemas']['CombinationCase'];
export type AnalysisArtifactRef = NonNullable<CaseManifest['analysis_artifact']>;
export type StreamingArtifactRef = NonNullable<CaseManifest['streaming_artifact']>;
