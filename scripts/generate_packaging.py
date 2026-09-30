#!/usr/bin/env python3
"""Ashvena cashew packaging generator.

Builds layered, Illustrator-editable SVG dielines for the Ashvena
Peri Peri and Kadi Patta cashew cartons in three design directions:

  A  Heritage Ivory  - cream carton, botanical illustration + gold window
  B  Noir Royale     - black & gold carton, engraved-style botanicals
  C  Spice Coast     - bright illustrated scene, bowl of cashews

Each SVG is one flat artboard: side panel (45 mm) + front panel (120 mm),
170 mm tall, drawn at 4 px per mm. Direction A also gets a back panel.
Text is kept live (Cinzel / Cormorant Garamond / Montserrat, all free
Google Fonts), and every region is a named group so it shows up as a
layer in Illustrator.

Usage:  python3 scripts/generate_packaging.py
"""
import math
import os
import random

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packaging")

SIDE, FRONT, H = 180, 480, 680          # px (4 px = 1 mm)
FX = SIDE                                # front panel x offset

F_DISPLAY = "Cinzel, 'Trajan Pro', serif"
F_SERIF = "'Cormorant Garamond', Garamond, Georgia, serif"
F_SANS = "Montserrat, Gotham, Helvetica, Arial, sans-serif"

INK = "#3a2a1c"
GOLD = "#b8903f"

FLAVORS = {
    "peri-peri": dict(
        name="Peri Peri",
        caption_a="Roasted in small batches",
        caption_b="BOLD HEAT  +  ROASTED CRUNCH",
        caption_c="FIERY  ·  TANGY  ·  CRUNCHY",
        desc=["Whole cashews slow-roasted and tossed in",
              "African bird's eye chilli, garlic & lemon"],
        heat=3,
        acc="#b3301c", acc_dark="#7e1f12", side_a="#8f2716",
        c_acc="#c4452a", c_acc2="#e8913a", c_side="#c4452a", c_leaf="#3f7355",
        style="peri",
        about=("Our Peri Peri Cashews start with plump W240 kernels, slow-"
               "roasted until golden and tossed in a fiery blend of African "
               "bird's eye chilli, roasted garlic and a squeeze of sun-dried "
               "lemon. Bold, tangy and addictively crunchy."),
        ingredients=("Cashew kernels (85%), peri peri seasoning (chilli, salt, "
                     "garlic, onion, lemon powder, paprika, spices & "
                     "condiments), edible vegetable oil."),
        uses=[("bowl", "Snack straight", "from the box"),
              ("glass", "Pair with chilled", "drinks & mocktails"),
              ("gift", "Festive gifting", "& hampers")],
    ),
    "kadi-patta": dict(
        name="Kadi Patta",
        caption_a="Tempered the southern way",
        caption_b="EARTHY AROMA  +  GOLDEN CRUNCH",
        caption_c="AROMATIC  ·  SAVOURY  ·  CRUNCHY",
        desc=["Golden-roasted cashews tempered with fresh",
              "curry leaves, mustard seeds & green chilli"],
        heat=1,
        acc="#3e6b2f", acc_dark="#284a1e", side_a="#2f5424",
        c_acc="#2f6b55", c_acc2="#7fa35a", c_side="#2f6b55", c_leaf="#2f6b55",
        style="kadi",
        about=("Our Kadi Patta Cashews are inspired by the classic South "
               "Indian tadka. Whole W240 kernels are roasted golden, then "
               "tempered with crackling mustard seeds, fresh curry leaves "
               "and a gentle hint of green chilli."),
        ingredients=("Cashew kernels (88%), edible vegetable oil, curry "
                     "leaves (4%), salt, green chilli, mustard seeds, black "
                     "pepper, asafoetida."),
        uses=[("bowl", "Tea-time", "snacking"),
              ("glass", "Pair with filter", "coffee or chai"),
              ("gift", "Festive gifting", "& hampers")],
    ),
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, t, size, fill, family=F_SANS, weight=400, anchor="middle",
         ls=0, italic=False, opacity=1, extra=""):
    st = ' font-style="italic"' if italic else ""
    op = f' opacity="{opacity}"' if opacity != 1 else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" letter-spacing="{ls}"{st}{op}{extra}>'
            f'{esc(t)}</text>')


def wrap(t, n):
    lines, cur = [], ""
    for w in t.split():
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


def para(x, y, t, n, size, lh, fill, family=F_SANS, weight=400):
    out = []
    for i, line in enumerate(wrap(t, n)):
        out.append(text(x, y + i * lh, line, size, fill, family, weight, "start"))
    return "\n".join(out), y + len(wrap(t, n)) * lh


def group(gid, body):
    return f'<g id="{gid}">\n{body}\n</g>'


# ---------------------------------------------------------------------------
# shared defs
# ---------------------------------------------------------------------------

DEFS = """
<radialGradient id="cg_plain" cx=".38" cy=".3" r=".8">
  <stop offset="0" stop-color="#fcefd2"/><stop offset=".55" stop-color="#edcb93"/><stop offset="1" stop-color="#c99558"/>
</radialGradient>
<radialGradient id="cg_peri" cx=".38" cy=".3" r=".8">
  <stop offset="0" stop-color="#f9d9a4"/><stop offset=".5" stop-color="#e3a061"/><stop offset="1" stop-color="#b95a2a"/>
</radialGradient>
<radialGradient id="cg_kadi" cx=".38" cy=".3" r=".8">
  <stop offset="0" stop-color="#fbe8bd"/><stop offset=".55" stop-color="#e2b670"/><stop offset="1" stop-color="#b3803d"/>
</radialGradient>
<linearGradient id="chg_red" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#ef4a2c"/><stop offset=".6" stop-color="#c0231a"/><stop offset="1" stop-color="#8e140e"/>
</linearGradient>
<linearGradient id="chg_dry" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#b3291c"/><stop offset=".6" stop-color="#861a11"/><stop offset="1" stop-color="#560c07"/>
</linearGradient>
<linearGradient id="lg_curry" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#79a846"/><stop offset="1" stop-color="#2e5a22"/>
</linearGradient>
<linearGradient id="lg_leaf" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#6d9a4a"/><stop offset="1" stop-color="#335c2a"/>
</linearGradient>
<linearGradient id="lg_noir" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#5a6b3a"/><stop offset="1" stop-color="#1f2a17"/>
</linearGradient>
<linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#ecd08a"/><stop offset=".45" stop-color="#b8903f"/><stop offset=".7" stop-color="#e6c877"/><stop offset="1" stop-color="#9c7630"/>
</linearGradient>
<linearGradient id="noir_bg" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#1d1a16"/><stop offset="1" stop-color="#0d0b09"/>
</linearGradient>
<radialGradient id="ivory_bg" cx=".5" cy=".42" r=".75">
  <stop offset="0" stop-color="#fbf6ea"/><stop offset="1" stop-color="#eee2c9"/>
</radialGradient>
<radialGradient id="pile_bg" cx=".5" cy=".5" r=".6">
  <stop offset="0" stop-color="#8a5526"/><stop offset="1" stop-color="#4e2c12"/>
</radialGradient>
<linearGradient id="bowl" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#fffdf7"/><stop offset="1" stop-color="#e3d9c4"/>
</linearGradient>
<linearGradient id="wood" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#c98f55"/><stop offset="1" stop-color="#8d5a2c"/>
</linearGradient>
"""

