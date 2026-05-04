import time
from pathlib import Path

import synthcad.review_assets as review_assets
from synthcad.review_assets import DisplayExportRequest, DisplayExportResult


def test_export_display_assets_batch_preserves_request_order(tmp_path: Path, monkeypatch) -> None:
    delays = {
        "slow-target": 0.05,
        "fast-target": 0.0,
    }

    def fake_run(repo_root: Path, target_name: str, asset_output_dir: Path) -> DisplayExportResult:
        assert repo_root == tmp_path
        time.sleep(delays[target_name])
        return DisplayExportResult(
            target_name=target_name,
            asset_output_dir=asset_output_dir,
            duration_seconds=delays[target_name],
            snapshot={"target": {"name": target_name}},
        )

    monkeypatch.setattr(review_assets, "_run_export_display_assets_subprocess", fake_run)

    results = review_assets.export_display_assets_batch(
        tmp_path,
        [
            DisplayExportRequest("slow-target", tmp_path / "slow-target"),
            DisplayExportRequest("fast-target", tmp_path / "fast-target"),
        ],
        jobs=2,
    )

    assert [result.target_name for result in results] == ["slow-target", "fast-target"]
    assert [result.asset_output_dir.name for result in results] == ["slow-target", "fast-target"]


def test_configured_display_export_jobs_respects_env_override(monkeypatch) -> None:
    monkeypatch.delenv(review_assets.DISPLAY_EXPORT_ENV_VAR, raising=False)
    assert review_assets.configured_display_export_jobs() == review_assets.DEFAULT_DISPLAY_EXPORT_JOBS

    monkeypatch.setenv(review_assets.DISPLAY_EXPORT_ENV_VAR, "3")
    assert review_assets.configured_display_export_jobs() == 3

    monkeypatch.setenv(review_assets.DISPLAY_EXPORT_ENV_VAR, "not-a-number")
    assert review_assets.configured_display_export_jobs() == review_assets.DEFAULT_DISPLAY_EXPORT_JOBS
