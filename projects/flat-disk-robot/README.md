# flat-disk-robot

Boundary: `project`

Robot-specific work for the flat disk platform. Keep chassis, assembly, and
validation notes here. Reusable primitives belong in `projects/library/`.

Current targets:

- `flat-disk-robot-chassis`: printable candidate.
- `flat-disk-robot-lid`: printable candidate.
- `flat-disk-robot`: reference assembly.
- `flat-disk-robot` URDF package: kinematic, visual, collision, and inertial
  robot description for ROS/simulation handoff.

Done means the chassis, lid, reference assembly, and URDF package regenerate,
inspect cleanly except for documented intentional overlaps, and preserve the
motor, wheel, sensor, battery, encoder, and USB service interfaces.
