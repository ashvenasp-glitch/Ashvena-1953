#!/usr/bin/env python3
"""Ashvena masala jar labels - Direction F "Jharokha Garden".

Modern, premium wrap-around labels for Chai Masala and Chaat Masala,
built from the botanical-miniature references (cusped Mughal arch,
jaali balcony, potted trees, banana leaves and palm fronds) and the
"Tea Leaves / Biscuits / Orange Peels / Roses / Green Tea" palette.

Each label is 171 x 70 mm (4 px = 1 mm):
  left info panel 44 mm | front panel 83 mm | right info panel 44 mm

Output (packaging/F-masala-jharokha/):
  ashvena-masala-labels.svg   editable master, both labels on one sheet
  ashvena-masala-labels.ai    the same sheet as a PDF-compatible .ai file
  ashvena-masala-labels_print.pdf  2 pages, one per label at 171 x 70 mm
  ashvena-masala-labels.png   preview
"""
import math
import os
import random
import re

from generate_packaging import barcode, esc, veg_mark, wrap

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packaging", "F-masala-jharokha")

W, H = 684, 280               # one label, 171 x 70 mm
P0, P1 = 176, 508             # front panel x range (44 mm | 83 mm | 44 mm)
M = 40                        # sheet margin (10 mm)
SHEET_W, SHEET_H = W + 2 * M, 2 * H + 3 * M

F_BRAND = "Cinzel, 'Trajan Pro', serif"
F_SERIF = "'Cormorant Garamond', Garamond, Georgia, serif"
F_SANS = "Montserrat, Gotham, Helvetica, Arial, sans-serif"

# Palette from the references
TEA_LEAVES, BISCUITS, ORANGE_PEELS, ROSES, GREEN_TEA = "#834316", "#EFE4C5", "#E26713", "#C13333", "#36541F"
RUST, APRICOT, SAGE, MARIGOLD, WINE = "#992610", "#E68035", "#BBC07D", "#FFAE56", "#8F263B"

LABELS = {
    "chai": dict(
        name="Chai", sub="MASALA", title="Chai Masala",
        tagline="A warming whole-spice blend for chai",
        notes="CARDAMOM · GINGER · CLOVE",
        panel=TEA_LEAVES, panel_ink=BISCUITS, panel_accent=MARIGOLD,
        front=BISCUITS, ink=TEA_LEAVES, accent=ORANGE_PEELS,
        frame=TEA_LEAVES, frame_line=MARIGOLD, window="#F3D7A4", jaali="#E9C68C",
        foliage="banana",
        about=("Green cardamom, dry ginger, cinnamon, clove and black pepper, roasted and "
               "stone-ground in small batches for a fragrant, full-bodied cup."),
        ingredients=("Dry ginger, green cardamom, cinnamon, black pepper, clove, fennel, nutmeg."),
        allergen="Packed in a facility that also handles nuts, mustard and sesame.",
        use=("Add 1/4 tsp per cup to simmering water, tea and milk. Brew 2-3 minutes, "
             "strain and sweeten to taste."),
    ),
    "chaat": dict(
        name="Chaat", sub="MASALA", title="Chaat Masala",
        tagline="A tangy, savoury finishing blend",
        notes="AMCHUR · CUMIN · BLACK SALT",
        panel=WINE, panel_ink=BISCUITS, panel_accent=MARIGOLD,
        front="#F3E1D6", ink=WINE, accent=ROSES,
        frame=WINE, frame_line=MARIGOLD, window="#E9C2B6", jaali="#DDA99B",
        foliage="palm",
        about=("Sun-dried mango, roasted cumin, black salt and mint, balanced to wake up "
               "fruit, chaat, salads and everyday snacks."),
        ingredients=("Dry mango powder, roasted cumin, black salt, coriander, iodised salt, "
                     "black pepper, dry mint, ginger, ajwain, asafoetida (with wheat flour)."),
        allergen="Contains wheat. Packed in a facility that also handles nuts, mustard and sesame.",
        use=("Sprinkle over fresh fruit, salads, chaat, raita, fries or a glass of "
             "lemonade."),
    ),
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def t(x, y, s, size, fill, family=F_SANS, weight=400, anchor="start", ls=0, italic=False):
    it = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}"{it}>{esc(s)}</text>')


def g(gid, body, extra=""):
    return f'<g id="{gid}"{extra}>\n{body}\n</g>'


def pts(p):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in p)


def qbez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])


