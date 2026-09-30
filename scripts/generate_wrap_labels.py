#!/usr/bin/env python3
"""Ashvena wrap-around jar/tin labels - Direction D "Peacock Flash".

A bold flat-colour label with striped bands, a tattoo-flash style peacock
mascot perched on a flavour branch (chillies / curry leaves), the brand
name set vertically on both sides and a rotated information panel.

Artboard: 220 x 180 mm (4 px = 1 mm) = front 155 mm + info panel 65 mm.
Output: packaging/D-peacock-flash/ashvena-<flavour>-cashews_wrap-label.svg
"""
import math
import os
import random

from generate_packaging import FLAVORS, CHILLI, LEAF, esc, wrap

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packaging", "D-peacock-flash")

W, H = 880, 720
FW = 620                      # front width; info panel is FW..W

F_HEAD = "'DM Serif Display', 'Playfair Display', Georgia, serif"
F_BODY = "Inter, 'Helvetica Neue', Arial, sans-serif"

LINE = "#2a1410"              # tattoo outline
YEL = "#f6c343"
CREAM = "#f8dc93"
MAROON = "#3e0f0c"

LABELS = {
    "peri-peri": dict(bg="#a8281f", top=["PERI PERI", "CASHEWS"]),
    "kadi-patta": dict(bg="#5f7a2b", top=["KADI PATTA", "CASHEWS"]),
}


def t(x, y, s, size, fill, family=F_BODY, weight=400, anchor="start", ls=0, extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}"{extra}>'
            f'{esc(s)}</text>')


def g(gid, body, extra=""):
    return f'<g id="{gid}"{extra}>\n{body}\n</g>'


# ---------------------------------------------------------------------------
# Peacock mascot (local frame: origin on the branch, ~ -240..235 tall)
# ---------------------------------------------------------------------------

def bez(p0, p1, p2, p3, u):
    a = [(1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u ** 2, u ** 3]
    return (sum(c * p[0] for c, p in zip(a, (p0, p1, p2, p3))),
            sum(c * p[1] for c, p in zip(a, (p0, p1, p2, p3))))


TAIL = ((-10, -20), (-50, 70), (50, 140), (5, 228))


def tail_frame(u):
    p = bez(*TAIL, u)
    q = bez(*TAIL, min(u + .01, 1)) if u < 1 else p
    r = bez(*TAIL, max(u - .01, 0))
    dx, dy = q[0] - r[0], q[1] - r[1]
    n = math.hypot(dx, dy)
    return p, (dx / n, dy / n)


def tail_width(u):
    return 30 + 84 * math.sin(math.pi * u * .85)


def eye(x, y, ang, s):
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({ang:.1f}) scale({s:.2f})">'
            f'<path d="M 0,-17 C 11,-8 13,7 0,17 C -13,7 -11,-8 0,-17 Z" fill="#3e9e5e" '
            f'stroke="{LINE}" stroke-width="2.2" stroke-linejoin="round"/>'
            f'<ellipse cx="0" cy="3" rx="8.5" ry="10" fill="{YEL}" stroke="{LINE}" stroke-width="1.4"/>'
            f'<ellipse cx="0" cy="4" rx="6" ry="7.3" fill="#1fa09a"/>'
            f'<ellipse cx="0" cy="5" rx="3.4" ry="4.2" fill="#16235c"/>'
            f'</g>')


