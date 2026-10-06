#!/usr/bin/env python3
"""Ashvena box belts, v3 "Heritage" - rebuilt to the Diwali 2026 style guide.

Same palace-garden bays as v1/v2 (generate_belts.py), restyled to the
house look: gold-ink line work over soft watercolour washes, a brass bowl
hero under a faint arch and palm, the Ashvena logo in its original
colours, Fraunces / Bricolage Grotesque / Lobster type, the candy-line
strip and the "Heirloom, remixed." sign-off. Uses the client palettes.

Artboard: 297.04 x 74.8 mm (4 px = 1 mm).
Output: packaging/F-palace-garden/ashvena-<flavour>-v3_belt.svg
"""
import math
import os
import random

import generate_belts as gb
from generate_belts import BAYS, SOFT_GREENS, arch_d, dark, esc, g, light, mango, mix, palm, round_fruit, small_leaf

ROOT = gb.ROOT
W_MM, H_MM = gb.W_MM, gb.H_MM
W, H = gb.W, gb.H
BAND = 18
BY, BH = BAND, H - 2 * BAND
TW = 400
TX = (W - TW) / 2
SW = TX / 3

F_SERIF = "Fraunces, Georgia, serif"
F_SANS = "'Bricolage Grotesque', Helvetica, Arial, sans-serif"
F_SCRIPT = "Lobster, 'Brush Script MT', cursive"
F_DEVA = "'Tiro Devanagari Hindi', 'Noto Serif Devanagari', serif"

INK = "#a07c34"                    # gold ink line work
LOGO_RED, LOGO_DARK = "#c4161c", "#2b2220"

STRIP = "MADE WITH REAL FRUIT  ·  73-YEAR-OLD RECIPE  ·  NO ADDED COLOUR"
SIGNOFF = "Heirloom, remixed.  ·  Since 1953"

# v3 recolours the shared bay artwork: dark outlines -> gold ink, foliage -> sage
INK_SWAP = dict(SOFT_GREENS, **{"#4a2a14": INK, "#3d4f2a": "#8a7a3a"})

FLAVOURS = {
    "aam-papad": dict(
        gb.FLAVOURS["aam-papad-v2"], name_size=48, ink="#680b1c",
        field="#fdf5dc", wash="#efdc6a", bowl="papad"),
    "fruit-cocktail": dict(
        gb.FLAVOURS["fruit-cocktail-v2"], name_size=42, ink="#6e2a36",
        field="#f0ead2", wash="#bb7881", bowl="cocktail"),
}


def t(x, y, s, size, fill, family=F_SANS, weight=400, anchor="middle", ls=0, italic=False, extra=""):
    it = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}"{it}{extra}>{esc(s)}</text>')


# ---------------------------------------------------------------------------
# brass bowl hero
# ---------------------------------------------------------------------------

