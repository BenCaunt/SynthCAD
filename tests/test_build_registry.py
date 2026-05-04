from pathlib import Path

import pytest

from synthcad.build import BUILD_TARGETS, filter_targets, target_lookup


def test_build_targets_have_unique_names() -> None:
    names = [target.name for target in BUILD_TARGETS]
    assert len(names) == len(set(names))


def test_build_targets_have_required_metadata_and_existing_refs() -> None:
    for target in BUILD_TARGETS:
        assert target.project
        assert target.status
        assert target.source_module
        for path in [*target.source_refs, *target.docs]:
            assert Path(path).exists(), f"{target.name} references missing path {path}"


def test_filter_targets_dedupes_explicit_names() -> None:
    selected = filter_targets(names=["flat-disk-robot", "flat-disk-robot"])
    assert [target.name for target in selected] == ["flat-disk-robot"]


def test_filter_targets_rejects_unknown_names() -> None:
    with pytest.raises(ValueError, match="Unknown build target"):
        filter_targets(names=["does-not-exist"])


def test_validation_references_resolve() -> None:
    lookup = target_lookup()
    for target in BUILD_TARGETS:
        for interference_target in target.validation.interference_targets:
            assert interference_target in lookup, (
                f"{target.name} references unknown interference target "
                f"{interference_target}"
            )