def cbez(p0, p1, p2, p3, u):
    a = [(1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u ** 2, u ** 3]
    return (sum(c * p[0] for c, p in zip(a, (p0, p1, p2, p3))),
            sum(c * p[1] for c, p in zip(a, (p0, p1, p2, p3))))


# ---------------------------------------------------------------------------
# architecture: cusped jharokha arch + jaali balcony
# ---------------------------------------------------------------------------

def arch_path(cx, w, top, spring, base, cusps=0):
    """Ogee arch; with cusps > 0 the curve is broken into inward-bulging lobes."""
    L, R, h = cx - w / 2, cx + w / 2, spring - top
    segs = [((L, spring), (L, spring - h * .62), (cx - w * .16, top + h * .32), (cx, top)),
            ((cx, top), (cx + w * .16, top + h * .32), (R, spring - h * .62), (R, spring))]
    n = cusps if cusps else 24
    p = []
    for s in segs:
        p += [cbez(*s, i / n) for i in range(n)]
    p.append((R, spring))
    d = f"M {L:.1f},{base:.1f} L {p[0][0]:.1f},{p[0][1]:.1f}"
    for (x0, y0), (x1, y1) in zip(p, p[1:]):
        if cusps:
            r = math.hypot(x1 - x0, y1 - y0) * .58
            d += f" A {r:.1f} {r:.1f} 0 0 1 {x1:.1f},{y1:.1f}"
        else:
            d += f" L {x1:.1f},{y1:.1f}"
    return d + f" L {R:.1f},{base:.1f} Z"


def quatrefoil(x, y, d):
    rr = d * .8
    k = (d - math.sqrt(2 * rr * rr - d * d)) / 2
    a = f"A {rr:.2f} {rr:.2f} 0 1 1"
    return (f"M {x - k:.2f},{y - k:.2f} {a} {x + k:.2f},{y - k:.2f} {a} {x + k:.2f},{y + k:.2f} "
            f"{a} {x - k:.2f},{y + k:.2f} {a} {x - k:.2f},{y - k:.2f} Z")


def jaali(x0, y0, w, h, step, fill, line, cid):
    o = [f'<clipPath id="{cid}"><rect x="{x0}" y="{y0}" width="{w}" height="{h}"/></clipPath>',
         f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="{fill}"/>',
         f'<g clip-path="url(#{cid})" fill="none" stroke="{line}" stroke-width=".9">']
    row = 0
    y = y0 + step / 2
    while y < y0 + h + step:
        x = x0 + (step / 2 if row % 2 else 0)
        while x < x0 + w + step:
            o.append(f'<path d="{quatrefoil(x, y, step * .26)}"/>')
            x += step
        y += step / 2
        row += 1
    o.append("</g>")
    o.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="none" stroke="{line}" stroke-width="1.4"/>')
    return "".join(o)


# ---------------------------------------------------------------------------
# botanicals
# ---------------------------------------------------------------------------

def leaf_shape(x, y, L, wd, ang, fill, vein=None, outline=None, sw=.5):
    """Pointed lanceolate leaf from (x,y) along angle ang (degrees)."""
    d = (f"M 0,0 C {L * .25:.1f},{-wd:.1f} {L * .7:.1f},{-wd * .8:.1f} {L:.1f},0 "
         f"C {L * .7:.1f},{wd * .8:.1f} {L * .25:.1f},{wd:.1f} 0,0 Z")
    st = f' stroke="{outline}" stroke-width="{sw}"' if outline else ""
    o = f'<g transform="translate({x:.1f} {y:.1f}) rotate({ang:.1f})"><path d="{d}" fill="{fill}"{st}/>'
    if vein:
        o += f'<path d="M {L * .08:.1f},0 Q {L * .5:.1f},{-wd * .12:.1f} {L * .92:.1f},0" fill="none" stroke="{vein}" stroke-width=".55"/>'
    return o + "</g>"


def banana_leaf(bx, by, ang, L, wmax, bend, c_light, c_dark, line, seed):
    """Long banana leaf: midrib curve, two-tone halves, parallel veins, a few splits."""
    rng = random.Random(seed)
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    p0 = (bx, by)
    p2 = (bx + dx * L, by + dy * L)
    p1 = (bx + dx * L * .5 + nx * bend, by + dy * L * .5 + ny * bend)
    N = 40
    mid, left, right = [], [], []
    for i in range(N + 1):
        u = i / N
        px, py = qbez(p0, p1, p2, u)
        tx, ty = (2 * (1 - u) * (p1[0] - p0[0]) + 2 * u * (p2[0] - p1[0]),
                  2 * (1 - u) * (p1[1] - p0[1]) + 2 * u * (p2[1] - p1[1]))
        n = math.hypot(tx, ty)
        tx, ty = tx / n, ty / n
        w = wmax * (math.sin(math.pi * min(1, u * 1.05)) ** .7) * (1 - .15 * u) if u > .04 else wmax * .1
        mid.append((px, py, -ty, tx))
        left.append((px - ty * w, py + tx * w))
        right.append((px + ty * w * .92, py - tx * w * .92))
    tip = mid[-1][:2]
    o = [f'<path d="M {bx:.1f},{by:.1f} L {pts(left)} L {tip[0]:.1f},{tip[1]:.1f} Z" fill="{c_light}" '
         f'stroke="{line}" stroke-width=".7" stroke-linejoin="round"/>',
         f'<path d="M {bx:.1f},{by:.1f} L {pts(right)} L {tip[0]:.1f},{tip[1]:.1f} Z" fill="{c_dark}" '
         f'stroke="{line}" stroke-width=".7" stroke-linejoin="round"/>']
    # parallel veins sweeping toward the tip
    for side, edge, op in ((1, left, .45), (-1, right, .35)):
        for i in range(4, N - 2, 3):
            mx, my = mid[i][:2]
            ex, ey = edge[min(N, i + 3)]
            o.append(f'<path d="M {mx:.1f},{my:.1f} L {ex:.1f},{ey:.1f}" stroke="{line}" stroke-width=".45" opacity="{op}"/>')
    # splits in the blade
    for _ in range(3):
        i = rng.randint(10, N - 8)
        mx, my = mid[i][:2]
        ex, ey = left[min(N, i + 3)] if rng.random() > .5 else right[min(N, i + 3)]
        o.append(f'<path d="M {mx + (ex - mx) * .45:.1f},{my + (ey - my) * .45:.1f} L {ex:.1f},{ey:.1f}" '
                 f'stroke="{line}" stroke-width=".9"/>')
    o.append(f'<path d="M {bx:.1f},{by:.1f} Q {p1[0]:.1f},{p1[1]:.1f} {tip[0]:.1f},{tip[1]:.1f}" fill="none" '
             f'stroke="{line}" stroke-width="1.3" stroke-linecap="round"/>')
    return "".join(o)


def palm_frond(bx, by, ang, L, bend, c1, c2, line, seed, droop=1):
    """Palm frond: curved rachis with narrow, drooping leaflets on both sides."""
    rng = random.Random(seed)
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    p0, p2 = (bx, by), (bx + dx * L, by + dy * L)
    p1 = (bx + dx * L * .5 + nx * bend, by + dy * L * .5 + ny * bend)
    o = []
    n = 26
    for i in range(3, n + 1):
        u = i / n
        px, py = qbez(p0, p1, p2, u)
        tx, ty = (2 * (1 - u) * (p1[0] - p0[0]) + 2 * u * (p2[0] - p1[0]),
                  2 * (1 - u) * (p1[1] - p0[1]) + 2 * u * (p2[1] - p1[1]))
        base = math.degrees(math.atan2(ty, tx))
        ll = L * .42 * math.sin(math.pi * (.15 + .8 * u)) * (1 - .35 * u)
        for side in (-1, 1):
            ang_l = base + side * (38 + 10 * u) + droop * 18 * u * side * .3
            col = c1 if (i + (side > 0)) % 2 else c2
            o.append(leaf_shape(px, py, ll * rng.uniform(.88, 1.05), ll * .07 + 1.2, ang_l, col, None, line, .4))
    o.append(f'<path d="M {bx:.1f},{by:.1f} Q {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="none" '
             f'stroke="{line}" stroke-width="1.4" stroke-linecap="round"/>')
    return "".join(o)


def pot(cx, base, w, h, body, shade, rim, line):
    """Rounded terracotta pot as in the reference (rim, swelling belly, foot)."""
    top = base - h
    r = w / 2
    d = (f"M {cx - r * .78:.1f},{top + h * .16:.1f} "
         f"C {cx - r * 1.12:.1f},{top + h * .38:.1f} {cx - r * 1.05:.1f},{top + h * .82:.1f} {cx - r * .55:.1f},{base - h * .06:.1f} "
         f"L {cx - r * .5:.1f},{base:.1f} L {cx + r * .5:.1f},{base:.1f} L {cx + r * .55:.1f},{base - h * .06:.1f} "
         f"C {cx + r * 1.05:.1f},{top + h * .82:.1f} {cx + r * 1.12:.1f},{top + h * .38:.1f} {cx + r * .78:.1f},{top + h * .16:.1f} Z")
    o = [f'<path d="{d}" fill="{body}" stroke="{line}" stroke-width=".8"/>',
         # shading on the right of the belly
         f'<path d="M {cx + r * .3:.1f},{top + h * .2:.1f} C {cx + r * .95:.1f},{top + h * .4:.1f} '
         f'{cx + r * .85:.1f},{top + h * .8:.1f} {cx + r * .45:.1f},{base - h * .07:.1f} '
         f'L {cx + r * .55:.1f},{base - h * .06:.1f} C {cx + r * 1.05:.1f},{top + h * .82:.1f} '
         f'{cx + r * 1.12:.1f},{top + h * .38:.1f} {cx + r * .78:.1f},{top + h * .16:.1f} Z" fill="{shade}" opacity=".55"/>',
         f'<path d="M {cx - r * .62:.1f},{top + h * .3:.1f} C {cx - r * .8:.1f},{top + h * .45:.1f} '
         f'{cx - r * .78:.1f},{top + h * .62:.1f} {cx - r * .62:.1f},{top + h * .74:.1f}" fill="none" '
         f'stroke="{rim}" stroke-width="1.4" stroke-linecap="round" opacity=".8"/>',
         f'<rect x="{cx - r * .88:.1f}" y="{top:.1f}" width="{r * 1.76:.1f}" height="{h * .17:.1f}" rx="{h * .05:.1f}" '
         f'fill="{rim}" stroke="{line}" stroke-width=".8"/>',
         f'<line x1="{cx - r * .55:.1f}" y1="{top + h * .5:.1f}" x2="{cx + r * .55:.1f}" y2="{top + h * .5:.1f}" '
         f'stroke="{line}" stroke-width=".5" opacity=".5"/>']
    return "".join(o)


def pomegranate(x, y, r, body, dark, light, line):
    return (f'<g transform="translate({x:.1f} {y:.1f})">'
            f'<path d="M -2,{-r * .9:.1f} L -3.2,{-r - 2.6:.1f} L -1,{-r - 1.4:.1f} L 0,{-r - 3.2:.1f} '
            f'L 1,{-r - 1.4:.1f} L 3.2,{-r - 2.6:.1f} L 2,{-r * .9:.1f} Z" fill="{dark}" stroke="{line}" stroke-width=".4"/>'
            f'<circle r="{r:.1f}" fill="{body}" stroke="{line}" stroke-width=".6"/>'
            f'<path d="M {r * .2:.1f},{-r * .95:.1f} A {r:.1f} {r:.1f} 0 0 1 {r * .55:.1f},{r * .83:.1f} '
            f'A {r * 1.3:.1f} {r * 1.3:.1f} 0 0 0 {r * .2:.1f},{-r * .95:.1f} Z" fill="{dark}" opacity=".45"/>'
            f'<ellipse cx="{-r * .38:.1f}" cy="{-r * .35:.1f}" rx="{r * .22:.1f}" ry="{r * .32:.1f}" '
            f'transform="rotate(30 {-r * .38:.1f} {-r * .35:.1f})" fill="{light}" opacity=".7"/></g>')


def pomegranate_tree(cx, base, P):
    """Small potted pomegranate tree (reference image 4)."""
    rng = random.Random(53)
    trunk_top = base - 70
    o = [f'<path d="M {cx - 1.8:.1f},{base - 30} C {cx - 3},{base - 50} {cx + 2},{base - 60} {cx:.1f},{trunk_top} '
         f'L {cx + 2.4:.1f},{trunk_top} C {cx + 4},{base - 58} {cx + 1},{base - 48} {cx + 1.8:.1f},{base - 30} Z" '
         f'fill="{RUST}" stroke="{P["line"]}" stroke-width=".5"/>']
    for ex, ey in [(-30, -112), (28, -110), (-10, -132), (14, -128), (-38, -92), (36, -90), (0, -140)]:
        o.append(f'<path d="M {cx:.1f},{trunk_top + 6} Q {cx + ex * .4:.1f},{base + ey * .7:.1f} '
                 f'{cx + ex:.1f},{base + ey:.1f}" fill="none" stroke="{RUST}" stroke-width="1.3" stroke-linecap="round"/>')
    # canopy of small leaves
    ccx, ccy, rx, ry = cx, base - 108, 48, 36
    leaves = []
    for _ in range(170):
        a = rng.uniform(0, 2 * math.pi)
        rr = math.sqrt(rng.uniform(.05, 1))
        lx, ly = ccx + math.cos(a) * rx * rr, ccy + math.sin(a) * ry * rr
        ang = math.degrees(a) + rng.uniform(-40, 40)
        col = rng.choice([GREEN_TEA, "#56713A", "#7E8D4C", SAGE, "#9DA766"])
        leaves.append((ly, leaf_shape(lx, ly, rng.uniform(8.5, 12), rng.uniform(2.4, 3.2), ang, col, "#E5E3B8", P["line"], .3)))
    leaves.sort()
    o += [s for _, s in leaves]
    for fx, fy, fr in [(-24, -98, 6.4), (18, -118, 6), (-6, -84, 6.8), (30, -94, 5.6), (-30, -124, 5.2),
                       (6, -136, 5), (-14, -112, 5.6)]:
        o.append(pomegranate(cx + fx, base + fy, fr, ROSES, WINE, "#F2A08A", P["line"]))
    o.append(pot(cx, base, 52, 40, APRICOT, RUST, MARIGOLD, P["line"]))
    return g("Pomegranate_Tree", "".join(o))


def tea_flower(x, y, r, line):
    o = [f'<g transform="translate({x:.1f} {y:.1f})">']
    for k in range(5):
        o.append(f'<ellipse cx="0" cy="{-r * .55:.1f}" rx="{r * .42:.1f}" ry="{r * .55:.1f}" '
                 f'transform="rotate({k * 72})" fill="#FBF6E6" stroke="{line}" stroke-width=".35"/>')
    o.append(f'<circle r="{r * .32:.1f}" fill="{MARIGOLD}"/>')
    return "".join(o) + "</g>"


def tea_plant(cx, base, P):
    """Potted tea bush: woody stems, glossy leaves, camellia flowers, cardamom & star anise at its foot."""
    rng = random.Random(1953)
    o = []
    stems = [(-34, -118, -18), (-16, -142, -6), (2, -150, 4), (20, -138, 12), (36, -112, 20), (-42, -86, -24),
             (44, -84, 26)]
    leaves = []
    for ex, ey, lean in stems:
        p0 = (cx + ex * .1, base - 34)
        p2 = (cx + ex, base + ey)
        p1 = (cx + ex * .35 + lean * .4, base + ey * .55)
        o.append(f'<path d="M {p0[0]:.1f},{p0[1]:.1f} Q {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" '
                 f'fill="none" stroke="#6B4A22" stroke-width="1.1" stroke-linecap="round"/>')
        for i in range(2, 15):
            u = i / 14
            px, py = qbez(p0, p1, p2, u)
            dxx = 2 * (1 - u) * (p1[0] - p0[0]) + 2 * u * (p2[0] - p1[0])
            dyy = 2 * (1 - u) * (p1[1] - p0[1]) + 2 * u * (p2[1] - p1[1])
            base_a = math.degrees(math.atan2(dyy, dxx))
            side = 1 if i % 2 else -1
            col = rng.choice([GREEN_TEA, GREEN_TEA, "#4B6A2C", "#6F8240", SAGE])
            L = rng.uniform(12, 16) * (1.05 - .25 * u)
            leaves.append(leaf_shape(px, py, L, L * .3, base_a + side * rng.uniform(45, 65), col,
                                     "#D9DDA6", P["line"], .3))
        leaves.append(leaf_shape(p2[0], p2[1], 9, 2.6, math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])),
                                 SAGE, None, P["line"], .3))
    o += leaves
    for fx, fy in [(-26, -104), (14, -126), (30, -96), (-8, -122), (-38, -72)]:
        o.append(tea_flower(cx + fx, base + fy, 4.6, P["line"]))
    o.append(pot(cx, base, 54, 40, ORANGE_PEELS, RUST, MARIGOLD, P["line"]))
    return g("Tea_Plant", "".join(o))