def brass_bowl(cx, rim, w, depth):
    """Wide brass urli on a short foot; returns (back, front) layers so a heap can sit between."""
    L, R = cx - w / 2, cx + w / 2
    back = (f'<ellipse cx="{cx:.1f}" cy="{rim:.1f}" rx="{w / 2:.1f}" ry="{w * .09:.1f}" fill="#6e4f1c" '
            f'stroke="{INK}" stroke-width=".8"/>')
    body = (f"M {L:.1f},{rim:.1f} C {L + w * .04:.1f},{rim + depth * .9:.1f} {cx - w * .22:.1f},{rim + depth:.1f} "
            f"{cx:.1f},{rim + depth:.1f} C {cx + w * .22:.1f},{rim + depth:.1f} {R - w * .04:.1f},{rim + depth * .9:.1f} "
            f"{R:.1f},{rim:.1f} A {w / 2:.1f} {w * .09:.1f} 0 0 1 {L:.1f},{rim:.1f} Z")
    fy = rim + depth
    front = [
        # foot
        f'<path d="M {cx - w * .14:.1f},{fy - 2:.1f} L {cx - w * .2:.1f},{fy + 12:.1f} L {cx + w * .2:.1f},{fy + 12:.1f} '
        f'L {cx + w * .14:.1f},{fy - 2:.1f} Z" fill="url(#brassG)" stroke="{INK}" stroke-width=".9"/>',
        f'<rect x="{cx - w * .24:.1f}" y="{fy + 11:.1f}" width="{w * .48:.1f}" height="5" rx="2" fill="url(#brassG)" '
        f'stroke="{INK}" stroke-width=".9"/>',
        f'<path d="{body}" fill="url(#brassG)" stroke="{INK}" stroke-width="1"/>',
        # rim lip, engraved band, highlight
        f'<path d="M {L:.1f},{rim:.1f} A {w / 2:.1f} {w * .09:.1f} 0 0 0 {R:.1f},{rim:.1f}" fill="none" '
        f'stroke="#f6e3a4" stroke-width="2.4"/>',
        f'<path d="M {L + w * .06:.1f},{rim + depth * .32:.1f} Q {cx:.1f},{rim + depth * .62:.1f} {R - w * .06:.1f},{rim + depth * .32:.1f}" '
        f'fill="none" stroke="{INK}" stroke-width=".7" stroke-dasharray="1.2 2.2"/>',
        f'<path d="M {L + w * .1:.1f},{rim + depth * .44:.1f} Q {cx:.1f},{rim + depth * .76:.1f} {R - w * .1:.1f},{rim + depth * .44:.1f}" '
        f'fill="none" stroke="{INK}" stroke-width=".6"/>',
        f'<path d="M {L + w * .12:.1f},{rim + depth * .2:.1f} Q {L + w * .18:.1f},{rim + depth * .6:.1f} {cx - w * .2:.1f},{rim + depth * .78:.1f}" '
        f'fill="none" stroke="#fff6d0" stroke-width="2.2" stroke-linecap="round" opacity=".55"/>',
    ]
    return back, "".join(front)


def papad_roll(x, y, s, r):
    """Rolled aam papad (fruit-leather scroll)."""
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({r:.1f}) scale({s})">'
            f'<rect x="-14" y="-5" width="28" height="10" rx="5" fill="url(#papadG)" stroke="{INK}" stroke-width=".7"/>'
            f'<ellipse cx="14" cy="0" rx="3" ry="5" fill="#d9741a" stroke="{INK}" stroke-width=".6"/>'
            f'<path d="M 14,0 m -1.4,0 a 1.4,2.4 0 1,0 2.8,0 a 1.4,2.4 0 1,0 -2.8,0" fill="none" stroke="#ffcf6a" stroke-width=".6"/>'
            f'<path d="M -11,-2.5 L 10,-2.5" stroke="#fff3b8" stroke-width="1" stroke-linecap="round" opacity=".7"/></g>')


def papad_square(x, y, s, r):
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({r:.1f}) scale({s})">'
            f'<path d="M -12,-8 Q 0,-10 12,-8 L 11,8 Q 0,10 -11,8 Z" fill="url(#papadG)" stroke="{INK}" stroke-width=".7"/>'
            f'<path d="M -8,-4 Q 0,-5 8,-4 M -7,1 Q 0,0 7,1" stroke="#ffd98a" stroke-width=".7" fill="none" opacity=".8"/></g>')


def chew(x, y, s, r, col):
    """Glossy fruit-candy cube for the cocktail heap."""
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({r:.1f}) scale({s})">'
            f'<rect x="-7" y="-6" width="14" height="12" rx="3.5" fill="{col}" stroke="{INK}" stroke-width=".7"/>'
            f'<rect x="-7" y="-6" width="14" height="5" rx="2.5" fill="{light(col, .35)}"/>'
            f'<circle cx="-3.5" cy="-3.5" r="1.4" fill="#fff" opacity=".75"/></g>')


