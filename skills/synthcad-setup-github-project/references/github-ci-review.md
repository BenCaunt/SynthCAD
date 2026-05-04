# GitHub CI Review

## Actions Workflow

Create a workflow like `.github/workflows/synthcad-ci.yml` with these jobs:

- compile Python sources;
- run root and project-local pytest suites, using the local `readline` shim if
  needed;
- export the flat disk robot targets;
- run assembly inspection and interference overlays;
- export the URDF package;
- write `synthcad-report` output into `$GITHUB_STEP_SUMMARY`; and
- upload `projects/flat-disk-robot/generated/` as a review artifact;
- build a static PR diff viewer with `synthcad-pr-pages`;
- publish the viewer to `gh-pages/pr-<number>/` for same-repository PRs; and
- create or update a PR comment linking to the web viewer, workflow run, and
  generated artifacts.

The workflow should run on `pull_request` and on pushes to the default branch.
The PR visualization/comment steps should run only for `pull_request` events.

Start new project repos from `references/synthcad-ci-template.yml`. Copy it to
`.github/workflows/synthcad-ci.yml`, then edit the `env:` values at the top for
the project slug, primary assembly target, optional URDF target, and artifact
name. Set `SYNTHCAD_PR_SITE_TARGETS` to the assembly targets that should appear
in the web diff viewer. For multi-project repos, convert those values into a
GitHub Actions matrix and keep the same checks per project.

The workflow needs these token permissions:

```yaml
permissions:
  contents: write
  pull-requests: write
  pages: write
```

Use `actions/checkout` with `fetch-depth: 0`, create a detached base worktree
from `${{ github.event.pull_request.base.sha }}`, then call `synthcad-pr-pages`
with the base root, base SHA, head SHA, output directory, and selected targets.
Upload the generated site as an artifact even when GitHub Pages is the primary
review link.

## Project Test Policy

Every CAD project should include tests under `projects/<project-slug>/tests/`.
Do not put project-specific geometry or interference invariants in root
`tests/`; keep root tests for shared SynthCAD tooling.

For each new project, require tests for:

- geometry invariants for printable parts and assemblies;
- critical real-component interfaces and clearances;
- expected assembly interferences and intentional-overlap exceptions;
- source reference and docs metadata resolving to checked-in project files; and
- project filtering or registry behavior when the project adds targets.

CI should run `uv run pytest` with `pyproject.toml` configured to discover both
root `tests/` and `projects/`.

## Artifact Policy

CI should upload generated review artifacts, but generated files should not be
committed:

```text
projects/*/generated/
*.brep
.venv/
.pytest_cache/
*.egg-info/
```

For PR review, the most useful artifacts are:

- `projects/flat-disk-robot/generated/manifest.json`
- `projects/flat-disk-robot/generated/*.step`
- `projects/flat-disk-robot/generated/*.stl`
- `projects/flat-disk-robot/generated/*.glb`
- `projects/flat-disk-robot/generated/inspection/inspection-report.json`
- `projects/flat-disk-robot/generated/inspection/*.svg`
- `projects/flat-disk-robot/generated/inspection/interference/*.svg`
- `projects/flat-disk-robot/generated/urdf/`
- `projects/flat-disk-robot/generated/ci/validation-report.md`
- `synthcad-pr-diff-viewer` workflow artifact

## PR Visualization Comment

Every PR should get one bot-managed comment identified by
`<!-- synthcad-pr-visualization -->`. The comment should be updated on each
push, not duplicated. Include:

- the base and head commit prefixes being compared;
- a link to the interactive diff viewer when the PR is not from a fork;
- a fallback link to the workflow run and uploaded viewer artifact; and
- enough target/project context for reviewers to know what was visualized.

For same-repository PRs, publish the viewer by replacing
`gh-pages/pr-<number>/` and pushing the `gh-pages` branch. Also ensure the repo
has GitHub Pages configured to serve that branch from `/`. For fork PRs, skip
Pages publishing and rely on uploaded artifacts.

## Branch Protection

For a shared GitHub project, prefer:

- require pull requests before merging into `main`;
- require the `CAD review` check to pass;
- require branches to be up to date before merge if the repo is active;
- disallow force pushes to `main`;
- keep generated CAD outputs out of review diffs; and
- use the PR visualization comment, artifact links, and the Actions summary for
  generated geometry evidence.

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
