---
name: synthcad-cad-authoring
description: Build, modify, and validate SynthCAD build123d CAD projects, including project-local tests and generated review artifacts.
---

# SynthCAD CAD Authoring

Use this skill when working in the SynthCAD repository on CAD projects, exports,
inspection, project-local tests, or URDF handoff.

## Operating Rules

- Use millimeters for all CAD dimensions.
- Prefer small parameterized changes in `synthcad/projects/flat_disk_robot/`.
- Preserve real component interfaces first: motor face holes, wheel and shaft
  clearances, encoder spacing, battery fit, sensor placement, USB access, and
  lid fastener locations.
- Do not hand-edit generated STEP, STL, GLB, URDF, inspection, or BREP files.
- Keep each project's source references, docs, tests, and generated artifacts
  inside `projects/<project-slug>/`.
- Put project-specific tests under `projects/<project-slug>/tests/`. Reserve
  root `tests/` for reusable framework, CLI, registry, and library behavior.
- When creating a new project or build target, add or update tests for its
  geometry invariants, critical component interfaces, source refs/docs metadata,
  and expected assembly interferences.
- If a drawing or component constraint is incomplete, record the assumption in
  the project's own `docs/` directory.

## Commands

```bash
uv run synthcad-build --project flat-disk-robot
uv run synthcad-probe --target flat-disk-robot --children
uv run synthcad-inspect --target flat-disk-robot
uv run show-interference --target flat-disk-robot
uv run synthcad-report --project flat-disk-robot
uv run synthcad-urdf --target flat-disk-robot
uv run pytest
uv run pytest projects/flat-disk-robot/tests
```

Use `synthcad-probe` before writing throwaway geometry scripts. It reports
target bounds, child labels, and inspection model structure quickly.

## Done Criteria

A flat disk robot CAD change is done when:

- the changed target imports and builds without errors;
- relevant project-local tests are added/updated and pass;
- exports regenerate for `flat-disk-robot`;
- inspection artifacts are generated for the changed target or assembly;
- unexpected interferences are fixed or documented as intentional; and
- robot-specific assumptions or validation notes are updated.

## Reference

Open `references/flat-disk-workflow.md` for the flat disk robot checklist and
project-local test examples.
