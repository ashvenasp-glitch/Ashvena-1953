#!/usr/bin/env python3
"""Ashvena box belts (sleeve bands) - Direction F "Palace Garden".

A colourful take on the pastel Rajasthani palace-garden references: a row
of bays (jharokha windows with jaali, cusped arched niches with banana
trees, palms, potted fruit trees) in bright festive colours, around a
central cusped-arch cartouche carrying the brand and product name.

Artboard: 297.04 x 74.8 mm (4 px = 1 mm), two flavours.
Output: packaging/F-palace-garden/ashvena-<flavour>_belt.svg
"""
import math
import os
import random

from generate_packaging import esc

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packaging", "F-palace-garden")

W_MM, H_MM = 297.04, 74.8
W, H = W_MM * 4, H_MM * 4          # 1188.16 x 299.2
BAND = 14                          # top / bottom border band
BY, BH = BAND, H - 2 * BAND        # bay area
TW = 372                           # title bay width
TX = (W - TW) / 2
SW = TX / 3                        # side bay width

F_BRAND = "Cinzel, 'Trajan Pro', serif"
F_HEAD = "'DM Serif Display', 'Playfair Display', Georgia, serif"
F_ITAL = "'Cormorant Garamond', Garamond, Georgia, serif"
F_SANS = "Montserrat, Helvetica, Arial, sans-serif"

LINE = "#4a2a14"                   # illustration outline
CREAM = "#fff4dc"
GOLD = "#e8b84a"

FLAVOURS = {
    "aam-papad": dict(
        name="Aam Papad", line1="Aam", line2="Papad", size2=62,
        sub="SUN-DRIED MANGO FRUIT SLAB",
        tag="TANGY  ·  SWEET  ·  SUN-KISSED",
        title_bg="#7a1636", head="#d8264f", accent="#f08a12",
        band="#7a1636", dots=["#ffc21a", "#14a39a", "#ff5c8a", "#fff4dc"],
        bays=[("palm_pot", "#14a39a"), ("niche_banana", "#e5336d"), ("palms", "#ffb81c"),
              ("banana_leaves", "#f57c1f"), ("jharokha", "#8cc63f"), ("niche_fruit", "#e5336d")],
        fruit="mango"),
    "fruit-cocktail": dict(
        name="Fruit Cocktail", line1="Fruit", line2="Cocktail", size2=50,
        sub="TROPICAL MIXED FRUIT SLAB",
        tag="TANGY  ·  SWEET  ·  FRUITY",
        title_bg="#22306e", head="#e0245e", accent="#7b3fb0",
        band="#22306e", dots=["#ffc21a", "#ff5c8a", "#9bd23c", "#19b5c9"],
        bays=[("palm_pot", "#8a4fc4"), ("niche_banana", "#ff6f3c"), ("palms", "#19b5c9"),
              ("banana_leaves", "#ff4f8b"), ("jharokha", "#9bd23c"), ("niche_fruit", "#ffb81c")],
        fruit="mixed"),
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def mix(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def dark(c, t):
    return mix(c, "#2a0e0a", t)


def light(c, t):
    return mix(c, "#ffffff", t)


def t(x, y, s, size, fill, family=F_SANS, weight=400, anchor="middle", ls=0, italic=False):
    it = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}"{it}>{esc(s)}</text>')


def g(gid, body, extra=""):
    return f'<g id="{gid}"{extra}>\n{body}\n</g>'


def pts_d(pts, close=True):
    d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return d + (" Z" if close else "")


def bez(p0, p1, p2, p3, u):
    a = [(1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u ** 2, u ** 3]
    return (sum(c * p[0] for c, p in zip(a, (p0, p1, p2, p3))),
            sum(c * p[1] for c, p in zip(a, (p0, p1, p2, p3))))


# ---------------------------------------------------------------------------
# architecture
# ---------------------------------------------------------------------------

def arch_pts(cx, top, w, spring, n):
    """Points along a gently pointed arch from the left spring to the right."""
    L, R = cx - w / 2, cx + w / 2
    hh = spring - top
    segs = [((L, spring), (L, spring - .62 * hh), (cx - .16 * w, top + .1 * hh), (cx, top)),
            ((cx, top), (cx + .16 * w, top + .1 * hh), (R, spring - .62 * hh), (R, spring))]
    out = []
    for s in segs:
        for i in range(n):
            out.append(bez(*s, i / n))
    out.append((R, spring))
    return out


def arch_d(cx, top, w, spring, base, cusps=0):
    """Closed arch opening; cusps > 0 gives a multifoil (lobed) Mughal arch."""
    pts = arch_pts(cx, top, w, spring, cusps or 24)
    d = f"M {cx - w / 2:.1f},{base:.1f} L {pts[0][0]:.1f},{pts[0][1]:.1f}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if cusps:
            r = math.hypot(x1 - x0, y1 - y0) * .58
            d += f" A {r:.1f} {r:.1f} 0 0 1 {x1:.1f},{y1:.1f}"
        else:
            d += f" L {x1:.1f},{y1:.1f}"
    return d + f" L {cx + w / 2:.1f},{base:.1f} Z"


def jaali(x, y, w, h, cell, base, hole, stroke=LINE, uid="j"):
    """Lattice screen: quatrefoil piercings on a stone panel."""
    o = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{base}" stroke="{stroke}" stroke-width="1"/>',
         f'<clipPath id="{uid}"><rect x="{x + 2:.1f}" y="{y + 2:.1f}" width="{w - 4:.1f}" height="{h - 4:.1f}"/></clipPath>',
         f'<g clip-path="url(#{uid})">']
    d = []
    r = cell * .2
    row = 0
    yy = y + cell / 2
    while yy < y + h + cell:
        xx = x + (cell / 2 if row % 2 else 0)
        while xx < x + w + cell:
            for dx, dy in ((r * .8, 0), (-r * .8, 0), (0, r * .8), (0, -r * .8)):
                cx, cy = xx + dx, yy + dy
                d.append(f"M {cx - r:.1f},{cy:.1f} a {r:.1f},{r:.1f} 0 1,0 {2 * r:.1f},0 a {r:.1f},{r:.1f} 0 1,0 {-2 * r:.1f},0")
            xx += cell
        yy += cell / 2
        row += 1
    o.append(f'<path d="{" ".join(d)}" fill="{hole}"/>')
    o.append("</g>")
    return "".join(o)


def dome_post(x, y, s, fill, col=LINE):
    """Little chhatri finial post (parapet end)."""
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({s})">'
            f'<rect x="-4" y="0" width="8" height="22" fill="{fill}" stroke="{col}" stroke-width="1"/>'
            f'<path d="M -6,0 C -6,-9 6,-9 6,0 Z" fill="{fill}" stroke="{col}" stroke-width="1"/>'
            f'<path d="M 0,-7 L 0,-12" stroke="{col}" stroke-width="1"/><circle cx="0" cy="-13" r="1.4" fill="{col}"/>'
            f'<rect x="-6" y="0" width="12" height="2.5" fill="{fill}" stroke="{col}" stroke-width=".8"/>'
            f'</g>')