CASHEW = ("M -30,-8 C -34,12 -14,24 2,22 C 20,20 34,8 30,-10 "
          "C 28,-16 20,-16 18,-10 C 14,-2 8,4 0,4 C -8,4 -16,-2 -18,-10 "
          "C -20,-16 -28,-16 -30,-8 Z")
CHILLI = "M 0,-5 C 25,-9 60,-7 100,2 C 62,6 28,8 0,5 C -3,2 -3,-2 0,-5 Z"
LEAF = "M 0,0 C 10,-9 30,-10 44,0 C 30,10 10,9 0,0 Z"


# ---------------------------------------------------------------------------
# illustration primitives
# ---------------------------------------------------------------------------

def cashew(x, y, s, r, style, rng, shadow=0.22, outline=None):
    o = [f'<g transform="translate({x:.1f} {y:.1f}) rotate({r:.1f}) scale({s:.3f})">']
    if shadow:
        o.append(f'<path d="{CASHEW}" transform="translate(2.5 4.5)" fill="#2a1406" opacity="{shadow}"/>')
    stroke = outline or "#9c6a34"
    sw = 1.4 if outline else 0.8
    o.append(f'<path d="{CASHEW}" fill="url(#cg_{style})" stroke="{stroke}" stroke-width="{sw}" stroke-opacity=".7"/>')
    o.append('<path d="M -25,-7 C -16,9 14,11 25,-8" fill="none" stroke="#a8743c" stroke-width="1" opacity=".45"/>')
    o.append('<ellipse cx="-12" cy="6" rx="11" ry="4" transform="rotate(28 -12 6)" fill="#fff8e8" opacity=".35"/>')
    if style == "peri":
        for _ in range(16):
            t = rng.random()
            px, py = -24 + 48 * t, -9 + 22 * math.sin(math.pi * t) + rng.uniform(-4, 4)
            col = rng.choice(["#b0200f", "#d2381c", "#8a1a0c", "#e0602a"])
            o.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{rng.uniform(.7, 1.7):.1f}" fill="{col}" opacity=".85"/>')
    elif style == "kadi":
        for _ in range(3):
            t = rng.uniform(.15, .85)
            px, py = -24 + 48 * t, -9 + 22 * math.sin(math.pi * t) + rng.uniform(-3, 3)
            o.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="1.5" fill="#2b1d14"/>')
        for _ in range(4):
            t = rng.uniform(.1, .9)
            px, py = -24 + 48 * t, -9 + 22 * math.sin(math.pi * t) + rng.uniform(-4, 4)
            o.append(f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="2.6" ry="1.1" '
                     f'transform="rotate({rng.uniform(0, 180):.0f} {px:.1f} {py:.1f})" fill="#3f6e2a" opacity=".9"/>')
    o.append("</g>")
    return "".join(o)


def cashew_pile(cx, cy, rx, ry, style, seed, scale=1.0):
    rng = random.Random(seed)
    items = []
    step = 30 * scale
    y = cy - ry - 20
    row = 0
    while y < cy + ry + 30:
        x = cx - rx - 30 + (row % 2) * step * .6
        while x < cx + rx + 30:
            items.append((x + rng.uniform(-8, 8), y + rng.uniform(-6, 6),
                          scale * rng.uniform(.85, 1.1), rng.uniform(0, 360)))
            x += step * 1.3
        y += step * .7
        row += 1
    rng.shuffle(items)
    return "\n".join(cashew(x, y, s, r, style, rng) for x, y, s, r in items)


def chilli(x, y, s, r, grad="chg_red", outline=None, dried=False):
    sw = f' stroke="{outline}" stroke-width="1.1"' if outline else ""
    o = [f'<g transform="translate({x:.1f} {y:.1f}) rotate({r:.1f}) scale({s:.3f})">',
         f'<path d="M -8,0 C -18,-2 -24,-8 -28,-16" fill="none" stroke="{"#6b5a2a" if dried else "#5e8a36"}" '
         f'stroke-width="3" stroke-linecap="round"/>',
         f'<path d="{CHILLI}" fill="url(#{grad})"{sw}/>',
         '<path d="M 6,-3 C 30,-6 60,-4 88,1" fill="none" stroke="#ffb09a" stroke-width="1.6" '
         'stroke-linecap="round" opacity=".55"/>']
    if dried:
        o.append('<path d="M 20,-5 C 24,0 22,4 26,6 M 45,-5 C 48,-1 46,3 50,6 M 68,-2 C 70,1 69,3 72,4" '
                 'fill="none" stroke="#3e0805" stroke-width="1" opacity=".6"/>')
    o.append(f'<path d="M 2,-7 C -6,-8 -10,-3 -8,0 C -10,3 -6,8 2,7 Z" fill="{"#7a6a34" if dried else "#4e7a2e"}"{sw}/>')
    o.append("</g>")
    return "".join(o)


def leaf(x, y, s, r, fill="url(#lg_curry)", stroke=None, vein="#d8e8b8", sw=1):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({r:.1f}) scale({s:.3f})">'
            f'<path d="{LEAF}" fill="{fill}"{st}/>'
            f'<path d="M 2,0 C 16,-1 30,-1 42,0" fill="none" stroke="{vein}" stroke-width=".9" opacity=".8"/>'
            f'</g>')


def sprig(x, y, ang, L, n, s=1.0, fill="url(#lg_curry)", stem="#4f6f2a",
          stroke=None, vein="#d8e8b8", bend=10):
    o = [f'<g transform="translate({x:.1f} {y:.1f}) rotate({ang:.1f})">',
         f'<path d="M 0,0 Q {L / 2:.1f},{-bend * 2:.1f} {L:.1f},0" fill="none" stroke="{stem}" '
         f'stroke-width="{2.2 * s:.1f}" stroke-linecap="round"/>']
    for i in range(n):
        t = (i + 1) / (n + 1)
        px, py = L * t, -4 * bend * t * (1 - t)
        a = math.degrees(math.atan2(-4 * bend * (1 - 2 * t), L))
        side = 1 if i % 2 else -1
        ls = s * (1.05 - .35 * t)
        o.append(leaf(px, py, ls, a + side * 50, fill, stroke, vein))
    a_end = math.degrees(math.atan2(4 * bend, L))
    o.append(leaf(L, 0, s * .72, a_end, fill, stroke, vein))
    o.append("</g>")
    return "".join(o)


