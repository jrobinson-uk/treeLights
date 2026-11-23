"""3D-printable case for the tree lights ProtoMate for Pico board.

Run:  python3 treelights_case.py      (needs: pip install manifold3d trimesh numpy)
Makes case-base.stl, case-lid.stl and case-plunger.stl in this folder.

Coordinates: millimetres. x runs left to right as on the planning sheet,
y runs from the cable edge (front, y=0) to the USB edge (back), z is up.
Board measurements come from protomate-dimensions.svg.
"""

import math

import numpy as np
import trimesh
from manifold3d import CrossSection, JoinType, Manifold

# ---------------- settings: check these against your parts ----------------

BOARD_W, BOARD_H, BOARD_T = 84.38, 56.59, 1.6   # ProtoMate outline and thickness
BOARD_R = 3.0                                   # corner radius
HOLE_DX, HOLE_DY = 78.0, 50.15                  # mounting-hole spacing

CLEAR = 0.4          # gap between board edge and inner wall
WALL = 2.0
FLOOR = 2.0
STANDOFF_H = 5.0     # room under the board for solder joints
STANDOFF_D = 5.0     # fits the 5 mm pad around each hole
SCREW_HOLE_D = 2.2   # pilot for M2.5 thread-forming screws (use 3.6 for heat-set inserts)

WALL_TOP_Z = 26.0    # height of the base walls (the lid sits on top)
# Stack (z from the case bottom): floor 2, standoffs to 7, board top 8.6,
# 8.5 mm sockets plus the Pico's own 2.5 mm header plastic -> Pico PCB top
# about 20.6, BOOTSEL top about 23.6. 26 leaves about 2.4 mm above the button. Lay the 1000 uF capacitor on its side,
# or raise WALL_TOP_Z to suit a standing one (board top + capacitor height + 2).
LID_T = 2.0
LID_LIP = 3.0        # depth of the lip that plugs into the base
LID_LIP_T = 1.2
LID_FIT = 0.25       # clearance of the lip (raise if the lid is too tight)

# Pico (board coordinates from the planning sheet: x from left, y from USB edge)
PICO_X = 16.49                 # Pico centre line
PICO_TOP_Y = 3.96              # Pico's USB-end edge
PICO_PCB_TOP_Z = 20.6
USB_W, USB_H = 12.0, 8.0       # opening for the micro-USB plug and its overmould

# BOOTSEL: MEASURE ON YOUR PICO before printing the lid.
# Distance from the Pico's USB-end edge to the button centre, and from the
# Pico's centre line (positive = towards the proto area).
BOOTSEL_FROM_TOP = 12.0
BOOTSEL_FROM_CENTRE = -1.0
BOOTSEL_TOP_Z = 23.6

# Lights cable: spring terminal on the bottom row, columns 7-9 (centre column 8)
CABLE_X = 28.63 + 7 * 2.54     # = 46.4
CABLE_W, CABLE_H = 7.0, 5.0    # slot for the 3-wire pigtail
CABLE_Z0 = 1.0                 # slot starts this far above the board top

KEYHOLES = True                # keyholes for hanging on two screws 50 mm apart, cable edge up

SEG = 64

# ---------------- derived positions ----------------

IN_W, IN_D = BOARD_W + 2 * CLEAR, BOARD_H + 2 * CLEAR
OUT_W, OUT_D = IN_W + 2 * WALL, IN_D + 2 * WALL
BOARD_X0, BOARD_Y0 = WALL + CLEAR, WALL + CLEAR        # board's lower-left corner
BOARD_BOTTOM_Z = FLOOR + STANDOFF_H
BOARD_TOP_Z = BOARD_BOTTOM_Z + BOARD_T
BASE_H = WALL_TOP_Z


def sheet_to_case(x, y_from_usb):
    """Planning-sheet coordinates (x from left, y down from the USB edge) to case x, y."""
    return BOARD_X0 + x, BOARD_Y0 + (BOARD_H - y_from_usb)


def rounded_rect(w, d, r, x0=0.0, y0=0.0):
    r = max(r, 0.01)
    cs = CrossSection.square((w - 2 * r, d - 2 * r)).translate((x0 + r, y0 + r))
    return cs.offset(r, JoinType.Round, circular_segments=SEG)


def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def cyl(x, y, z0, h, d, d2=None):
    return Manifold.cylinder(h, d / 2, (d2 if d2 else d) / 2, SEG).translate((x, y, z0))


def hole_centres():
    hx = (BOARD_W - HOLE_DX) / 2
    hy = (BOARD_H - HOLE_DY) / 2
    return [(BOARD_X0 + x, BOARD_Y0 + y) for x in (hx, BOARD_W - hx) for y in (hy, BOARD_H - hy)]


# ---------------- base ----------------