# ---------------------------------------------------------------------------
# botanicals
# ---------------------------------------------------------------------------

LEAF_L, LEAF_D, LEAF_O, RIB = "#9fd36a", "#4f9a45", "#24502a", "#f3dc84"


def banana_leaf(x, y, ang, L, wd, bend, seed, cols=None):
    """Banana blade: base at (x, y), pointing at `ang` degrees, two-tone halves."""
    lc, dc, oc, rc = cols or (LEAF_L, LEAF_D, LEAF_O, RIB)
    rng = random.Random(seed)
    n = 26
    mid, up, lo = [], [], []
    for i in range(n + 1):
        u = i / n
        mx, my = L * u, bend * L * u * u
        tx, ty = L, 2 * bend * L * u
        k = math.hypot(tx, ty)
        nx, ny = -ty / k, tx / k
        wu = wd / 2 * (math.sin(math.pi * min(1, u * 1.05)) ** .55) * (1 - .25 * u)
        mid.append((mx, my))
        up.append((mx - nx * wu, my - ny * wu))
        lo.append((mx + nx * wu * .92, my + ny * wu * .92))
    half_a = pts_d(mid + up[::-1])
    half_b = pts_d(mid + lo[::-1])
    o = [f'<g transform="translate({x:.1f} {y:.1f}) rotate({ang:.1f})">',
         f'<path d="{half_a}" fill="{lc}" stroke="{oc}" stroke-width="1" stroke-linejoin="round"/>',
         f'<path d="{half_b}" fill="{dc}" stroke="{oc}" stroke-width="1" stroke-linejoin="round"/>']
    # side veins
    vs = []
    for i in range(3, n - 2, 2):
        mx, my = mid[i]
        for edge, f in ((up, .85), (lo, .85)):
            ex, ey = edge[min(n, i + 1)]
            vs.append(f"M {mx:.1f},{my:.1f} L {mx + (ex - mx) * f:.1f},{my + (ey - my) * f:.1f}")
    o.append(f'<path d="{" ".join(vs)}" stroke="{oc}" stroke-width=".45" opacity=".45" fill="none"/>')
    # a couple of tears in the blade
    for _ in range(2):
        i = rng.randint(6, n - 6)
        edge = rng.choice((up, lo))
        mx, my = mid[i]
        ex, ey = edge[i + 1]
        o.append(f'<path d="M {ex:.1f},{ey:.1f} L {mx + (ex - mx) * .35:.1f},{my + (ey - my) * .35:.1f}" '
                 f'stroke="{oc}" stroke-width=".9" fill="none"/>')
    o.append(f'<path d="{pts_d(mid, False)}" fill="none" stroke="{rc}" stroke-width="1.4" stroke-linecap="round"/>')
    o.append("</g>")
    return "".join(o)


def banana_tree(cx, base, crown, s, seed, cols=None):
    """Banana plant: tapered pseudostem with radiating blades."""
    rng = random.Random(seed)
    o = [f'<path d="M {cx - 7 * s:.1f},{base:.1f} C {cx - 6 * s:.1f},{(base + crown) / 2:.1f} {cx - 3 * s:.1f},{crown + 10:.1f} '
         f'{cx - 2 * s:.1f},{crown:.1f} L {cx + 2 * s:.1f},{crown:.1f} C {cx + 3 * s:.1f},{crown + 10:.1f} '
         f'{cx + 6 * s:.1f},{(base + crown) / 2:.1f} {cx + 7 * s:.1f},{base:.1f} Z" fill="#7fae4e" stroke="{LEAF_O}" stroke-width="1"/>',
         f'<path d="M {cx:.1f},{base:.1f} C {cx - 1:.1f},{(base + crown) / 2:.1f} {cx:.1f},{crown + 10:.1f} {cx:.1f},{crown:.1f}" '
         f'stroke="{LEAF_O}" stroke-width=".6" fill="none" opacity=".5"/>']
    leaves = [(-172, 58, .2), (-8, 58, .2), (-146, 66, .1), (-34, 66, .1),
              (-122, 70, .03), (-58, 70, .03), (-102, 66, -.02), (-78, 66, -.02), (-90, 56, 0)]
    for i, (a, L, b) in enumerate(leaves):
        a += rng.uniform(-5, 5)
        L *= s * rng.uniform(.92, 1.05)
        sl = 10 * s
        bx = cx + sl * math.cos(math.radians(a))
        by = crown + sl * math.sin(math.radians(a))
        o.append(f'<line x1="{cx:.1f}" y1="{crown:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{LEAF_O}" stroke-width="{2.4 * s:.1f}" stroke-linecap="round"/>')
        o.append(f'<line x1="{cx:.1f}" y1="{crown:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#86b85a" stroke-width="{1.2 * s:.1f}" stroke-linecap="round"/>')
        o.append(banana_leaf(bx, by, a, L, L * .4, -b if a < -90 else b, seed * 31 + i, cols))
    return "".join(o)


