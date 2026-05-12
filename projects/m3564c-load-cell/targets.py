from __future__ import annotations

from m3564c_load_cell.load_cell import make_m3564c_load_cell
from synthcad.registry import BuildTarget


M3564C_SOURCE_REFS = (
    "projects/m3564c-load-cell/real-parts/m3564c-drawing.pdf",
)
M3564C_DOCS = ("projects/m3564c-load-cell/docs/m3564c-load-cell-notes.md",)


BUILD_TARGETS = (
    BuildTarget(
        "m3564c-six-axis-load-cell",
        make_m3564c_load_cell,
        "vendor-reference-part",
        "m3564c_load_cell.load_cell",
        False,
        "m3564c-load-cell",
        "reference-model",
        source_refs=M3564C_SOURCE_REFS,
        docs=M3564C_DOCS,
    ),
)

URDF_TARGETS = ()
