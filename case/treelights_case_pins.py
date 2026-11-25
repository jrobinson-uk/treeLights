"""Low-profile case for the tree lights board: the board drops onto pins.

A version of treelights_case.py without screws. The ProtoMate slides down four
printed pins onto shoulders, and posts under the lid hold it down. Every height
comes from the stack settings below, so changing one moves everything else.

Run:  python3 treelights_case_pins.py   (needs: pip install manifold3d trimesh numpy)
Makes case-pins-base.stl, case-pins-lid.stl and case-pins-plunger.stl.

Coordinates in mm: x left to right as on the planning sheet, y from the cable
edge (front, y=0) to the USB edge (back), z up.
"""

import numpy as np
import trimesh
from manifold3d import CrossSection, JoinType, Manifold

from treelights_case import add_print_aids, tree_hole  # shared with the screw version

# ---------------- board (from protomate-dimensions.svg) ----------------

BOARD_W, BOARD_H, BOARD_T = 84.38, 56.59, 1.6
BOARD_R = 3.0
HOLE_DX, HOLE_DY = 78.0, 50.15

# ---------------- stack: measure these ----------------

FLOOR = 2.0
SHOULDER_H = 3.0         # room under the board for solder joints (trim pins flush)
PICO_GAP = 11.0          # board top to Pico underside: 11 = Pico in 8.5 mm sockets
                         # (as built); 2.5 if it's soldered straight onto the board
PICO_T = 1.0
BOOTSEL_H = 3.0          # button top above the Pico's top surface
PICO_PINS_ABOVE = 2.5    # header pin tips sticking out of the Pico's top surface
TALLEST_PART = 13.0      # tallest part on the board above its top surface
                         # (the lever terminal, levers closed: about 13 mm)
HEADROOM = 1.0           # space left under the lid
LID_T = 2.0

# ---------------- pins ----------------

HOLE_D = 2.7             # measure the ProtoMate's holes
PIN_D_SNUG = 2.45        # two diagonal pins locate the board
PIN_D_LOOSE = 2.30       # the other two allow for print error
SHOULDER_D = 4.5         # stays inside the 5 mm bare pad
PIN_ABOVE_BOARD = 2.5
PIN_CHAMFER = 0.6

# Lid posts come down onto the board's corners, over the pin tips.
POST_OD = 5.0
POST_ID = 3.2
POST_GAP = 0.0           # gap between post and board; 0 clamps it, raise if the lid won't close

# ---------------- case ----------------

CLEAR = 0.4
WALL = 2.0
LID_LIP = 3.0
LID_LIP_T = 1.2
LID_FIT = 0.25

PICO_X = 16.49           # Pico centre line, sheet coordinates
PICO_TOP_Y = 3.96        # Pico's USB-end edge, measured down from the USB edge of the board
USB_W, USB_H = 12.0, 8.0

BOOTSEL_FROM_TOP = 12.0      # MEASURE: Pico USB end to button centre
BOOTSEL_FROM_CENTRE = -4.5   # Pico centre line to button centre (was -1; first print 3-4 mm out)

CABLE_X = 28.63 + 6 * 2.54   # terminal in columns 6-8 (docs/BUILD.md); middle contact, column 7
CABLE_W, CABLE_H = 10.0, 6.0  # slot for the wires: covers all three openings with room to spare
WIRE_Z = 7.0                  # MEASURED: board top to the centre of the terminal's wire openings
TERMINAL_W = 17.0            # width of the 3-way lever terminal
CABLE_Z0 = WIRE_Z - CABLE_H / 2   # slot starts this far above the board top (centred on the openings)

KEYHOLES = True
SEG = 64

# ---------------- derived heights ----------------

