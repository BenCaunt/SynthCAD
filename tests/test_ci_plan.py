from pathlib import Path

from synthcad.ci_plan import detect_projects, plan_for_changed_paths, project_from_changed_path


def test_project_from_changed_path_detects_project_package() -> None:
    assert (
        project_from_changed_path("synthcad/projects/demo_ftc_robot/robot.py")
        == "demo-ftc-robot"
    )


def test_project_from_changed_path_detects_project_directory() -> None:
    assert (
        project_from_changed_path("projects/demo-ftc-robot/docs/demo-ftc-robot-notes.md")
        == "demo-ftc-robot"
    )


def test_detect_projects_prefers_explicit_project_changes() -> None:
    projects = detect_projects(
        [
            "synthcad/build.py",
            "projects/demo-ftc-robot/README.md",
        ]
    )

    assert projects == ["demo-ftc-robot"]


def test_detect_projects_defaults_to_all_projects_for_shared_only_changes() -> None:
    assert detect_projects(["synthcad/library/crayon.py"]) == [
        "demo-ftc-robot",
        "flat-disk-robot",
    ]


def test_ci_plan_selects_demo_project_targets_and_tests(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "projects" / "demo-ftc-robot" / "tests").mkdir(parents=True)

    plan = plan_for_changed_paths(
        ["projects/demo-ftc-robot/README.md"],
        repo_root=repo_root,
    )

    assert plan.projects == ["demo-ftc-robot"]
    assert plan.test_paths == ["tests", "projects/demo-ftc-robot/tests"]
    assert plan.inspect_targets == ["demo-ftc-robot"]
    assert plan.pr_site_targets == ["demo-ftc-robot"]
    assert plan.artifact_paths == ["projects/demo-ftc-robot/generated"]