# ---------------------------------------------------------------------------
# spice icons (line art) for the front
# ---------------------------------------------------------------------------

def icon(kind, x, y, col):
    s = f'fill="none" stroke="{col}" stroke-width=".9" stroke-linecap="round" stroke-linejoin="round"'
    if kind == "star_anise":
        o = []
        for k in range(8):
            o.append(f'<path d="M 0,0 C 1.6,-2 1.6,-5 0,-7.5 C -1.6,-5 -1.6,-2 0,0 Z" transform="rotate({k * 45})" {s}/>')
        return f'<g transform="translate({x} {y})">{"".join(o)}<circle r="1" fill="{col}"/></g>'
    if kind == "cardamom":
        return (f'<g transform="translate({x} {y}) rotate(-30)"><path d="M -7,0 C -4,-4.2 4,-4.2 7,0 C 4,4.2 -4,4.2 -7,0 Z" {s}/>'
                f'<path d="M -5,0 L 5,0 M -4,-1.8 L 4,-1.8 M -4,1.8 L 4,1.8" {s} stroke-width=".5"/>'
                f'<path d="M 7,0 L 9,-.5" {s}/></g>')
    if kind == "cinnamon":
        return (f'<g transform="translate({x} {y}) rotate(-30)"><rect x="-8" y="-2.4" width="16" height="4.8" rx="1" {s}/>'
                f'<path d="M -8,0 C -6,-2.4 -6,2.4 -8,0" {s}/><path d="M -4,-2.4 L -4,2.4 M 3,-2.4 L 3,2.4" {s} stroke-width=".5"/></g>')
    if kind == "mango":
        return (f'<g transform="translate({x} {y}) rotate(-20)"><path d="M -6,1 C -7,-5 2,-8 6,-3 C 9,1 5,7 0,6 C -3,5.6 -5.5,4 -6,1 Z" {s}/>'
                f'<path d="M -4.5,-3.5 C -6,-6.5 -4,-8 -1.5,-6.8" {s}/></g>')
    if kind == "cumin":
        o = []
        for k, (dx, dy, r) in enumerate([(-4, 1, -30), (1, -2, 20), (4, 3, -60)]):
            o.append(f'<g transform="translate({dx} {dy}) rotate({r})"><path d="M -4,0 C -2,-1.8 2,-1.8 4,0 C 2,1.8 -2,1.8 -4,0 Z" {s}/>'
                     f'<path d="M -3,0 L 3,0" {s} stroke-width=".4"/></g>')
        return f'<g transform="translate({x} {y})">{"".join(o)}</g>'
    # mint
    return (f'<g transform="translate({x} {y})"><path d="M 0,6 L 0,-2" {s}/>'
            f'<path d="M 0,0 C -6,-1 -7,-5 -5,-8 C -2,-6 0,-4 0,0 Z" {s}/>'
            f'<path d="M 0,-2 C 6,-3 7,-7 5,-10 C 2,-8 0,-6 0,-2 Z" {s}/></g>')


