from __future__ import annotations

from build123d import Compound

from synthcad.cad.common import BLACK, COPPER_GOLD, PCB_THICKNESS, RADAR_PURPLE, SILK_WHITE, box, rounded_board, tag


RADAR_BOARD_LENGTH = 24.0
RADAR_BOARD_WIDTH = 18.0
RADAR_BOARD_RADIUS = 1.5


def make_forward_radar_module() -> Compound:
    """Small assumed radar module used until a real STEP or drawing is added."""

    children = [rounded_board("assumed radar sensor PCB", RADAR_BOARD_LENGTH, RADAR_BOARD_WIDTH, RADAR_BOARD_RADIUS)]
    children.append(
        box(
            "radar RF shield",
            0,
            1.5,
            PCB_THICKNESS + 1.0,
            13.0,
            10.0,
            2.0,
            SILK_WHITE,
        )
    )
    children.append(
        box(
            "radar antenna keepout",
            0,
            6.2,
            PCB_THICKNESS + 0.06,
            20.0,
            4.0,
            0.08,
            COPPER_GOLD,
        )
    )
    children.append(
        box(
            "radar connector",
            0,
            -7.1,
            PCB_THICKNESS + 1.0,
            8.0,
            2.2,
            2.0,
            BLACK,
        )
    )
    return tag(Compound(children=children, label="forward-radar-module"), "forward radar module", RADAR_PURPLE)
