"""Breadboard mock-up of the tree lights circuit, for testing the logic without the ProtoMate.

    python3 docs/make_breadboard.py   -> docs/breadboard/breadboard.svg, schematic.svg

Half-size breadboard: 30 columns, rows a-e (bottom half) and f-j (top half), no power rails.
Pico W straddles the gap with its pins in rows c and h, columns 1-20, USB end on the left,
which leaves holes a-b and i-j free beside every Pico pin.
"""

import os

P = 2.54
S = 13.0
NCOL = 30
ROWS = "jihgf" + "edcba"
ROW_IDX = {r: (i if i < 5 else i + 2) for i, r in enumerate(ROWS)}   # gap of 3 pitches between f and e
X0, Y0 = 12.0, 12.0
BW, BH = 2 * X0 + (NCOL - 1) * P, 2 * Y0 + 11 * P
M = 30

RED, BLACK, GREEN, AMBER = "#d62828", "#222", "#1f9d55", "#f4a300"


def X(c):
    return X0 + (c - 1) * P


def Y(r):
    return Y0 + ROW_IDX[r] * P


def pico_pin(col, row):
    """Pico pin number at a breadboard hole (USB end left, pins in rows c and h)."""
    return col if row == "c" else 41 - col


PIN_NAMES = {1: "GP0", 2: "GP1", 3: "GND", 4: "GP2", 8: "GND", 13: "GND", 18: "GND",
             40: "VBUS", 39: "VSYS", 38: "GND", 37: "3V3_EN", 36: "3V3", 33: "GND", 28: "GND", 23: "GND"}


class C:
    def __init__(self):
        self.p = []

    def px(self, x, y):
        return M + x * S, M + y * S

    def add(self, s):
        self.p.append(s)

    def circle(self, x, y, r, **a):
        cx, cy = self.px(x, y)
        self.add('<circle cx="%.1f" cy="%.1f" r="%.1f" %s/>' % (cx, cy, r * S, at(a)))

    def rect(self, x0, y0, x1, y1, **a):
        a0, b0 = self.px(x0, y0)
        a1, b1 = self.px(x1, y1)
        self.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" %s/>' % (a0, b0, a1 - a0, b1 - b0, at(a)))

    def poly(self, pts, **a):
        d = " ".join("%.1f,%.1f" % self.px(*p) for p in pts)
        self.add('<polyline points="%s" fill="none" %s/>' % (d, at(a)))

    def text(self, x, y, s, size=11, anchor="middle", **a):
        cx, cy = self.px(x, y)
        self.add('<text x="%.1f" y="%.1f" font-size="%d" text-anchor="%s" dominant-baseline="central" %s>%s</text>'
                 % (cx, cy, size, anchor, at(a), s))

    def svg(self, w, h, title):
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.0f %.0f" font-family="Helvetica,Arial,sans-serif" role="img">'
                '<title>%s</title>%s</svg>' % (w, h, title, "".join(self.p)))


def at(a):
    return " ".join('%s="%s"' % (k.replace("_", "-"), v) for k, v in a.items())


def badge(c, x, y, s):
    cx, cy = c.px(x, y)
    c.add('<circle cx="%.1f" cy="%.1f" r="12" fill="%s" stroke="#111" stroke-width="1.5"/>'
          '<text x="%.1f" y="%.1f" font-size="11" font-weight="bold" text-anchor="middle" dominant-baseline="central" fill="#111">%s</text>'
          % (cx, cy, AMBER, cx, cy, s))


def wire(c, pts, colour, label, where):
    pts = [(X(a), Y(b)) if isinstance(a, int) else (a, b) for a, b in pts]
    c.poly(pts, stroke="#111", stroke_width=9, stroke_linecap="round", stroke_linejoin="round")
    c.poly(pts, stroke=colour, stroke_width=6, stroke_linecap="round", stroke_linejoin="round")
    for p in (pts[0], pts[-1]):
        c.circle(*p, 0.6, fill="#ddd", stroke="#111", stroke_width=1.2)
    badge(c, *where, label)


# ---- the circuit ----
T_ROW, T_COLS = "a", (24, 26, 28)          # screw terminal: D, +, G; openings face the bottom edge
T_DEPTH = 8.0


