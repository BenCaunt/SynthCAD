from synthcad.project_selection import select_projects_for_paths


def test_project_selection_scopes_project_local_changes() -> None:
    selection = select_projects_for_paths(
        [
            "projects/m3564c-load-cell/m3564c_load_cell/load_cell.py",
            "projects/m3564c-load-cell/tests/test_m3564c_load_cell.py",
        ]
    )

    assert selection.projects == ("m3564c-load-cell",)
    assert selection.reason == "project-local changes"
    assert selection.test_paths == ("tests", "projects/m3564c-load-cell/tests")
    assert selection.build_target_args == ("--project", "m3564c-load-cell")
    assert selection.build_targets == ("m3564c-six-axis-load-cell",)
    assert selection.assembly_targets == ()
    assert selection.urdf_targets == ()
    assert selection.pr_site_targets == ("m3564c-six-axis-load-cell",)


def test_project_selection_runs_all_projects_for_core_changes() -> None:
    selection = select_projects_for_paths(["synthcad/build.py"])

    assert selection.projects == ("flat-disk-robot", "m3564c-load-cell")
    assert "projects/flat-disk-robot/tests" in selection.test_paths
    assert "projects/m3564c-load-cell/tests" in selection.test_paths
    assert "flat-disk-robot" in selection.assembly_targets
    assert "flat-disk-robot" in selection.urdf_targets
    assert "m3564c-six-axis-load-cell" in selection.pr_site_targets
