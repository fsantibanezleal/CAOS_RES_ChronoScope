# Source-bound walkthrough

| ID | Requirement | Verification |
|---|---|---|
| SH-1 | Six directly addressable story views SHALL represent the system, components, domain geometry, error dynamics, information timing and descriptive comparison using the selected source. | `frontend/src/test/navigation.test.tsx`, `frontend/src/test/showcase.test.ts` |
| SH-2 | Three-coordinate geometry SHALL use only observed-prefix values. A positive affine unit conversion SHALL preserve displayed relative geometry. | `frontend/src/test/showcase.test.ts` |
| SH-3 | A historical memory block SHALL be observable only when its complete horizon ends at or before the query. Moving the query SHALL NOT imply a new fitted combination. | `frontend/src/test/showcase.test.ts` |
| SH-4 | Story keyboard navigation and Exit SHALL preserve source configuration. Scene and panel selection SHALL use the same object identity. | `frontend/src/test/navigation.test.tsx` |
