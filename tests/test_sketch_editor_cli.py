from pathlib import Path

from synthcad.sketch_editor_cli import apply_constant_updates, discover_editable_constants


def test_discover_editable_constants(tmp_path: Path):
    module = tmp_path / "model.py"
    module.write_text(
        "A = 1\nB = (1.0, 2.0)\nname='x'\nnot_upper = 2\n", encoding="utf-8"
    )

    constants = discover_editable_constants(module)
    names = [c.name for c in constants]
    assert names == ["A", "B"]


def test_apply_constant_updates(tmp_path: Path):
    module = tmp_path / "model.py"
    module.write_text("A = 1\nB = (1.0, 2.0)\n", encoding="utf-8")

    apply_constant_updates(module, {"A": 4, "B": (5.0, 6.0)})

    text = module.read_text(encoding="utf-8")
    assert "A = 4" in text
    assert "B = (5.0, 6.0)" in text
