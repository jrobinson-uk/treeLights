"""Draw the step-by-step build images for the tree lights board (ProtoMate for Pico).

    python3 docs/make_build_guide.py      -> docs/build/step-*.svg

Geometry is in mm, from case/protomate-dimensions.svg. The board is drawn with the
USB end at the top. "Top" views look at the component side; "underside" views are
the board turned over left-to-right, so everything is mirrored, as on the real board.
"""

import os

# ---------------- board geometry (mm) ----------------
BW, BH = 84.38, 56.59
P = 2.54
COL1_X, ROW0_Y = 28.63, 6.68              # column 1, top edge pad row
RIGHT_RAIL_X = COL1_X + 20.8 * P
HOLES = [(3.19, 3.22), (81.19, 3.22), (3.19, 53.37), (81.19, 53.37)]
PICO_X0, PICO_Y0, PICO_W, PICO_H = 5.99, 3.96, 21.0, 51.0
SOCKET_X = (16.49 - 8.89, 16.49 + 8.89)
SOCKET_Y0 = PICO_Y0 + 1.61

TOP_LABELS = ["VB", "VS", "G", "3E", "3V", "VR", "28", "AG", "27", "26",
              "RU", "22", "G", "21", "20", "19", "18", "G", "17", "16"]
BOT_LABELS = ["0", "1", "G", "2", "3", "4", "5", "G", "6", "7",
              "8", "9", "G", "10", "11", "12", "13", "G", "14", "15"]
BLOCKS = [(1, 3), (6, 8), (9, 11), (14, 16)]   # rows of the 3-hole column strips
RAILS = [4, 5, 12, 13]                          # rows of the horizontal rails (two halves each)


def X(c):
    return COL1_X + (c - 1) * P


def Y(r):
    return ROW0_Y + r * P


# ---------------- the build ----------------
RED, GREY, GREEN, AMBER = "#d62828", "#3a3a3a", "#1f9d55", "#f4a300"
NETS = {"5V": RED, "GND": GREY, "DATA": GREEN}

# Terminal: 3 contacts in columns 6-8, back pins in row 14, front pins in row 16,
# wire openings facing the bottom edge (the case's cable slot).
T_COLS, T_BACK, T_FRONT = (6, 7, 8), 14, 16
T_CONTACTS = {6: "DATA", 7: "5V", 8: "GND"}


def terminal_body():
    x0 = X(T_COLS[0]) - 0.4 * P
    x1 = X(T_COLS[-1]) + 1.6 * P
    y0 = Y(T_BACK) - 1.5 * P
    y1 = Y(T_FRONT) + 2.7 * P
    return x0, y0, x1, y1


# Underside bridges: (step, (col,row), (col,row), net, label)
# (badge position, in columns/rows)
BRIDGES = [
    (3, (1, 17), (1, 16), "DATA", "B1", (0.5, 16.5)),   # GP0 pad -> resistor's column 1 strip
    (3, (3, 17), (3, 16), "GND", "B2", (3.5, 16.5)),    # G pad -> column 3 strip (capacitor's - leg)
    (5, (5, 16), (6, 16), "DATA", "B3", (5.5, 15.5)),   # resistor's column 5 -> terminal DATA
    (5, (7, 14), (7, 13), "5V", "B4", (7.5, 13.5)),     # terminal +5V -> 5V rail
    (5, (8, 16), (8, 17), "GND", "B5", (8.5, 16.5)),    # terminal GND -> G pad
]

# ---------------- SVG helpers ----------------
S = 12.0           # px per mm
M = 34             # margin px


class Canvas:
    def __init__(self, underside):
        self.u = underside
        self.parts = []

    def px(self, x, y):
        if self.u:
            x = BW - x
        return M + x * S, M + y * S

    def add(self, s):
        self.parts.append(s)

    def circle(self, x, y, r, **a):
        cx, cy = self.px(x, y)
        self.add('<circle cx="%.1f" cy="%.1f" r="%.1f" %s/>' % (cx, cy, r * S, attrs(a)))

    def line(self, x1, y1, x2, y2, **a):
        a1, b1 = self.px(x1, y1)
        a2, b2 = self.px(x2, y2)
        self.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" %s/>' % (a1, b1, a2, b2, attrs(a)))

    def rect(self, x0, y0, x1, y1, **a):
        a0, b0 = self.px(x0, y0)
        a1, b1 = self.px(x1, y1)
        self.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" %s/>'
                 % (min(a0, a1), min(b0, b1), abs(a1 - a0), abs(b1 - b0), attrs(a)))

    def text(self, x, y, s, size=11, rotate=False, **a):
        cx, cy = self.px(x, y)
        tr = ' transform="rotate(-90 %.1f %.1f)"' % (cx, cy) if rotate else ""
        self.add('<text x="%.1f" y="%.1f" font-size="%d" text-anchor="middle" dominant-baseline="central"%s %s>%s</text>'
                 % (cx, cy, size, tr, attrs(a), s))

    def svg(self, title):
        w, h = BW * S + 2 * M, BH * S + 2 * M + 22
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.0f %.0f" font-family="Helvetica,Arial,sans-serif" role="img">'
                '<title>%s</title>%s</svg>' % (w, h, title, "".join(self.parts)))


