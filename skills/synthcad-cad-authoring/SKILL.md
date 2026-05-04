---
name: synthcad-cad-authoring
description: Build, modify, and validate SynthCAD build123d CAD projects, including project-local tests and generated review artifacts.
---

# SynthCAD CAD Authoring

Use this skill when working in the SynthCAD repository on CAD projects, exports,
inspection, project-local tests, or URDF handoff.

## Operating Rules

- Use millimeters for all CAD dimensions.
- Discover the active project and target before editing. Use the build
  registry or user request as the source of truth.
- Prefer small parameterized changes in the target's existing source module.
- Preserve real component interfaces first: hole patterns, shafts, registers,
  fastener clearances, mounting faces, service access, cable/connector access,
  and other constraints documented by the current project.
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

Set these from the current repo and request:

```bash
uv run synthcad-build --list
PROJECT=<project-slug>
TARGET=<changed-build-target>
ASSEMBLY_TARGET=<assembly-target-to-review>
URDF_TARGET=<urdf-target-or-empty>
```

Use the variables consistently:

```bash
uv run synthcad-build --project "$PROJECT"
uv run synthcad-probe --target "$TARGET" --children
uv run synthcad-inspect --target "$ASSEMBLY_TARGET"
uv run show-interference --target "$ASSEMBLY_TARGET"
uv run synthcad-report --project "$PROJECT"
test -z "$URDF_TARGET" || uv run synthcad-urdf --target "$URDF_TARGET"
uv run pytest
uv run pytest "projects/$PROJECT/tests"
```

Use `synthcad-probe` before writing throwaway geometry scripts. It reports
target bounds, child labels, and inspection model structure quickly.

## Done Criteria

A CAD change is done when:

- the changed target imports and builds without errors;
- relevant project-local tests are added/updated and pass;
- exports regenerate for the affected project or target;
- inspection artifacts are generated for the changed target or assembly;
- unexpected interferences are fixed or documented as intentional; and
- project-specific assumptions or validation notes are updated.

## Reference

Open `references/project-workflow.md` for the generic project workflow and
test expectations.
