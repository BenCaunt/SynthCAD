# SynthCAD Project Workflow

## Discover Context

Do not assume the project slug or target names. Start with:

```bash
uv run synthcad-build --list
```

Then set:

- `PROJECT`: the project slug under `projects/<project-slug>/`.
- `TARGET`: the part or assembly target being changed.
- `ASSEMBLY_TARGET`: the assembly target used for inspection/interference
  review.
- `URDF_TARGET`: the target to export as URDF, or empty when not applicable.

Find source ownership from `projects/<project-slug>/targets.py` and each
target's `source_module`. Project-specific CAD should live under the owning
`projects/<project-slug>/` tree. Keep `synthcad/` for shared framework code,
CLI tooling, and generic CAD utilities.

## Project Files

For every project, keep distribution assets grouped under the project slug:

- source references: `projects/<project-slug>/real-parts/`
- generated outputs: `projects/<project-slug>/generated/`
- project docs: `projects/<project-slug>/docs/`
- project tests: `projects/<project-slug>/tests/`

Generated outputs and BREP caches should stay out of git.

## Project Tests

Project-specific tests belong under `projects/<project-slug>/tests/`, not root
`tests/`. Root tests are for shared SynthCAD tooling.

For each project, write tests that cover:

- geometry invariants for printable parts and assemblies;
- critical real-component interfaces such as holes, shafts, registers,
  clearances, service access, cable/connector access, and mounting faces;
- expected assembly interferences and documented intentional overlaps;
- source reference and docs metadata resolving to checked-in project files; and
- target selection or project filtering when the project adds registry behavior.

Useful project-local test names include `test_geometry_invariants.py`,
`test_interference_invariants.py`, and `test_<interface>_clearances.py`. Pick
names that match the current project behavior being protected.

## Typical Loop

1. Probe the current target.

```bash
uv run synthcad-probe --target "$TARGET" --children
```

2. Edit parameterized CAD source in the target's existing module.

3. Run focused tests.

```bash
uv run pytest "projects/$PROJECT/tests" tests/test_build_registry.py
```

4. Regenerate and inspect.

```bash
uv run synthcad-build --project "$PROJECT"
uv run synthcad-inspect --target "$ASSEMBLY_TARGET"
uv run show-interference --target "$ASSEMBLY_TARGET"
uv run synthcad-report --project "$PROJECT"
```

5. Export URDF only when the project has a URDF target.

```bash
test -z "$URDF_TARGET" || uv run synthcad-urdf --target "$URDF_TARGET"
```

6. Update project docs with changed assumptions, known interferences, or
   validation evidence.