BOARD_BOTTOM_Z = FLOOR + SHOULDER_H
BOARD_TOP_Z = BOARD_BOTTOM_Z + BOARD_T
PICO_TOP_Z = BOARD_TOP_Z + PICO_GAP + PICO_T
BOOTSEL_TOP_Z = PICO_TOP_Z + BOOTSEL_H
CONTENT_TOP_Z = max(BOARD_TOP_Z + TALLEST_PART, BOOTSEL_TOP_Z, PICO_TOP_Z + PICO_PINS_ABOVE,
                    BOARD_TOP_Z + PIN_ABOVE_BOARD)
WALL_TOP_Z = CONTENT_TOP_Z + HEADROOM          # underside of the lid
TOTAL_H = WALL_TOP_Z + LID_T

IN_W, IN_D = BOARD_W + 2 * CLEAR, BOARD_H + 2 * CLEAR
OUT_W, OUT_D = IN_W + 2 * WALL, IN_D + 2 * WALL
BOARD_X0, BOARD_Y0 = WALL + CLEAR, WALL + CLEAR
OUT_R = BOARD_R + CLEAR + WALL


def sheet_to_case(x, y_from_usb):
    return BOARD_X0 + x, BOARD_Y0 + (BOARD_H - y_from_usb)


def rounded_rect(w, d, r, x0=0.0, y0=0.0):
    cs = CrossSection.square((w - 2 * r, d - 2 * r)).translate((x0 + r, y0 + r))
    return cs.offset(r, JoinType.Round, circular_segments=SEG)


def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def cyl(x, y, z0, h, d, d2=None):
    return Manifold.cylinder(h, d / 2, (d2 if d2 else d) / 2, SEG).translate((x, y, z0))


def hole_centres():
    """Board holes in case coordinates, with the pin size for each (snug on one diagonal)."""
    hx, hy = (BOARD_W - HOLE_DX) / 2, (BOARD_H - HOLE_DY) / 2
    return [
        (BOARD_X0 + hx, BOARD_Y0 + hy, PIN_D_SNUG),
        (BOARD_X0 + BOARD_W - hx, BOARD_Y0 + BOARD_H - hy, PIN_D_SNUG),
        (BOARD_X0 + BOARD_W - hx, BOARD_Y0 + hy, PIN_D_LOOSE),
        (BOARD_X0 + hx, BOARD_Y0 + BOARD_H - hy, PIN_D_LOOSE),
    ]


def make_base():
    base = rounded_rect(OUT_W, OUT_D, OUT_R).extrude(WALL_TOP_Z)
    base -= rounded_rect(IN_W, IN_D, BOARD_R + CLEAR, WALL, WALL).extrude(WALL_TOP_Z).translate((0, 0, FLOOR))

    for x, y, d in hole_centres():
        base += cyl(x, y, FLOOR - 0.01, SHOULDER_H + 0.01, SHOULDER_D)          # shoulder
        straight = BOARD_T + PIN_ABOVE_BOARD - PIN_CHAMFER
        base += cyl(x, y, BOARD_BOTTOM_Z - 0.01, straight + 0.01, d)            # pin
        base += cyl(x, y, BOARD_BOTTOM_Z + straight, PIN_CHAMFER, d, d - 2 * PIN_CHAMFER + 0.4)

    # USB opening, open to the top (the lid closes it)
    ux, _ = sheet_to_case(PICO_X, 0)
    uz = PICO_TOP_Z + 1.3
    base -= box(ux - USB_W / 2, OUT_D - WALL - 1, uz - USB_H / 2, ux + USB_W / 2, OUT_D + 1, WALL_TOP_Z + 1)

    # Cable slot in line with the terminal
    cx, _ = sheet_to_case(CABLE_X, 0)
    slot = rounded_rect(CABLE_W, CABLE_H, 1.2).extrude(WALL + 2)
    base -= slot.rotate((90, 0, 0)).translate((cx - CABLE_W / 2, WALL + 1, BOARD_TOP_Z + CABLE_Z0))

    if KEYHOLES:
        for kx in (OUT_W / 2 - 25, OUT_W / 2 + 25):
            ky = OUT_D / 2 + 6
            base -= cyl(kx, ky, -1, FLOOR + 2, 7.5)
            base -= box(kx - 1.9, ky - 10, -1, kx + 1.9, ky, FLOOR + 1)
            base -= cyl(kx, ky - 10, -1, FLOOR + 2, 3.8)
    return add_print_aids(base, OUT_W, OUT_D, OUT_R, WALL_TOP_Z)


