# demo-ftc-robot Notes

## Intent

This project is a CrayonPlan-style blockout for an FTC DECODE robot concept.
It is not detailed fabrication CAD. The purpose is to evaluate packaging,
ball path, motor placement, service zones, and refinement anchors before
replacing placeholders with real STEP parts and manufacturable geometry.

## Organization

Reusable robot-planning primitives live in `synthcad/library/crayon.py`. That
module should stay generic: colored boxes, cylinders, spheres, simple intent
metadata, and shared planning colors.

Robot-specific details live inside this project package:

- `synthcad/projects/demo_ftc_robot/robot.py`: the concept assembly.
- `synthcad/projects/demo_ftc_robot/parts.py`: FTC-specific proxies, including
  the goBILDA Yellow Jacket sized motor envelope.
- `projects/demo-ftc-robot/tests/`: project-owned invariants for this concept.

Do not move FTC-specific product geometry into the shared crayon library unless
the repo grows a general FTC parts library with a broader ownership boundary.

## Current Concept

- Target envelope: 16 in x 16 in x 16 in.
- FTC starting cube reference: 18 in x 18 in x 18 in.
- Game piece: DECODE ARTIFACT, modeled as a nominal 5 in diameter ball.
- Capacity: 3 ARTIFACTS in a center queue.
- Drivetrain: six 96 mm wheels, three per side.
- Intake direction: front of robot, +Y.
- Shooter direction: front of robot, +Y.
- Shooter: 72 mm flywheel at the lower contact point, with the ball path above
  the flywheel and two 1 in diameter hood rollers above the ball path.
- Hood/top structure: the top plate is now modeled as a removable service plate
  and shooter hood bridge. It ties into the shooter side plates and locates the
  hood roller bearing blocks; it is not intended to represent a full robot lid.
- Indexing: main intake roller plus a second 1 in roller before the flywheel.
- Intake/indexer detail: the intake roller now includes an 8 mm shaft,
  compliant wheel stack, bearing blocks, pulley, and belt span. The second
  stage indexer has a shaft, sidewall bearing blocks, pulley, and belt span.
- Structure: flat drivetrain side plates, frame standoffs, intake side plates,
  queue sidewall plates, shooter side plates, and a sloped queue floor are
  modeled as separate crayon parts so the architecture is mechanically legible.
- Drive transmission: each wheel now has an 8 mm axle, bearing block, planning
  pulley, and visible belt spans from the paired Yellow Jacket motor locations.
- Motor proxies: low-resolution Yellow Jacket sized envelopes; replace with
  vendor STEP files before detailed packaging decisions.

## Refinement Targets

- Replace the Yellow Jacket proxies with real motor STEP files and confirm
  gearbox face, shaft, and wire exit clearance.
- Replace wheel, flywheel, roller, battery, and REV Hub placeholders with
  STEP references.
- Turn the frame blockout into plates, channel, bearing blocks, and fastener
  patterns.
- Add ball compression studies for the intake, indexer, flywheel, and hood;
  the current shooter path captures approximate flywheel and hood roller
  compression but not dynamic ball deformation.
- Add service access for battery changes, hub USB access, and belt tensioning.

## Inspection Notes

`synthcad-inspect` reports many direct-child interferences for this target.
That is expected for this crayon concept because swept volumes, game pieces,
rollers, frame placeholders, electronics placeholders, and refinement keepouts
are all shown as direct solids in one review assembly. Treat those overlaps as
planning evidence until the concept is promoted to detailed part CAD.

When this concept is refined, create a separate inspection model or split the
target into physical parts versus reference envelopes so real collisions can
be checked without noise from planning volumes.

## Rule/Source Assumptions

- FIRST's current DECODE manual describes ARTIFACTS as 5 in nominal balls in
  purple and green, with variation around the nominal size.
- The FTC robot starting configuration is treated as an 18 in cube reference;
  this concept intentionally targets a smaller 16 in cube.
- The Yellow Jacket proxy follows the goBILDA 5203 family at a planning level:
  RS-555 motor body, 36 mm gearbox, and 24 mm long 8 mm REX shaft.

Official references checked while creating this blockout:

- https://ftc-resources.firstinspires.org/ftc/archive/2026/game/manual
- https://www.gobilda.com/yellow-jacket-planetary-gear-motors/
