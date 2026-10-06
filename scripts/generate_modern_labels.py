#!/usr/bin/env python3
"""Ashvena modern botanical labels - Direction F.

Wrap labels for Peri Peri and Kadi Patta cashews, 171 x 70 mm:

  | side panel 40 mm | front panel 91 mm | side panel 40 mm |
  | story, what's in,| arch illustration | nutrition, MRP,  |
  | ingredients,     | + logo, name,     | best before,     |
  | allergens,       | notes, veg / heat |  manufacturer,   |
  | storage          | / net weight      | FSSAI, barcode   |

All illustrations are drawn here as vectors (no raster art), in the
style of the reference watercolours: a cusped Mughal arch with a jaali
screen and a potted plant tied to the flavour (bird's eye chilli for
Peri Peri, curry leaf for Kadi Patta), plus ingredient icons.

Output (packaging/F-modern-botanical/):
  ashvena-cashews_modern-labels.ai     ONE Illustrator file (PDF-compatible)
                                       with both labels on a sheet, each
                                       with 3 mm bleed + crop marks
  ashvena-modern-labels-board.png      preview of that sheet
  ashvena-<flavour>-cashews_label.pdf  print PDF per label, TrimBox set
  ashvena-<flavour>-cashews_label.png  preview (trim only)

Fonts: Lobster (name), Fraunces 9pt (headings), Bricolage Grotesque 14pt
(body) - the Ashvena candies & dry-fruits fonts, in scripts/fonts/.
Colours: each label uses only its two brand colours, solid or tinted.

Usage:  pip install reportlab svglib
        python3 scripts/generate_modern_labels.py
"""
import math
import os
import random
import subprocess
import tempfile

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import eanbc
from reportlab.graphics.shapes import STATE_DEFAULTS, Drawing
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "packaging", "F-modern-botanical")
FONTS = os.path.join(HERE, "fonts")
# horizontal lockup from art/logo/logo_final.ai (artboard 2), background removed
LOGO = os.path.join(OUT, "art", "logo", "ashvena-logo_horizontal.svg")
TMP = tempfile.mkdtemp(prefix="ashvena-labels-")

W, H, B = 171.0, 70.0, 3.0           # trim width/height, bleed (mm)
SIDE_W = 40.0                        # each side panel
FX0, FX1 = SIDE_W, W - SIDE_W        # front panel span

# brand fonts (same as the Ashvena candies & dry-fruits range)
F_NAME = "Lobster-Regular"                   # product name
F_HEAD = "Fraunces9pt-SemiBold"              # headings, CASHEWS
F_BODY = "BricolageGrotesque14pt-Regular"    # body copy
F_BODY_M = "BricolageGrotesque14pt-Medium"   # labels, small caps, pill
for name in (F_NAME, F_HEAD, "Fraunces9pt-Regular", F_BODY, F_BODY_M):
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, name + ".ttf")))

# renderPDF (logo, barcode) otherwise references an unembedded Times-Roman
STATE_DEFAULTS["fontName"] = F_BODY

PAPER = "#FBF6EF"


def mix(a, b, t):
    """t of colour a over colour b (hex strings)."""
    a, b = HexColor(a), HexColor(b)
    r, g, bl = (t * x + (1 - t) * y for x, y in ((a.red, b.red), (a.green, b.green), (a.blue, b.blue)))
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(bl * 255))


def palette(D, A):
    """Every colour on a label is the two supplied brand colours, solid or
    tinted toward paper (D = dark, A = accent)."""
    return dict(
        bg=mix(A, PAPER, .10), ink=D, acc=A, pill_ink=PAPER, muted=mix(A, PAPER, .7),
        panel=D, panel_ink=mix(A, PAPER, .06), panel_head=mix(A, PAPER, .42),
        panel_rule=mix(A, D, .55), icon_bg=mix(A, PAPER, .12),
        line=A, frame=mix(A, PAPER, .20), recess=(mix(D, PAPER, .42), mix(A, PAPER, .16)),
        jaali=mix(A, PAPER, .10), jaali_line=mix(A, PAPER, .55), ledge=mix(A, PAPER, .32),
        leaf=mix(A, PAPER, .55), leaf_dark=mix(D, PAPER, .72), leaf_line=D, stem=mix(A, D, .6),
        fruit=(D, A), shine=mix(A, PAPER, .45),
        pot=mix(A, PAPER, .78), pot_shade=mix(D, PAPER, .8), pot_rim=mix(A, PAPER, .62),
        pot_band=mix(A, PAPER, .35), pot_line=D, petal=PAPER, eye=mix(A, PAPER, .6),
    )


P = {}   # palette of the label being drawn (set in draw())