ICONS = {"chai": ["cardamom", "star_anise", "cinnamon"], "chaat": ["mango", "cumin", "mint"]}


# ---------------------------------------------------------------------------
# panels
# ---------------------------------------------------------------------------

def para(x, y, s, n, size=8.6, lh=11.4, fill=BISCUITS, weight=400, family=F_SANS, italic=False):
    lines = wrap(s, n)
    return "".join(t(x, y + i * lh, l, size, fill, family, weight, italic=italic) for i, l in enumerate(lines)), \
        y + len(lines) * lh


def heading(x, y, s, col):
    return t(x, y, s, 8.6, col, F_SANS, 600, ls=2)


def panel_frame(x0, x1, L):
    return (f'<rect x="{x0}" y="0" width="{x1 - x0}" height="{H}" fill="{L["panel"]}"/>'
            f'<rect x="{x0 + 8}" y="8" width="{x1 - x0 - 16}" height="{H - 16}" fill="none" '
            f'stroke="{L["panel_accent"]}" stroke-width=".6" opacity=".7"/>')


def left_panel(L):
    x, c, a = 20, L["panel_ink"], L["panel_accent"]
    o = [panel_frame(0, P0, L)]
    o.append(heading(x, 30, "THE BLEND", a))
    txt, y = para(x, 44, L["about"], 30, size=11, lh=12.6, family=F_SERIF, italic=True, weight=500)
    o.append(txt)
    o.append(heading(x, y + 12, "INGREDIENTS", a))
    txt, y = para(x, y + 25, L["ingredients"], 31)
    o.append(txt)
    o.append(heading(x, y + 12, "HOW TO USE", a))
    txt, y = para(x, y + 25, L["use"], 31)
    o.append(txt)
    o.append(f'<line x1="{x}" y1="{H - 30}" x2="{P0 - 20}" y2="{H - 30}" stroke="{a}" stroke-width=".5" opacity=".7"/>')
    o.append(veg_mark(x, H - 26, 13))
    o.append(t(x + 20, H - 16, "100% VEGETARIAN", 7.8, c, F_SANS, 600, ls=1.2))
    return g("Left_Info_Panel", "\n".join(o))


