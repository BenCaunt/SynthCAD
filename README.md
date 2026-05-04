# SynthCAD

SynthCAD is a small `build123d` CAD workflow for generating, inspecting, and
exporting 3D-printable robotics parts from Python.

This open-source extraction contains only the flat disk robot project and its
required reference inputs.

## Quick Start

```bash
uv run synthcad-build --project flat-disk-robot
uv run synthcad-probe --target flat-disk-robot --children
uv run synthcad-inspect --target flat-disk-robot
uv run show-interference --target flat-disk-robot
uv run synthcad-urdf --target flat-disk-robot
```

Generated STEP, STL, GLB, inspection, and URDF artifacts are written under
`projects/flat-disk-robot/generated/`, which is intentionally ignored by git.

## Build Targets

- `flat-disk-robot-chassis`: printable 216 mm chassis.
- `flat-disk-robot-lid`: printable service lid.
- `flat-disk-robot`: reference assembly with motors, wheels, electronics,
  sensors, battery, and lid.

The source references used by the flat disk robot live under
`projects/flat-disk-robot/real-parts/`. BREP cache files may be generated
beside STEP inputs during local builds; they are ignored and should not be
committed.

## GitHub CI

`.github/workflows/synthcad-ci.yml` runs tests, exports the flat disk robot,
generates inspection/interference evidence, exports the URDF package, writes a
Markdown Actions summary, and uploads `projects/flat-disk-robot/generated/` as
review artifacts.

## Agent Skills

This repository can be used with `vercel-labs/skills`:

```bash
npx skills add BenCaunt/SynthCAD --list
npx skills add BenCaunt/SynthCAD --skill synthcad-cad-authoring
npx skills add BenCaunt/SynthCAD --skill synthcad-setup-github-project
```

Skill sources are in `skills/`. The repo intentionally does not include a root
`SKILL.md`, so skill installers copy only the selected skill directory instead
of the whole CAD repository.

## Validation

Run the regression suite:

```bash
uv run pytest
```

For geometry changes, regenerate exports and inspect the affected flat disk
targets before calling the change done:

```bash
uv run synthcad-build --project flat-disk-robot
uv run synthcad-inspect --target flat-disk-robot
uv run synthcad-report --project flat-disk-robot
```

See `projects/flat-disk-robot/docs/flat-disk-robot-notes.md` for robot-specific
layout assumptions and current validation notes.
