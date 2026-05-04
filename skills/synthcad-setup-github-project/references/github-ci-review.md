# GitHub CI Review

## Actions Workflow

Create a workflow like `.github/workflows/synthcad-ci.yml` with these jobs:

- compile Python sources;
- run pytest, using the local `readline` shim if needed;
- export the flat disk robot targets;
- run assembly inspection and interference overlays;
- export the URDF package;
- write `synthcad-report` output into `$GITHUB_STEP_SUMMARY`; and
- upload `real-parts/generated/` as a review artifact.

The workflow should run on `pull_request` and on pushes to the default branch.

## Artifact Policy

CI should upload generated review artifacts, but generated files should not be
committed:

```text
real-parts/generated/
*.brep
.venv/
.pytest_cache/
*.egg-info/
```

For PR review, the most useful artifacts are:

- `real-parts/generated/manifest.json`
- `real-parts/generated/flat-disk-robot/*.step`
- `real-parts/generated/flat-disk-robot/*.stl`
- `real-parts/generated/flat-disk-robot/*.glb`
- `real-parts/generated/inspection/inspection-report.json`
- `real-parts/generated/inspection/*.svg`
- `real-parts/generated/inspection/interference/*.svg`
- `real-parts/generated/flat-disk-robot/urdf/`
- `real-parts/generated/ci/validation-report.md`

## Branch Protection

For a shared GitHub project, prefer:

- require pull requests before merging into `main`;
- require the `CAD review` check to pass;
- require branches to be up to date before merge if the repo is active;
- disallow force pushes to `main`;
- keep generated CAD outputs out of review diffs; and
- use artifact links and the Actions summary for generated geometry evidence.

## Repository Setup

Useful commands:

```bash
gh repo create OWNER/REPO --private --source=. --remote=origin --push
gh repo view OWNER/REPO --json nameWithOwner,visibility,defaultBranchRef
gh workflow list
gh run list --limit 5
```

Branch protection usually needs a repository-specific `gh api` call. Inspect
current defaults first and only apply protection once the CI check has run at
least once, so the required status name is known.