def tail():
    left, right = [], []
    for i in range(31):
        u = i / 30
        (px, py), (tx, ty) = tail_frame(u)
        nx, ny = -ty, tx
        w = tail_width(u) / 2
        left.append((px + nx * w, py + ny * w))
        right.append((px - nx * w, py - ny * w))
    (ex, ey), (tx, ty) = tail_frame(1)
    d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in left)
    # scalloped tip from left end to right end
    a, b = left[-1], right[-1]
    for k in range(3):
        s0 = (a[0] + (b[0] - a[0]) * k / 3, a[1] + (b[1] - a[1]) * k / 3)
        s1 = (a[0] + (b[0] - a[0]) * (k + 1) / 3, a[1] + (b[1] - a[1]) * (k + 1) / 3)
        c = ((s0[0] + s1[0]) / 2 + tx * 26, (s0[1] + s1[1]) / 2 + ty * 26)
        d += f" Q {c[0]:.1f},{c[1]:.1f} {s1[0]:.1f},{s1[1]:.1f}"
    d += " L " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in reversed(right)) + " Z"
    o = [f'<path d="{d}" fill="#1f4d3a" stroke="{LINE}" stroke-width="3" stroke-linejoin="round"/>']
    # rachis lines
    for off in (-.3, 0, .3):
        pts = []
        for i in range(26):
            u = i / 25
            (px, py), (tx2, ty2) = tail_frame(u)
            w = tail_width(u) * off
            pts.append(f"{px - ty2 * w:.1f},{py + tx2 * w:.1f}")
        o.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#5fb07a" stroke-width="1.2" opacity=".7"/>')
    # eye feathers, top rows first so lower rows overlap
    rows = [.2, .31, .42, .53, .64, .75, .86, .97]
    for r_i, u in enumerate(rows):
        (px, py), (tx, ty) = tail_frame(u)
        w = tail_width(u)
        n = max(1, round(w / 34))
        ang = math.degrees(math.atan2(ty, tx)) - 90
        for k in range(n):
            off = (k - (n - 1) / 2) * (w / n) * .92
            if r_i % 2 and n > 1:
                off += (w / n) * .2
            o.append(eye(px - ty * off, py + tx * off, ang, .8 + .35 * math.sin(math.pi * u * .85)))
    return g("Tail", "\n".join(o))


def flat_chilli(x, y, s, r):
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({r:.1f}) scale({s:.2f})">'
            f'<path d="M -8,0 C -18,-2 -24,-8 -28,-16" fill="none" stroke="{LINE}" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="M -8,0 C -18,-2 -24,-8 -28,-16" fill="none" stroke="#5e9a36" stroke-width="3" stroke-linecap="round"/>'
            f'<path d="{CHILLI}" fill="#e03a22" stroke="{LINE}" stroke-width="3.2" stroke-linejoin="round"/>'
            f'<path d="M 8,-3 C 30,-6 58,-4 82,1" fill="none" stroke="#ff9a7a" stroke-width="2.4" stroke-linecap="round"/>'
            f'<path d="M 2,-7 C -6,-8 -10,-3 -8,0 C -10,3 -6,8 2,7 Z" fill="#5e9a36" stroke="{LINE}" stroke-width="2.4"/>'
            f'</g>')


def flat_leaf(x, y, s, r):
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({r:.1f}) scale({s:.2f})">'
            f'<path d="{LEAF}" fill="#4e8a3a" stroke="{LINE}" stroke-width="2.4" stroke-linejoin="round"/>'
            f'<path d="M 3,0 C 16,-1 30,-1 40,0" fill="none" stroke="#a9d27a" stroke-width="1.4"/></g>')


def flat_sprig(x, y, ang, L, n, s):
    o = [f'<g transform="translate({x:.1f} {y:.1f}) rotate({ang:.1f})">',
         f'<path d="M 0,0 Q {L / 2:.1f},-14 {L:.1f},0" fill="none" stroke="{LINE}" stroke-width="5" stroke-linecap="round"/>',
         f'<path d="M 0,0 Q {L / 2:.1f},-14 {L:.1f},0" fill="none" stroke="#6b8a3a" stroke-width="2.4" stroke-linecap="round"/>']
    for i in range(n):
        u = (i + 1) / (n + 1)
        px, py = L * u, -28 * u * (1 - u)
        a = math.degrees(math.atan2(-28 * (1 - 2 * u), L))
        side = 1 if i % 2 else -1
        o.append(flat_leaf(px, py, s * (1.05 - .3 * u), a + side * 52))
    o.append(flat_leaf(L, 0, s * .75, math.degrees(math.atan2(28, L))))
    o.append("</g>")
    return "".join(o)


