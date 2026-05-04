---
name: synthcad-setup-github-project
description: Set up GitHub repository, Actions CI review, artifacts, and branch protection for SynthCAD CAD projects.
---

# SynthCAD GitHub Project Setup

Use this skill when asked to prepare a SynthCAD repository for GitHub-based
collaboration, pull-request review, or CI validation.

## Setup Workflow

1. Confirm the intended repository, default branch, and visibility.
2. Check local git status before editing or pushing.
3. Add or update a GitHub Actions CAD review workflow under
   `.github/workflows/`.
4. Make CI produce reviewable artifacts, not just pass/fail logs:
   generated CAD exports, inspection reports, interference overlays, URDF
   packages, and a Markdown summary in `$GITHUB_STEP_SUMMARY`.
5. Keep `projects/*/generated/`, BREP caches, virtualenvs, and build outputs
   ignored.
6. Run the local checks that mirror CI before committing.
7. Push intentionally and, for nontrivial changes, open a PR rather than
   pushing directly to the protected default branch.

## Commands

```bash
gh auth status
gh repo view --json nameWithOwner,visibility,defaultBranchRef
git status --short --ignored
uv run python -m compileall -q -f main.py synthcad tests projects
uv run pytest
uv run synthcad-build --project flat-disk-robot --profile
uv run synthcad-inspect --target flat-disk-robot --interference all
uv run show-interference --target flat-disk-robot
uv run synthcad-report --project flat-disk-robot
uv run synthcad-urdf --target flat-disk-robot
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
It includes the expected Actions shape, required artifact policy, and branch
protection checklist.
