# Contiguous-history correction

The initial comparison in commit `daed985` incorrectly treated display-decimated replay
histories as consecutive observations. Nine cases have a released history length greater
than the display array length. This changes seasonal lag meaning, fitting inputs and the
MASE denominator. Consequently, that comparison's scores and aggregate values are invalid.
The old artifact remains inspectable in Git; it must not be used as scientific evidence.

The corrected protocol reconstructs each original series from its committed real-data CSV
or deterministic case definition and manifest seed. Every displayed observation is checked
at its original `history_index`, and every final target is checked to the trace's rounding
tolerance of 0.000051. All fifteen reconstructions match. The complete original prefix is
then used for light fitting and for the historical metric scale. The released four-decimal
targets and frozen forecast paths remain unchanged. Individual engine context caps remain
part of each method's configuration; models do not all consume the same number of points.

Artifact `chronoscope.reevaluation/v2` includes the complete fitting histories and hashes
of the original CSV inputs, case generator, scoring code, light forecasters, combination
implementation and source traces. A replay array is rejected as a fit input when its
declared original length differs. Independent Python and browser-consumer tests verify
the full observations and common scales. The app and real browser inference now use the
complete histories, while the original replay artifacts retain their historical identity.

The fixed ContextMemory configuration is unchanged. Corrected mean MASE is 1.4504 for
ContextMemory, 1.4489 for RecencyMean and 1.8970 for EqualMean. The contextual component
still fails its predeclared aggregate improvement criterion. No setting was tuned in
response. This new result replaces the invalidated calculation; it does not rehabilitate
the earlier protocol. One origin per selected case still provides no population ranking,
significance test, pretraining-overlap clearance or operational service guarantee.