def palm(bx, by, cx, cy, s, seed, lean=0, frond_col="#5fae4a", frond_dk="#2f7a3a", trunk="#d9b383"):
    """Coconut palm: tapered curved trunk from (bx, by) to crown (cx, cy)."""
    rng = random.Random(seed)
    p0, p3 = (bx, by), (cx, cy)
    p1 = (bx + lean * .2, by - (by - cy) * .4)
    p2 = (cx + lean, cy + (by - cy) * .3)
    left, right, rings = [], [], []
    for i in range(41):
        u = i / 40
        x, y = bez(p0, p1, p2, p3, u)
        x2, y2 = bez(p0, p1, p2, p3, min(1, u + .01))
        x1, y1 = bez(p0, p1, p2, p3, max(0, u - .01))
        dx, dy = x2 - x1, y2 - y1
        k = math.hypot(dx, dy) or 1
        nx, ny = -dy / k, dx / k
        w = (6.5 - 2.5 * u) * s
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
        if i % 3 == 1 and i < 38:
            rings.append(f"M {x + nx * w:.1f},{y + ny * w:.1f} Q {x + dx / k * 2 * s:.1f},{y + dy / k * 2 * s:.1f} {x - nx * w:.1f},{y - ny * w:.1f}")
    o = [f'<path d="{pts_d(left + right[::-1])}" fill="{trunk}" stroke="{LINE}" stroke-width="1"/>',
         f'<path d="{" ".join(rings)}" stroke="{dark(trunk, .45)}" stroke-width=".7" fill="none"/>']
    # fronds
    fronds = []
    for a in (-170, -150, -128, -105, -80, -55, -32, -10, 160, 20, 130, 50):
        a += rng.uniform(-6, 6)
        L = rng.uniform(52, 64) * s * (.8 if a in (130, 50) else 1)
        fronds.append((a, L))
    for k, (a, L) in enumerate(sorted(fronds, key=lambda f: -abs(math.sin(math.radians(f[0]))))):
        ar = math.radians(a)
        droop = L * (.55 if math.sin(ar) > -.5 else .25)
        q0 = (cx, cy)
        q1 = (cx + math.cos(ar) * L * .55, cy + math.sin(ar) * L * .55 - L * .12)
        q2 = (cx + math.cos(ar) * L, cy + math.sin(ar) * L + droop)
        col = frond_col if k % 2 else mix(frond_col, frond_dk, .4)
        leaflets = []
        for i in range(2, 23):
            u = i / 22
            x = (1 - u) ** 2 * q0[0] + 2 * (1 - u) * u * q1[0] + u * u * q2[0]
            y = (1 - u) ** 2 * q0[1] + 2 * (1 - u) * u * q1[1] + u * u * q2[1]
            tx = 2 * (1 - u) * (q1[0] - q0[0]) + 2 * u * (q2[0] - q1[0])
            ty = 2 * (1 - u) * (q1[1] - q0[1]) + 2 * u * (q2[1] - q1[1])
            ta = math.degrees(math.atan2(ty, tx))
            ll = (18 - 11 * u) * s
            for side in (-1, 1):
                la = math.radians(ta + side * 48)
                ex = x + math.cos(la) * ll
                ey = y + math.sin(la) * ll + ll * .55
                mx, my = (x + ex) / 2, (y + ey) / 2
                nx, ny = -(ey - y), ex - x
                kk = math.hypot(nx, ny) or 1
                wv = 1.5 * s
                leaflets.append(f"M {x:.1f},{y:.1f} Q {mx + nx / kk * wv:.1f},{my + ny / kk * wv:.1f} {ex:.1f},{ey:.1f} "
                                f"Q {mx - nx / kk * wv:.1f},{my - ny / kk * wv:.1f} {x:.1f},{y:.1f} Z")
        o.append(f'<path d="{" ".join(leaflets)}" fill="{col}" stroke="{dark(frond_dk, .3)}" stroke-width=".45"/>')
        o.append(f'<path d="M {q0[0]:.1f},{q0[1]:.1f} Q {q1[0]:.1f},{q1[1]:.1f} {q2[0]:.1f},{q2[1]:.1f}" '
                 f'fill="none" stroke="{RIB}" stroke-width="1" stroke-linecap="round"/>')
    # coconuts
    for dx in (-4, 3):
        o.append(f'<circle cx="{cx + dx * s:.1f}" cy="{cy + 5 * s:.1f}" r="{3.6 * s:.1f}" fill="#8a5a2b" stroke="{LINE}" stroke-width=".8"/>')
    return "".join(o)


MANGO = "M 0,-11 C 8,-11 12,-3 10,5 C 8,12 -1,14 -6,10 C -10,6 -10,-1 -7,-5 C -5,-8 -3,-11 0,-11 Z"


def mango(x, y, s, r=0):
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({r}) scale({s})">'
            f'<path d="{MANGO}" fill="url(#mangoG)" stroke="{LINE}" stroke-width="{1 / s:.2f}"/>'
            f'<path d="M 3,-7 C 7,-6 8,-2 7,1" fill="none" stroke="#fff6c8" stroke-width="{1.4 / s:.2f}" stroke-linecap="round" opacity=".8"/>'
            f'<path d="M 0,-11 L 1,-15" stroke="#5a3a1a" stroke-width="{1.4 / s:.2f}" stroke-linecap="round"/>'
            f'</g>')


def small_leaf(x, y, s, r, fill=LEAF_D, rib=LEAF_L):
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({r:.1f}) scale({s})">'
            f'<path d="M 0,0 C 6,-5 16,-5 22,0 C 16,5 6,5 0,0 Z" fill="{fill}" stroke="{LEAF_O}" stroke-width="{.8 / s:.2f}"/>'
            f'<path d="M 1,0 L 20,0" stroke="{rib}" stroke-width="{.7 / s:.2f}"/></g>')


def round_fruit(x, y, r, grad, shine=True):
    o = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="url(#{grad})" stroke="{LINE}" stroke-width=".8"/>'
    if shine:
        o += f'<circle cx="{x - r * .35:.1f}" cy="{y - r * .35:.1f}" r="{r * .22:.1f}" fill="#fff" opacity=".55"/>'
    return o


