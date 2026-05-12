# SynthCAD

SynthCAD is a small `build123d` CAD workflow for generating, inspecting, and
exporting CAD parts from Python.

The `synthcad/` package is the reusable framework: CLIs, registries, export
helpers, inspection tools, web viewer assets, and generic CAD utilities.
Project-owned CAD source, references, tests, docs, and target declarations live
under `projects/<project-slug>/`.

## Demo

Photos of the physical robot and printed chassis details:

| Built flat disk robot | Printed chassis internals |
| --- | --- |
| ![Built flat disk robot with assembled top lid and electronics visible](docs/assets/flat-disk-robot-part-assembly.jpg) | ![Printed flat disk robot chassis interior with standoffs and component mounts](docs/assets/flat-disk-robot-part-detail.jpg) |

## Quick Start

```bash
uv run synthcad-build --project flat-disk-robot
uv run synthcad-build --target m3564c-six-axis-load-cell
uv run synthcad-probe --target flat-disk-robot --children
uv run synthcad-inspect --target flat-disk-robot
uv run show-interference --target flat-disk-robot
uv run synthcad-urdf --target flat-disk-robot
```

Generated STEP, STL, GLB, inspection, and URDF artifacts are written under each
project's `generated/` directory by default. Generated directories are
intentionally ignored by git.

## Build Targets

- `flat-disk-robot-chassis`: printable 216 mm chassis.
- `flat-disk-robot-lid`: printable service lid.
- `flat-disk-robot`: reference assembly with motors, wheels, electronics,
  sensors, battery, and lid.
- `m3564c-six-axis-load-cell`: reference model of the Sunrise Instruments
  M3564C 60 mm six-axis circular load cell.

The source references used by the flat disk robot live under
`projects/flat-disk-robot/real-parts/`. BREP cache files may be generated
beside STEP inputs during local builds; they are ignored and should not be
committed.
The M3564C source drawing lives under
`projects/m3564c-load-cell/real-parts/`.

Each project declares its build and optional URDF targets in
`projects/<project-slug>/targets.py`. `uv run synthcad-build --list` discovers
those project-local declarations without keeping project factories in the core
package.

## GitHub CI

`.github/workflows/synthcad-ci.yml` selects affected projects from changed
paths, runs root framework tests plus those projects' local tests, exports only
the selected projects, and builds the PR diff viewer for selected targets. Core
framework changes fan out to every project; project-local changes stay scoped
to that project.

Example: [PR #1 CAD review comment](https://github.com/BenCaunt/SynthCAD/pull/1#issuecomment-4373932308).

![SynthCAD PR diff viewer showing the flat disk robot wheel diameter change](docs/assets/pr-diff-viewer.png)

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

For geometry changes, regenerate exports and inspect the affected project
before calling the change done:

```bash
PROJECT=flat-disk-robot
uv run synthcad-build --project "$PROJECT"
uv run synthcad-inspect --project "$PROJECT" --output-dir "projects/$PROJECT/generated/inspection"
uv run synthcad-report --project "$PROJECT"
```

See `projects/flat-disk-robot/docs/flat-disk-robot-notes.md` for robot-specific
layout assumptions, and `projects/m3564c-load-cell/docs/m3564c-load-cell-notes.md`
for the M3564C drawing interpretation.