def make_base():
    outer = rounded_rect(OUT_W, OUT_D, BOARD_R + CLEAR + WALL).extrude(BASE_H)
    inner = rounded_rect(IN_W, IN_D, BOARD_R + CLEAR, WALL, WALL).extrude(BASE_H).translate((0, 0, FLOOR))
    base = outer - inner

    for x, y in hole_centres():
        base += cyl(x, y, FLOOR - 0.01, STANDOFF_H + 0.01, STANDOFF_D)
        base -= cyl(x, y, FLOOR + 0.8, STANDOFF_H, SCREW_HOLE_D)

    # USB opening in the back wall, centred on the Pico's micro-USB socket
    ux, _ = sheet_to_case(PICO_X, 0)
    uz = PICO_PCB_TOP_Z + 1.3
    base -= box(ux - USB_W / 2, OUT_D - WALL - 1, uz - USB_H / 2,
                ux + USB_W / 2, OUT_D + 1, BASE_H + 1)   # open to the top; the lid closes it

    # Cable slot in the front wall, in line with the terminal
    cx, _ = sheet_to_case(CABLE_X, 0)
    z0 = BOARD_TOP_Z + CABLE_Z0
    slot = rounded_rect(CABLE_W, CABLE_H, 1.2).extrude(WALL + 2)
    slot = slot.rotate((90, 0, 0)).translate((cx - CABLE_W / 2, WALL + 1, z0))
    base -= slot

    if KEYHOLES:
        for kx in (OUT_W / 2 - 25, OUT_W / 2 + 25):
            ky = OUT_D / 2 + 6
            base -= cyl(kx, ky, -1, FLOOR + 2, 7.5)                      # screw head
            base -= box(kx - 1.9, ky - 10, -1, kx + 1.9, ky, FLOOR + 1)   # neck slides down
            base -= cyl(kx, ky - 10, -1, FLOOR + 2, 3.8)
    return base


# ---------------- lid ----------------

def tree_outline():
    """The app's tree: three tiers and a star, about 34 mm tall, in lid coordinates."""
    s = 0.13
    tiers = [((150, 140), (28, 288), (272, 288)),
             ((150, 72), (58, 204), (242, 204)),
             ((150, 22), (90, 124), (210, 124))]
    polys = [[(x * s, -y * s) for x, y in t] for t in tiers]
    polys.append([(x * s, -y * s) for x, y in ((133, 290), (167, 290), (167, 334), (133, 334))])
    star = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        r = 16 if i % 2 == 0 else 7
        star.append(((150 + r * math.cos(a)) * s, (-24 + r * math.sin(a)) * s))
    polys.append(star)
    cs = CrossSection()
    for p in polys:
        cs += CrossSection([p])
    return cs


def bootsel_xy():
    return sheet_to_case(PICO_X + BOOTSEL_FROM_CENTRE, PICO_TOP_Y + BOOTSEL_FROM_TOP)


def make_lid():
    # Printed upside down: top face on the bed, lip pointing up.
    lid = rounded_rect(OUT_W, OUT_D, BOARD_R + CLEAR + WALL).extrude(LID_T)
    lip_o = rounded_rect(IN_W - 2 * LID_FIT, IN_D - 2 * LID_FIT, BOARD_R + CLEAR - LID_FIT, WALL + LID_FIT, WALL + LID_FIT)
    lip_i = lip_o.offset(-LID_LIP_T, JoinType.Round, circular_segments=SEG)
    lid += (lip_o - lip_i).extrude(LID_LIP).translate((0, 0, LID_T))

    # Leave the lip clear of the USB opening and the BOOTSEL plunger's flange
    ux, _ = sheet_to_case(PICO_X, 0)
    # (the lid is modelled upside down, so the USB edge is at y=0 here)
    lid -= box(ux - USB_W / 2 - 1, 0, LID_T,
               ux + USB_W / 2 + 1, WALL + LID_FIT + LID_LIP_T + 1, LID_T + LID_LIP + 1)

    # Engraved tree on the top face, centred over the proto area. The lid prints
    # face down, so as printed the star points to the back; assembled, it points
    # to the cable edge, which is the top when the case hangs from its keyholes.
    tree = tree_outline()
    bx = tree.bounds()
    tw, th = bx[2] - bx[0], bx[3] - bx[1]
    cx = BOARD_X0 + 30 + (BOARD_W - 30) / 2
    cy = OUT_D / 2
    tree = tree.translate((cx - (bx[0] + tw / 2), cy - (bx[1] + th / 2)))
    lid -= tree.extrude(1.0).translate((0, 0, -0.01))

    # BOOTSEL plunger hole (lid is printed upside down, so mirror y)
    bx_, by_ = bootsel_xy()
    lid -= cyl(bx_, OUT_D - by_, -1, LID_T + 2, 5.0)
    return lid


def make_plunger():
    # Flange sits under the lid; shaft pokes 2.5 mm above it; foot rests on BOOTSEL.
    lid_under_z = BASE_H
    flange_t = 1.0
    foot_len = lid_under_z - flange_t - BOOTSEL_TOP_Z
    p = cyl(0, 0, 0, max(foot_len, 0.5), 5.5)                      # foot (wide to forgive position error)
    p += cyl(0, 0, foot_len, flange_t, 8.0)                        # flange, can't pass up through the lid
    p += cyl(0, 0, foot_len + flange_t, LID_T + 2.5, 4.4)          # shaft through the 5 mm hole
    return p


def save(m, name):
    mesh = m.to_mesh()
    tm = trimesh.Trimesh(vertices=np.array(mesh.vert_properties)[:, :3], faces=np.array(mesh.tri_verts))
    tm.export(name)
    b = tm.bounds
    print("%-18s %5.1f x %5.1f x %5.1f mm  watertight=%s" % (name, *(b[1] - b[0]), tm.is_watertight))


if __name__ == "__main__":
    save(make_base(), "case-base.stl")
    save(make_lid(), "case-lid.stl")
    save(make_plunger(), "case-plunger.stl")