def right_panel(L, seed):
    x, c, a = P1 + 20, L["panel_ink"], L["panel_accent"]
    o = [panel_frame(P1, W, L)]
    o.append(heading(x, 30, "STORAGE", a))
    txt, y = para(x, 44, "Store in a cool, dry place. Close the lid tightly after use.", 31)
    o.append(txt)
    o.append(heading(x, y + 10, "ALLERGEN", a))
    txt, y = para(x, y + 23, L["allergen"], 31)
    o.append(txt)
    txt, y = para(x, y + 8, "Mfd. & packed by Ashvena Foods Pvt. Ltd., [Address], [City] - [PIN], India. "
                            "FSSAI Lic. No. XXXXXXXXXXXXXX", 33, size=7.6, lh=10)
    o.append(txt)
    txt, y = para(x, y + 3, "Batch XXXX · Mfd XX/XX · Best before 12 months from mfg. · "
                            "MRP ₹ XXX (incl. of all taxes)", 33, size=7.6, lh=10, weight=600)
    o.append(txt)
    o.append(barcode(x + 6, H - 56, 100, 26, seed))
    return g("Right_Info_Panel", "\n".join(o))


def front_panel(key, L):
    cid = f"{key}_front_clip"
    o = [f'<clipPath id="{cid}"><rect x="{P0}" y="0" width="{P1 - P0}" height="{H}"/></clipPath>',
         f'<rect x="{P0}" y="0" width="{P1 - P0}" height="{H}" fill="{L["front"]}"/>']

    # background foliage, behind the arch and peeking in from the panel edges
    fol = []
    if L["foliage"] == "banana":
        fol.append(banana_leaf(P0 - 4, H + 6, -62, 150, 22, 18, "#D3D49C", SAGE, "#8C7A3E", 3))
        fol.append(banana_leaf(P0 + 30, H + 10, -78, 120, 18, -10, SAGE, "#9DA766", "#8C7A3E", 5))
        fol.append(banana_leaf(P0 - 8, -14, 48, 96, 15, -10, "#D3D49C", SAGE, "#8C7A3E", 7))
        fol.append(banana_leaf(P1 + 8, H + 12, -152, 62, 11, 6, "#D3D49C", SAGE, "#8C7A3E", 9))
        fol.append(banana_leaf(P1 + 8, -10, 158, 52, 10, -6, "#D3D49C", SAGE, "#8C7A3E", 15))
    else:
        fol.append(palm_frond(P0 - 6, H + 4, -58, 170, 26, SAGE, "#9DA766", "#7F7A45", 11))
        fol.append(palm_frond(P0 - 8, -12, 46, 110, -14, SAGE, "#9DA766", "#7F7A45", 19))
        fol.append(palm_frond(P1 + 10, H + 14, -150, 56, 8, SAGE, "#9DA766", "#7F7A45", 13))
        fol.append(palm_frond(P1 + 8, -8, 160, 58, -6, SAGE, "#9DA766", "#7F7A45", 17))
    o.append(g("Foliage", f'<g clip-path="url(#{cid})">{"".join(fol)}</g>'))

    # jharokha arch
    ax, aw = 262, 128
    arch = [f'<path d="{arch_path(ax, aw + 14, 14, 92, 262)}" fill="{L["front"]}"/>',
            f'<path d="{arch_path(ax, aw, 22, 96, 258)}" fill="{L["frame"]}"/>',
            f'<path d="{arch_path(ax, aw - 14, 31, 101, 252, cusps=4)}" fill="none" stroke="{L["frame_line"]}" '
            f'stroke-width=".7"/>',
            f'<path d="{arch_path(ax, aw - 26, 40, 106, 216, cusps=4)}" fill="{L["window"]}"/>']
    # small finial at the apex
    arch.append(f'<path d="M {ax},{4} C {ax + 4},{10} {ax + 4},{14} {ax},{18} C {ax - 4},{14} {ax - 4},{10} {ax},{4} Z" '
                f'fill="{L["frame"]}"/><circle cx="{ax}" cy="{20}" r="2.4" fill="{L["frame"]}"/>')
    o.append(g("Jharokha_Arch", "".join(arch)))

    # plant inside the window, clipped to the arch opening
    wid = f"{key}_window_clip"
    plant = tea_plant(ax, 214, {"line": "#6B4A22"}) if key == "chai" else pomegranate_tree(ax, 214, {"line": "#6B3A2A"})
    o.append(f'<clipPath id="{wid}"><path d="{arch_path(ax, aw - 26, 40, 106, 216, cusps=4)}"/></clipPath>')
    o.append(g("Illustration", f'<g clip-path="url(#{wid})">{plant}</g>'))

    # jaali balcony + ledge
    jw = aw - 18
    o.append(g("Jaali_Balcony",
               jaali(ax - jw / 2, 216, jw, 32, 14, L["jaali"], L["frame"], f"{key}_jaali_clip")
               + f'<rect x="{ax - jw / 2 - 5}" y="212" width="{jw + 10}" height="5" fill="{L["frame_line"]}" '
                 f'stroke="{L["frame"]}" stroke-width=".6"/>'))

    # typography block
    cx = 418
    ty = [t(cx, 46, "ASHVENA", 19, L["ink"], F_BRAND, 600, "middle", 7),
          f'<line x1="{cx - 56}" y1="58" x2="{cx - 30}" y2="58" stroke="{L["accent"]}" stroke-width=".7"/>',
          t(cx, 61, "EST. 1953", 8, L["ink"], F_SANS, 600, "middle", 2.4),
          f'<line x1="{cx + 30}" y1="58" x2="{cx + 56}" y2="58" stroke="{L["accent"]}" stroke-width=".7"/>',
          t(cx, 124, L["name"], 66, L["ink"], F_SERIF, 500, "middle", 0, italic=True),
          t(cx + 4, 150, L["sub"], 15, L["accent"], F_SANS, 500, "middle", 10),
          t(cx, 176, L["tagline"], 12.5, L["ink"], F_SERIF, 500, "middle", 0, italic=True)]
    for i, k in enumerate(ICONS[key]):
        ty.append(icon(k, cx - 36 + i * 36, 196, L["ink"]))
    ty.append(t(cx, 222, L["notes"], 8, L["ink"], F_SANS, 600, "middle", 1.6))
    ty.append(f'<line x1="{cx - 70}" y1="236" x2="{cx + 70}" y2="236" stroke="{L["accent"]}" stroke-width=".6"/>')
    ty.append(t(cx, 254, "NET WT. 100 g", 8.6, L["ink"], F_SANS, 600, "middle", 1.6))
    o.append(g("Product_Typography", "".join(ty)))
    return g("Front_Panel", "\n".join(o))