def pot(cx, base, w, h, fill="#d9774a"):
    """Rounded terracotta matka with rim and painted band."""
    top = base - h
    d = (f"M {cx - w * .32:.1f},{top + h * .12:.1f} C {cx - w * .62:.1f},{top + h * .3:.1f} {cx - w * .58:.1f},{base - h * .08:.1f} "
         f"{cx - w * .3:.1f},{base:.1f} L {cx + w * .3:.1f},{base:.1f} C {cx + w * .58:.1f},{base - h * .08:.1f} "
         f"{cx + w * .62:.1f},{top + h * .3:.1f} {cx + w * .32:.1f},{top + h * .12:.1f} Z")
    return (f'<path d="{d}" fill="{fill}" stroke="{LINE}" stroke-width="1"/>'
            f'<path d="M {cx - w * .48:.1f},{top + h * .42:.1f} Q {cx:.1f},{top + h * .52:.1f} {cx + w * .48:.1f},{top + h * .42:.1f}" '
            f'stroke="{CREAM}" stroke-width="1.6" fill="none" opacity=".8"/>'
            f'<path d="M {cx - w * .5:.1f},{top + h * .5:.1f} Q {cx:.1f},{top + h * .6:.1f} {cx + w * .5:.1f},{top + h * .5:.1f}" '
            f'stroke="{dark(fill, .35)}" stroke-width="1" fill="none" stroke-dasharray="2 2.5"/>'
            f'<rect x="{cx - w * .36:.1f}" y="{top:.1f}" width="{w * .72:.1f}" height="{h * .14:.1f}" rx="2" '
            f'fill="{light(fill, .15)}" stroke="{LINE}" stroke-width="1"/>'
            f'<path d="M {cx - w * .22:.1f},{top + h * .3:.1f} Q {cx - w * .32:.1f},{top + h * .55:.1f} {cx - w * .2:.1f},{base - h * .15:.1f}" '
            f'stroke="#fff" stroke-width="2" opacity=".25" fill="none" stroke-linecap="round"/>')


def fruit_tree(cx, base, s, kind, seed, pot_col="#d9774a"):
    """Potted fruit tree: mangoes or citrus/pomegranate."""
    rng = random.Random(seed)
    ph = 34 * s
    crown_y = base - ph - 52 * s
    o = [f'<path d="M {cx:.1f},{base - ph + 2:.1f} C {cx - 1:.1f},{base - ph - 20 * s:.1f} {cx + 2:.1f},{crown_y + 20 * s:.1f} {cx:.1f},{crown_y + 8 * s:.1f}" '
         f'stroke="#6b4423" stroke-width="{3 * s:.1f}" fill="none" stroke-linecap="round"/>']
    for a in (-60, -120, -95):
        ex = cx + math.cos(math.radians(a)) * 22 * s
        ey = crown_y + 14 * s + math.sin(math.radians(a)) * 22 * s
        o.append(f'<path d="M {cx:.1f},{crown_y + 22 * s:.1f} Q {(cx + ex) / 2:.1f},{crown_y + 16 * s:.1f} {ex:.1f},{ey:.1f}" '
                 f'stroke="#6b4423" stroke-width="{1.6 * s:.1f}" fill="none" stroke-linecap="round"/>')
    leaves = []
    for i in range(58):
        a = rng.uniform(0, 2 * math.pi)
        rr = 30 * s * math.sqrt(rng.uniform(.05, 1))
        x = cx + math.cos(a) * rr * 1.15
        y = crown_y + math.sin(a) * rr * .85
        leaves.append(small_leaf(x, y, s * rng.uniform(.5, .62), math.degrees(a) + rng.uniform(-40, 40),
                                 rng.choice([LEAF_D, "#5fae4a", "#3f8a3e"]), LEAF_L))
    o += leaves
    fr = [(-16, 8), (12, 4), (-2, 16), (20, 18), (-22, -6), (4, -12), (24, -4), (-8, -2)]
    for i, (dx, dy) in enumerate(fr):
        fx, fy = cx + dx * s, crown_y + dy * s
        if kind == "mango":
            o.append(mango(fx, fy, .62 * s, rng.uniform(-25, 25)))
        else:
            grad = ["orangeG", "pomG", "orangeG", "limeG"][i % 4]
            o.append(round_fruit(fx, fy, 5.2 * s, grad))
    o.append(pot(cx, base, 42 * s, ph, pot_col))
    return "".join(o)


def ivy_pot(cx, base, s, seed):
    """Small pot with trailing round leaves (bottom-corner accent)."""
    rng = random.Random(seed)
    o = []
    for i in range(22):
        a = rng.uniform(-170, -10)
        rr = rng.uniform(8, 24) * s
        x = cx + math.cos(math.radians(a)) * rr * 1.3
        y = base - 26 * s + math.sin(math.radians(a)) * rr
        o.append(f'<g transform="translate({x:.1f} {y:.1f}) rotate({a + 90 + rng.uniform(-30, 30):.0f}) scale({s})">'
                 f'<path d="M 0,0 C -6,-3 -6,-10 0,-13 C 6,-10 6,-3 0,0 Z" fill="{rng.choice(["#6cbf5a", "#3f8a3e", "#8fd36a"])}" '
                 f'stroke="{LEAF_O}" stroke-width="{.7 / s:.2f}"/>'
                 f'<path d="M 0,-1 L 0,-11" stroke="{RIB}" stroke-width="{.5 / s:.2f}"/></g>')
    o.append(pot(cx, base, 40 * s, 26 * s, "#c9683f"))
    return "".join(o)


# ---------------------------------------------------------------------------
# bays (local coords 0..w x 0..h)
# ---------------------------------------------------------------------------

def floor(w, h, col):
    return (f'<rect x="0" y="{h - 12:.1f}" width="{w:.1f}" height="12" fill="{dark(col, .22)}"/>'
            f'<line x1="0" y1="{h - 12:.1f}" x2="{w:.1f}" y2="{h - 12:.1f}" stroke="{light(col, .55)}" stroke-width="1.2"/>')