def lemon(x, y, r, outline=None):
    o = [f'<g transform="translate({x:.1f} {y:.1f})">',
         f'<circle r="{r}" fill="#e9b81f"{f" stroke={chr(34)}{outline}{chr(34)} stroke-width={chr(34)}1.2{chr(34)}" if outline else ""}/>',
         f'<circle r="{r * .88:.1f}" fill="#fbf1c4"/>']
    for i in range(8):
        a0, a1 = math.radians(i * 45 + 4), math.radians(i * 45 + 41)
        rr = r * .78
        o.append(f'<path d="M 0,0 L {rr * math.cos(a0):.1f},{rr * math.sin(a0):.1f} '
                 f'A {rr:.1f} {rr:.1f} 0 0 1 {rr * math.cos(a1):.1f},{rr * math.sin(a1):.1f} Z" fill="#f6d24a"/>')
    o.append(f'<circle r="{r * .08:.1f}" fill="#fbf1c4"/></g>')
    return "".join(o)


def swirl(x, y, h, color, op=.35, w=3):
    return (f'<path d="M {x:.1f},{y:.1f} c 12,{-h * .2:.1f} -12,{-h * .35:.1f} 0,{-h * .5:.1f} '
            f's 12,{-h * .35:.1f} 0,{-h * .5:.1f}" fill="none" stroke="{color}" stroke-width="{w}" '
            f'stroke-linecap="round" opacity="{op}"/>')


def specks(cx, cy, rx, ry, n, colors, seed, rmin=.8, rmax=2.2):
    rng = random.Random(seed)
    o = []
    for _ in range(n):
        a, d = rng.uniform(0, 2 * math.pi), math.sqrt(rng.random())
        o.append(f'<circle cx="{cx + rx * d * math.cos(a):.1f}" cy="{cy + ry * d * math.sin(a):.1f}" '
                 f'r="{rng.uniform(rmin, rmax):.1f}" fill="{rng.choice(colors)}"/>')
    return "".join(o)


def emblem(cx, cy, r, col, fill_cashew=None):
    s = r / 70
    return (f'<g id="Ashvena_Emblem">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="1.5"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r - 4}" fill="none" stroke="{col}" stroke-width=".6"/>'
            f'<path d="M {cx},{cy - r * .78:.1f} l {r * .07:.1f},{r * .09:.1f} l {-r * .07:.1f},{r * .09:.1f} '
            f'l {-r * .07:.1f},{-r * .09:.1f} Z" fill="{col}"/>'
            f'<text x="{cx}" y="{cy + r * .14:.1f}" font-family="{F_DISPLAY}" font-size="{r * .82:.1f}" '
            f'font-weight="600" fill="{col}" text-anchor="middle">A</text>'
            f'<path d="{CASHEW}" transform="translate({cx} {cy + r * .42:.1f}) scale({s:.3f})" '
            f'fill="{fill_cashew or col}"/>'
            f'</g>')


def wordmark(cx, y, size, col, sub_col=None, est=True):
    o = [text(cx, y, "ASHVENA", size, col, F_DISPLAY, 600, ls=size * .22)]
    if est:
        o.append(f'<line x1="{cx - size * 2.6:.1f}" y1="{y + size * .48:.1f}" x2="{cx - size * 1.6:.1f}" '
                 f'y2="{y + size * .48:.1f}" stroke="{sub_col or col}" stroke-width=".8"/>')
        o.append(f'<line x1="{cx + size * 1.6:.1f}" y1="{y + size * .48:.1f}" x2="{cx + size * 2.6:.1f}" '
                 f'y2="{y + size * .48:.1f}" stroke="{sub_col or col}" stroke-width=".8"/>')
        o.append(text(cx, y + size * .6, "EST. 1953", size * .3, sub_col or col, F_SANS, 600, ls=size * .12))
    return group("Ashvena_Wordmark", "\n".join(o))


def ornament(cx, y, half, col, w=.8):
    return (f'<line x1="{cx - half}" y1="{y}" x2="{cx - 8}" y2="{y}" stroke="{col}" stroke-width="{w}"/>'
            f'<path d="M {cx},{y - 4} l 4,4 l -4,4 l -4,-4 Z" fill="{col}"/>'
            f'<line x1="{cx + 8}" y1="{y}" x2="{cx + half}" y2="{y}" stroke="{col}" stroke-width="{w}"/>')


def veg_mark(x, y, s=18):
    return group("Veg_Mark",
                 f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="#fff" stroke="#138a36" stroke-width="1.6"/>'
                 f'<circle cx="{x + s / 2}" cy="{y + s / 2}" r="{s * .27:.1f}" fill="#138a36"/>')


def heat_meter(x, y, level, col, empty, label_col, anchor="start"):
    o = [text(x, y + 4, "HEAT", 9, label_col, F_SANS, 700, "start", ls=2)]
    for i in range(4):
        filled = i < level
        o.append(f'<g transform="translate({x + 40 + i * 22} {y + 2}) rotate(-20) scale(.19)">'
                 f'<path d="{CHILLI}" fill="{col if filled else "none"}" '
                 f'stroke="{col if filled else empty}" stroke-width="{0 if filled else 8}"/></g>')
    return group("Heat_Meter", "".join(o))


def net_wt(x, y, col, anchor="end", size=12):
    return text(x, y, "NET WT. 200 g ℮ 7.05 oz", size, col, F_SANS, 600, anchor, ls=1)


def pattern_tile(style, col, x, y, s, r):
    if style == "peri":
        return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({r}) scale({s})">'
                f'<path d="{CHILLI}" fill="{col}"/>'
                f'<path d="M -8,0 C -18,-2 -24,-8 -28,-16" fill="none" stroke="{col}" stroke-width="3"/></g>')
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({r}) scale({s})">'
            f'<path d="{LEAF}" fill="{col}"/><path d="{LEAF}" transform="rotate(60) scale(.8)" fill="{col}"/>'
            f'<path d="{LEAF}" transform="rotate(-60) scale(.8)" fill="{col}"/></g>')


def svg_doc(w, h, body, title):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w / 4:.0f}mm" height="{h / 4:.0f}mm" '
            f'viewBox="0 0 {w} {h}">\n<title>{esc(title)}</title>\n<defs>{DEFS}</defs>\n{body}\n</svg>\n')


# ---------------------------------------------------------------------------
# botanical clusters per flavour
# ---------------------------------------------------------------------------