def label(key, seed):
    L = LABELS[key]
    body = [g("Background", f'<rect width="{W}" height="{H}" fill="{L["front"]}"/>'),
            front_panel(key, L), left_panel(L), right_panel(L, seed)]
    return "\n".join(body)


# ---------------------------------------------------------------------------
# documents
# ---------------------------------------------------------------------------

def crop_marks(x, y, w, h):
    o = []
    for cx, cy, sx, sy in [(x, y, -1, -1), (x + w, y, 1, -1), (x, y + h, -1, 1), (x + w, y + h, 1, 1)]:
        o.append(f'<line x1="{cx + sx * 4}" y1="{cy}" x2="{cx + sx * 24}" y2="{cy}" stroke="#000" stroke-width=".4"/>')
        o.append(f'<line x1="{cx}" y1="{cy + sy * 4}" x2="{cx}" y2="{cy + sy * 24}" stroke="#000" stroke-width=".4"/>')
    return "".join(o)


def sheet():
    o = [g("Sheet", f'<rect width="{SHEET_W}" height="{SHEET_H}" fill="#ffffff"/>')]
    for i, key in enumerate(LABELS):
        y = M + i * (H + M)
        L = LABELS[key]
        o.append(g(f"{L['title'].replace(' ', '_')}_Label_171x70mm", label(key, 31 + i),
                   f' transform="translate({M} {y})"'))
        o.append(g(f"{L['title'].replace(' ', '_')}_Crop_Marks", crop_marks(M, y, W, H)))
        o.append(t(M + 26, y - 8, f"ASHVENA {L['title'].upper()}  ·  WRAP LABEL 171 × 70 mm  ·  "
                                  f"44 | 83 | 44 mm", 7, "#777", F_SANS, 500, ls=1))
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHEET_W / 4:.0f}mm" height="{SHEET_H / 4:.0f}mm" '
            f'viewBox="0 0 {SHEET_W} {SHEET_H}">\n<title>Ashvena Chai Masala and Chaat Masala labels</title>\n'
            + "\n".join(o) + "\n</svg>\n")


