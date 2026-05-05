from synthcad.build import target_lookup
from synthcad.paths import project_generated_dir
from synthcad.report_cli import build_report_bundle


def test_report_bundle_defaults_to_selected_project_generated_dir() -> None:
    target = target_lookup()["demo-ftc-robot"]

    bundle = build_report_bundle(selected_targets=[target])

    assert bundle["artifacts"]["manifest"]["path"] == str(
        project_generated_dir("demo-ftc-robot") / "manifest.json"
    )
    assert bundle["artifacts"]["inspection"]["path"] == str(
        project_generated_dir("demo-ftc-robot") / "inspection" / "inspection-report.json"
    )