def botanicals_back(f, x, y, noir=False):
    """Elements behind the product window, anchored around (x, y)."""
    o = []
    lf = "url(#lg_noir)" if noir else ("url(#lg_leaf)" if f["style"] == "peri" else "url(#lg_curry)")
    st = GOLD if noir else None
    vein = "#d9b866" if noir else "#d8e8b8"
    if f["style"] == "peri":
        o.append(leaf(x - 40, y - 60, 1.6, -130, lf, st, vein))
        o.append(leaf(x - 20, y - 30, 1.4, -160, lf, st, vein))
        o.append(leaf(x - 10, y + 70, 1.5, 150, lf, st, vein))
        o.append(chilli(x - 75, y - 88, .95, 58, outline=st))
        o.append(chilli(x - 95, y - 30, 1.05, 20, outline=st))
        o.append(chilli(x - 110, y + 40, .95, -15, outline=st))
    else:
        o.append(sprig(x - 70, y + 110, -80, 190, 9, 1.0, lf, "#6b7f3a" if noir else "#4f6f2a", st, vein))
        o.append(sprig(x - 100, y + 90, -120, 150, 7, .9, lf, "#6b7f3a" if noir else "#4f6f2a", st, vein))
        o.append(sprig(x - 40, y + 120, -45, 150, 7, .9, lf, "#6b7f3a" if noir else "#4f6f2a", st, vein))
    return "\n".join(o)


def botanicals_front(f, x, y, seed, noir=False):
    """Elements that overlap the bottom-left edge of the product window."""
    rng = random.Random(seed)
    st = GOLD if noir else None
    o = []
    if f["style"] == "peri":
        o.append(chilli(x - 30, y + 20, 1.1, -10, outline=st))
        o.append(lemon(x - 70, y + 60, 30, st))
        o.append(chilli(x + 10, y + 55, .9, 12, outline=st))
    else:
        o.append(chilli(x - 90, y + 40, .95, -8, "chg_dry", st, dried=True))
        o.append(chilli(x - 20, y + 62, .85, 18, "chg_dry", st, dried=True))
        o.append(sprig(x - 110, y + 70, -20, 110, 5, .8,
                       "url(#lg_noir)" if noir else "url(#lg_curry)",
                       "#6b7f3a" if noir else "#4f6f2a", st, "#d9b866" if noir else "#d8e8b8", 6))
        o.append(specks(x - 40, y + 90, 50, 10, 22, ["#2b1d14", "#3a2618", "#5a3a20"], seed, 1.4, 2.2))
    for dx, dy, r in [(-5, 95, 20), (40, 100, -30), (-70, 105, 160)]:
        o.append(cashew(x + dx, y + dy, .95, r, f["style"], rng, outline=st))
    if f["style"] == "peri":
        o.append(specks(x - 20, y + 118, 70, 8, 40, ["#b0200f", "#d2381c", "#e0602a"], seed))
    return "\n".join(o)


# ---------------------------------------------------------------------------
# Direction A - Heritage Ivory
# ---------------------------------------------------------------------------

def side_A(f):
    o = [f'<rect x="0" y="0" width="{SIDE}" height="{H}" fill="{f["side_a"]}"/>']
    pat = []
    rng = random.Random(7)
    for row in range(12):
        for col in range(3):
            pat.append(pattern_tile(f["style"], "#ffffff", 20 + col * 62 + (row % 2) * 30,
                                    30 + row * 58, .32, rng.choice([-30, 20, 60, 110])))
    o.append(f'<g id="Side_Pattern" opacity=".09">{"".join(pat)}</g>')
    o.append(f'<rect x="12" y="12" width="{SIDE - 24}" height="{H - 24}" fill="none" stroke="#e6c877" stroke-width="1"/>')
    o.append(emblem(90, 78, 34, "#f5e6c4"))
    o.append(f'<g transform="translate(104 350) rotate(-90)">'
             + text(0, 0, "ASHVENA", 44, "#f5e6c4", F_DISPLAY, 600, ls=12) + "</g>")
    o.append(f'<g transform="translate(128 350) rotate(-90)">'
             + text(0, 0, f"{f['name'].upper()} CASHEWS", 10, "#e6c877", F_SANS, 600, ls=5) + "</g>")
    o.append(ornament(90, 560, 55, "#e6c877"))
    o.append(text(90, 592, "Premium", 18, "#f5e6c4", F_SERIF, 600, italic=True))
    o.append(text(90, 612, "Roasted Cashews", 18, "#f5e6c4", F_SERIF, 600, italic=True))
    o.append(text(90, 645, "200 g", 11, "#e6c877", F_SANS, 600, ls=2))
    return group("Side_Panel", "\n".join(o))


def front_A(f, seed):
    X = FX
    cx = X + 240
    o = [group("Background",
               f'<rect x="{X}" y="0" width="{FRONT}" height="{H}" fill="url(#ivory_bg)"/>'
               f'<rect x="{X + 14}" y="14" width="{FRONT - 28}" height="{H - 28}" fill="none" stroke="{GOLD}" stroke-width="1.2"/>'
               f'<rect x="{X + 19}" y="19" width="{FRONT - 38}" height="{H - 38}" fill="none" stroke="{GOLD}" stroke-width=".5"/>')]
    o.append(group("Brand",
                   emblem(cx, 64, 30, f["acc"]) + wordmark(cx, 132, 36, INK, GOLD)))
    o.append(group("Caption",
                   ornament(cx, 182, 120, GOLD)
                   + text(cx, 204, f["caption_a"].upper(), 9.5, f["acc_dark"], F_SANS, 600, ls=3.5)))

    wx, wy, wr = X + 300, 345, 118
    clip = f'<clipPath id="win"><circle cx="{wx}" cy="{wy}" r="{wr}"/></clipPath>'
    ill = [clip]
    for i, sx in enumerate([X + 70, X + 105, X + 140]):
        ill.append(swirl(sx, 280 - i * 8, 70, f["acc"], .22, 2.5))
    ill.append(botanicals_back(f, X + 190, 330))
    ill.append(f'<circle cx="{wx}" cy="{wy}" r="{wr + 12}" fill="none" stroke="{GOLD}" stroke-width=".8"/>')
    ill.append(f'<circle cx="{wx}" cy="{wy}" r="{wr}" fill="url(#pile_bg)"/>')
    ill.append(f'<g clip-path="url(#win)">{cashew_pile(wx, wy, wr, wr, f["style"], seed)}</g>')
    ill.append(f'<circle cx="{wx}" cy="{wy}" r="{wr - 7}" fill="none" stroke="#fff6e0" stroke-width="1.2" '
               f'stroke-dasharray="3 5" opacity=".85"/>')
    ill.append(f'<circle cx="{wx}" cy="{wy}" r="{wr + 3}" fill="none" stroke="url(#gold)" stroke-width="7"/>')
    ill.append(botanicals_front(f, X + 150, 370, seed))
    o.append(group("Illustration", "\n".join(ill)))

    nm = [text(cx, 536, f["name"], 58, f["acc"], F_SERIF, 600),
          text(cx, 566, "CASHEWS", 19, INK, F_DISPLAY, 600, ls=12),
          text(cx, 594, f["desc"][0], 15.5, "#5a4632", F_SERIF, 500, italic=True),
          text(cx, 613, f["desc"][1], 15.5, "#5a4632", F_SERIF, 500, italic=True)]
    o.append(group("Product_Name", "\n".join(nm)))
    o.append(group("Footer",
                   veg_mark(X + 36, 633)
                   + heat_meter(X + 72, 642, f["heat"], f["acc"], "#c9b48a", INK)
                   + net_wt(X + 444, 647, INK)))
    return group("Front_Panel", "\n".join(o))