LABELS = {
    "peri-peri": dict(
        name="Peri Peri",
        # Maple Spice + Burnt Orange
        colors=palette("#692721", "#8B4729"),
        arch=dict(eave=False, lattice="quatrefoil"),
        plant="chilli",
        desc="Whole W240 cashews, slow-roasted and tossed in bird's eye chilli, roasted garlic & lemon.",
        notes="FIERY  ·  TANGY  ·  CRUNCHY",
        heat=3,
        story=("Since 1953, Ashvena has roasted cashews the slow way. Plump W240 kernels "
               "are roasted golden, then tossed in a fiery blend of African bird's eye "
               "chilli, roasted garlic and sun-dried lemon."),
        icons=[("chilli", "CHILLI"), ("garlic", "GARLIC"), ("lemon", "LEMON")],
        ingredients=("Cashew kernels (85%), peri peri seasoning (chilli, salt, garlic, onion, "
                     "lemon powder, paprika, spices & condiments), edible vegetable oil."),
        nutrition=[("Energy", "590 kcal"), ("Protein", "17.5 g"), ("Carbohydrate", "30.2 g"),
                   ("  Total sugars", "5.4 g"), ("  Added sugars", "0 g"), ("Total fat", "46.0 g"),
                   ("  Saturated fat", "8.2 g"), ("  Trans fat", "0 g"), ("Sodium", "480 mg")],
    ),
    "kadi-patta": dict(
        name="Kadi Patta",
        # Pakistan Green + Dark Moss Green
        colors=palette("#283618", "#606C38"),
        arch=dict(eave=True, lattice="diamond"),
        plant="curry",
        desc="Golden-roasted W240 cashews tempered with curry leaves, mustard seeds & green chilli.",
        notes="AROMATIC  ·  SAVOURY  ·  CRUNCHY",
        heat=1,
        story=("Since 1953, Ashvena has roasted cashews the slow way. These are tempered "
               "the South Indian way, with crackling mustard seeds, fresh curry leaves "
               "and a gentle hint of green chilli."),
        icons=[("curry", "CURRY LEAF"), ("mustard", "MUSTARD"), ("greenchilli", "GREEN CHILLI")],
        ingredients=("Cashew kernels (88%), edible vegetable oil, curry leaves (4%), salt, "
                     "green chilli, mustard seeds, black pepper, asafoetida."),
        nutrition=[("Energy", "585 kcal"), ("Protein", "17.8 g"), ("Carbohydrate", "29.6 g"),
                   ("  Total sugars", "5.1 g"), ("  Added sugars", "0 g"), ("Total fat", "45.8 g"),
                   ("  Saturated fat", "8.1 g"), ("  Trans fat", "0 g"), ("Sodium", "420 mg")],
    ),
}


# ---------------------------------------------------------------------------
# page-level helpers (trim-space mm, y measured from the top edge)
# ---------------------------------------------------------------------------

class Label:
    """Draws in trim space; (ox, oy) is the trim's bottom-left on the page, mm."""

    def __init__(self, c, ox=B, oy=B):
        self.c, self.ox, self.oy = c, ox, oy
        self.dry = False    # measure only (used to fit side-panel copy)

    def X(self, x):
        return (self.ox + x) * mm

    def Y(self, y):
        return (self.oy + H - y) * mm

    def text(self, x, y, s, font, size, color, anchor="middle", track=0.0):
        """Draw text with tracking (em fraction); y is the baseline."""
        c = self.c
        cs = size * track
        w = pdfmetrics.stringWidth(s, font, size) + cs * (len(s) - 1)
        if self.dry:
            return w / mm
        x0 = self.X(x) - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
        t = c.beginText(x0, self.Y(y))
        t.setFont(font, size)
        t.setCharSpace(cs)
        t.setFillColor(HexColor(color))
        t.textOut(s)
        c.drawText(t)
        return w / mm

    @staticmethod
    def width(s, font, size, track=0.0):
        return (pdfmetrics.stringWidth(s, font, size) + size * track * (len(s) - 1)) / mm

    def para(self, x, y, s, font, size, color, maxw, lead, anchor="start"):
        """Word-wrap s to maxw mm; returns the y below the last line."""
        lines, cur = [], ""
        for word in s.split():
            trial = (cur + " " + word).strip()
            if cur and self.width(trial, font, size) > maxw:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        lines.append(cur)
        for i, ln in enumerate(lines):
            self.text(x, y + i * lead, ln, font, size, color, anchor)
        return y + len(lines) * lead

    def rect(self, x, y, w, h, fill=None, stroke=None, lw=.25, r=0):
        if self.dry:
            return
        c = self.c
        if fill:
            c.setFillColor(HexColor(fill))
        if stroke:
            c.setStrokeColor(HexColor(stroke))
            c.setLineWidth(lw * mm)
        args = (self.X(x), self.Y(y + h), w * mm, h * mm)
        if r:
            c.roundRect(*args, r * mm, stroke=1 if stroke else 0, fill=1 if fill else 0)
        else:
            c.rect(*args, stroke=1 if stroke else 0, fill=1 if fill else 0)

    def circle(self, x, y, r, fill=None, stroke=None, lw=.25):
        if self.dry:
            return
        c = self.c
        if fill:
            c.setFillColor(HexColor(fill))
        if stroke:
            c.setStrokeColor(HexColor(stroke))
            c.setLineWidth(lw * mm)
        c.circle(self.X(x), self.Y(y), r * mm, stroke=1 if stroke else 0, fill=1 if fill else 0)

    def line(self, x0, y0, x1, y1, color, lw=.2):
        if self.dry:
            return
        c = self.c
        c.setStrokeColor(HexColor(color))
        c.setLineWidth(lw * mm)
        c.line(self.X(x0), self.Y(y0), self.X(x1), self.Y(y1))

    def logo(self, cx, top, height):
        """Place the brand lockup centred on cx, vector, original colours."""
        d = svg2rlg(LOGO)
        bx0, by0, bx1, by1 = d.getBounds()
        k = height * mm / (by1 - by0)
        w = (bx1 - bx0) * k / mm
        c = self.c
        c.saveState()
        c.translate(self.X(cx - w / 2), self.Y(top + height))
        c.scale(k, k)
        renderPDF.draw(d, c, -bx0, -by0)
        c.restoreState()
        return w

    def local(self, x, y, s=1.0):
        """Enter a local frame: origin at trim (x, y), units mm, y down."""
        return _Local(self.c, self.X(x), self.Y(y), s)


class _Local:
    def __init__(self, c, px, py, s):
        self.c, self.px, self.py, self.s = c, px, py, s

    def __enter__(self):
        self.c.saveState()
        self.c.translate(self.px, self.py)
        self.c.scale(mm * self.s, -mm * self.s)
        return self.c

    def __exit__(self, *a):
        self.c.restoreState()


