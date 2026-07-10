# MSEA_daily_weekly - multiple seasonality

**Category:** multi-seasonal (m=24 + 168) · **Seasonality (declared):** 24 · **Horizon:** 24 · **Synthetic**

## What generates it

Two superposed cycles on an hourly grid - a daily one (period 24, amplitude 12) and a weekly one (period 168,
amplitude 8) - plus Gaussian noise, over four full weeks (672 points).

## What it teaches

Real load/traffic/demand series almost always carry **multiple seasonal periods**. A method fed only the
declared m=24:

- Holt-Winters / seasonal-naive capture the daily cycle but treat the weekly component as slow drift, so
  their errors breathe with the day-of-week.
- The **analysis panel exposes the truth**: the periodogram shows BOTH spectral peaks (24 and 168), the
  seasonal-strength Fs at 24 is high but the residual still carries structure, and the MSTL decomposition
  (see [docs/analysis/seasonality.md](../analysis/seasonality.md)) splits the two seasonal components cleanly.
- Deep and foundation models with enough context (NHITS multi-rate pooling; TimesFM/Chronos with 500+ point
  windows) can pick up the weekly pattern without being told - one of the places the SOTA tier genuinely
  earns its keep over single-m classical methods.

## Expected honest outcome

The ladder should show a visible gap between single-m classical methods and the context-rich tiers, WITH the
periodogram/MSTL panels explaining WHY. If a classical method still wins, that is worth reporting honestly -
at this noise level the weekly amplitude is detectable but modest.