# ---------------------------------------------------------------------------
# Direction B - Noir Royale
# ---------------------------------------------------------------------------

def vine(x, y0, y1, style, col):
    o = [f'<path d="M {x},{y0} C {x - 25},{y0 + 120} {x + 25},{y0 + 240} {x},{y0 + 360} '
         f'S {x - 20},{y1 - 80} {x},{y1}" fill="none" stroke="{col}" stroke-width="1.4"/>']
    rng = random.Random(3)
    for i, yy in enumerate(range(y0 + 30, y1 - 20, 46)):
        side = 1 if i % 2 else -1
        if style == "kadi":
            o.append(sprig(x, yy, -90 + side * 55, 50, 5, .5, "none", col, col, col, 4))
        else:
            if i % 2:
                o.append(f'<g transform="translate({x} {yy}) rotate({90 + side * 35}) scale(.5)">'
                         f'<path d="{CHILLI}" fill="none" stroke="{col}" stroke-width="2.4"/>'
                         f'<path d="M 2,-7 C -6,-8 -10,-3 -8,0 C -10,3 -6,8 2,7 Z" fill="none" stroke="{col}" stroke-width="2.4"/></g>')
            else:
                o.append(leaf(x, yy, .7, side * 40 - 90 + (180 if side < 0 else 0), "none", col, col, 1.2))
        _ = rng
    return "".join(o)


def side_B(f):
    o = [f'<rect x="0" y="0" width="{SIDE}" height="{H}" fill="url(#noir_bg)"/>',
         f'<rect x="12" y="12" width="{SIDE - 24}" height="{H - 24}" fill="none" stroke="url(#gold)" stroke-width="1"/>',
         f'<clipPath id="sideB"><rect x="13" y="13" width="{SIDE - 26}" height="{H - 26}"/></clipPath>',
         f'<g opacity=".5" clip-path="url(#sideB)">{vine(60, 150, 640, f["style"], GOLD)}</g>',
         emblem(90, 78, 32, GOLD),
         f'<g transform="translate(138 360) rotate(-90)">'
         + text(0, 0, "ASHVENA", 34, "url(#gold)", F_DISPLAY, 600, ls=10) + "</g>",
         f'<g transform="translate(158 360) rotate(-90)">'
         + text(0, 0, f"{f['name'].upper()} CASHEWS", 9, "#d8cbb0", F_SANS, 600, ls=4) + "</g>"]
    return group("Side_Panel", "\n".join(o))


def front_B(f, seed):
    X = FX
    cx = X + 240
    o = [group("Background",
               f'<rect x="{X}" y="0" width="{FRONT}" height="{H}" fill="url(#noir_bg)"/>'
               f'<rect x="{X + 16}" y="16" width="{FRONT - 32}" height="{H - 32}" fill="none" stroke="url(#gold)" stroke-width="1.2"/>')]
    o.append(group("Brand",
                   text(cx, 44, f["caption_b"], 10, GOLD, F_SANS, 600, ls=4)
                   + emblem(cx, 94, 28, GOLD)
                   + wordmark(cx, 162, 38, "url(#gold)", "#d8cbb0")))

    ox, oy, rx, ry = X + 290, 372, 128, 148
    ill = [f'<clipPath id="oval"><ellipse cx="{ox}" cy="{oy}" rx="{rx}" ry="{ry}"/></clipPath>']
    ill.append(f'<g opacity=".12">{swirl(X + 90, 300, 90, GOLD, 1, 2)}{swirl(X + 120, 290, 80, GOLD, 1, 2)}</g>')
    ill.append(botanicals_back(f, X + 180, 360, noir=True))
    ill.append(f'<ellipse cx="{ox}" cy="{oy}" rx="{rx}" ry="{ry}" fill="#2a170a"/>')
    ill.append(f'<g clip-path="url(#oval)">{cashew_pile(ox, oy, rx, ry, f["style"], seed)}'
               f'<ellipse cx="{ox}" cy="{oy}" rx="{rx}" ry="{ry}" fill="none" stroke="#000" stroke-width="30" opacity=".25"/></g>')
    ill.append(f'<ellipse cx="{ox}" cy="{oy}" rx="{rx - 7}" ry="{ry - 7}" fill="none" stroke="{GOLD}" stroke-width=".8"/>')
    ill.append(f'<ellipse cx="{ox}" cy="{oy}" rx="{rx + 2}" ry="{ry + 2}" fill="none" stroke="url(#gold)" stroke-width="6"/>')
    ill.append(f'<ellipse cx="{ox}" cy="{oy}" rx="{rx + 11}" ry="{ry + 11}" fill="none" stroke="url(#gold)" '
               f'stroke-width="3.2" stroke-linecap="round" stroke-dasharray="0.1 9"/>')
    ill.append(botanicals_front(f, X + 150, 410, seed, noir=True))
    o.append(group("Illustration", "\n".join(ill)))

    nm = [text(cx, 578, f["name"].upper(), 40, "url(#gold)", F_DISPLAY, 600, ls=4),
          text(cx, 602, "PREMIUM ROASTED CASHEWS", 11, "#e9dfc8", F_SANS, 600, ls=6),
          ornament(cx, 618, 80, GOLD, .6)]
    o.append(group("Product_Name", "\n".join(nm)))
    o.append(group("Footer",
                   veg_mark(X + 36, 632, 16)
                   + heat_meter(X + 70, 640, f["heat"], "#d8452a" if f["style"] == "peri" else "#8aa84f", "#6f6250", "#d8cbb0")
                   + net_wt(X + 444, 646, "#e9dfc8", size=11)))
    return group("Front_Panel", "\n".join(o))


# ---------------------------------------------------------------------------
# Direction C - Spice Coast
# ---------------------------------------------------------------------------

