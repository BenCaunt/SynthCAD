---
name: synthcad-setup-github-project
description: Set up GitHub repository, Actions CI review, project-local tests, artifacts, and branch protection for SynthCAD CAD projects.
---

# SynthCAD GitHub Project Setup

Use this skill when asked to prepare a SynthCAD repository for GitHub-based
collaboration, pull-request review, or CI validation.

## Setup Workflow

1. Confirm the intended repository, default branch, and visibility.
2. Check local git status before editing or pushing.
3. Add or update a GitHub Actions CAD review workflow under
   `.github/workflows/`.
4. Make CI produce reviewable artifacts and PR review links, not just pass/fail
   logs:
   generated CAD exports, inspection reports, interference overlays, URDF
   packages, a Markdown summary in `$GITHUB_STEP_SUMMARY`, a static PR diff
   viewer, and an upserted PR comment linking to the viewer and workflow run.
5. Ensure every CAD project has tests under `projects/<project-slug>/tests/`
   and that CI runs both root tests and project-local tests.
6. Keep `projects/*/generated/`, BREP caches, virtualenvs, and build outputs
   ignored.
7. Run the local checks that mirror CI before committing.
8. Push intentionally and, for nontrivial changes, open a PR rather than
   pushing directly to the protected default branch.

## Commands

Set the project variables from `uv run synthcad-build --list` and the current
repo's build registry:

```bash
gh auth status
gh repo view --json nameWithOwner,visibility,defaultBranchRef
git status --short --ignored
uv run synthcad-build --list
PROJECT=<project-slug>
ASSEMBLY_TARGET=<assembly-target>
URDF_TARGET=<urdf-target-or-empty>
uv run python -m compileall -q -f main.py synthcad tests projects
uv run pytest
uv run pytest "projects/$PROJECT/tests"
uv run synthcad-build --project "$PROJECT" --profile
uv run synthcad-inspect --target "$ASSEMBLY_TARGET" --interference all
uv run show-interference --target "$ASSEMBLY_TARGET"
uv run synthcad-report --project "$PROJECT"
test -z "$URDF_TARGET" || uv run synthcad-urdf --target "$URDF_TARGET"
```

Use the local `readline` shim for pytest if the local uv Python crashes before
collection:

```bash
uv run python - <<'PY'
import sys
import types
sys.modules["readline"] = types.ModuleType("readline")
import pytest
raise SystemExit(pytest.main(["-q"]))
PY
```

## CI Review Pattern

Read `references/github-ci-review.md` when creating or changing the workflow.
It includes the expected Actions shape, artifact policy,
PR visualization/comment policy, branch protection checklist, and reusable
workflow template at `references/synthcad-ci-template.yml`.