def branch(style):
    d = "M -128,22 C -60,4 40,20 128,4"
    o = [f'<path d="{d}" fill="none" stroke="{LINE}" stroke-width="17" stroke-linecap="round"/>',
         f'<path d="{d}" fill="none" stroke="#7a4524" stroke-width="11" stroke-linecap="round"/>',
         f'<path d="M -70,11 C -60,4 -40,6 -30,9" fill="none" stroke="#a8683a" stroke-width="2.5" stroke-linecap="round"/>',
         f'<path d="M 60,12 C 75,8 95,8 105,7" fill="none" stroke="#a8683a" stroke-width="2.5" stroke-linecap="round"/>']
    if style == "peri":
        for x, y, r in [(-104, 22, 78), (-78, 18, 96), (84, 16, 84), (110, 10, 100)]:
            o.append(flat_chilli(x, y, .62, r))
    else:
        o.append(flat_sprig(-112, 20, 110, 95, 7, .8))
        o.append(flat_sprig(-80, 16, 80, 70, 5, .7))
        o.append(flat_sprig(98, 10, 72, 95, 7, .8))
    return g("Branch", "\n".join(o))


def body():
    o = []
    # legs + toes
    for x0, x1 in [(-4, -8), (12, 14)]:
        for col, w in [(LINE, 8), ("#b08a60", 4.5)]:
            o.append(f'<path d="M {x0},-14 L {x1},10" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>')
        o.append(f'<path d="M {x1 - 9},14 Q {x1},4 {x1 + 9},14" fill="none" stroke="{LINE}" stroke-width="3.5" stroke-linecap="round"/>')
    o.append(f'<ellipse cx="4" cy="-58" rx="32" ry="52" transform="rotate(-18 4 -58)" fill="#1e56a0" '
             f'stroke="{LINE}" stroke-width="3"/>')
    # wing
    o.append(f'<path d="M 12,-92 C -22,-88 -44,-52 -40,-14 C -22,-24 6,-50 20,-72 Z" fill="#d9a45a" '
             f'stroke="{LINE}" stroke-width="2.8" stroke-linejoin="round"/>')
    for i in range(5):
        y = -80 + i * 13
        o.append(f'<path d="M {-6 - i * 6},{y} q 10,2 18,-6" fill="none" stroke="{LINE}" stroke-width="2"/>')
    o.append(f'<path d="M -40,-14 C -34,-2 -22,2 -12,-3 C -18,-14 -26,-18 -40,-14 Z" fill="#a8552a" '
             f'stroke="{LINE}" stroke-width="2.4" stroke-linejoin="round"/>')
    # neck
    o.append(f'<path d="M 0,-100 C -5,-135 20,-162 30,-180 L 56,-176 C 48,-150 30,-128 34,-92 Z" '
             f'fill="#1e6fb0" stroke="{LINE}" stroke-width="3" stroke-linejoin="round"/>')
    for x, y in [(18, -112), (26, -128), (14, -136), (32, -148), (24, -158), (38, -164), (22, -96)]:
        o.append(f'<path d="M {x - 4},{y} q 4,5 8,0" fill="none" stroke="#7cc0f0" stroke-width="1.6"/>')
    # head
    o.append(f'<circle cx="44" cy="-188" r="15" fill="#1e6fb0" stroke="{LINE}" stroke-width="3"/>')
    o.append(f'<path d="M 38,-194 Q 48,-199 56,-192" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>')
    o.append(f'<path d="M 40,-183 Q 48,-179 55,-184" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/>')
    o.append(f'<circle cx="49" cy="-189" r="2.8" fill="{LINE}"/><circle cx="50" cy="-190" r=".9" fill="#fff"/>')
    # crest
    for a, L in [(-128, 26), (-112, 31), (-96, 34), (-80, 31), (-64, 26)]:
        ex = 42 + L * math.cos(math.radians(a))
        ey = -202 + L * math.sin(math.radians(a))
        o.append(f'<line x1="42" y1="-202" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{LINE}" stroke-width="1.8"/>')
        o.append(f'<ellipse cx="{ex:.1f}" cy="{ey:.1f}" rx="3.2" ry="4.6" transform="rotate({a + 90} {ex:.1f} {ey:.1f})" '
                 f'fill="#1fa09a" stroke="{LINE}" stroke-width="1.5"/>')
    return g("Body", "\n".join(o))