def attrs(a):
    return " ".join('%s="%s"' % (k.replace("_", "-"), v) for k, v in a.items())


# ---------------- drawing ----------------
def board(c):
    u = c.u
    path_pts = [(3.0, 0), (9.7, 0), (12.0, 2.25), (21.3, 2.25), (23.6, 0), (BW, 0), (BW, BH), (0, BH), (0, 0)]
    d = "M%.1f,%.1f " % c.px(*path_pts[0]) + " ".join("L%.1f,%.1f" % c.px(*p) for p in path_pts[1:]) + " Z"
    c.add('<path d="%s" fill="%s" stroke="#111" stroke-width="2" stroke-linejoin="round"/>' % (d, "#1d1d1f" if u else "#202124"))
    for hx, hy in HOLES:
        c.circle(hx, hy, 2.4, fill="none", stroke="#c9a227", stroke_width=5)
        c.circle(hx, hy, 1.25, fill="#f6f5f1")
    # Pico sockets (already soldered)
    c.rect(PICO_X0 + 0.6, PICO_Y0 + 0.4, PICO_X0 + PICO_W - 0.6, PICO_Y0 + PICO_H - 0.4,
           fill="none", stroke="#555", stroke_width=1, stroke_dasharray="4 3")
    for sx in SOCKET_X:
        for i in range(20):
            if u:
                c.circle(sx, SOCKET_Y0 + i * P, 0.85, fill="#b8bcc2", stroke="#7d8288", stroke_width=1)
            else:
                c.rect(sx - 1.27, SOCKET_Y0 + i * P - 1.27, sx + 1.27, SOCKET_Y0 + i * P + 1.27, fill="#2b2b2b", stroke="#444", stroke_width=0.6)
                c.circle(sx, SOCKET_Y0 + i * P, 0.45, fill="#111")
    c.text(16.49, 28, "Pico sockets", 13, fill="#9aa0a6")
    c.text(16.49, 30.6, "(already soldered)", 11, fill="#9aa0a6")
    c.text(16.49, PICO_Y0 + 1.6, "USB end", 11, fill="#9aa0a6")
    pad = "#d4af37"
    # traces (top side only)
    if not u:
        tr = dict(stroke="#8a7a3a", stroke_width=5, stroke_linecap="round")
        for r0, r1 in BLOCKS:
            for col in range(1, 21):
                c.line(X(col), Y(r0), X(col), Y(r1), **tr)
        for r in RAILS:
            c.line(X(1), Y(r), X(10), Y(r), **tr)
            c.line(X(11), Y(r), X(20), Y(r), **tr)
        for r in RAILS:   # the rails are split in the middle
            c.line(X(10.5), Y(r) - 0.9, X(10.5), Y(r) + 0.9, stroke="#e8e6df", stroke_width=1.5)
        c.line(RIGHT_RAIL_X, Y(1), RIGHT_RAIL_X, Y(8), **tr)
        c.line(RIGHT_RAIL_X, Y(9), RIGHT_RAIL_X, Y(16), **tr)
    # pads
    rows = [0, 17] + [r for a, b in BLOCKS for r in range(a, b + 1)] + RAILS
    for col in range(1, 21):
        for r in rows:
            c.circle(X(col), Y(r), 0.72, fill="#1d1d1f", stroke=pad, stroke_width=4)
    for r in range(1, 17):
        if r in RAILS or any(a <= r <= b for a, b in BLOCKS):
            c.circle(RIGHT_RAIL_X, Y(r), 0.72, fill="#1d1d1f", stroke=pad, stroke_width=4)
    # edge labels
    for col in range(1, 21):
        for r, labels, dy in ((0, TOP_LABELS, -1.75), (17, BOT_LABELS, 1.75)):
            lab = labels[col - 1]
            hot = lab in ("VB", "G", "0")
            c.rect(X(col) - 1.0, Y(r) + dy - 1.05, X(col) + 1.0, Y(r) + dy + 1.05,
                   fill="#e8e6df" if hot else "#55554f", rx=2)
            c.text(X(col), Y(r) + dy, lab, 9 if len(lab) < 2 else 8, fill="#111" if hot else "#f0efe9", font_weight="bold")
    # column numbers below the board, to count by
    for col in range(1, 21):
        c.text(X(col), BH + 1.7, str(col), 11, fill="#6b6a65")
    c.text(X(1) - 3.6, BH + 1.7, "col", 11, fill="#6b6a65")
    c.text(BW / 2, -1.9, "UNDERSIDE (board turned over left to right)" if u else "TOP (component side)", 13,
           fill="#6b6a65", font_weight="bold")