def side_C(f):
    col = f["c_side"]
    o = [f'<rect x="0" y="0" width="{SIDE}" height="{H}" fill="{col}"/>']
    pat = []
    for row in range(11):
        for c in range(3):
            xx, yy = 25 + c * 65 + (row % 2) * 30, 35 + row * 62
            pat.append(sprig(xx, yy, -60 + (row % 3) * 40, 40, 3, .45, "none", "#ffffff", "#ffffff", "#ffffff", 3))
    o.append(f'<g id="Side_Pattern" opacity=".2">{"".join(pat)}</g>')
    o.append(f'<rect x="30" y="200" width="120" height="280" rx="60" fill="#f8f4ea"/>')
    o.append(f'<g transform="translate(98 340) rotate(-90)">'
             + text(0, 0, "ASHVENA", 30, col, F_DISPLAY, 600, ls=8) + "</g>")
    o.append(f'<g transform="translate(118 340) rotate(-90)">'
             + text(0, 0, f"{f['name'].upper()} CASHEWS", 8.5, INK, F_SANS, 600, ls=3) + "</g>")
    return group("Side_Panel", "\n".join(o))


def bowl_scene(f, cx, cy, seed):
    rng = random.Random(seed)
    o = []
    bw, rim = 92, 17
    # back rim + inner
    o.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{bw}" ry="{rim}" fill="#6b4420"/>')
    # mound
    pts = []
    for _ in range(400):
        x = rng.uniform(-bw + 12, bw - 12)
        y = rng.uniform(-78, 6)
        if (x / (bw - 6)) ** 2 + (y / 80) ** 2 <= 1:
            if all((x - a) ** 2 + (y - b) ** 2 > 330 for a, b in pts):
                pts.append((x, y))
    pts.sort(key=lambda p: p[1])
    for x, y in pts:
        o.append(cashew(cx + x, cy + y, .82, rng.uniform(0, 360), f["style"], rng, .18))
    # bowl front
    L, R = cx - bw, cx + bw
    o.append(f'<path d="M {L},{cy} A {bw} {rim} 0 0 0 {R},{cy} A {bw} 66 0 0 1 {L},{cy} Z" fill="url(#bowl)"/>')
    o.append(f'<path d="M {L + 30},{cy + 40} A {bw} 50 0 0 0 {R - 30},{cy + 40}" fill="none" stroke="#d9cdb3" stroke-width="1"/>')
    o.append(f'<path d="M {L},{cy} A {bw} {rim} 0 0 0 {R},{cy}" fill="none" stroke="url(#gold)" stroke-width="3.5"/>')
    o.append(f'<path d="M {L},{cy} A {bw} {rim} 0 0 1 {R},{cy}" fill="none" stroke="url(#gold)" stroke-width="2" opacity=".7"/>')
    o.append(f'<path d="M {cx - 40},{cy + 64} Q {cx},{cy + 72} {cx + 40},{cy + 64}" fill="none" stroke="#c9bb9c" stroke-width="3"/>')
    return "\n".join(o)


def scoop(x, y, style, seed):
    rng = random.Random(seed)
    o = [f'<g transform="translate({x} {y}) rotate(-28)">',
         '<rect x="-110" y="-7" width="80" height="14" rx="7" fill="url(#wood)"/>',
         '<path d="M -36,-22 C -10,-30 30,-26 38,0 C 30,26 -10,30 -36,22 Z" fill="url(#wood)"/>',
         '<path d="M -30,-16 C -8,-22 24,-18 30,0 C 24,18 -8,22 -30,16 Z" fill="#6b4420"/>',
         '</g>']
    for dx, dy, r in [(-6, -14, 10), (14, -6, 80), (-2, 8, 200), (30, 14, 150), (52, 34, 30), (78, 44, 300)]:
        o.append(cashew(x + dx, y + dy, .72, r, style, rng, .18))
    return "\n".join(o)


def front_C(f, seed):
    X = FX
    cx = X + 240
    acc, acc2, lf = f["c_acc"], f["c_acc2"], f["c_leaf"]
    o = [group("Background",
               f'<rect x="{X}" y="0" width="{FRONT}" height="{H}" fill="#f8f4ea"/>'
               f'<rect x="{X + 18}" y="18" width="{FRONT - 36}" height="{H - 36}" fill="none" stroke="{acc}" stroke-width="1.2"/>')]
    o.append(group("Brand",
                   ornament(cx, 42, 150, acc)
                   + wordmark(cx, 92, 34, acc, INK)
                   + f'<line x1="{X + 40}" y1="132" x2="{X + 100}" y2="132" stroke="{acc}" stroke-width=".8"/>'
                   + f'<line x1="{X + 380}" y1="132" x2="{X + 440}" y2="132" stroke="{acc}" stroke-width=".8"/>'
                   + text(cx, 136, f["caption_c"], 10, INK, F_SANS, 600, ls=3)))

    rng = random.Random(seed)
    ill = []
    # flowing swirls
    for i, (sx, sy) in enumerate([(X + 60, 300), (X + 330, 260)]):
        ill.append(f'<path d="M {sx},{sy} c 30,-30 60,10 90,-20 s 50,-30 70,0" fill="none" stroke="{acc2}" '
                   f'stroke-width="2.5" stroke-linecap="round" opacity=".45"/>')
        ill.append(f'<path d="M {sx + 10},{sy + 16} c 30,-24 55,8 80,-16" fill="none" stroke="{acc2}" '
                   f'stroke-width="1.5" stroke-linecap="round" opacity=".35"/>')
    bx, by = cx, 400
    if f["style"] == "peri":
        for ang, L, n, xo in [(-115, 190, 7, -40), (-65, 190, 7, 40), (-140, 150, 5, -70), (-40, 150, 5, 70)]:
            ill.append(sprig(bx + xo, by, ang, L, n, 1.05, "url(#lg_leaf)", "#3f6b3a", None, "#d8e8b8", 16))
        for ang, s in [(-158, .9), (-132, 1.0), (-106, 1.05), (-78, 1.05), (-52, 1.0), (-26, .9)]:
            a = math.radians(ang)
            ill.append(chilli(bx + 70 * math.cos(a), by - 20 + 55 * math.sin(a), s, ang))
        for x, y in [(-120, 300), (110, 290)]:
            ill.append(f'<path d="M {bx + x},{y} c -14,-18 6,-30 -4,-50 c 18,14 22,30 10,46 c 8,-4 10,-12 8,-20 '
                       f'c 10,14 4,28 -14,24 Z" fill="{acc2}" opacity=".55"/>')
    else:
        for ang, L, n, xo, s in [(-100, 230, 11, -20, 1.05), (-75, 220, 10, 30, 1.05), (-130, 180, 8, -60, .95),
                                 (-45, 180, 8, 70, .95), (-155, 130, 6, -80, .85), (-20, 130, 6, 85, .85)]:
            ill.append(sprig(bx + xo, by, ang, L, n, s, "url(#lg_curry)", "#3d5f2a", None, "#d8e8b8", 12))
        ill.append(chilli(bx - 170, 330, .9, -40, "chg_dry", dried=True))
        ill.append(chilli(bx + 120, 300, .9, 30, "chg_dry", dried=True))
        ill.append(specks(bx, 250, 180, 90, 26, ["#2b1d14", "#3a2618"], seed, 1.6, 2.4))
    ill.append(specks(bx, 260, 200, 110, 30, ["#d4af5a", "#e6c877"], seed + 1, 1.2, 2.4))
    ill.append(f'<ellipse cx="{bx}" cy="{by + 72}" rx="130" ry="12" fill="{INK}" opacity=".12"/>')
    ill.append(bowl_scene(f, bx, by, seed))
    ill.append(scoop(X + 112, 466, f["style"], seed))
    ill.append(cashew(bx + 120, by + 80, .8, 20, f["style"], rng, .18))
    ill.append(cashew(bx + 150, by + 86, .72, 160, f["style"], rng, .18))
    if f["style"] == "peri":
        ill.append(lemon(bx + 150, by + 40, 26))
    else:
        ill.append(leaf(bx + 140, by + 50, 1.1, -20))
        ill.append(leaf(bx + 175, by + 62, .9, 35))
    o.append(f'<clipPath id="frameC"><rect x="{X + 19}" y="150" width="{FRONT - 38}" height="{H - 169}"/></clipPath>')
    o.append(f'<g id="Illustration" clip-path="url(#frameC)">\n' + "\n".join(ill) + "\n</g>")

    nm = [text(cx, 570, f["name"], 50, acc, F_SERIF, 600),
          text(cx, 598, "CASHEWS", 17, INK, F_DISPLAY, 600, ls=12)]
    o.append(group("Product_Name", "\n".join(nm)))
    o.append(group("Footer",
                   veg_mark(X + 40, 628)
                   + heat_meter(X + 76, 637, f["heat"], "#c4452a", "#c9b48a", INK)
                   + net_wt(X + 440, 642, acc, "end", 12)))
    return group("Front_Panel", "\n".join(o))