def heap(kind, cx, rim, w, seed):
    rng = random.Random(seed)
    o = []
    rows = [(rim - 2, .9, 10), (rim - 12, .76, 8), (rim - 22, .58, 6), (rim - 31, .38, 4), (rim - 39, .16, 2)]
    for y, span, n in rows:
        for i in range(n):
            x = cx - w * span / 2 + w * span * (i + .5) / n + rng.uniform(-3, 3)
            yy = y + rng.uniform(-2, 2)
            if kind == "papad":
                o.append(papad_roll(x, yy, .85, rng.uniform(-35, 35)) if (i + n) % 2 else
                         papad_square(x, yy, .8, rng.uniform(-25, 25)))
            else:
                col = rng.choice(["#9e4554", "#bb7881", "#dbb44f", "#b9b75f", "#e0838f", "#f0c64e"])
                o.append(chew(x, yy, .95, rng.uniform(-30, 30), col))
    return "".join(o)


# ---------------------------------------------------------------------------
# palette fruits around the bowl
# ---------------------------------------------------------------------------

def citrus_slice(x, y, r, rind, flesh, pith="#fbf3d0"):
    o = [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{rind}" stroke="{INK}" stroke-width=".8"/>',
         f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * .84:.1f}" fill="{pith}"/>']
    for k in range(9):
        a0, a1 = math.radians(k * 40 + 4), math.radians(k * 40 + 36)
        rr = r * .76
        o.append(f'<path d="M {x:.1f},{y:.1f} L {x + rr * math.cos(a0):.1f},{y + rr * math.sin(a0):.1f} '
                 f'A {rr:.1f} {rr:.1f} 0 0 1 {x + rr * math.cos(a1):.1f},{y + rr * math.sin(a1):.1f} Z" fill="{flesh}"/>')
    return "".join(o)


def raspberry(x, y, s):
    o = [f'<g transform="translate({x:.1f} {y:.1f}) scale({s})">']
    for dx, dy in [(-3, -4), (0, -5), (3, -4), (-4, -1), (-1, -1), (2, -1), (4, 0), (-3, 2), (0, 2), (3, 2), (-1, 5), (2, 4)]:
        o.append(f'<circle cx="{dx}" cy="{dy}" r="2.1" fill="#b23a52" stroke="{INK}" stroke-width=".35"/>'
                 f'<circle cx="{dx - .6}" cy="{dy - .6}" r=".6" fill="#ffd0da"/>')
    o.append(f'<path d="M -3,-7 L 0,-5.5 L 3,-7 L 1,-4.5 L -1,-4.5 Z" fill="#7f9e52" stroke="{INK}" stroke-width=".4"/></g>')
    return "".join(o)


def side_fruit(kind, cx, base):
    if kind == "papad":
        return (small_leaf(cx - 122, base - 24, 1.3, -150) + small_leaf(cx + 120, base - 24, 1.3, -30)
                + mango(cx - 108, base - 11, 1.65, -20) + mango(cx - 134, base - 5, 1.45, 15)
                + mango(cx + 110, base - 10, 1.65, 22) + papad_roll(cx + 138, base - 5, 1.15, -12))
    return (citrus_slice(cx - 122, base - 16, 16, "#c2c24a", "#dfe08c")              # lime
            + raspberry(cx - 96, base - 6, 1.6) + raspberry(cx - 146, base - 5, 1.35)
            + citrus_slice(cx + 116, base - 17, 17, "#d9a03e", "#f0d36a")             # lemon
            + citrus_slice(cx + 146, base - 8, 13, "#c96a74", "#e89aa0"))             # pink grapefruit


# ---------------------------------------------------------------------------
# logo (placeholder in the original colours)
# ---------------------------------------------------------------------------

def logo(cx, y):
    """Stacked Ashvena logo: red mark, dark name, red year. Replace with Ashvena logo final.pdf."""
    return g("Logo_PLACEHOLDER_replace_with_Ashvena_logo_final",
             t(cx, y + 26, "अ", 30, LOGO_RED, F_DEVA, 400)
             + t(cx, y + 46, "Ashvena", 21, LOGO_DARK, F_SERIF, 600, ls=.6)
             + t(cx, y + 57, "1953", 8.5, LOGO_RED, F_SANS, 700, ls=2.5))


# ---------------------------------------------------------------------------
# panels
# ---------------------------------------------------------------------------