def halo(c, kind, *args):
    """Amber highlight behind a new item."""
    a = dict(fill="none", stroke=AMBER, stroke_opacity="0.55", stroke_linecap="round", stroke_linejoin="round")
    if kind == "line":
        c.line(*args, stroke_width=22, **a)
    elif kind == "dot":
        c.circle(*args, 1.9, fill=AMBER, fill_opacity="0.5")
    elif kind == "rect":
        x0, y0, x1, y1 = args
        c.rect(x0 - 1.0, y0 - 1.0, x1 + 1.0, y1 + 1.0, fill=AMBER, fill_opacity="0.35", rx=6)


def badge(c, x, y, n):
    cx, cy = c.px(x, y)
    c.add('<circle cx="%.1f" cy="%.1f" r="11" fill="%s" stroke="#111" stroke-width="1.5"/>'
          '<text x="%.1f" y="%.1f" font-size="12" font-weight="bold" text-anchor="middle" dominant-baseline="central" fill="#111">%s</text>'
          % (cx, cy, AMBER, cx, cy, n))


# ---- components (top side) ----
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
        badge(c, X(1) - 3.2, Y(6.5), "W")


def resistor(c, new):
    y = Y(16)
    if new:
        halo(c, "line", X(1), y, X(5), y)
    c.line(X(1), y, X(5), y, stroke="#b9bcc0", stroke_width=3)
    c.rect(X(2) - 0.6, y - 1.05, X(4) + 0.6, y + 1.05, fill="#d9b77a", stroke="#7a5a2a", stroke_width=1, rx=6)
    for i, colr in enumerate(("#e07b00", "#e07b00", "#7a3e12", "#c9a227")):
        xx = X(2) + 0.2 + i * 1.25 + (0.6 if i == 3 else 0)
        c.rect(xx, y - 1.05, xx + 0.45, y + 1.05, fill=colr)
    for col in (1, 5):
        c.circle(X(col), y, 0.5, fill="#c0c4c8", stroke="#555", stroke_width=1)
    if new:
        badge(c, X(3), y - 2.6, "R")


def terminal(c, new, show_pins):
    x0, y0, x1, y1 = terminal_body()
    if new:
        halo(c, "rect", x0, y0, x1, y1)
    c.rect(x0, y0, x1, y1, fill="#43b649", fill_opacity="0.82" if show_pins else "1", stroke="#1e6b22", stroke_width=1.5, rx=3)
    for col in T_COLS:      # orange levers at the front
        c.rect(X(col) - 0.75, y1 - 4.2, X(col) + 0.75, y1 - 0.4, fill="#ff8c1a", stroke="#a34f00", stroke_width=1, rx=2)
    if show_pins:
        for col in T_COLS:
            for r in (T_BACK, T_FRONT):
                fill = NETS[T_CONTACTS[col]] if show_pins == "nets" else "#ffd400"
                c.circle(X(col), Y(r), 0.75 if show_pins == "nets" else 0.55, fill=fill, stroke="#fff" if show_pins == "nets" else "#111", stroke_width=1.2)
    for col in T_COLS:
        lab = {"DATA": "D", "5V": "+", "GND": "G"}[T_CONTACTS[col]]
        c.text(X(col), y1 - 5.6, lab, 12, fill="#0e3d11", font_weight="bold")
    if new:
        badge(c, x1 + 2.2, (y0 + y1) / 2, "T")


def capacitor(c, new):
    # + leg in the 5V rail at column 4, - leg in column 3 (diagonal: about 3.6 mm apart)
    cx, cy, r = (X(3) + X(4)) / 2, (Y(13) + Y(14)) / 2, 4.0
    if new:
        c.circle(cx, cy, r + 1.1, fill=AMBER, fill_opacity="0.45")
    c.circle(cx, cy, r, fill="#2e2a6b", stroke="#15123d", stroke_width=1.5)
    # stripe on the - side (towards the bottom edge)
    x_l, y_l = c.px(cx - r * 0.8, cy + r * 0.6)
    x_r, y_r = c.px(cx + r * 0.8, cy + r * 0.6)
    c.add('<path d="M%.1f,%.1f A%.1f,%.1f 0 0 1 %.1f,%.1f Z" fill="#c9c9d6"/>'
          % (x_r, y_r, r * S, r * S, x_l, y_l) if c.u else
          '<path d="M%.1f,%.1f A%.1f,%.1f 0 0 0 %.1f,%.1f Z" fill="#c9c9d6"/>' % (x_l, y_l, r * S, r * S, x_r, y_r))
    c.text(cx, cy - 1.4, "+", 15, fill="#fff", font_weight="bold")
    c.text(cx, cy + 3.0, "−", 15, fill="#2e2a6b", font_weight="bold")
    if new:
        badge(c, cx + r + 2.0, cy - r, "C")