def breadboard():
    c = C()
    c.rect(0, 0, BW, BH, fill="#f3f1ea", stroke="#c9c5b8", stroke_width=2, rx=8)
    gap_y = (Y("f") + Y("e")) / 2
    c.rect(0, gap_y - 1.2, BW, gap_y + 1.2, fill="#e2ded2")
    for col in range(1, NCOL + 1):
        c.text(X(col), Y0 - 8.4, str(col), 9, fill="#8a867a")
        c.text(X(col), BH - Y0 + 6.0, str(col), 9, fill="#8a867a")
        for r in ROWS:
            c.rect(X(col) - 0.55, Y(r) - 0.55, X(col) + 0.55, Y(r) + 0.55, fill="#4a4740", rx=1)
    for r in ROWS:
        c.text(X0 - 6.5, Y(r), r, 10, fill="#8a867a")
        c.text(BW - X0 + 6.5, Y(r), r, 10, fill="#8a867a")
    # strips: each column's a-e and f-j are joined (shown faintly)
    for col in (1, 3, 21, 24, 26, 28):
        for top, bot in (("e", "a"), ("j", "f")):
            c.rect(X(col) - 0.95, Y(top) - 0.95, X(col) + 0.95, Y(bot) + 0.95, fill="none",
                   stroke="#b8b2a0", stroke_width=1, stroke_dasharray="3 2", rx=4)

    # Pico W
    px0, px1 = X(1) - 1.37, X(20) + 1.37
    py0, py1 = Y("h") - 1.61, Y("c") + 1.61
    c.rect(px0 - 1.3, (py0 + py1) / 2 - 4.0, px0 + 4.4, (py0 + py1) / 2 + 4.0, fill="#c7ccd1", stroke="#555", stroke_width=1)
    c.rect(px0, py0, px1, py1, fill="#1f7a3a", fill_opacity="0.88", stroke="#0b3d1a", stroke_width=2, rx=3)
    c.text((px0 + px1) / 2 + 3, (py0 + py1) / 2, "Pico W", 16, fill="#fff", font_weight="bold")
    c.text(px0 + 1.6, (py0 + py1) / 2 + 5.6, "USB", 10, fill="#e8f5ec")
    for col in range(1, 21):
        for r in ("c", "h"):
            n = pico_pin(col, r)
            name = PIN_NAMES.get(n)
            key = name in ("GP0", "VBUS") or (name == "GND" and col == 3)
            c.circle(X(col), Y(r), 0.55, fill="#e9c46a" if key else "#d8d2b8", stroke="#111", stroke_width=1)
            if key:
                dy = -2.0 if r == "c" else 2.0
                c.text(X(col) + (0.9 if col == 1 else 0), Y(r) + dy, name, 9, fill="#fff", font_weight="bold")

    # J1 data: GP0 (col 1, b) -> col 21 a
    wire(c, [(1, "b"), (X(1), Y("a") + 1.3), (X(21), Y("a") + 1.3), (21, "a")], GREEN, "J1", (X(11), Y("a") + 1.3))
    # J2 +5V: VBUS (col 1, j) -> col 26 j;  J3 GND: GND (col 3, j) -> col 28 j
    wire(c, [(1, "j"), (X(1), Y("j") - 1.4), (X(26), Y("j") - 1.4), (26, "j")], RED, "J2", (X(12), Y("j") - 1.4))
    wire(c, [(3, "j"), (X(3), Y("j") - 3.6), (X(28), Y("j") - 3.6), (28, "j")], BLACK, "J3", (X(16), Y("j") - 3.6))
    # J4, J5: carry +5V and GND across the gap to the terminal's strips
    wire(c, [(26, "f"), (26, "c")], RED, "J4", (X(24.6), Y("e") - 1.3))
    wire(c, [(28, "f"), (28, "c")], BLACK, "J5", (X(29.5), Y("e") - 1.3))

    # R: col 21 d -> col 24 d
    y = Y("d")
    c.poly([(X(21), y), (X(24), y)], stroke="#9aa0a6", stroke_width=3)
    c.rect(X(21) + 1.4, y - 1.0, X(24) - 1.4, y + 1.0, fill="#d9b77a", stroke="#7a5a2a", stroke_width=1, rx=5)
    for i, colr in enumerate(("#e07b00", "#e07b00", "#7a3e12")):
        xx = X(21) + 1.9 + i * 0.9
        c.rect(xx, y - 1.0, xx + 0.4, y + 1.0, fill=colr)
    for col in (21, 24):
        c.circle(X(col), y, 0.5, fill="#c0c4c8", stroke="#555", stroke_width=1)
    badge(c, X(22.5), y - 2.6, "R")

    # T: screw terminal, legs in row a
    tx0, tx1 = X(T_COLS[0]) - P, X(T_COLS[-1]) + P
    ty0, ty1 = Y(T_ROW) - T_DEPTH / 2, Y(T_ROW) + T_DEPTH / 2
    c.rect(tx0, ty0, tx1, ty1, fill="#2f6fd6", fill_opacity="0.85", stroke="#123a7a", stroke_width=1.5, rx=3)
    for col, lab in zip(T_COLS, "D+G"):
        c.circle(X(col), ty0 + 2.2, 1.5, fill="#9fb8e0", stroke="#123a7a", stroke_width=1.2)
        c.circle(X(col), Y(T_ROW), 0.5, fill="#ffd400", stroke="#111", stroke_width=1)
        c.text(X(col) + 1.25, Y(T_ROW) + 1.4, lab, 12, fill="#fff", font_weight="bold")
    badge(c, tx1 + 2.4, Y(T_ROW) - 1.5, "T")

    # C: + col 26 h, - col 28 h (top half, on J2's and J3's strips)
    cx, cy, rr = X(27), Y("h"), 4.0
    c.circle(cx, cy, rr, fill="#2e2a6b", stroke="#15123d", stroke_width=1.5)
    c.rect(cx + rr * 0.45, cy - rr * 0.85, cx + rr * 0.85, cy + rr * 0.85, fill="#c9c9d6", rx=3)
    c.text(cx - 1.6, cy, "+", 15, fill="#fff", font_weight="bold")
    for col in (26, 28):
        c.circle(X(col), cy, 0.5, fill="#c0c4c8", stroke="#555", stroke_width=1)
    badge(c, cx + rr + 2.4, cy - rr + 0.5, "C")

    # lights' wires out of the terminal, off the bottom edge
    for col, colr in zip(T_COLS, (GREEN, RED, "#f0efe9")):
        c.poly([(X(col), ty1 - 0.4), (X(col), BH + 5)], stroke="#111", stroke_width=9, stroke_linecap="round")
        c.poly([(X(col), ty1 - 0.4), (X(col), BH + 5)], stroke=colr, stroke_width=6, stroke_linecap="round")
    c.text(X(26), BH + 7.2, "to the lights' input end", 11, fill="#6b6a65")
    return c.svg(BW * S + 2 * M, (BH + 9) * S + 2 * M, "Tree lights circuit on a breadboard")


