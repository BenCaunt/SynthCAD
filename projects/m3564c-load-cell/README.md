# m3564c-load-cell

Boundary: `project`

Reference CAD model for the Sunrise Instruments M3564C six-axis circular load
cell drawing.

Project-owned files live with this bundle:

- `real-parts/`: checked-in source drawing reference.
- `docs/`: drawing interpretation and modeling assumptions.
- `tests/`: geometry invariants for the dimensioned interfaces.
- `generated/`: ignored local/CI review artifacts.

Current targets:

- `m3564c-six-axis-load-cell`: reference model of the 60 mm OD, extra-thin,
  F2000N six-axis load cell.

Done means the reference target regenerates, the drawing-derived mounting
interfaces stay dimensionally stable, and any undimensioned visual features are
called out in the notes.