def bay_niche(w, h, col, inner, seed):
    fr = light(col, .18)
    deep = dark(col, .28)
    cx = w / 2
    o = [f'<rect x="10" y="16" width="{w - 20:.1f}" height="{h - 26:.1f}" fill="{fr}" stroke="{light(col, .6)}" stroke-width="1.2"/>',
         f'<rect x="14" y="20" width="{w - 28:.1f}" height="{h - 34:.1f}" fill="none" stroke="{dark(col, .15)}" stroke-width=".8"/>',
         f'<path d="{arch_d(cx, 30, w - 40, 112, h - 40, cusps=4)}" fill="{deep}" stroke="{light(col, .6)}" stroke-width="1.4"/>',
         f'<path d="{arch_d(cx, 36, w - 52, 116, h - 40, cusps=4)}" fill="url(#niche_{seed})"/>',
         f'<radialGradient id="niche_{seed}" cx=".5" cy=".35" r=".7"><stop offset="0" stop-color="{light(deep, .25)}"/>'
         f'<stop offset="1" stop-color="{dark(deep, .15)}"/></radialGradient>',
         inner,
         jaali(18, h - 70, w - 36, 38, 11, CREAM, mix(col, "#2a0e0a", .35), uid=f"jn{seed}"),
         f'<rect x="14" y="{h - 74:.1f}" width="{w - 28:.1f}" height="5" fill="{CREAM}" stroke="{LINE}" stroke-width="1"/>',
         dome_post(20, h - 96, 1, CREAM), dome_post(w - 20, h - 96, 1, CREAM),
         floor(w, h, col)]
    return "".join(o)


def bay_niche_banana(w, h, col, f, seed):
    return bay_niche(w, h, col, banana_tree(w / 2, h - 60, 128, 1.0, seed), seed)


def bay_niche_fruit(w, h, col, f, seed):
    return bay_niche(w, h, col, fruit_tree(w / 2, h - 66, 1.25, f["fruit"], seed, "#e98a3c"), seed)


def bay_palms(w, h, col, f, seed):
    o = [palm(w * .64, h, w * .56, 56, 1.0, seed, lean=-8),
         palm(w * .3, h, w * .34, 138, .82, seed + 1, lean=6, frond_col="#7cc35a"),
         floor(w, h, col)]
    return "".join(o)


def bay_palm_pot(w, h, col, f, seed):
    o = [palm(w * .86, h, w * .42, 62, 1.0, seed, lean=30),
         fruit_tree(w * .34, h - 12, 1.05, f["fruit"], seed + 3),
         floor(w, h, col)]
    return "".join(o)


def bay_banana_leaves(w, h, col, f, seed):
    cx, base = w * .72, h
    o = [f'<path d="M {cx - 6:.1f},{base:.1f} C {cx - 5:.1f},{h * .7:.1f} {cx - 3:.1f},{h * .5:.1f} {cx - 1:.1f},{h * .42:.1f} '
         f'L {cx + 3:.1f},{h * .42:.1f} C {cx + 5:.1f},{h * .5:.1f} {cx + 6:.1f},{h * .7:.1f} {cx + 7:.1f},{base:.1f} Z" '
         f'fill="#7fae4e" stroke="{LEAF_O}" stroke-width="1"/>']
    for i, (a, L, yy, b) in enumerate([(-150, 118, .5, .08), (-118, 128, .44, .02), (-92, 112, .42, -.02),
                                       (-66, 96, .44, -.04), (-172, 96, .62, .12), (-40, 80, .5, .06),
                                       (-135, 92, .72, .14)]):
        o.append(banana_leaf(cx + 1, h * yy, a, L, L * .34, b, seed + i))
    o.append(ivy_pot(w * .22, h - 12, 1.0, seed))
    o.append(floor(w, h, col))
    return "".join(o)


def bay_jharokha(w, h, col, f, seed):
    st, edge, deep = CREAM, LINE, dark(col, .3)
    x0, x1 = 16, w - 30
    cx = (x0 + x1) / 2
    o = [  # chhajja (sloped awning)
        f'<path d="M {x0 - 8},40 L {x1 + 8},40 L {x1 + 2},30 L {x0 - 2},30 Z" fill="{st}" stroke="{edge}" stroke-width="1"/>',
        f'<rect x="{x0 - 10}" y="40" width="{x1 - x0 + 20}" height="5" fill="{light(col, .45)}" stroke="{edge}" stroke-width="1"/>',
        f'<rect x="{x0 - 4}" y="22" width="{x1 - x0 + 8}" height="8" fill="{st}" stroke="{edge}" stroke-width="1"/>',
        # frame
        f'<rect x="{x0}" y="45" width="{x1 - x0}" height="{h - 120:.1f}" fill="{st}" stroke="{edge}" stroke-width="1"/>',
        f'<rect x="{x0 + 5}" y="50" width="{x1 - x0 - 10}" height="{h - 130:.1f}" fill="none" stroke="{edge}" stroke-width=".6"/>',
        f'<path d="{arch_d(cx, 58, x1 - x0 - 22, 116, 150, cusps=4)}" fill="url(#jh_{seed})" stroke="{edge}" stroke-width="1"/>',
        f'<linearGradient id="jh_{seed}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{deep}"/>'
        f'<stop offset="1" stop-color="{light(deep, .3)}"/></linearGradient>',
        jaali(x0 + 9, 156, x1 - x0 - 18, h - 238, 9, light(col, .7), dark(col, .25), uid=f"jj{seed}"),
        # sill + brackets with scalloped fringe
        f'<rect x="{x0 - 6}" y="{h - 75:.1f}" width="{x1 - x0 + 12}" height="7" fill="{st}" stroke="{edge}" stroke-width="1"/>',
        f'<path d="M {x0 + 2},{h - 68:.1f} L {x1 - 2},{h - 68:.1f} L {x1 - 10},{h - 58:.1f} L {x0 + 10},{h - 58:.1f} Z" fill="{st}" stroke="{edge}" stroke-width="1"/>']
    sc = []
    n = 7
    for i in range(n):
        a = x0 + 10 + (x1 - x0 - 20) * i / n
        b = x0 + 10 + (x1 - x0 - 20) * (i + 1) / n
        sc.append(f"M {a:.1f},{h - 58:.1f} A {(b - a) / 2:.1f} {(b - a) / 2:.1f} 0 0 0 {b:.1f},{h - 58:.1f}")
    o.append(f'<path d="{" ".join(sc)}" fill="{st}" stroke="{edge}" stroke-width="1"/>')
    for i in range(3):
        o.append(banana_leaf(w + 6, h - 20 - i * 34, -150 + i * 22, 92 - i * 14, 30 - i * 3, .08, seed + i))
    o.append(floor(w, h, col))
    return "".join(o)