def beak(style):
    o = [f'<path d="M 57,-193 L 77,-186 L 57,-180 Z" fill="#e2bd82" stroke="{LINE}" stroke-width="2.4" stroke-linejoin="round"/>']
    if style == "peri":
        o.append(flat_chilli(80, -183, .42, 62))
    else:
        o.append(flat_leaf(74, -184, .9, 48))
    return g("Beak", "\n".join(o))


def peacock(style, x, y, s):
    return g("Peacock_Mascot",
             tail() + "\n" + branch(style) + "\n" + body() + "\n" + beak(style),
             f' transform="translate({x} {y}) scale({s})"')


# ---------------------------------------------------------------------------
# label
# ---------------------------------------------------------------------------

def stripes(y, h):
    o = [f'<rect x="24" y="{y}" width="{FW - 48}" height="{h}" fill="{MAROON}"/>']
    x = 24
    while x < FW - 24 - 6:
        o.append(f'<rect x="{x}" y="{y}" width="12" height="{h}" fill="{YEL}"/>')
        x += 24
    return "".join(o)


def vertical_word(cx, cy, size):
    # rotate(90): reads top-to-bottom, letter tops face right
    return (f'<g transform="translate({cx - size * .35:.1f} {cy}) rotate(90)">'
            + t(0, 0, "ASHVENA", size, YEL, F_HEAD, 400, "middle", 6) + "</g>")


def barcode(x, y, w, h, seed):
    rng = random.Random(seed)
    o = []
    cx = x
    while cx < x + w:
        bw = rng.choice([1, 1.5, 2, 3])
        if rng.random() > .4:
            o.append(f'<rect x="{cx:.1f}" y="{y}" width="{bw}" height="{h}" fill="{CREAM}"/>')
        cx += bw + rng.choice([1, 1.5, 2])
    o.append(t(x, y + h + 11, "8 90XXXX XXXXX X", 8, CREAM, F_BODY, 500))
    return g("Barcode_PLACEHOLDER", "".join(o))


def para(x, y, s, n, lh=12.5, size=9.5, fill=CREAM, weight=400):
    lines = wrap(s, n)
    return "".join(t(x, y + i * lh, l, size, fill, F_BODY, weight) for i, l in enumerate(lines)), y + len(lines) * lh