# ---------------------------------------------------------------------------
# Back panel (Direction A)
# ---------------------------------------------------------------------------

def barcode(x, y, w, h, seed):
    rng = random.Random(seed)
    o = [f'<rect x="{x - 6}" y="{y - 6}" width="{w + 12}" height="{h + 22}" fill="#fff"/>']
    cx = x
    while cx < x + w:
        bw = rng.choice([1, 1, 1.5, 2, 3])
        if rng.random() > .45:
            o.append(f'<rect x="{cx:.1f}" y="{y}" width="{bw}" height="{h}" fill="#000"/>')
        cx += bw + rng.choice([1, 1.5, 2])
    o.append(text(x + w / 2, y + h + 12, "8 90XXXX XXXXX X", 9, "#000", F_SANS, 500, ls=1))
    return group("Barcode_PLACEHOLDER", "".join(o))


def qr(x, y, s, seed):
    rng = random.Random(seed)
    c = s / 21
    o = [f'<rect x="{x - 4}" y="{y - 4}" width="{s + 8}" height="{s + 8}" fill="#fff"/>']
    for i in range(21):
        for j in range(21):
            if rng.random() > .52:
                o.append(f'<rect x="{x + i * c:.1f}" y="{y + j * c:.1f}" width="{c:.2f}" height="{c:.2f}" fill="#000"/>')
    for fx, fy in [(0, 0), (14, 0), (0, 14)]:
        o.append(f'<rect x="{x + fx * c:.1f}" y="{y + fy * c:.1f}" width="{7 * c:.1f}" height="{7 * c:.1f}" fill="#fff"/>'
                 f'<rect x="{x + (fx + .5) * c:.1f}" y="{y + (fy + .5) * c:.1f}" width="{6 * c:.1f}" height="{6 * c:.1f}" '
                 f'fill="none" stroke="#000" stroke-width="{c:.1f}"/>'
                 f'<rect x="{x + (fx + 2) * c:.1f}" y="{y + (fy + 2) * c:.1f}" width="{3 * c:.1f}" height="{3 * c:.1f}" fill="#000"/>')
    return group("QR_PLACEHOLDER", "".join(o))


def use_icon(kind, x, y, col):
    if kind == "bowl":
        d = (f'<path d="M {x - 14},{y} A 14 10 0 0 0 {x + 14},{y} Z" fill="none" stroke="{col}" stroke-width="1.6"/>'
             f'<path d="M {x - 8},{y - 2} q 3,-7 8,-3 q 5,-6 8,2" fill="none" stroke="{col}" stroke-width="1.4"/>')
    elif kind == "glass":
        d = (f'<path d="M {x - 9},{y - 14} L {x + 9},{y - 14} L {x + 6},{y + 10} L {x - 6},{y + 10} Z" '
             f'fill="none" stroke="{col}" stroke-width="1.6"/>'
             f'<line x1="{x - 8}" y1="{y - 5}" x2="{x + 8}" y2="{y - 5}" stroke="{col}" stroke-width="1.2"/>')
    else:
        d = (f'<rect x="{x - 12}" y="{y - 6}" width="24" height="16" fill="none" stroke="{col}" stroke-width="1.6"/>'
             f'<rect x="{x - 14}" y="{y - 12}" width="28" height="6" fill="none" stroke="{col}" stroke-width="1.6"/>'
             f'<line x1="{x}" y1="{y - 12}" x2="{x}" y2="{y + 10}" stroke="{col}" stroke-width="1.6"/>')
    return f'<circle cx="{x}" cy="{y - 2}" r="19" fill="none" stroke="{col}" stroke-width=".8" opacity=".5"/>' + d


