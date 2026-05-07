# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SynthCAD is a `build123d` CAD workflow for generating, inspecting, and exporting
3D-printable robotics parts from Python. The open-source extraction contains
the flat disk robot project plus its reference inputs and a small set of
reusable CAD primitives. Python 3.12+ is required and the project is managed
with `uv`.

All CAD dimensions are in millimeters. Coordinate convention for the flat disk
robot: chassis disk centered on XY, +Z up, +Y forward, drive axle parallel to X.

## Common Commands

```bash
# Build (export STEP/STL/GLB + manifest.json + per-target snapshot.json)
uv run synthcad-build --list                    # show projects and targets
uv run synthcad-build --project flat-disk-robot # build all targets in a project
uv run synthcad-build --target <target-name>    # build one target
uv run synthcad-build --profile                 # add per-format timings

# Inspect / probe / interference review
uv run synthcad-probe --target <target> --children
uv run synthcad-inspect --target <target> --interference all --view isometric --view rear-isometric
uv run show-interference --target <assembly> --view isometric --view rear-isometric
uv run synthcad-report --project <project>     # markdown validation report

# URDF (ROS / sim handoff)
uv run synthcad-urdf --target <target>

# Tests
uv run pytest
uv run pytest projects/<project>/tests          # project-local tests only
uv run pytest tests/test_build_registry.py::test_build_targets_have_unique_names
```

If `uv run pytest` segfaults during collection on the local Python (a known
`readline` quirk), preload a stub before invoking pytest. CI uses the same
pattern in `.github/workflows/synthcad-ci.yml`:

```bash
uv run python - <<'PY'
import sys, types
sys.modules["readline"] = types.ModuleType("readline")
import pytest
raise SystemExit(pytest.main(["-q"]))
PY
```

Compile-check before pushing: `uv run python -m compileall -q -f main.py synthcad tests projects`.

## Architecture

### Build registry is the source of truth

`synthcad/build.py` defines a single `BUILD_TARGETS` list of `BuildTarget`
dataclasses. Every CLI (`build`, `inspect_cli`, `probe_cli`, `report_cli`,
`show_interference_cli`, `urdf_cli`, `viewer_cli`, `pr_pages`) reads from this
registry. To add a new exportable part or assembly, register it here with its
factory callable, project slug, source module, source refs, docs, validation
plan, and any documented `IntentionalInterference` exceptions. Don't add CLI
flags to wire in new geometry — the registry drives discovery.

A `BuildTarget` carries:
- `factory` — zero-arg callable returning the build123d model
- `inspection_factory` (optional) — lighter variant used by inspection/probe
- `formats` — defaults to `("step", "stl", "glb")`
- `validation.interference_targets` — assemblies whose interference must be
  re-checked when this target changes
- `intentional_interferences` — overlaps that are expected (e.g. TPU
  press-fit), so inspection doesn't flag them as failures

`output_prefix()` resolves to `<output_dir>/<project>/<name>` unless the
output_dir is already the project's generated dir, in which case the project
prefix is dropped. Both layouts are produced in practice.

### Project layout convention

Each robot/CAD project lives in two places:

- **Source** under `synthcad/projects/<project_slug>/` — Python modules
  (`robot.py`, `urdf.py`, etc.) that build the geometry.
- **Project assets** under `projects/<project-slug>/`:
  - `real-parts/` — checked-in vendor STEP / drawings / images
  - `docs/` — design notes and validation history
  - `tests/` — geometry and assembly invariants specific to this project
  - `generated/` — STEP/STL/GLB/inspection/URDF outputs (gitignored)
  - `project.toml` — metadata (boundary, lifecycle, summary, layout)

Test split: root `tests/` is reserved for framework, CLI, registry, library,
and shared review-asset behavior. Project-specific tests must live under
`projects/<project-slug>/tests/`. CI requires at least one
`projects/<SYNTHCAD_PROJECT>/tests/test_*.py` to exist.

### Shared CAD code lives outside projects

- `synthcad/cad/common.py` — drawing primitives, color palette, `tag()`,
  `export_model[_with_timings]` (handles STEP/STL/GLB with the documented GLB
  deflection settings), `load_cad`.
- `synthcad/cad/features.py`, `synthcad/cad/serviceability.py` — shared
  feature-detection and keepout helpers.
- `synthcad/library/` — reusable parts (`batteries`, `boards`, `repeat_drive`,
  `sensors`) that any project can compose.
- `synthcad/external_parts.py` — `ExternalPart` registry for vendor STEPs
  with a transparent `.brep` cache layer (25–45x faster than re-parsing STEP).
  BREP cache files are written next to STEP sources and are gitignored.

### Inspection and review pipeline

- `synthcad/inspection.py` — interference detection between assembly children,
  bounding-box summaries, `PROJECTION_VIEWS` (isometric, left/right/rear).
- `synthcad/review_assets.py` — `build_display_snapshot()` writes a
  `<target>.snapshot.json` alongside each export so the web viewer and PR diff
  viewer can render without re-running build123d.
- `synthcad/webviewer/` — packaged static assets (declared in
  `[tool.setuptools.package-data]`) served by the viewer CLI.
- `synthcad/pr_pages.py` — builds the static base/head diff site that CI
  uploads as an artifact and (when Pages is enabled) publishes to a
  `gh-pages` branch with a comment on the PR.

### URDF generation

`synthcad/urdf.py` plus `synthcad/projects/<project>/urdf.py` produce a URDF
package under `projects/<project>/generated/urdf/<project>/` containing the
URDF file, STL meshes (millimeters; URDF references them with a `0.001` scale
so the robot loads in meters), and a `urdf-manifest.json`. Mass and inertial
assumptions are encoded in the project's `urdf.py` and documented in the
project's notes — they are starting values, not measured.

## Conventions

- **Don't hand-edit generated files** (STEP, STL, GLB, URDF, inspection,
  `.brep`, `manifest.json`, `*.snapshot.json`). Regenerate via the CLIs.
- **Preserve real component interfaces first** — hole patterns, shafts,
  registers, fastener clearances, mounting faces, cable/connector access. The
  flat disk robot's encoded constraints are documented in
  `projects/flat-disk-robot/docs/flat-disk-robot-notes.md`; update that file
  when assumptions change.
- **Prefer small parameterized changes** in the existing project module and
  expose new constants at module level so tests can assert on them
  (see `projects/flat-disk-robot/tests/test_geometry_invariants.py` for
  the pattern of importing constants directly from `robot.py`).
- **Reusable primitives belong in `synthcad/library/` or `synthcad/cad/`**,
  never inside a project module that other projects would have to import.
- **When you add or change a build target**, also update the project's tests
  for geometry invariants, source refs/docs metadata, and expected
  intentional interferences. CI fails closed on missing project-local tests
  and on unknown interference target references in the registry.

## Done criteria for a CAD change

A change is done when:
- the changed target imports and builds without errors,
- relevant root and project-local tests pass,
- exports regenerate for the affected project or target,
- inspection artifacts are regenerated for the changed target/assembly,
- unexpected interferences are fixed or recorded as `IntentionalInterference`
  on the target, and
- project-specific assumptions or validation notes are updated in
  `projects/<project>/docs/`.

## Agent skills

This repo ships two skill bundles under `skills/` that can be installed via
`vercel-labs/skills`:

- `synthcad-cad-authoring` — operating rules and command set for CAD work.
- `synthcad-setup-github-project` — CI, PR review artifacts, and branch
  protection setup.

The repo intentionally has no root `SKILL.md` so installers copy only the
selected skill rather than the whole CAD repo.
