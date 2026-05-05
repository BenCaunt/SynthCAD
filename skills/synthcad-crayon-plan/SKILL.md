---
name: synthcad-crayon-plan
description: Create low-resolution, color-coded SynthCAD robot concept blockouts for architecture, packaging, motion envelopes, game-piece flow, and later refinement into detailed CAD.
---

# SynthCAD Crayon Plan

Use this skill when creating or revising rough robot concept CAD in SynthCAD:
drivebase layouts, manipulators, intakes, shooters, conveyors, hoppers,
motion envelopes, service zones, or multiple architecture options.

## Workflow

- Build a low-detail assembly first: boxes, cylinders, spheres, and transparent
  envelopes are preferred over detailed fabricated geometry.
- Keep the architecture mechanically legible. Crayon CAD is rough CAD, not
  arbitrary blobs: represent frame rails, crossmembers, plates, shafts, rollers,
  wheels, motor locations, game-piece channels, supports, and major hardpoints
  as distinct geometry with plausible spacing and attachment relationships.
- Use distinct colors for subsystems and game pieces.
- Label every direct child with the subsystem/function it represents.
- Attach or document refinement intent: preserved interfaces, later STEP
  replacements, fastening, shafts, bearings, belts, pulleys, motors, service
  access, and material removal.
- Use transparent volumes for swept paths, game-piece storage, keepouts, and
  service envelopes. Do not let those envelopes substitute for the structural
  mechanism that creates or constrains the motion.
- Keep the assembly inside the requested planning envelope unless the user
  explicitly asks to study expansion.
- Add project-local tests for envelope size, required mechanism count/capacity,
  critical diameters, front/rear orientation, and expected color metadata.
- Regenerate GLB/snapshot artifacts so the viewer shows colored parts and
  part-list swatches.

## Quality Bar

- The first pass should communicate how the robot is put together, not just
  where subsystems roughly live.
- Wheels, rollers, flywheels, belts, pulleys, shafts, tubes, plates, and motors
  should be recognizable at concept scale. A wheel or roller may be simplified,
  but it should not appear as a square block in geometry intended for review.
- Use blockouts to preserve real decisions: intake width and height, indexer
  path, shooter compression/hood path, drive wheelbase, frame perimeter,
  electronics/battery service access, and motor/shaft packaging.
- Prefer a small number of meaningful structural parts over one large amorphous
  body. Split major subsystems into direct children when it helps inspection,
  color coding, or later replacement with real STEP parts.
- If a concept is intentionally under-detailed, document the missing structure
  and the next refinement targets in the project notes.

## Visualization Expectations

- Treat the colorized `*-detail.svg` as a fast labeled layout map. It may use
  simplified projected child bounds and is not the source of truth for curved
  geometry fidelity.
- Use the GLB viewer and exact projection SVG to judge whether wheels, rollers,
  flywheels, and other curved parts are actually modeled clearly.
- If a review image makes cylinders look square or severely faceted, call that
  out as a visualization/rendering problem unless the CAD geometry itself was
  intentionally blocky. Improve tessellation or use a better render before
  asking the user to evaluate shape quality.
- Always verify that subsystem colors survive into generated review artifacts;
  colorless output is a workflow issue to fix before calling the concept done.

## Ownership Boundary

- Shared planning primitives belong in `synthcad/library/crayon.py`.
- Robot-specific parts and vendor proxies belong in the active project package,
  such as `synthcad/projects/<project_module>/parts.py`.
- Game-specific assumptions and validation notes belong under
  `projects/<project-slug>/docs/`.
- Do not move one-off competition, vendor, or robot-specific geometry into the
  shared crayon library unless it is promoted into a deliberate reusable parts
  library.

## Done Criteria

- The concept target imports and builds.
- Direct children are labeled and visibly color-coded.
- Project docs state assumptions and refinement targets.
- Project tests pass.
- `uv run synthcad-build --project <project-slug>` writes STEP/GLB/snapshot
  review artifacts.
- `uv run synthcad-inspect --target <target-name>` writes both the exact
  projection SVG and the colorized `*-detail.svg` planning overview.