def info_panel(f):
    o = []
    # in the rotated frame x runs bottom->top of the label, y runs left->right
    y0 = 12
    txt, y = para(0, y0, f["about"].replace("Our ", "Since 1953, Ashvena has roasted cashews the slow way. Our "), 44)
    o.append(txt)
    # icons
    iy = y + 14
    o.append(f'<rect x="0" y="{iy}" width="20" height="20" fill="none" stroke="{CREAM}" stroke-width="1.6"/>'
             f'<circle cx="10" cy="{iy + 10}" r="5.5" fill="{CREAM}"/>')
    o.append(f'<circle cx="42" cy="{iy + 10}" r="10" fill="none" stroke="{CREAM}" stroke-width="1.4"/>'
             + t(42, iy + 13, "FSSAI", 5.5, CREAM, F_BODY, 700, "middle"))
    o.append(f'<path d="M 64,{iy + 16} l 8,-14 l 8,14 Z" fill="none" stroke="{CREAM}" stroke-width="1.5" stroke-linejoin="round"/>'
             f'<path d="M 68,{iy + 13} l 4,-6 l 4,6" fill="none" stroke="{CREAM}" stroke-width="1.2"/>')
    o.append(t(88, iy + 13, "RECYCLABLE TIN & LABEL", 7, CREAM, F_BODY, 600, ls=.5))
    o.append(barcode(0, iy + 34, 130, 42, 17))
    o.append(t(150, iy + 50, "NET WT.", 8, YEL, F_BODY, 700, ls=1))
    o.append(t(150, iy + 72, "200 g", 20, YEL, F_HEAD))

    x = 262
    o.append(t(x, y0 + 2, "INGREDIENTS", 12, YEL, F_BODY, 700, ls=1.5))
    txt, y = para(x, y0 + 22, f["ingredients"], 38)
    o.append(txt)
    txt, y = para(x, y + 6, "Allergen information: contains cashew (tree nut). Made in a facility that also "
                           "handles peanuts, other tree nuts and sesame.", 38, weight=700)
    o.append(txt)

    x = 490
    o.append(t(x, y0 + 2, "STORAGE", 12, YEL, F_BODY, 700, ls=1.5))
    txt, y = para(x, y0 + 22, "Store in a cool, dry place away from direct sunlight and moisture. "
                              "Close the lid tightly after opening.", 34)
    o.append(txt)
    o.append(t(x, y + 14, "MANUFACTURER", 12, YEL, F_BODY, 700, ls=1.5))
    txt, y = para(x, y + 34, "ASHVENA FOODS PVT. LTD. [Address], [City] - [PIN], India. "
                             "FSSAI Lic. No. XXXXXXXXXXXXXX. MRP ₹ XXX (incl. of all taxes). "
                             "For questions, write to care@ashvena.in", 34)
    o.append(txt)
    return g("Info_Panel", "\n".join(o), f' transform="translate({FW + 24} {H - 30}) rotate(-90)"')


def label(key):
    f, L = FLAVORS[key], LABELS[key]
    cx = FW / 2
    o = [g("Background", f'<rect width="{W}" height="{H}" fill="{L["bg"]}"/>'),
         g("Stripes", stripes(20, 36) + stripes(H - 56, 36)),
         g("Product_Name",
           t(cx, 104, L["top"][0], 38, YEL, F_HEAD, 400, "middle", 1.5)
           + t(cx, 142, L["top"][1], 38, YEL, F_HEAD, 400, "middle", 1.5)),
         g("Vertical_Brand", vertical_word(84, 372, 94) + vertical_word(FW - 84, 372, 94)),
         peacock(f["style"], cx - 8, 376, .82),
         g("Brand_Block",
           t(cx, 618, "ASHVENA", 38, YEL, F_HEAD, 400, "middle", 3)
           + t(cx, 646, "EST. 1953  ·  200g", 15, YEL, F_HEAD, 400, "middle", 2)),
         f'<line x1="{FW}" y1="30" x2="{FW}" y2="{H - 30}" stroke="{YEL}" stroke-width=".6" stroke-dasharray="3 5" opacity=".35"/>',
         info_panel(f)]
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W / 4:.0f}mm" height="{H / 4:.0f}mm" viewBox="0 0 {W} {H}">\n'
            f'<title>Ashvena {esc(f["name"])} Cashews - wrap label</title>\n' + "\n".join(o) + "\n</svg>\n")


def main():
    os.makedirs(ROOT, exist_ok=True)
    for key in LABELS:
        p = os.path.join(ROOT, f"ashvena-{key}-cashews_wrap-label.svg")
        open(p, "w").write(label(key))
        print(os.path.relpath(p, os.path.join(ROOT, "..", "..")))


if __name__ == "__main__":
    main()