# ---- underside items ----
def joint(c, col, r, new):
    if new:
        halo(c, "dot", X(col), Y(r))
    c.circle(X(col), Y(r), 0.95, fill="#c8ccd0", stroke="#6d7277", stroke_width=1.2)


def bridge(c, a, b, net, label, new, where):
    (c1, r1), (c2, r2) = a, b
    if new:
        halo(c, "line", X(c1), Y(r1), X(c2), Y(r2))
    c.line(X(c1), Y(r1), X(c2), Y(r2), stroke="#6d7277", stroke_width=11, stroke_linecap="round")
    c.line(X(c1), Y(r1), X(c2), Y(r2), stroke="#d9dde1", stroke_width=6, stroke_linecap="round")
    for col, r in (a, b):
        c.circle(X(col), Y(r), 0.8, fill="#c8ccd0", stroke="#6d7277", stroke_width=1.2)
    if new:
        badge(c, X(where[0]), Y(where[1]), label)
    else:
        cx, cy = c.px(X(where[0]), Y(where[1]))
        c.add('<circle cx="%.1f" cy="%.1f" r="9" fill="#f0efe9" stroke="#111" stroke-width="1"/>'
              '<text x="%.1f" y="%.1f" font-size="10" font-weight="bold" text-anchor="middle" dominant-baseline="central" fill="#111">%s</text>'
              % (cx, cy, cx, cy, label))


def nets_overlay(c):
    """Colour every hole by the net it's on (for the checks step)."""
    groups = {
        "5V": [(col, 13) for col in range(1, 11)] + [(1, 0), (7, 14), (7, 15), (7, 16)],
        "GND": [(3, 14), (3, 15), (3, 16), (3, 17), (8, 14), (8, 15), (8, 16), (8, 17)],
        "DATA": [(1, 17), (1, 14), (1, 15), (1, 16), (5, 14), (5, 15), (5, 16), (6, 14), (6, 15), (6, 16)],
    }
    for net, holes in groups.items():
        for col, r in holes:
            c.circle(X(col), Y(r), 1.15, fill=NETS[net], fill_opacity="0.85", stroke="#fff", stroke_width=1)


# ---------------- steps ----------------
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
            terminal(c, step == 4, show_pins="nets" if nets else (step == 4))
        if final:
            x0, y0, x1, y1 = terminal_body()
            for col, colr in zip(T_COLS, (GREEN, RED, "#f0efe9")):
                c.line(X(col), y1 - 0.5, X(col), BH + 6, stroke=colr, stroke_width=7, stroke_linecap="round")
            c.rect(PICO_X0, PICO_Y0, PICO_X0 + PICO_W, PICO_Y0 + PICO_H, fill="#1f7a3a", stroke="#0b3d1a", stroke_width=2, rx=4)
            c.rect(12.5, 2.4, 20.5, 8.0, fill="#c7ccd1", stroke="#555", stroke_width=1)
            c.text(16.49, 28, "Pico W", 16, fill="#fff", font_weight="bold")
    else:
        joints_new = []
        if step >= 3:
            for col, r in ((1, 0), (1, 13), (1, 16), (5, 16)):     # VB wire + resistor
                joint(c, col, r, step == 3)
        if step >= 5:
            for col in T_COLS:
                for r in (T_BACK, T_FRONT):
                    joint(c, col, r, step == 5)
        if step >= 6:
            for col, r in ((4, 13), (3, 14)):
                joint(c, col, r, step == 6)
        for st, a, b, net, lab, where in BRIDGES:
            if step >= st:
                bridge(c, a, b, net, lab, step == st, where)
    return c.svg(title)


STEPS = [
    ("step-0-start", 0, False, "Starting point"),
    ("step-1-vb-wire", 1, False, "VB wire to the 5V rail"),
    ("step-2-resistor", 2, False, "330 ohm resistor"),
    ("step-3-underside", 3, True, "Underside: solder, links B1 and B2"),
    ("step-4-terminal", 4, False, "Terminal block"),
    ("step-5-underside", 5, True, "Underside: terminal pins, links B3 to B5"),
    ("step-6-capacitor", 6, False, "1000 uF capacitor"),
    ("step-7-check", 6, False, "What's connected"),
    ("step-8-done", 6, False, "Finished"),
]

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
    os.makedirs(out, exist_ok=True)
    for name, step, under, title in STEPS:
        svg = render(step, under, title, nets=name.endswith("check"), final=name.endswith("done"))
        with open(os.path.join(out, name + ".svg"), "w") as f:
            f.write(svg)
        print(name)
