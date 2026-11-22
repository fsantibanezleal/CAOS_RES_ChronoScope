# Walkthrough adversaries

| requirement | adversarial check | gate |
|---|---|---|
| SH-1 | Traverse first and final steps by keyboard and require source-preserving route changes and an actual return to Explore. | `frontend/src/test/navigation.test.tsx::adversarial: story keyboard navigation preserves the selected generator and exits to the actual atlas` |
| SH-2 | Use a long prefix, nonfinite values, too-short histories and invalid delays; require bounded prefix-only coordinates and unchanged geometry under unit conversions. | `frontend/src/test/showcase.test.ts::adversarial: every delay coordinate stays inside the observed prefix` |
| SH-3 | Move the query one observation before a block completes; require its removal from observable memory. | `frontend/src/test/showcase.test.ts::adversarial: a partly observed block cannot enter memory at the query` |
| SH-4 | Select different objects from each side; require reciprocal identity rather than independent visual flags. | `frontend/src/test/navigation.test.tsx::adversarial: linked scene selection and panel selection use the same source object` |

The shared shell supplies story navigation, motion, linked selection, annotation layout and chart rendering. The product browser matrix is `frontend/scripts/check-showcase.mjs`; it checks rendered theme and language, subject, three callouts, viewport share, overflow and callout bounds at three sizes in both languages and themes. The full shared shell gate, including G21, remains a separate release gate; a custom matrix does not replace it or establish product-wide acceptance.