# ---------------------------------------------------------------------------
# vector illustration primitives (local frame: mm, y down, angles clockwise)
# ---------------------------------------------------------------------------

def paint(c, p, fill=None, stroke=None, lw=.2):
    if fill:
        c.setFillColor(HexColor(fill))
    if stroke:
        c.setStrokeColor(HexColor(stroke))
        c.setLineWidth(lw)
        c.setLineJoin(1)
        c.setLineCap(1)
    c.drawPath(p, fill=1 if fill else 0, stroke=1 if stroke else 0)


def quad(p, a, ctrl, b):
    """Quadratic bezier from the current point a via ctrl to b."""
    p.curveTo(a[0] + 2 / 3 * (ctrl[0] - a[0]), a[1] + 2 / 3 * (ctrl[1] - a[1]),
              b[0] + 2 / 3 * (ctrl[0] - b[0]), b[1] + 2 / 3 * (ctrl[1] - b[1]), *b)


def bez(p0, p1, p2, p3, t):
    a = ((1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3)
    return (sum(k * q[0] for k, q in zip(a, (p0, p1, p2, p3))),
            sum(k * q[1] for k, q in zip(a, (p0, p1, p2, p3))))


def rotated(c, x, y, ang, fn, *args):
    c.saveState()
    c.translate(x, y)
    c.rotate(ang)
    fn(c, *args)
    c.restoreState()


def leaf(c, L, Wd, light, dark, line):
    """Leaf along +x from 0 to L: two-tone with a midrib."""
    p = c.beginPath()
    p.moveTo(0, 0)
    p.curveTo(L * .25, -Wd * .62, L * .68, -Wd * .55, L, 0)
    p.curveTo(L * .68, Wd * .55, L * .25, Wd * .62, 0, 0)
    p.close()
    paint(c, p, fill=light)
    h = c.beginPath()
    h.moveTo(0, 0)
    h.curveTo(L * .25, Wd * .62, L * .68, Wd * .55, L, 0)
    h.curveTo(L * .6, Wd * .12, L * .3, Wd * .1, 0, 0)
    h.close()
    paint(c, h, fill=dark)
    paint(c, p, stroke=line, lw=.13)
    m = c.beginPath()
    m.moveTo(L * .05, 0)
    m.curveTo(L * .4, -Wd * .04, L * .7, -Wd * .02, L * .92, 0)
    paint(c, m, stroke=line, lw=.09)


def chilli(c, L, Wd, body, shine, calyx, line):
    """Bird's eye chilli along +x (tip at L), calyx and stem at the origin."""
    p = c.beginPath()
    p.moveTo(0, -Wd / 2)
    p.curveTo(L * .4, -Wd * .62, L * .8, -Wd * .35, L, Wd * .12)
    p.curveTo(L * .78, Wd * .42, L * .38, Wd * .58, 0, Wd / 2)
    p.close()
    paint(c, p, fill=body, stroke=line, lw=.12)
    s = c.beginPath()
    s.moveTo(L * .12, -Wd * .22)
    s.curveTo(L * .4, -Wd * .34, L * .65, -Wd * .22, L * .8, -Wd * .02)
    paint(c, s, stroke=shine, lw=Wd * .16)
    k = c.beginPath()
    k.moveTo(Wd * .45, -Wd * .55)
    k.curveTo(Wd * .1, -Wd * .75, -Wd * .3, -Wd * .4, -Wd * .3, 0)
    k.curveTo(-Wd * .3, Wd * .4, Wd * .1, Wd * .75, Wd * .45, Wd * .55)
    k.curveTo(Wd * .25, 0, Wd * .25, 0, Wd * .45, -Wd * .55)
    k.close()
    paint(c, k, fill=calyx, stroke=line, lw=.1)
    st = c.beginPath()
    st.moveTo(-Wd * .3, 0)
    st.curveTo(-Wd * .9, Wd * .1, -Wd * 1.2, Wd * .5, -Wd * 1.5, Wd * .9)
    paint(c, st, stroke=calyx, lw=Wd * .22)


def flower(c, x, y, r):
    for i in range(5):
        a = math.radians(i * 72 - 90)
        c.setFillColor(HexColor(P["petal"]))
        c.setStrokeColor(HexColor(P["line"]))
        c.setLineWidth(.07)
        c.circle(x + math.cos(a) * r * .55, y + math.sin(a) * r * .55, r * .48, stroke=1, fill=1)
    c.setFillColor(HexColor(P["eye"]))
    c.circle(x, y, r * .3, stroke=0, fill=1)


def stem(c, pts, color, lw):
    p = c.beginPath()
    p.moveTo(*pts[0])
    p.curveTo(*pts[1], *pts[2], *pts[3])
    paint(c, p, stroke=color, lw=lw)


def pot(c, cx, base, w, h):
    """Clay pot standing on y = base, centred on cx."""
    line = P["pot_line"]
    body = c.beginPath()
    body.moveTo(cx - w * .46, base - h * .82)
    body.curveTo(cx - w * .55, base - h * .45, cx - w * .4, base - h * .05, cx - w * .3, base)
    body.lineTo(cx + w * .3, base)
    body.curveTo(cx + w * .4, base - h * .05, cx + w * .55, base - h * .45, cx + w * .46, base - h * .82)
    body.close()
    paint(c, body, fill=P["pot"], stroke=line, lw=.15)
    sh = c.beginPath()
    sh.moveTo(cx + w * .12, base - h * .78)
    sh.curveTo(cx + w * .4, base - h * .55, cx + w * .36, base - h * .2, cx + w * .2, base - h * .02)
    sh.lineTo(cx + w * .3, base)
    sh.curveTo(cx + w * .4, base - h * .05, cx + w * .55, base - h * .45, cx + w * .46, base - h * .82)
    sh.close()
    paint(c, sh, fill=P["pot_shade"])
    rim = c.beginPath()
    rim.roundRect(cx - w * .52, base - h, w * 1.04, h * .22, h * .08)
    paint(c, rim, fill=P["pot_rim"], stroke=line, lw=.15)
    band = c.beginPath()
    band.moveTo(cx - w * .43, base - h * .55)
    band.curveTo(cx - w * .15, base - h * .5, cx + w * .15, base - h * .5, cx + w * .43, base - h * .55)
    paint(c, band, stroke=P["pot_band"], lw=.18)


# ---------------------------------------------------------------------------
# arch with jaali screen (local frame, origin at the panel's top-left)
# ---------------------------------------------------------------------------

def cusped_arch(c, xl, xr, ys, ya, yb, lobes=4):
    """Path of a Mughal multifoil arch opening from springs ys to apex ya."""
    cx = (xl + xr) / 2
    left = [bez((xl, ys), (xl, ys - (ys - ya) * .62), (cx - (cx - xl) * .4, ya + (ys - ya) * .12),
                (cx, ya), i / lobes) for i in range(lobes + 1)]
    right = [(2 * cx - x, y) for x, y in reversed(left)]
    inner = (cx, ys + 4)
    p = c.beginPath()
    p.moveTo(xl, yb)
    p.lineTo(xl, ys)
    for seq in (left, right):
        for a, b in zip(seq, seq[1:]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy)
            nx, ny = -dy / n, dx / n
            if nx * (mx - inner[0]) + ny * (my - inner[1]) < 0:
                nx, ny = -nx, -ny
            quad(p, a, (mx + nx * n * .42, my + ny * n * .42), b)
    p.lineTo(xr, yb)
    p.close()
    return p


def lattice(c, x0, y0, x1, y1, kind, color):
    c.saveState()
    clip = c.beginPath()
    clip.rect(x0, y0, x1 - x0, y1 - y0)
    c.clipPath(clip, stroke=0, fill=0)
    c.setStrokeColor(HexColor(color))
    c.setLineWidth(.11)
    if kind == "quatrefoil":
        s = 2.3
        r = s * .27
        for j in range(int((y1 - y0) / s) + 2):
            for i in range(int((x1 - x0) / s) + 2):
                px, py = x0 + i * s + (s / 2 if j % 2 else 0), y0 + j * s
                for ox, oy in ((r, 0), (-r, 0), (0, r), (0, -r)):
                    c.circle(px + ox, py + oy, r, stroke=1, fill=0)
    else:
        s = 1.7
        span = (x1 - x0) + (y1 - y0)
        k = -span
        while k < span:
            c.line(x0 + k, y0, x0 + k + (y1 - y0), y1)
            c.line(x0 + k, y1, x0 + k + (y1 - y0), y0)
            k += s
        c.setFillColor(HexColor(color))
        for j in range(int((y1 - y0) / s * 2) + 2):
            for i in range(int((x1 - x0) / s) + 2):
                c.circle(x0 + i * s + (s / 2 if j % 2 else 0), y0 + j * s / 2, .16, stroke=0, fill=1)
    c.restoreState()


def arch_panel(c, w, h, a, plant):
    ln = P["line"]
    m = w * .11
    ledge = 6.0
    jaali_h = 11.0
    yj0 = h - ledge - jaali_h
    ys, ya = w * .56, w * .16
    top = .6 if a["eave"] else 0

    if a["eave"]:   # chhajja: sloping stone eave over the window
        e = c.beginPath()
        e.moveTo(-2.6, 0.6)
        e.lineTo(w + 2.6, 0.6)
        e.lineTo(w + .4, -2.2)
        e.lineTo(-.4, -2.2)
        e.close()
        paint(c, e, fill=P["frame"], stroke=ln, lw=.16)
        t = c.beginPath()
        t.rect(-.8, -3.4, w + 1.6, 1.2)
        paint(c, t, fill=P["frame"], stroke=ln, lw=.16)
        c.setStrokeColor(HexColor(ln))
        c.setLineWidth(.08)
        c.line(-1.6, -.6, w + 1.6, -.6)

    f = c.beginPath()
    f.rect(0, top, w, h)
    paint(c, f, fill=P["frame"], stroke=ln, lw=.18)
    inset = c.beginPath()
    inset.rect(m * .45, m * .45 + top, w - m * .9, yj0 + 1.2 - m * .45)
    paint(c, inset, stroke=ln, lw=.1)

    arch = cusped_arch(c, m, w - m, ys, ya, yj0)
    c.saveState()
    c.clipPath(arch, stroke=0, fill=0)
    c.linearGradient(0, ya, 0, yj0, [HexColor(P["recess"][0]), HexColor(P["recess"][1])], extend=True)
    c.restoreState()
    paint(c, cusped_arch(c, m, w - m, ys, ya, yj0), stroke=ln, lw=.18)

    plant(c, w / 2, yj0)

    j = c.beginPath()
    j.rect(m, yj0, w - 2 * m, jaali_h)
    paint(c, j, fill=P["jaali"])
    lattice(c, m + .5, yj0 + .5, w - m - .5, yj0 + jaali_h - .5, a["lattice"], P["jaali_line"])
    paint(c, j, stroke=ln, lw=.16)
    jj = c.beginPath()
    jj.rect(m + .5, yj0 + .5, w - 2 * m - 1, jaali_h - 1)
    paint(c, jj, stroke=ln, lw=.08)

    # finials either side of the screen
    for x in (m * .55, w - m * .55):
        p = c.beginPath()
        p.moveTo(x - .9, yj0 + .2)
        p.lineTo(x - .9, yj0 - 1.4)
        p.curveTo(x - .9, yj0 - 2.4, x, yj0 - 2.6, x, yj0 - 3.3)
        p.curveTo(x, yj0 - 2.6, x + .9, yj0 - 2.4, x + .9, yj0 - 1.4)
        p.lineTo(x + .9, yj0 + .2)
        p.close()
        paint(c, p, fill=P["ledge"], stroke=ln, lw=.12)

    led = c.beginPath()
    led.rect(-.8, h - ledge, w + 1.6, ledge + 4)
    paint(c, led, fill=P["ledge"], stroke=ln, lw=.16)
    c.setStrokeColor(HexColor(ln))
    c.setLineWidth(.1)
    c.line(-.8, h - ledge + 1.1, w + .8, h - ledge + 1.1)
    for i in range(int(w / 1.8) + 1):     # scalloped trim under the ledge line
        x = -.2 + i * 1.8
        p = c.beginPath()
        p.moveTo(x, h - ledge + 1.1)
        quad(p, (x, h - ledge + 1.1), (x + .9, h - ledge + 2.6), (x + 1.8, h - ledge + 1.1))
        paint(c, p, stroke=ln, lw=.08)


# ---------------------------------------------------------------------------
# plants (drawn in the label's two colours)
# ---------------------------------------------------------------------------

def leaf_args():
    return P["leaf"], P["leaf_dark"], P["leaf_line"]


def fruit_chilli(c, L, Wd, body):
    chilli(c, L, Wd, body, P["shine"], P["leaf_dark"], P["leaf_line"])


def chilli_plant(c, cx, base):
    rnd = random.Random(7)
    pot(c, cx, base, 9.0, 6.4)
    top = base - 6.4
    branches = [
        ((cx, top), (cx - 1, top - 4), (cx - 6, top - 6), (cx - 8.5, top - 13)),
        ((cx, top - 1), (cx + 1.5, top - 5), (cx + 6, top - 7), (cx + 9.5, top - 14.5)),
        ((cx, top), (cx - .5, top - 8), (cx - 2.5, top - 14), (cx - 5, top - 23)),
        ((cx, top), (cx + .5, top - 9), (cx + 2.5, top - 15), (cx + 4.5, top - 24.5)),
        ((cx, top), (cx, top - 10), (cx + .4, top - 19), (cx - .3, top - 28)),
        ((cx - 3.2, top - 8.5), (cx - 6, top - 11), (cx - 9, top - 14), (cx - 10.5, top - 20)),
        ((cx + 3.6, top - 8), (cx + 7, top - 11), (cx + 9.5, top - 15), (cx + 10.4, top - 21.5)),
    ]
    for b in branches:
        stem(c, b, P["stem"], .42)
    for bi, b in enumerate(branches):
        for k, t in enumerate((.42, .7, 1.0)):
            x, y = bez(*b, t)
            x2, y2 = bez(*b, min(t + .02, 1)) if t < 1 else bez(*b, t)
            x1, y1 = bez(*b, t - .02)
            ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
            side = 1 if (k + bi) % 2 else -1
            a = ang + (0 if t == 1 else side * 48) + rnd.uniform(-8, 8)
            L = (4.6 if t == 1 else 4.0) * rnd.uniform(.85, 1.1)
            rotated(c, x, y, a, leaf, L, L * .42, *leaf_args())
    # upright bird's eye chillies at the nodes, alternating the two colours
    spots = [(0, .55), (1, .5), (2, .55), (3, .6), (4, .62), (5, .55), (6, .6), (2, .85), (1, .85)]
    for i, (bi, t) in enumerate(spots):
        x, y = bez(*branches[bi], t)
        a = -90 + rnd.uniform(-22, 22)
        rotated(c, x, y - .3, a, fruit_chilli, rnd.uniform(4.0, 5.0), 1.2, P["fruit"][i % 2])
    for bi, t in ((0, .8), (3, .35), (6, .85)):
        x, y = bez(*branches[bi], t)
        flower(c, x + .6, y - .4, .7)


def compound_leaf(c, L, n, s):
    """Curry leaf (pinnate): rachis along +x with n alternating leaflets."""
    r = c.beginPath()
    r.moveTo(0, 0)
    r.curveTo(L * .35, -L * .05, L * .7, -L * .04, L, 0)
    paint(c, r, stroke=P["stem"], lw=.18)
    for i in range(n):
        t = (i + 1) / (n + 1)
        x = L * t
        y = -L * .05 * math.sin(math.pi * t)
        side = 1 if i % 2 else -1
        size = s * (1.05 - .35 * t)
        rotated(c, x, y, side * 55, leaf, size, size * .42, *leaf_args())
    rotated(c, L, 0, 0, leaf, s * .8, s * .34, *leaf_args())


def curry_plant(c, cx, base):
    rnd = random.Random(11)
    pot(c, cx, base, 9.0, 6.4)
    top = base - 6.4
    sprays = [(-150, 11.5, 13), (-128, 15, 15), (-106, 18, 17), (-84, 20.5, 17),
              (-64, 17.5, 15), (-42, 14, 13), (-118, 9, 9), (-58, 9.5, 9)]
    for ang, L, n in sprays:
        a = math.radians(ang)
        sx, sy = cx + math.cos(a) * 1.2, top - .4
        ex, ey = sx + math.cos(a) * L * .28, sy + math.sin(a) * L * .28
        stem(c, ((cx, top), (cx, top - 1), (sx, sy), (ex, ey)), P["stem"], .4)
        rotated(c, ex, ey, ang + rnd.uniform(-5, 5), compound_leaf, L * .72, n, 2.4 * rnd.uniform(.92, 1.08))
    # berry clusters and blossom
    for bx, by in ((cx - 6.5, top - 15.5), (cx + 7.2, top - 13.5)):
        for i in range(6):
            a = math.radians(i * 60 + 15)
            c.setFillColor(HexColor(P["fruit"][i % 2]))
            c.circle(bx + math.cos(a) * .75, by + math.sin(a) * .75, .48, stroke=0, fill=1)
        c.setFillColor(HexColor(P["fruit"][0]))
        c.circle(bx, by, .48, stroke=0, fill=1)
    for fx, fy in ((cx - 1.8, top - 21.5), (cx + 2.6, top - 22.5), (cx + .3, top - 23.6)):
        flower(c, fx, fy, .62)


PLANTS = {"chilli": chilli_plant, "curry": curry_plant}


# ---------------------------------------------------------------------------
# ingredient icons (local frame centred on the icon, radius ~3 mm)
# ---------------------------------------------------------------------------

def icon(c, kind):
    D, A = P["fruit"]
    c.setFillColor(HexColor(P["icon_bg"]))
    c.circle(0, 0, 3.4, stroke=0, fill=1)
    if kind == "chilli":
        rotated(c, -1.9, 1.3, -35, fruit_chilli, 4.6, 1.15, D)
    elif kind == "greenchilli":
        rotated(c, -1.9, 1.3, -35, fruit_chilli, 4.6, 1.15, A)
    elif kind == "garlic":
        p = c.beginPath()
        p.moveTo(0, -2.6)
        p.curveTo(.3, -1.6, 2.4, -1.2, 2.3, .6)
        p.curveTo(2.2, 2.1, .9, 2.4, 0, 2.4)
        p.curveTo(-.9, 2.4, -2.2, 2.1, -2.3, .6)
        p.curveTo(-2.4, -1.2, -.3, -1.6, 0, -2.6)
        p.close()
        paint(c, p, fill=PAPER, stroke=A, lw=.14)
        for dx in (-1.1, 0, 1.1):
            q = c.beginPath()
            q.moveTo(dx * .4, -1.6)
            q.curveTo(dx * 1.1, -.4, dx * 1.1, 1.2, dx * .6, 2.3)
            paint(c, q, stroke=P["jaali_line"], lw=.1)
        r = c.beginPath()
        r.moveTo(-.7, 2.4)
        r.lineTo(-.4, 2.9)
        r.moveTo(0, 2.4)
        r.lineTo(0, 3.0)
        r.moveTo(.7, 2.4)
        r.lineTo(.4, 2.9)
        paint(c, r, stroke=A, lw=.1)
    elif kind == "lemon":
        c.setFillColor(HexColor(P["leaf"]))
        c.setStrokeColor(HexColor(D))
        c.setLineWidth(.15)
        c.circle(0, 0, 2.5, stroke=1, fill=1)
        c.setFillColor(HexColor(P["frame"]))
        c.circle(0, 0, 2.05, stroke=0, fill=1)
        c.setStrokeColor(HexColor(P["leaf"]))
        c.setLineWidth(.16)
        for i in range(8):
            a = math.radians(i * 45)
            c.line(0, 0, math.cos(a) * 1.95, math.sin(a) * 1.95)
        c.setFillColor(HexColor(PAPER))
        c.circle(0, 0, .3, stroke=0, fill=1)
    elif kind == "curry":
        rotated(c, -2.5, 1.6, -38, compound_leaf, 4.5, 7, 1.35)
    elif kind == "mustard":
        rnd = random.Random(3)
        for i in range(16):
            a, r = rnd.uniform(0, 6.28), 2.1 * math.sqrt(rnd.random())
            c.setFillColor(HexColor(rnd.choice([D, D, A, P["leaf"]])))
            c.circle(math.cos(a) * r, math.sin(a) * r * .8 + .3, .42, stroke=0, fill=1)


# ---------------------------------------------------------------------------
# label layout
# ---------------------------------------------------------------------------

def veg_mark(L, x, y, s=3.0):
    # statutory FSSAI veg symbol: keeps its regulation green
    L.rect(x, y, s, s, fill="#FFFFFF", stroke="#2E8B3A", lw=.28)
    L.circle(x + s / 2, y + s / 2, s * .26, fill="#2E8B3A")


def left_panel(L, f, k=1.0):
    """Story, ingredient icons, ingredients, allergens, storage. k scales type."""
    x, w = 3.4, SIDE_W - 6.4
    ink, head, rule = P["panel_ink"], P["panel_head"], P["panel_rule"]
    hs, bs, lead = 5.6 * k, 5.0 * k, 2.2 * k

    def heading(y, s):
        L.text(x, y, s, F_HEAD, hs, head, "start", .06)
        return y + 2.9 * k

    y = heading(5.6, "Our story")
    y = L.para(x, y, f["story"], F_BODY, bs, ink, w, lead)
    y += .9
    L.line(x, y, x + w, y, rule, .12)
    y = heading(y + 3.6 * k, "What's inside")
    y += 3.3
    for i, (kind, lab) in enumerate(f["icons"]):
        ix = x + w / 6 + i * w / 3
        if not L.dry:
            with L.local(ix, y, .78) as c:
                icon(c, kind)
        L.text(ix, y + 4.7, lab, F_BODY_M, 3.9, ink, track=.08)
    y += 6.6
    L.line(x, y, x + w, y, rule, .12)
    y = heading(y + 3.6 * k, "Ingredients")
    y = L.para(x, y, f["ingredients"], F_BODY, bs, ink, w, lead)
    y = heading(y + 1.5 * k, "Allergens")
    y = L.para(x, y, "Contains cashew (tree nut). Made in a facility that also handles "
               "peanuts, sesame & milk.", F_BODY, bs, ink, w, lead)
    y = heading(y + 1.5 * k, "Storage")
    y = L.para(x, y, "Store in a cool, dry place. Once opened, keep airtight and enjoy "
               "within 7 days.", F_BODY, bs, ink, w, lead)
    return y - lead + .8


BAR_W, BAR_H = 21.0, 10.4


def right_panel(L, f, k=1.0):
    """Nutrition, net wt / MRP, dates, manufacturer, FSSAI. Barcode drawn separately."""
    x0, x1 = FX1 + 3.0, W - 3.4
    w = x1 - x0
    ink, head, rule = P["panel_ink"], P["panel_head"], P["panel_rule"]
    hs, bs, rs = 5.6 * k, 4.5 * k, 4.6 * k
    y = 5.6
    L.text(x0, y, "Nutrition information", F_HEAD, hs, head, "start", .03)
    y += 2.6 * k
    L.text(x0, y, "Approx. values per 100 g", F_BODY, bs * .95, ink, "start")
    y += 1.1 * k
    L.line(x0, y, x1, y, ink, .2)
    for lab, val in f["nutrition"]:
        y += 2.45 * k
        sub = lab.startswith("  ")
        font = F_BODY if sub else F_BODY_M
        L.text(x0 + (1.8 if sub else 0), y, lab.strip(), font, rs, ink, "start")
        L.text(x1, y, val, font, rs, ink, "end")
        L.line(x0, y + .85 * k, x1, y + .85 * k, rule, .1)
    y += 3.7 * k
    L.text(x0, y, "Net wt.", F_HEAD, 5.2 * k, head, "start")
    L.text(x1, y, "200 g", F_HEAD, 5.2 * k, ink, "end")
    y += 2.6 * k
    L.text(x0, y, "MRP", F_HEAD, 5.2 * k, head, "start")
    L.text(x1, y, "₹ 000.00", F_HEAD, 5.2 * k, ink, "end")
    y += 2.0 * k
    L.text(x0, y, "(Incl. of all taxes)", F_BODY, 3.9 * k, ink, "start")
    y += 2.5 * k
    y = L.para(x0, y, "Batch no., packed on & best before: see base. Best before 6 months "
               "from packing.", F_BODY, 4.1 * k, ink, w, 1.95 * k)
    y += -.6 * k
    L.line(x0, y, x1, y, rule, .12)
    y += 2.6 * k
    L.text(x0, y, "Mfd. & packed by", F_HEAD, 4.8 * k, head, "start")
    y = L.para(x0, y + 2.2 * k, "Ashvena Foods, [address line], [city] - [PIN], India. "
               "Care: care@ashvena.in", F_BODY, 4.1 * k, ink, w, 1.95 * k)
    L.text(x0, y, "FSSAI Lic. No. 00000000000000", F_BODY_M, 4.1 * k, ink, "start")
    return y + .6


def barcode(L, x1):
    bx, by = FX1 + 3.0, H - 3.0 - BAR_H
    L.rect(bx, by, BAR_W, BAR_H, fill="#FFFFFF", r=.8)
    bc = eanbc.Ean13BarcodeWidget("890000000000")      # placeholder EAN-13
    bc.barHeight = 6.2 * mm
    bc.barWidth = .23 * mm
    bc.fontSize = 4.6
    bc.fontName = F_BODY
    x_a, y_a, x_b, y_b = bc.getBounds()
    d = Drawing(x_b - x_a, y_b - y_a)
    d.add(bc)
    sx = (BAR_W - 2.0) * mm / (x_b - x_a)
    c = L.c
    c.saveState()
    c.translate(L.X(bx + 1.0), L.Y(by + BAR_H - .7))
    c.scale(sx, sx)
    renderPDF.draw(d, c, -x_a, -y_a)
    c.restoreState()
    veg_mark(L, x1 - 3.0, H - 3.0 - 3.0, 3.0)


def fit(L, panel, f, limit):
    """Largest type scale (<= 1) at which panel ends above limit, then draw it."""
    k = 1.0
    L.dry = True
    while k > .7 and panel(L, f, k) > limit:
        k -= .01
    L.dry = False
    panel(L, f, k)
    return k


def front_panel(L, f):
    ink, acc, muted = P["ink"], P["acc"], P["muted"]
    # arch illustration standing on the bottom edge
    aw, ah, atop = 30.0, 66.0, 7.5
    ax = FX0 + 4.0
    with L.local(ax, atop) as c:
        arch_panel(c, aw, ah, f["arch"], PLANTS[f["plant"]])

    x0, x1 = ax + aw + 3.0, FX1 - 3.0
    cx = (x0 + x1) / 2
    L.logo(cx, 5.4, 9.6)

    size = 36
    while L.width(f["name"], F_NAME, size) > (x1 - x0) - 3:
        size -= .5
    L.text(cx, 30.2, f["name"], F_NAME, size, ink)
    cw = L.text(cx, 37.0, "CASHEWS", F_HEAD, 8.2, acc, track=.42)
    gap, ln = 2.6, 6.0
    L.line(cx - cw / 2 - gap - ln, 35.9, cx - cw / 2 - gap, 35.9, acc, .2)
    L.line(cx + cw / 2 + gap, 35.9, cx + cw / 2 + gap + ln, 35.9, acc, .2)

    L.para(cx, 42.6, f["desc"], F_BODY, 5.6, ink, (x1 - x0) - 3, 2.65, anchor="middle")

    pw = L.width(f["notes"], F_BODY_M, 5.0, .12) + 7
    L.rect(cx - pw / 2, 49.2, pw, 4.9, fill=acc, r=2.45)
    L.text(cx, 52.55, f["notes"], F_BODY_M, 5.0, P["pill_ink"], track=.12)

    fy = 63.0
    L.line(x0, 57.6, x1, 57.6, muted, .14)
    veg_mark(L, x0, fy - 2.7, 3.0)
    L.text(x0 + 4.2, fy - .2, "100% VEG", F_BODY_M, 4.6, ink, "start", .08)
    hw = L.width("HEAT", F_BODY_M, 4.6, .12)
    hx = cx - (hw + 2.0 + 3 * 2.1) / 2 + 1
    L.text(hx, fy - .2, "HEAT", F_BODY_M, 4.6, ink, "start", .12)
    for i in range(3):
        px = hx + hw + 2.2 + i * 2.1
        if i < f["heat"]:
            L.circle(px, fy - 1.05, .7, fill=acc)
        else:
            L.circle(px, fy - 1.05, .65, stroke=acc, lw=.2)
    L.text(x1, fy - .2, "NET WT. 200 g", F_BODY_M, 4.6, ink, "end", .08)


def draw(c, f, ox=B, oy=B):
    P.clear()
    P.update(f["colors"])
    L = Label(c, ox, oy)
    c.saveState()
    p = c.beginPath()
    p.rect((ox - B) * mm, (oy - B) * mm, (W + 2 * B) * mm, (H + 2 * B) * mm)
    c.clipPath(p, stroke=0, fill=0)

    L.rect(-B, -B, W + 2 * B, H + 2 * B, fill=P["bg"])
    L.rect(-B, -B, SIDE_W + B, H + 2 * B, fill=P["panel"])
    L.rect(FX1, -B, SIDE_W + B, H + 2 * B, fill=P["panel"])
    fit(L, left_panel, f, H - 3.0)
    front_panel(L, f)
    fit(L, right_panel, f, H - 3.0 - BAR_H - 1.2)
    barcode(L, W - 3.4)
    c.restoreState()


# ---------------------------------------------------------------------------
# files
# ---------------------------------------------------------------------------

def new_canvas(path, w, h, title):
    c = canvas.Canvas(path, pagesize=(w * mm, h * mm),
                      initialFontName=F_BODY, initialFontSize=6)
    c.setTitle(title)
    c.setAuthor("Ashvena")
    c.setSubject("Direction F - Modern Botanical")
    return c


def build(f, path, crop_to_trim):
    """One label on its own page: bleed page with TrimBox set."""
    c = new_canvas(path, W + 2 * B, H + 2 * B, f"Ashvena {f['name']} Cashews - label 171 x 70 mm")
    trim = (B * mm, B * mm, (B + W) * mm, (B + H) * mm)
    c.setTrimBox(trim)
    c.setBleedBox((0, 0, (W + 2 * B) * mm, (H + 2 * B) * mm))
    if crop_to_trim:
        c.setCropBox(trim)
    draw(c, f)
    c.showPage()
    c.save()


# combined Illustrator sheet: both labels stacked, each with bleed + crop marks
SIDE, TOP, GAP = 14.0, 16.0, 22.0
SHEET_W = SIDE + W + 2 * B + SIDE
SHEET_H = TOP + 2 * (H + 2 * B) + GAP + TOP


def crop_marks(c, ox, oy):
    """Registration-colour crop marks around a trim box at (ox, oy) mm,
    plus short panel-division ticks top and bottom."""
    c.setStrokeColorCMYK(1, 1, 1, 1)
    c.setLineWidth(.25)
    off, ln = B + 2, 5
    for x in (ox, ox + FX0, ox + FX1, ox + W):
        tick = ln if x in (ox, ox + W) else 3
        for y, d in ((oy, -1), (oy + H, 1)):
            c.line(x * mm, (y + d * off) * mm, x * mm, (y + d * (off + tick)) * mm)
    for y in (oy, oy + H):
        for x, d in ((ox, -1), (ox + W, 1)):
            c.line((x + d * off) * mm, y * mm, (x + d * (off + ln)) * mm, y * mm)


def build_sheet(path):
    c = new_canvas(path, SHEET_W, SHEET_H, "Ashvena Peri Peri & Kadi Patta Cashews - labels 171 x 70 mm")
    for i, (slug, f) in enumerate(LABELS.items()):
        bleed_top = TOP + i * (H + 2 * B + GAP)          # from the sheet top
        ox = SIDE + B
        oy = SHEET_H - bleed_top - B - H
        draw(c, f, ox, oy)
        crop_marks(c, ox, oy)
        t = c.beginText((ox + 8) * mm, (SHEET_H - bleed_top + 6) * mm)
        t.setFont(F_BODY, 6.5)
        t.setFillColor(HexColor("#7a7a7a"))
        t.textOut(f"{f['name'].upper()} CASHEWS   ·   171 × 70 mm trim   ·   "
                  f"panels 40 / 91 / 40 mm   ·   3 mm bleed")
        c.drawText(t)
    c.showPage()
    c.save()


def main():
    os.makedirs(OUT, exist_ok=True)
    sheet = os.path.join(OUT, "ashvena-cashews_modern-labels.ai")
    build_sheet(sheet)
    subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile", sheet,
                    os.path.join(OUT, "ashvena-modern-labels-board")], check=True)
    print("built", os.path.basename(sheet))
    for slug, f in LABELS.items():
        base = os.path.join(OUT, f"ashvena-{slug}-cashews_label")
        build(f, base + ".pdf", crop_to_trim=False)
        trim_pdf = os.path.join(TMP, slug + ".pdf")
        build(f, trim_pdf, crop_to_trim=True)
        subprocess.run(["pdftoppm", "-png", "-r", "300", "-singlefile", "-cropbox",
                        trim_pdf, base], check=True)
        print("built", os.path.relpath(base, OUT))


if __name__ == "__main__":
    main()