BAYS = {"niche_banana": bay_niche_banana, "niche_fruit": bay_niche_fruit, "palms": bay_palms,
        "palm_pot": bay_palm_pot, "banana_leaves": bay_banana_leaves, "jharokha": bay_jharokha}


def bay(i, x, kind, col, f):
    uid = f"bay{i}"
    body = BAYS[kind](SW, BH, col, f, 11 + i * 7)
    return g(f"Bay_{i + 1}_{kind}",
             f'<clipPath id="{uid}"><rect x="0" y="0" width="{SW:.2f}" height="{BH:.2f}"/></clipPath>'
             f'<radialGradient id="{uid}bg" cx=".5" cy=".4" r=".75"><stop offset="0" stop-color="{light(col, .18)}"/>'
             f'<stop offset="1" stop-color="{col}"/></radialGradient>'
             f'<g clip-path="url(#{uid})"><rect width="{SW:.2f}" height="{BH:.2f}" fill="url(#{uid}bg)"/>{body}</g>',
             f' transform="translate({x:.2f} {BY})"')


# ---------------------------------------------------------------------------
# hero fruit for the title bay
# ---------------------------------------------------------------------------

def aam_papad_stack(x, y, s):
    """Three thin sun-dried mango slabs, fanned like a hand of cards."""
    o = [f'<g transform="translate({x:.1f} {y:.1f}) scale({s})">']
    for dx, dy, r in [(-5, 6, -12), (3, 2, 5), (-1, -4, -3)]:
        o.append(f'<g transform="translate({dx} {dy}) rotate({r})">'
                 f'<rect x="-21" y="-3" width="42" height="12" rx="4" fill="#c4600f" stroke="{LINE}" stroke-width=".8"/>'
                 f'<rect x="-21" y="-8" width="42" height="13" rx="4" fill="url(#papadG)" stroke="{LINE}" stroke-width=".8"/>'
                 f'<path d="M -16,-5.5 C -6,-6.5 6,-4.5 16,-5.5" stroke="#fff6c0" stroke-width="1.1" fill="none" '
                 f'stroke-linecap="round" opacity=".75"/>'
                 f'<path d="M -14,0 C -4,1 4,-1 12,0" stroke="#d9741a" stroke-width=".6" fill="none" opacity=".8"/></g>')
    o.append("</g>")
    return "".join(o)


def mango_cluster(x, y, s, flip=False):
    sx = -1 if flip else 1
    o = [f'<g transform="translate({x:.1f} {y:.1f}) scale({sx * s} {s})">']
    for lx, ly, r in [(-6, -26, -130), (4, -28, -60), (-12, -18, 170), (10, -20, -10), (0, -32, -95)]:
        o.append(small_leaf(lx, ly, 1.3, r))
    o.append(f'<path d="M 0,-30 Q -4,-18 -10,-8 M 0,-30 Q 4,-18 10,-4" stroke="#5a3a1a" stroke-width="1.6" fill="none"/>')
    o.append(mango(-10, 4, 1.6, 15))
    o.append(mango(12, 8, 1.75, -20))
    o.append("</g>")
    return "".join(o)


def pineapple(x, y, s):
    o = [f'<g transform="translate({x:.1f} {y:.1f}) scale({s})">']
    for a in (-40, -20, 0, 20, 40):
        o.append(f'<path d="M 0,-12 Q {a * .35},-30 {a * .6},-40 Q {a * .1},-26 0,-12 Z" fill="#3f9a3e" stroke="{LEAF_O}" stroke-width=".8"/>')
    o.append(f'<ellipse cx="0" cy="4" rx="12" ry="17" fill="url(#pineG)" stroke="{LINE}" stroke-width=".9"/>')
    o.append('<clipPath id="pc"><ellipse cx="0" cy="4" rx="12" ry="17"/></clipPath><g clip-path="url(#pc)">'
             + "".join(f'<path d="M {-20 + i * 6},-14 l 24,36 M {16 - i * 6 + 8},-14 l -24,36" stroke="#a8620f" stroke-width=".7"/>' for i in range(8))
             + "</g>")
    o.append("</g>")
    return "".join(o)


def watermelon(x, y, s, r=0):
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({r}) scale({s})">'
            f'<path d="M -18,0 A 18 18 0 0 0 18,0 Z" fill="#3f9a3e" stroke="{LINE}" stroke-width=".9"/>'
            f'<path d="M -15.5,0 A 15.5 15.5 0 0 0 15.5,0 Z" fill="#e9f5c8"/>'
            f'<path d="M -14,0 A 14 14 0 0 0 14,0 Z" fill="#f2445e"/>'
            + "".join(f'<ellipse cx="{sx}" cy="{sy}" rx=".9" ry="1.6" fill="#2a1410"/>' for sx, sy in
                      [(-8, 4), (-3, 7), (3, 7), (8, 4), (0, 3), (-5, 10), (5, 10)])
            + '</g>')


def orange_slice(x, y, s):
    o = [f'<g transform="translate({x:.1f} {y:.1f}) scale({s})">',
         f'<circle r="13" fill="#ff9a1f" stroke="{LINE}" stroke-width=".9"/><circle r="11" fill="#fff1c9"/>']
    for k in range(8):
        a = k * 45
        o.append(f'<path d="M 0,0 L 9.5,-3.4 A 10 10 0 0 1 9.5,3.4 Z" transform="rotate({a + 22.5})" fill="#ffb53a" '
                 f'stroke="#fff1c9" stroke-width=".9"/>')
    o.append("</g>")
    return "".join(o)