def bay(i, x, kind, col, f):
    uid = f"hb{i}"
    body = BAYS[kind](SW, BH, col, f, 11 + i * 7)
    return g(f"Bay_{i + 1}_{kind}",
             f'<clipPath id="{uid}"><rect width="{SW:.2f}" height="{BH:.2f}"/></clipPath>'
             f'<radialGradient id="{uid}bg" cx=".5" cy=".38" r=".8"><stop offset="0" stop-color="{light(col, .32)}"/>'
             f'<stop offset="1" stop-color="{light(col, .08)}"/></radialGradient>'
             f'<g clip-path="url(#{uid})"><rect width="{SW:.2f}" height="{BH:.2f}" fill="url(#{uid}bg)"/>{body}</g>',
             f' transform="translate({x:.2f} {BY})"')


def title_panel(f):
    cx = W / 2
    o = [f'<rect x="{TX:.2f}" y="{BY}" width="{TW}" height="{BH:.2f}" fill="{f["field"]}"/>',
         f'<clipPath id="tclip"><rect x="{TX:.2f}" y="{BY}" width="{TW}" height="{BH:.2f}"/></clipPath>',
         '<g clip-path="url(#tclip)">',
         # faint palms behind
         f'<g opacity=".16">{palm(TX + 30, H, TX + 56, BY + 60, 1.05, 5, lean=-20)}'
         f'{palm(TX + TW - 30, H, TX + TW - 56, BY + 70, .95, 6, lean=20)}</g>',
         # faint watercolour arch / niche
         f'<path d="{arch_d(cx, BY + 6, 286, BY + 92, H)}" fill="{f["wash"]}" opacity=".32"/>',
         f'<path d="{arch_d(cx, BY + 14, 268, BY + 98, H, cusps=5)}" fill="none" stroke="{INK}" stroke-width="1" opacity=".75"/>',
         f'<path d="{arch_d(cx, BY + 6, 286, BY + 92, H)}" fill="none" stroke="{INK}" stroke-width=".6" opacity=".6"/>',
         "</g>"]
    o.append(logo(cx, BY + 6))
    o.append(g("Product_Name", t(cx, BY + 116, f["name"], f["name_size"], f["head"], F_SCRIPT, 400, ls=.4)))
    o.append(g("Signoff", t(cx, BY + 132, SIGNOFF, 8.5, f["ink"], F_SERIF, 400, italic=True, ls=.4)))
    # bowl hero
    rim, bw = BY + 184, 176
    back, front = brass_bowl(cx, rim, bw, 48)
    o.append(g("Brass_Bowl_Hero", back + heap(f["bowl"], cx, rim, bw, 7) + front))
    o.append(g("Bowl_Fruit", side_fruit(f["bowl"], cx, H - BAND - 8)))
    o.append(g("Veg_Mark", f'<rect x="{TX + 14:.1f}" y="{BY + 10}" width="12" height="12" fill="#fff" stroke="#138a36" stroke-width="1.2"/>'
                           f'<circle cx="{TX + 20:.1f}" cy="{BY + 16}" r="3.2" fill="#138a36"/>'))
    o.append(g("Net_Wt_PLACEHOLDER", t(TX + TW - 14, BY + 20, "NET WT. XXX g", 7.5, f["ink"], F_SANS, 700, "end", ls=1)))
    return g("Title_Panel", "\n".join(o))


def top_band(f):
    o = [f'<rect width="{W:.2f}" height="{BAND}" fill="{f["band"]}"/>',
         f'<line x1="0" y1="{BAND - .8}" x2="{W:.2f}" y2="{BAND - .8}" stroke="{gb.GOLD}" stroke-width="1.6"/>']
    step = 16
    for i in range(int(W / step) + 1):
        x = i * step + step / 2
        o.append(f'<path d="M {x:.1f},{BAND / 2 - 4:.1f} l 4,4 l -4,4 l -4,-4 Z" fill="{gb.GOLD}"/>')
        o.append(f'<circle cx="{x + step / 2:.1f}" cy="{BAND / 2:.1f}" r="1.8" fill="{f["dots"][i % len(f["dots"])]}"/>')
    return "".join(o)


