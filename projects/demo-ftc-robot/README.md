# demo-ftc-robot

Boundary: `project`

Crayon-style FTC DECODE concept robot for fast architecture review. The target
is a 16 in × 16 in × 16 in planning envelope with a six-wheel drive, front
intake, two-stage ball path, and front-facing 72 mm flywheel shooter.

Ownership rule:

- Reusable low-resolution planning primitives belong in `synthcad/library/`.
- Robot-specific FTC proxies, such as the Yellow Jacket motor envelope, belong
  in `synthcad/projects/demo_ftc_robot/`.
- Project assumptions, rule references, and validation notes belong in
  `projects/demo-ftc-robot/docs/`.

Current target:

- `demo-ftc-robot`: reference planning assembly.