def strawberry(x, y, s, r=0):
    o = [f'<g transform="translate({x:.1f} {y:.1f}) rotate({r}) scale({s})">',
         f'<path d="M 0,14 C -10,8 -12,-4 -8,-8 C -4,-11 4,-11 8,-8 C 12,-4 10,8 0,14 Z" fill="url(#berryG)" stroke="{LINE}" stroke-width=".9"/>']
    for sx, sy in [(-4, -3), (2, -4), (5, 1), (-1, 2), (-5, 4), (2, 7), (-2, 9)]:
        o.append(f'<ellipse cx="{sx}" cy="{sy}" rx=".7" ry="1.1" fill="#ffe27a"/>')
    o.append(f'<path d="M -7,-9 L -2,-7 L 0,-12 L 2,-7 L 7,-9 L 3,-5 L -3,-5 Z" fill="#3f9a3e" stroke="{LEAF_O}" stroke-width=".7"/>')
    o.append("</g>")
    return "".join(o)


def cherries(x, y, s):
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({s})">'
            f'<path d="M -6,4 Q -4,-12 4,-18 M 7,6 Q 6,-8 4,-18" stroke="#4a6b1f" stroke-width="1.3" fill="none"/>'
            f'{small_leaf(4, -18, .6, -20)}'
            f'{round_fruit(-6, 6, 6, "cherryG")}{round_fruit(7, 8, 6, "cherryG")}</g>')


def grapes(x, y, s):
    o = [f'<g transform="translate({x:.1f} {y:.1f}) scale({s})">',
         f'<path d="M 0,-14 L 1,-20" stroke="#5a3a1a" stroke-width="1.4"/>', small_leaf(1, -18, .6, -30)]
    for gx, gy in [(-6, -10), (0, -11), (6, -10), (-9, -4), (-3, -4), (3, -4), (9, -4), (-6, 2), (0, 2), (6, 2), (-3, 8), (3, 8), (0, 13)]:
        o.append(round_fruit(gx, gy, 3.6, "grapeG"))
    o.append("</g>")
    return "".join(o)


def fruit_pile_left(kind):
    x = TX + 30
    if kind == "mango":
        return mango_cluster(x + 2, 200, 1.1) + aam_papad_stack(x + 2, 252, 1.05)
    return (cherries(x + 14, 150, 1.15) + pineapple(x - 2, 196, 1.4) + strawberry(x + 16, 226, 1.3, 15)
            + watermelon(x + 2, 254, 1.4, -8))


def fruit_pile_right(kind):
    x = TX + TW - 30
    if kind == "mango":
        return mango_cluster(x - 2, 200, 1.1, flip=True) + aam_papad_stack(x - 2, 252, 1.05)
    return (mango(x - 2, 152, 1.6, 25) + grapes(x + 2, 196, 1.4) + orange_slice(x - 8, 242, 1.35)
            + strawberry(x + 14, 258, 1.15, 18))


# ---------------------------------------------------------------------------
# title bay + bands
# ---------------------------------------------------------------------------

def rosette(cx, cy, r, fill, centre):
    pet = "M 0,0 C -5,-4 -4,-10 0,-15 C 4,-10 5,-4 0,0 Z"
    o = [f'<g transform="translate({cx:.1f} {cy:.1f})">']
    for k in range(12):
        o.append(f'<path d="{pet}" transform="rotate({k * 30}) scale({r / 15:.2f})" fill="{fill}" stroke="{LINE}" stroke-width=".5"/>')
    o.append(f'<circle r="{r * .28:.1f}" fill="{centre}" stroke="{LINE}" stroke-width=".6"/></g>')
    return "".join(o)


def veg_mark(x, y, s=12):
    return g("Veg_Mark", f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="#fff" stroke="#138a36" stroke-width="1.2"/>'
                         f'<circle cx="{x + s / 2}" cy="{y + s / 2}" r="{s * .27:.1f}" fill="#138a36"/>')


def title_bay(f):
    cx = W / 2
    bg = f["title_bg"]
    aw = 236
    top, spring, base = BY + 12, BY + 92, H - BAND - 6
    o = [f'<rect x="{TX:.2f}" y="{BY}" width="{TW}" height="{BH:.2f}" fill="{bg}"/>',
         f'<clipPath id="tclip"><rect x="{TX:.2f}" y="{BY}" width="{TW}" height="{BH:.2f}"/></clipPath>',
         f'<g clip-path="url(#tclip)" opacity=".22">'
         + jaali(TX - 10, BY - 10, TW + 20, BH + 20, 18, "none", GOLD, stroke="none", uid="tj") + "</g>",
         # arch: gold rim, coloured band, cream field
         f'<path d="{arch_d(cx, top - 6, aw + 22, spring, base + 4)}" fill="{GOLD}" stroke="{LINE}" stroke-width="1"/>',
         f'<path d="{arch_d(cx, top, aw + 10, spring + 2, base + 4)}" fill="{f["accent"]}"/>',
         f'<path d="{arch_d(cx, top + 6, aw, spring + 4, base + 4, cusps=5)}" fill="{CREAM}" stroke="{GOLD}" stroke-width="1.6"/>',
         f'<path d="{arch_d(cx, top + 12, aw - 12, spring + 6, base + 4, cusps=5)}" fill="none" stroke="{f["head"]}" '
         f'stroke-width=".7" stroke-dasharray="1.5 2.5" opacity=".6"/>',
         # finial
         f'<path d="M {cx},{top - 24} C {cx + 6},{top - 14} {cx + 6},{top - 8} {cx},{top - 3} '
         f'C {cx - 6},{top - 8} {cx - 6},{top - 14} {cx},{top - 24} Z" fill="{GOLD}" stroke="{LINE}" stroke-width=".8"/>',
         rosette(cx, top + 34, 9, "#ffc21a", f["head"])]
    o.append(fruit_pile_left(f["fruit"]))
    o.append(fruit_pile_right(f["fruit"]))
    # type
    ink = dark(f["title_bg"], .1)
    o.append(g("Brand",
               t(cx, BY + 74, "ASHVENA", 22, ink, F_BRAND, 600, ls=6)
               + f'<line x1="{cx - 70}" y1="{BY + 82}" x2="{cx - 34}" y2="{BY + 82}" stroke="{f["head"]}" stroke-width=".8"/>'
               + f'<line x1="{cx + 34}" y1="{BY + 82}" x2="{cx + 70}" y2="{BY + 82}" stroke="{f["head"]}" stroke-width=".8"/>'
               + t(cx, BY + 85, "EST. 1953", 7.5, ink, F_SANS, 700, ls=2.5)))
    o.append(g("Product_Name",
               t(cx, BY + 122, f["line1"], 34, f["accent"], F_ITAL, 700, italic=True)
               + t(cx, BY + 178, f["line2"], f["size2"], f["head"], F_HEAD, 400, ls=.5)))
    o.append(g("Descriptor",
               t(cx, BY + 200, f["sub"], 8.5, ink, F_SANS, 700, ls=2.2)
               + f'<path d="M {cx - 60},{BY + 210} L {cx - 8},{BY + 210} M {cx + 8},{BY + 210} L {cx + 60},{BY + 210}" stroke="{GOLD}" stroke-width="1"/>'
               + f'<path d="M {cx},{BY + 206} l 4,4 l -4,4 l -4,-4 Z" fill="{f["head"]}"/>'
               + t(cx, BY + 226, f["tag"], 7.5, f["accent"], F_SANS, 700, ls=1.6)))
    o.append(veg_mark(cx - 80, BY + 238))
    o.append(g("Net_Wt_PLACEHOLDER", t(cx + 80, BY + 248, "NET WT. XXX g", 8, ink, F_SANS, 700, "end", ls=1)))
    return g("Title_Bay", "\n".join(o))