def back_A(f):
    W = FRONT
    acc = f["acc"]
    o = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#ivory_bg)"/>',
         f'<rect x="14" y="14" width="{W - 28}" height="{H - 28}" fill="none" stroke="{GOLD}" stroke-width="1.2"/>',
         emblem(58, 60, 26, acc),
         text(96, 58, "ASHVENA", 24, INK, F_DISPLAY, 600, "start", ls=5),
         text(97, 74, "EST. 1953", 7.5, GOLD, F_SANS, 600, "start", ls=2),
         text(W - 34, 56, f["name"], 24, acc, F_SERIF, 600, "end"),
         text(W - 34, 74, "PREMIUM ROASTED CASHEWS", 7.5, GOLD, F_SANS, 600, "end", ls=2),
         f'<line x1="34" y1="98" x2="{W - 34}" y2="98" stroke="{GOLD}" stroke-width=".8"/>',
         f'<line x1="244" y1="112" x2="244" y2="470" stroke="{GOLD}" stroke-width=".6"/>']
    L, R = 34, 258
    y = 124
    o.append(text(L, y, f"ABOUT {f['name'].upper()} CASHEWS", 10.5, acc, F_SANS, 700, "start", ls=1))
    p, y = para(L, y + 18, f["about"], 38, 9, 13, "#4a3a2a")
    o.append(p)
    # nutrition table
    y += 10
    rows = [("Nutrient", "Per 100 g*"), ("Energy", "590 kcal"), ("Protein", "17 g"),
            ("Carbohydrate", "30 g"), ("  of which Sugars", "5 g"), ("Total Fat", "46 g"),
            ("  Saturated Fat", "9 g"), ("Trans Fat", "0 g"), ("Sodium", "480 mg")]
    tw, rh = 194, 16
    th = 22 + rh * len(rows)
    o.append(f'<rect x="{L}" y="{y}" width="{tw}" height="{th}" fill="#fffaf0" stroke="{acc}" stroke-width="1"/>')
    o.append(f'<rect x="{L}" y="{y}" width="{tw}" height="22" fill="{acc}"/>')
    o.append(text(L + tw / 2, y + 15, "NUTRITION INFORMATION", 9.5, "#fff", F_SANS, 700, ls=1.5))
    for i, (a, b) in enumerate(rows):
        ry = y + 22 + i * rh
        if i:
            o.append(f'<line x1="{L}" y1="{ry}" x2="{L + tw}" y2="{ry}" stroke="#d8c7a4" stroke-width=".6"/>')
        wgt = 700 if i == 0 else 500
        o.append(text(L + (18 if a.startswith(" ") else 8), ry + 11.5, a.strip(), 8.5, INK, F_SANS, wgt, "start"))
        o.append(text(L + tw - 8, ry + 11.5, b, 8.5, INK, F_SANS, wgt, "end"))
    o.append(f'<line x1="{L + 120}" y1="{y + 22}" x2="{L + 120}" y2="{y + th}" stroke="#d8c7a4" stroke-width=".6"/>')
    y += th + 12
    o.append(text(L, y, "*Indicative values - replace with lab-tested data.", 7, "#8a765a", F_SANS, 500, "start", italic=True))

    y = 124
    o.append(text(R, y, "INGREDIENTS", 10.5, acc, F_SANS, 700, "start", ls=1))
    p, y = para(R, y + 18, f["ingredients"], 37, 9, 13, "#4a3a2a")
    o.append(p)
    p, y = para(R, y + 4, "ALLERGEN ADVICE: Contains cashew (tree nut). Packed in a facility that also "
                          "handles peanuts, other tree nuts & sesame.", 37, 8, 12, INK, F_SANS, 600)
    o.append(p)
    y += 14
    o.append(text(R, y, "STORAGE INSTRUCTIONS", 10.5, acc, F_SANS, 700, "start", ls=1))
    p, y = para(R, y + 18, "Store in a cool, dry place away from direct sunlight. Once opened, "
                           "transfer to an airtight container and consume within 7 days.", 37, 9, 13, "#4a3a2a")
    o.append(p)
    y += 14
    o.append(text(R, y, "BEST ENJOYED", 10.5, acc, F_SANS, 700, "start", ls=1))
    y += 30
    for i, (k, a, b) in enumerate(f["uses"]):
        yy = y + i * 44
        o.append(use_icon(k, R + 24, yy, acc))
        o.append(text(R + 58, yy - 3, a, 9.5, INK, F_SANS, 600, "start"))
        o.append(text(R + 58, yy + 10, b, 9.5, INK, F_SANS, 500, "start"))

    # lower band
    o.append(f'<line x1="34" y1="486" x2="{W - 34}" y2="486" stroke="{GOLD}" stroke-width=".8"/>')
    yb = 506
    o.append(text(L, yb, "MANUFACTURED & PACKED BY", 8.5, acc, F_SANS, 700, "start", ls=1))
    for i, line in enumerate(["Ashvena Foods Pvt. Ltd.", "[Address line 1], [City] - [PIN], India",
                              "Customer care: [phone]  ·  [email]", "www.ashvena.in"]):
        o.append(text(L, yb + 15 + i * 12, line, 8.5, "#4a3a2a", F_SANS, 500, "start"))
    for i, line in enumerate(["FSSAI Lic. No. XXXXXXXXXXXXXX", "Country of Origin: India",
                              "MRP ₹ XXX.00 (incl. of all taxes)", "Batch No.:            Mfd.:",
                              "Best Before: 6 months from manufacture"]):
        o.append(text(L, yb + 72 + i * 12, line, 8.5, INK, F_SANS, 600 if i < 2 else 500, "start"))
    o.append(barcode(R + 4, 506, 104, 44, 11))
    o.append(qr(R + 130, 502, 56, 5))
    o.append(text(R + 158, 574, "SCAN FOR RECIPES", 6.5, INK, F_SANS, 700, ls=.8))
    badges = [veg_mark(R + 12, 603, 18)]
    for i, lab in enumerate([["RECYCLE", "CARTON"], ["MADE IN", "INDIA"]]):
        bx = R + 80 + i * 62
        badges.append(f'<circle cx="{bx}" cy="612" r="18" fill="none" stroke="{acc}" stroke-width="1.2"/>')
        badges.append(text(bx, 610, lab[0], 5.5, acc, F_SANS, 700))
        badges.append(text(bx, 618, lab[1], 5.5, acc, F_SANS, 700))
    o.append(group("Badges", "".join(badges)))
    o.append(net_wt(W - 34, 656, INK, size=11))
    return group("Back_Panel", "\n".join(o))


# ---------------------------------------------------------------------------

DIRECTIONS = {
    "A-heritage-ivory": (side_A, front_A),
    "B-noir-royale": (side_B, front_B),
    "C-spice-coast": (side_C, front_C),
}


def main():
    written = []
    for d, (side_fn, front_fn) in DIRECTIONS.items():
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
        for i, (key, f) in enumerate(FLAVORS.items()):
            body = (side_fn(f)
                    + f'\n<clipPath id="frontClip"><rect x="{FX}" y="0" width="{FRONT}" height="{H}"/></clipPath>'
                    + f'\n<g clip-path="url(#frontClip)">\n{front_fn(f, 42 + i)}\n</g>')
            body += (f'\n<g id="Guides" opacity="0"><line x1="{SIDE}" y1="0" x2="{SIDE}" y2="{H}" '
                     f'stroke="#ff00ff" stroke-dasharray="6 4"/></g>')
            path = os.path.join(ROOT, d, f"ashvena-{key}-cashews_front-side.svg")
            with open(path, "w") as fh:
                fh.write(svg_doc(SIDE + FRONT, H, body, f"Ashvena {f['name']} Cashews - {d}"))
            written.append(path)
        if d.startswith("A"):
            for key, f in FLAVORS.items():
                path = os.path.join(ROOT, d, f"ashvena-{key}-cashews_back.svg")
                with open(path, "w") as fh:
                    fh.write(svg_doc(FRONT, H, back_A(f), f"Ashvena {f['name']} Cashews - back"))
                written.append(path)
    for p in written:
        print(os.path.relpath(p, os.path.join(ROOT, "..")))


if __name__ == "__main__":
    main()
