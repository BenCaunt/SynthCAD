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
- Use distinct colors for subsystems and game pieces.
- Label every direct child with the subsystem/function it represents.
- Attach or document refinement intent: preserved interfaces, later STEP
  replacements, fastening, shafts, bearings, belts, pulleys, motors, service
  access, and material removal.
- Keep the assembly inside the requested planning envelope unless the user
  explicitly asks to study expansion.
- Add project-local tests for envelope size, required mechanism count/capacity,
  critical diameters, front/rear orientation, and expected color metadata.
- Regenerate GLB/snapshot artifacts so the viewer shows colored parts and
  part-list swatches.

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