def band(y, f, flip):
    o = [f'<rect x="0" y="{y:.2f}" width="{W:.2f}" height="{BAND}" fill="{f["band"]}"/>']
    edge = y + BAND if not flip else y
    o.append(f'<line x1="0" y1="{edge:.2f}" x2="{W:.2f}" y2="{edge:.2f}" stroke="{GOLD}" stroke-width="1.6"/>')
    step = 14
    n = int(W / step) + 1
    tri = []
    for i in range(n):
        x = i * step
        if not flip:
            tri.append(f"M {x:.1f},{y + BAND - .8:.1f} l {step / 2:.1f},-5 l {step / 2:.1f},5 Z")
        else:
            tri.append(f"M {x:.1f},{y + .8:.1f} l {step / 2:.1f},5 l {step / 2:.1f},-5 Z")
    o.append(f'<path d="{" ".join(tri)}" fill="{GOLD}" opacity=".9"/>')
    cy = y + (4.6 if not flip else BAND - 4.6)
    for i in range(n):
        o.append(f'<circle cx="{i * step + step / 2:.1f}" cy="{cy:.1f}" r="2.1" fill="{f["dots"][i % len(f["dots"])]}"/>')
    return "".join(o)


def pillars():
    o = []
    xs = [SW * i for i in range(1, 3)] + [TX, TX + TW] + [TX + TW + SW * i for i in range(1, 3)]
    for x in xs:
        o.append(f'<rect x="{x - 2.5:.2f}" y="{BY}" width="5" height="{BH:.2f}" fill="{CREAM}" stroke="{LINE}" stroke-width=".6"/>'
                 f'<rect x="{x - 4:.2f}" y="{BY}" width="8" height="5" fill="{GOLD}" stroke="{LINE}" stroke-width=".6"/>'
                 f'<rect x="{x - 4:.2f}" y="{H - BAND - 5:.2f}" width="8" height="5" fill="{GOLD}" stroke="{LINE}" stroke-width=".6"/>')
    return "".join(o)


DEFS = """
<linearGradient id="mangoG" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#ffe45c"/><stop offset=".45" stop-color="#ffb81c"/><stop offset=".8" stop-color="#f26b2a"/><stop offset="1" stop-color="#d93a2b"/>
</linearGradient>
<linearGradient id="papadG" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#ffb43a"/><stop offset=".5" stop-color="#ef8a1c"/><stop offset="1" stop-color="#c9621a"/>
</linearGradient>
<radialGradient id="orangeG" cx=".35" cy=".35" r=".8"><stop offset="0" stop-color="#ffd27a"/><stop offset="1" stop-color="#f27a12"/></radialGradient>
<radialGradient id="pomG" cx=".35" cy=".35" r=".8"><stop offset="0" stop-color="#ff8a8a"/><stop offset="1" stop-color="#c8202f"/></radialGradient>
<radialGradient id="limeG" cx=".35" cy=".35" r=".8"><stop offset="0" stop-color="#f4ff9a"/><stop offset="1" stop-color="#9bc22a"/></radialGradient>
<radialGradient id="cherryG" cx=".35" cy=".35" r=".8"><stop offset="0" stop-color="#ff6b7a"/><stop offset="1" stop-color="#a5102a"/></radialGradient>
<radialGradient id="grapeG" cx=".35" cy=".35" r=".8"><stop offset="0" stop-color="#c58ef0"/><stop offset="1" stop-color="#5b2290"/></radialGradient>
<radialGradient id="berryG" cx=".4" cy=".3" r=".9"><stop offset="0" stop-color="#ff6b6b"/><stop offset="1" stop-color="#c8102e"/></radialGradient>
<linearGradient id="pineG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd84a"/><stop offset="1" stop-color="#e8961a"/></linearGradient>
"""


def belt(key):
    f = FLAVOURS[key]
    o = [g("Background", f'<rect width="{W:.2f}" height="{H:.2f}" fill="{f["band"]}"/>')]
    bays = f["bays"]
    for i, (kind, col) in enumerate(bays[:3]):
        o.append(bay(i, SW * i, kind, col, f))
    for i, (kind, col) in enumerate(bays[3:]):
        o.append(bay(i + 3, TX + TW + SW * i, kind, col, f))
    o.append(g("Pillars", pillars()))
    o.append(title_bay(f))
    o.append(g("Border_Bands", band(0, f, False) + band(H - BAND, f, True)))
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_MM}mm" height="{H_MM}mm" viewBox="0 0 {W:.2f} {H:.2f}">\n'
            f'<title>Ashvena {esc(f["name"])} - box belt</title>\n<defs>{DEFS}</defs>\n' + "\n".join(o) + "\n</svg>\n")


def main():
    os.makedirs(ROOT, exist_ok=True)
    for key in FLAVOURS:
        p = os.path.join(ROOT, f"ashvena-{key}_belt.svg")
        open(p, "w").write(belt(key))
        print(os.path.relpath(p, os.path.join(ROOT, "..", "..")))


if __name__ == "__main__":
    main()