def bootsel_xy():
    return sheet_to_case(PICO_X + BOOTSEL_FROM_CENTRE, PICO_TOP_Y + BOOTSEL_FROM_TOP)


def make_lid():
    """Modelled in printing position: top face on the bed (z=0), lip and posts up.
    Case y maps to OUT_D - y here because the lid is flipped."""
    flip = lambda y: OUT_D - y
    lid = rounded_rect(OUT_W, OUT_D, OUT_R).extrude(LID_T)
    lip_o = rounded_rect(IN_W - 2 * LID_FIT, IN_D - 2 * LID_FIT, BOARD_R + CLEAR - LID_FIT, WALL + LID_FIT, WALL + LID_FIT)
    lip_i = lip_o.offset(-LID_LIP_T, JoinType.Round, circular_segments=SEG)
    lid += (lip_o - lip_i).extrude(LID_LIP).translate((0, 0, LID_T))

    # No lip across the USB opening
    ux, _ = sheet_to_case(PICO_X, 0)
    lid -= box(ux - USB_W / 2 - 1, 0, LID_T, ux + USB_W / 2 + 1, WALL + LID_FIT + LID_LIP_T + 1, LID_T + LID_LIP + 1)

    # ...or over the lever terminal at the cable edge (it reaches the lip's depth)
    cx, _ = sheet_to_case(CABLE_X, 0)
    lid -= box(cx - TERMINAL_W / 2 - 1, OUT_D - (WALL + LID_FIT + LID_LIP_T + 1), LID_T,
               cx + TERMINAL_W / 2 + 1, OUT_D + 1, LID_T + LID_LIP + 1)

    # Hold-down posts: from the lid's underside down to the board's top surface
    post_len = WALL_TOP_Z - BOARD_TOP_Z - POST_GAP
    for x, y, _ in hole_centres():
        lid += cyl(x, flip(y), LID_T - 0.01, post_len + 0.01, POST_OD)
        lid -= cyl(x, flip(y), LID_T + post_len - (PIN_ABOVE_BOARD + 0.8), PIN_ABOVE_BOARD + 1.6, POST_ID)

    # Tree hole for the inlay (case-tree-inlay.stl), star towards the cable edge
    lid -= tree_hole(OUT_D)

    bx, by = bootsel_xy()
    lid -= cyl(bx, flip(by), -1, LID_T + 2, 5.0)
    return lid


def make_plunger():
    flange_t = 1.0
    foot = max(WALL_TOP_Z - flange_t - BOOTSEL_TOP_Z, 0.5)
    p = cyl(0, 0, 0, foot, 5.5)
    p += cyl(0, 0, foot, flange_t, 8.0)
    p += cyl(0, 0, foot + flange_t, LID_T + 2.5, 4.4)
    return p


def save(m, name):
    mesh = m.to_mesh()
    tm = trimesh.Trimesh(vertices=np.array(mesh.vert_properties)[:, :3], faces=np.array(mesh.tri_verts))
    tm.export(name)
    b = tm.bounds
    print("%-24s %5.1f x %5.1f x %5.1f mm  watertight=%s" % (name, *(b[1] - b[0]), tm.is_watertight))


if __name__ == "__main__":
    print("board top %.1f, Pico top %.1f, BOOTSEL %.1f, lid underside %.1f, total height %.1f mm"
          % (BOARD_TOP_Z, PICO_TOP_Z, BOOTSEL_TOP_Z, WALL_TOP_Z, TOTAL_H))
    save(make_base(), "case-pins-base.stl")
    save(make_lid(), "case-pins-lid.stl")
    save(make_plunger(), "case-pins-plunger.stl")
