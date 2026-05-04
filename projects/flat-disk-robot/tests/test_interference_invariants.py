from functools import lru_cache

from synthcad.build import target_lookup
from synthcad.inspection import find_interferences


@lru_cache(maxsize=None)
def _interference_pairs(target_name: str) -> set[tuple[str, str]]:
    target = target_lookup()[target_name]
    report = find_interferences(target.factory())
    return {
        tuple(sorted((interference.first, interference.second)))
        for interference in report.interferences
    }


def test_flat_disk_robot_only_has_known_press_fit_interferences() -> None:
    assert _interference_pairs("flat-disk-robot") == {
        (
            "left Repeat Compact 1806 gearmotor",
            "left TPU press-fit wheel",
        ),
        (
            "right Repeat Compact 1806 gearmotor",
            "right TPU press-fit wheel",
        ),
    }
