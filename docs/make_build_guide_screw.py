"""Build images for the screw-terminal version of the tree lights board.

    python3 docs/make_build_guide_screw.py      -> docs/build-screw/step-*.svg

Same board and drawing helpers as make_build_guide.py. The 3-way screw terminal
(5.08 mm pitch, 3 legs in one row) sits set back from the cable slot: legs in the
middle row of the block just above the rails, columns 5, 7 and 9, openings facing
the bottom edge, so the wires have room to spread out before they go in.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_build_guide import (S, AMBER, BH, GREEN, NETS, P, PICO_H, PICO_W, PICO_X0, PICO_Y0, RED,
                              X, Y, Canvas, badge, board, bridge, halo, joint, resistor)

WHITE = "#f0efe9"
T_ROW = 10
T_COLS = (5, 7, 9)
T_CONTACTS = {5: "DATA", 7: "5V", 9: "GND"}
T_DEPTH = 8.0          # mm, front to back (measure yours)


def body():
    return X(T_COLS[0]) - P, Y(T_ROW) - T_DEPTH / 2, X(T_COLS[-1]) + P, Y(T_ROW) + T_DEPTH / 2


def vb_wire(c, new):
    pts = [(X(1), Y(0)), (X(1) - 1.25, Y(0) + 1.0), (X(1) - 1.25, Y(13) - 1.0), (X(1), Y(13))]
    if new:
        for a, b in zip(pts, pts[1:]):
            halo(c, "line", *a, *b)
    for a, b in zip(pts, pts[1:]):
        c.line(*a, *b, stroke=RED, stroke_width=7, stroke_linecap="round")
    for p in (pts[0], pts[-1]):
        c.circle(*p, 0.55, fill=RED, stroke="#fff", stroke_width=1.5)
    if new:
        badge(c, X(1) - 3.2, Y(6.5), "W1")


def screw_terminal(c, new, pins):
    x0, y0, x1, y1 = body()
    if new:
        halo(c, "rect", x0, y0, x1, y1)
    c.rect(x0, y0, x1, y1, fill="#2f6fd6", fill_opacity="0.8" if pins else "1", stroke="#123a7a", stroke_width=1.5, rx=3)
    for col in T_COLS:
        # screw head (top) and wire opening (front face)
        c.circle(X(col), y0 + 2.4, 1.6, fill="#9fb8e0", stroke="#123a7a", stroke_width=1.2)
        c.line(X(col) - 1.0, y0 + 2.4, X(col) + 1.0, y0 + 2.4, stroke="#123a7a", stroke_width=2)
        c.rect(X(col) - 1.1, y1 - 1.4, X(col) + 1.1, y1 - 0.2, fill="#0d1f40", rx=2)
        lab = {"DATA": "D", "5V": "+", "GND": "G"}[T_CONTACTS[col]]
        c.text(X(col), y1 - 3.0, lab, 12, fill="#fff", font_weight="bold")
    if pins:
        for col in T_COLS:
            fill = NETS[T_CONTACTS[col]] if pins == "nets" else "#ffd400"
            c.circle(X(col), Y(T_ROW), 0.75 if pins == "nets" else 0.55, fill=fill,
                     stroke="#fff" if pins == "nets" else "#111", stroke_width=1.2)
    if new:
        badge(c, x1 + 2.2, (y0 + y1) / 2, "T")


def capacitor(c, new):
    """+ leg in the 5V rail at column 2, - leg in column 3 of the bottom block (diagonal, about 3.6 mm).
    Further left than in the lever-terminal build, to keep it clear of the data wire."""
    cx, cy, r = (X(2) + X(3)) / 2, (Y(13) + Y(14)) / 2, 4.0
    if new:
        c.circle(cx, cy, r + 1.1, fill=AMBER, fill_opacity="0.45")
    c.circle(cx, cy, r, fill="#2e2a6b", stroke="#15123d", stroke_width=1.5)
    xl, yl = c.px(cx - r * 0.8, cy + r * 0.6)
    xr, yr = c.px(cx + r * 0.8, cy + r * 0.6)
    c.add('<path d="M%.1f,%.1f A%.1f,%.1f 0 0 0 %.1f,%.1f Z" fill="#c9c9d6"/>' % (xl, yl, r * S, r * S, xr, yr))
    c.text(cx, cy - 1.4, "+", 15, fill="#fff", font_weight="bold")
    c.text(cx, cy + 3.0, "−", 15, fill="#2e2a6b", font_weight="bold")
    if new:
        badge(c, cx + r + 2.0, cy - r, "C")


def under_wire(c, pts, colour, label, new, where):
    """Insulated wire laid flat on the underside, soldered only at its two ends."""
    pts = [(X(a), Y(b)) for a, b in pts]
    if new:
        for a, b in zip(pts, pts[1:]):
            halo(c, "line", *a, *b)
    for a, b in zip(pts, pts[1:]):
        c.line(*a, *b, stroke="#111", stroke_width=9, stroke_linecap="round")
        c.line(*a, *b, stroke=colour, stroke_width=6, stroke_linecap="round")
    for p in (pts[0], pts[-1]):
        c.circle(*p, 0.8, fill="#c8ccd0", stroke="#6d7277", stroke_width=1.2)
    if new:
        badge(c, X(where[0]), Y(where[1]), label)


BRIDGES = [
    (3, (1, 17), (1, 16), "DATA", "B1", (0.5, 16.5)),
    (3, (3, 17), (3, 16), "GND", "B2", (3.5, 16.5)),
    (5, (7, 11), (7, 13), "5V", "B3", (7.6, 12.0)),
]
WIRES = [  # step, points (col,row), colour, label, badge
    (5, [(5, 14), (5, 11)], GREEN, "W2", (4.3, 12.5)),
    (5, [(13, 17), (12.5, 16.5), (12.5, 11.5), (9.5, 11.5), (9, 11)], WHITE, "W3", (13.1, 14.0)),
]


def nets_overlay(c):
    groups = {
        "5V": [(col, r) for col in range(1, 11) for r in (12, 13)] + [(1, 0), (7, 9), (7, 10), (7, 11)],
        "GND": [(3, 14), (3, 15), (3, 16), (3, 17), (13, 17), (9, 9), (9, 10), (9, 11)],
        "DATA": [(1, 17), (1, 14), (1, 15), (1, 16), (5, 14), (5, 15), (5, 16), (5, 9), (5, 10), (5, 11)],
    }
    for net, holes in groups.items():
        for col, r in holes:
            c.circle(X(col), Y(r), 1.15, fill=NETS[net], fill_opacity="0.85", stroke="#fff", stroke_width=1)


def render(step, underside, title, nets=False, final=False):
    c = Canvas(underside)
    board(c)
    if not underside:
        if nets:
            nets_overlay(c)
        if step >= 1:
            vb_wire(c, step == 1)
        if step >= 2:
            resistor(c, step == 2)
        if step >= 6:
            capacitor(c, step == 6 and not nets and not final)
        if step >= 4:
            screw_terminal(c, step == 4, pins="nets" if nets else (step == 4))
        if final:
            x0, y0, x1, y1 = body()
            for col, colr in zip(T_COLS, (GREEN, RED, WHITE)):
                end = X(7) + (col - 7) * 0.45
                d = "M%.1f,%.1f " % c.px(X(col), y1 - 0.6)
                d += "C%.1f,%.1f %.1f,%.1f %.1f,%.1f" % (*c.px(X(col), y1 + 3), *c.px(end, BH - 9), *c.px(end, BH + 6))
                c.add('<path d="%s" fill="none" stroke="#111" stroke-width="10" stroke-linecap="round"/>' % d)
                c.add('<path d="%s" fill="none" stroke="%s" stroke-width="7" stroke-linecap="round"/>' % (d, colr))
            c.rect(PICO_X0, PICO_Y0, PICO_X0 + PICO_W, PICO_Y0 + PICO_H, fill="#1f7a3a", stroke="#0b3d1a", stroke_width=2, rx=4)
            c.rect(12.5, 2.4, 20.5, 8.0, fill="#c7ccd1", stroke="#555", stroke_width=1)
            c.text(16.49, 28, "Pico W", 16, fill="#fff", font_weight="bold")
            c.text(X(7) + 9, BH + 4.6, "to the cable slot", 11, fill="#6b6a65")
    else:
        if step >= 3:
            for col, r in ((1, 0), (1, 13), (1, 16), (5, 16)):
                joint(c, col, r, step == 3)
        if step >= 5:
            for col in T_COLS:
                joint(c, col, T_ROW, step == 5)
        if step >= 6:
            for col, r in ((2, 13), (3, 14)):
                joint(c, col, r, step == 6)
        for st, a, b, net, lab, where in BRIDGES:
            if step >= st:
                bridge(c, a, b, net, lab, step == st, where)
        for st, pts, colr, lab, where in WIRES:
            if step >= st:
                under_wire(c, pts, colr, lab, step == st, where)
    return c.svg(title)


STEPS = [
    ("step-0-start", 0, False, "Starting point"),
    ("step-1-vb-wire", 1, False, "VB wire to the 5V rail"),
    ("step-2-resistor", 2, False, "330 ohm resistor"),
    ("step-3-underside", 3, True, "Underside: solder, links B1 and B2"),
    ("step-4-terminal", 4, False, "Screw terminal"),
    ("step-5-underside", 5, True, "Underside: terminal legs, link B3, wires W2 and W3"),
    ("step-6-capacitor", 6, False, "1000 uF capacitor"),
    ("step-7-check", 6, False, "What's connected"),
    ("step-8-done", 6, False, "Finished"),
]

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build-screw")
    os.makedirs(out, exist_ok=True)
    for name, step, under, title in STEPS:
        with open(os.path.join(out, name + ".svg"), "w") as f:
            f.write(render(step, under, title, nets=name.endswith("check"), final=name.endswith("done")))
        print(name)