def schematic():
    c = C()
    def ln(pts, colr="#333", w=3):
        c.poly(pts, stroke=colr, stroke_width=w, stroke_linecap="round", stroke_linejoin="round")
    yv, yg, yd = 9, 21, 31
    c.rect(2, 4, 20, 35, fill="#1f7a3a", stroke="#0b3d1a", stroke_width=2, rx=3)
    c.text(10, 15, "Pico W", 15, fill="#fff", font_weight="bold")
    c.rect(56, 4, 66, 35, fill="#2f6fd6", stroke="#123a7a", stroke_width=2, rx=3)
    c.text(61, 38.2, "terminal", 11, fill="#6b6a65")
    for y, a, b, colr, j in ((yv, "VBUS", "+", RED, "J2, J4"), (yg, "GND", "G", BLACK, "J3, J5"), (yd, "GP0", "D", GREEN, "J1")):
        c.text(19, y, a, 11, "end", fill="#fff", font_weight="bold")
        c.text(61, y, b, 14, fill="#fff", font_weight="bold")
        c.text(23, y - 1.6, j, 10, "start", fill=colr, font_weight="bold")
    ln([(20, yv), (56, yv)], RED)
    ln([(20, yg), (56, yg)], BLACK)
    ln([(20, yd), (31, yd)], GREEN)
    c.rect(31, yd - 1.4, 41, yd + 1.4, fill="#d9b77a", stroke="#7a5a2a", stroke_width=1.5, rx=4)
    c.text(36, yd - 3.2, "R 330 Ω", 11, fill="#333")
    ln([(41, yd), (56, yd)], GREEN)
    # capacitor between 5V and GND
    ln([(46, yv), (46, 14.2)], RED)
    ln([(43, 14.2), (49, 14.2)], "#333", 4)
    c.add('<path d="M%.1f,%.1f Q%.1f,%.1f %.1f,%.1f" fill="none" stroke="#333" stroke-width="4"/>'
          % (*c.px(43, 17.6), *c.px(46, 15.7), *c.px(49, 17.6)))
    ln([(46, 16.4), (46, yg)], BLACK)
    c.text(44.0, 12.6, "+", 12, fill="#333", font_weight="bold")
    c.text(50.0, 15.6, "C 1000 µF", 10, "start", fill="#333")
    return c.svg(68 * S + 2 * M, 40 * S + 2 * M, "Tree lights circuit schematic")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "breadboard")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "breadboard.svg"), "w").write(breadboard())
    open(os.path.join(out, "schematic.svg"), "w").write(schematic())
    print("wrote", out)