def strip_band(f):
    """Bottom band carries the candy-line promise, repeated round the belt."""
    y = H - BAND
    o = [f'<rect x="0" y="{y:.2f}" width="{W:.2f}" height="{BAND}" fill="{f["band"]}"/>',
         f'<line x1="0" y1="{y + .8:.2f}" x2="{W:.2f}" y2="{y + .8:.2f}" stroke="{gb.GOLD}" stroke-width="1.6"/>']
    span = W / 3
    for k in range(3):
        cx = span * (k + .5)
        o.append(t(cx, y + 12.4, STRIP, 7.2, f["field"], F_SANS, 700, ls=1.2,
                   extra=f' textLength="{span - 40:.1f}" lengthAdjust="spacingAndGlyphs"'))
        o.append(f'<path d="M {span * (k + 1):.1f},{y + 5.5:.1f} l 4,4 l -4,4 l -4,-4 Z" fill="{gb.GOLD}"/>')
    return "".join(o)


TEXTURE = """
<filter id="paper" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="4"/>
  <feColorMatrix values="0 0 0 0 .42  0 0 0 0 .32  0 0 0 0 .18  0 0 0 .55 -.18"/>
</filter>
<filter id="wash" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".012 .02" numOctaves="3" seed="9"/>
  <feColorMatrix values="0 0 0 0 .45  0 0 0 0 .3  0 0 0 0 .2  0 0 0 .9 -.38"/>
</filter>
<linearGradient id="brassG" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#8a6420"/><stop offset=".22" stop-color="#d8b056"/><stop offset=".42" stop-color="#f3dc8a"/>
  <stop offset=".65" stop-color="#c9a14a"/><stop offset="1" stop-color="#7a5418"/>
</linearGradient>
"""


def belt(key):
    f = FLAVOURS[key]
    gb.CREAM, gb.GOLD = f["cream"], f["gold"]
    o = [g("Background", f'<rect width="{W:.2f}" height="{H:.2f}" fill="{f["band"]}"/>')]
    for i, (kind, col) in enumerate(f["bays"][:3]):
        o.append(bay(i, SW * i, kind, col, f))
    for i, (kind, col) in enumerate(f["bays"][3:]):
        o.append(bay(i + 3, TX + TW + SW * i, kind, col, f))
    o.append(g("Pillars", "".join(
        f'<rect x="{x - 2:.2f}" y="{BY}" width="4" height="{BH:.2f}" fill="{gb.CREAM}" stroke="{INK}" stroke-width=".6"/>'
        for x in [SW, 2 * SW, TX, TX + TW, TX + TW + SW, TX + TW + 2 * SW])))
    o.append(title_panel(f))
    # watercolour mottling + paper grain over the artwork (delete this group for flat colour)
    o.append(g("Texture_Overlay",
               f'<rect y="{BY}" width="{W:.2f}" height="{BH:.2f}" filter="url(#wash)" opacity=".5" style="mix-blend-mode:multiply"/>'
               f'<rect width="{W:.2f}" height="{H:.2f}" filter="url(#paper)" opacity=".45" style="mix-blend-mode:multiply"/>'))
    o.append(g("Border_Bands", top_band(f) + strip_band(f)))
    doc = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_MM}mm" height="{H_MM}mm" viewBox="0 0 {W:.2f} {H:.2f}">\n'
           f'<title>Ashvena {esc(f["name"])} - box belt (heritage)</title>\n<defs>{gb.DEFS}{TEXTURE}</defs>\n'
           + "\n".join(o) + "\n</svg>\n")
    for v1, v2 in INK_SWAP.items():
        doc = doc.replace(v1, v2)
    return doc


def main():
    os.makedirs(ROOT, exist_ok=True)
    for key in FLAVOURS:
        p = os.path.join(ROOT, f"ashvena-{key}-v3_belt.svg")
        open(p, "w").write(belt(key))
        print(os.path.relpath(p, os.path.join(ROOT, "..", "..")))


if __name__ == "__main__":
    main()