def single(key, seed):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W / 4:.1f}mm" height="{H / 4:.1f}mm" '
            f'viewBox="0 0 {W} {H}" style="display:block">{label(key, seed)}</svg>')


def render(svg_path):
    """PNG preview, PDF-compatible .ai sheet and a 2-page print PDF (needs playwright + Chromium)."""
    import glob
    from playwright.sync_api import sync_playwright

    kw = {}
    exe = glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome")
    if exe:
        kw["executable_path"] = exe[0]
    base = svg_path[:-4]
    src = open(svg_path).read().split("?>", 1)[1]
    with sync_playwright() as p:
        b = p.chromium.launch(**kw)
        pg = b.new_page(viewport={"width": SHEET_W, "height": SHEET_H}, device_scale_factor=3)
        px = re.sub(r'width="[^"]+mm" height="[^"]+mm"', f'width="{SHEET_W}" height="{SHEET_H}"', src, count=1)
        pg.set_content(f"<html><body style='margin:0'>{px.replace('<svg ', '<svg style=\"display:block\" ', 1)}</body></html>")
        pg.evaluate("document.fonts.ready")
        pg.screenshot(path=base + ".png", clip={"x": 0, "y": 0, "width": SHEET_W, "height": SHEET_H})
        zero = {"top": "0", "right": "0", "bottom": "0", "left": "0"}
        pg.set_content(f"<html><body style='margin:0'>{src.replace('<svg ', '<svg style=\"display:block\" ', 1)}</body></html>")
        pg.evaluate("document.fonts.ready")
        pg.pdf(path=base + ".ai", width=f"{SHEET_W / 4}mm", height=f"{SHEET_H / 4}mm",
               print_background=True, margin=zero)
        pages = "".join(f"<div style='page-break-after:always'>{single(k, 31 + i)}</div>"
                        for i, k in enumerate(LABELS))
        pg.set_content(f"<html><body style='margin:0'>{pages}</body></html>")
        pg.evaluate("document.fonts.ready")
        pg.pdf(path=base + "_print.pdf", width=f"{W / 4}mm", height=f"{H / 4}mm",
               print_background=True, margin=zero)
        b.close()


def main():
    os.makedirs(ROOT, exist_ok=True)
    p = os.path.join(ROOT, "ashvena-masala-labels.svg")
    open(p, "w").write(sheet())
    print(os.path.relpath(p))
    try:
        render(p)
        print("rendered .png, .ai and _print.pdf")
    except ImportError:
        print("playwright not installed: skipped PNG/PDF/AI rendering")


if __name__ == "__main__":
    main()
