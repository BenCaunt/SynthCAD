# flat-disk-robot

Boundary: `project`

Robot-specific work for the flat disk platform. Keep chassis, assembly, and
validation notes here. Reusable primitives belong in `projects/library/`.

Project-owned files live with this bundle:

- `real-parts/`: checked-in source STEP/image references for this robot.
- `docs/`: robot-specific design notes and validation history.
- `tests/`: robot-specific geometry and assembly invariants.
- `generated/`: ignored local/CI review artifacts.

Current targets:

- `flat-disk-robot-chassis`: printable candidate.
- `flat-disk-robot-lid`: printable candidate.
- `flat-disk-robot`: reference assembly.
- `flat-disk-robot` URDF package: kinematic, visual, collision, and inertial
  robot description for ROS/simulation handoff.

Done means the chassis, lid, reference assembly, and URDF package regenerate,
inspect cleanly except for documented intentional overlaps, and preserve the
motor, wheel, sensor, battery, encoder, and USB service interfaces.

## OpenSCAD exploration

- Migration notes: `docs/openscad-migration-evaluation.md`
- Prototype port: `openscad/flat_disk_robot.scad`
