# Frameworks

One card per research-chosen engine/library: the deep research, made binding. Every engine the pipeline uses
gets a card here AND an exact pin in the matching `requirements-*.txt`. No hand-rolled toy substitute for a SOTA
engine the research prescribed.

- [00 card TEMPLATE](frameworks/00_TEMPLATE.md): copy per engine.
- [01 statsforecast](frameworks/01_statsforecast.md): the auto-tuned statistical tier (AutoARIMA, AutoETS,
  AutoTheta). Offline-only; the classical numpy ladder is the live-lane fallback.

Planned cards as their engines are wired (per `_CAOS_MANAGE/wip/chronoscope/plan.md`): `02_mlforecast_lightgbm`
(ML tier), and the zero-shot foundation models `03_chronos`, `04_tirex`, `05_timesfm`. The reference research
library (papers, model landscape) lives under [`docs/research/`](research/).
