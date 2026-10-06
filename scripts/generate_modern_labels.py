#!/usr/bin/env python3
"""Ashvena modern botanical labels - Direction F.

Clean, modern front labels for Peri Peri and Kadi Patta cashews built only
from the supplied watercolour illustrations (coconut palm, pink arch,
sage window, twin palms). Flat colour fields that match each painting's
paper tone, so the art bleeds into the label, with a centred type stack.

Size: 174 x 80 mm trim, 3 mm bleed.
Output (packaging/F-modern-botanical/):
  ashvena-<flavour>-cashews_label.ai   Illustrator file (PDF-compatible),
                                       artboard = 174 x 80 mm trim
  ashvena-<flavour>-cashews_label.pdf  print PDF with bleed, TrimBox set
  ashvena-<flavour>-cashews_label.png  preview (trim only)

Usage:  pip install reportlab pillow
        python3 scripts/generate_modern_labels.py
"""
import os
import subprocess
import tempfile

from PIL import Image, ImageFilter
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "packaging", "F-modern-botanical")
ART = os.path.join(OUT, "art")
FONTS = os.path.join(HERE, "fonts")

W, H, B = 174.0, 80.0, 3.0          # trim width/height, bleed (mm)
UPSCALE = 4                          # source art is ~270 px wide
TMP = tempfile.mkdtemp(prefix="ashvena-art-")

for name in ("Fraunces-SemiBold", "Manrope-Regular", "Manrope-Medium", "Manrope-Bold", "Manrope-ExtraBold"):
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, name + ".ttf")))

LABELS = {
    "peri-peri": dict(
        name="Peri Peri",
        bg="#EBDBD0", ink="#692721", acc="#8B4729", pill_ink="#F7EDE6", muted="#9A6F5E",
        # palette: Maple Spice #692721 + Burnt Orange #8B4729
        left=("src_coconut-palm-pomegranate.png", "right"),
        right=("src_pink-arch-banana.png", "left"),
        desc=["Whole W240 cashews, slow-roasted and tossed",
              "in bird's eye chilli, roasted garlic & lemon."],
        notes="FIERY  ·  TANGY  ·  CRUNCHY",
        heat=3,
    ),
    "kadi-patta": dict(
        name="Kadi Patta",
        bg="#E1E6D2", ink="#283618", acc="#606C38", pill_ink="#EEF2E4", muted="#6F7858",
        # palette: Pakistan Green #283618 + Dark Moss Green #606C38
        left=("src_sage-twin-palms.png", "right"),
        right=("src_sage-window-banana.png", "left"),
        desc=["Golden-roasted W240 cashews tempered with",
              "curry leaves, mustard seeds & green chilli."],
        notes="AROMATIC  ·  SAVOURY  ·  CRUNCHY",
        heat=1,
    ),
}


# ---------------------------------------------------------------------------
# artwork prep
# ---------------------------------------------------------------------------

def prep_art(src, feather_side):
    """Clean, upscale and feather one illustration; returns (path, w, h)."""
    im = Image.open(os.path.join(ART, src)).convert("RGB")
    px = im.load()
    w, h = im.size
    # remove flat grey UI rules (rows that are a single neutral grey) by
    # blending the nearest clean rows above and below
    def is_rule(y):
        row = {px[x, y] for x in range(0, w, 7)}
        v = next(iter(row))
        return len(row) == 1 and len(set(v)) == 1 and 100 < v[0] < 200
    rules = {y for y in range(1, h - 1) if is_rule(y)}
    for y in sorted(rules):
        up = max(k for k in range(y) if k not in rules)
        dn = min(k for k in range(y + 1, h) if k not in rules)
        u = (y - up) / (dn - up)
        for x in range(w):
            a, b = px[x, up], px[x, dn]
            px[x, y] = tuple(round(i + (j - i) * u) for i, j in zip(a, b))
    im = im.resize((w * UPSCALE, h * UPSCALE), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=40, threshold=2))
    W2, H2 = im.size
    alpha = Image.new("L", (W2, H2), 255)
    a = alpha.load()
    f = int(W2 * .07)
    for x in range(f):
        v = int(255 * (x / f) ** 1.6)
        col = x if feather_side == "left" else W2 - 1 - x
        for y in range(H2):
            a[col, y] = v
    im.putalpha(alpha)
    path = os.path.join(TMP, src.replace("src_", ""))
    im.save(path, optimize=True)
    return path, w, h


# ---------------------------------------------------------------------------
# drawing helpers (trim-space mm, y measured from the top edge)
# ---------------------------------------------------------------------------

class Label:
    def __init__(self, c):
        self.c = c

    @staticmethod
    def X(x):
        return (B + x) * mm

    @staticmethod
    def Y(y):
        return (B + H - y) * mm

    def text(self, x, y, s, font, size, color, anchor="middle", track=0.0):
        """Draw text with tracking (em fraction); y is the baseline."""
        c = self.c
        cs = size * track
        w = pdfmetrics.stringWidth(s, font, size) + cs * (len(s) - 1)
        x0 = self.X(x) - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
        t = c.beginText(x0, self.Y(y))
        t.setFont(font, size)
        t.setCharSpace(cs)
        t.setFillColor(HexColor(color))
        t.textOut(s)
        c.drawText(t)
        return w / mm

    def width(self, s, font, size, track=0.0):
        return (pdfmetrics.stringWidth(s, font, size) + size * track * (len(s) - 1)) / mm

    def rect(self, x, y, w, h, fill=None, stroke=None, lw=.25, r=0):
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
        c = self.c
        if fill:
            c.setFillColor(HexColor(fill))
        if stroke:
            c.setStrokeColor(HexColor(stroke))
            c.setLineWidth(lw * mm)
        c.circle(self.X(x), self.Y(y), r * mm, stroke=1 if stroke else 0, fill=1 if fill else 0)

    def line(self, x0, y0, x1, y1, color, lw=.2):
        c = self.c
        c.setStrokeColor(HexColor(color))
        c.setLineWidth(lw * mm)
        c.line(self.X(x0), self.Y(y0), self.X(x1), self.Y(y1))

    def image(self, path, x, y, w, h):
        self.c.drawImage(path, self.X(x), self.Y(y + h), w * mm, h * mm, mask="auto")


# ---------------------------------------------------------------------------
# label layout
# ---------------------------------------------------------------------------

def veg_mark(L, x, y, s=3.6):
    L.rect(x, y, s, s, stroke="#2E8B3A", lw=.3)
    L.circle(x + s / 2, y + s / 2, s * .26, fill="#2E8B3A")


def draw(c, f):
    L = Label(c)
    # background, full bleed
    L.rect(-B, -B, W + 2 * B, H + 2 * B, fill=f["bg"])

    # left illustration: full bleed height, flush to the left bleed edge
    lp, lw, lh = prep_art(*f["left"])
    left_h = H + 2 * B
    left_w = left_h * lw / lh
    L.image(lp, -B, -B, left_w, left_h)

    # right illustration: framed piece standing on the bottom edge
    rp, rw, rh = prep_art(*f["right"])
    right_h = H + 2 * B
    right_w = right_h * rw / rh
    L.image(rp, W + B - right_w, -B, right_w, right_h)

    # centred type stack between the two artworks
    x0, x1 = left_w - B + 2, W + B - right_w + 2
    cx = (x0 + x1) / 2
    ink, acc, muted = f["ink"], f["acc"], f["muted"]

    L.text(cx, 12.2, "ASHVENA", "Manrope-ExtraBold", 10.5, ink, track=.42)
    L.text(cx, 16.6, "SMALL-BATCH ROASTED  ·  EST. 1953", "Manrope-Medium", 4.6, muted, track=.22)

    name_size = 38
    while L.width(f["name"], "Fraunces-SemiBold", name_size, -.01) > (x1 - x0) - 6:
        name_size -= .5
    L.text(cx, 36.5, f["name"], "Fraunces-SemiBold", name_size, ink, track=-.01)

    cw = L.text(cx, 44.2, "CASHEWS", "Manrope-Bold", 9, acc, track=.62)
    # hairlines either side of CASHEWS
    gap, ln = 3.2, 9
    L.line(cx - cw / 2 - gap - ln, 43.0, cx - cw / 2 - gap, 43.0, acc, .22)
    L.line(cx + cw / 2 + gap, 43.0, cx + cw / 2 + gap + ln, 43.0, acc, .22)

    for i, s in enumerate(f["desc"]):
        L.text(cx, 51.4 + i * 3.4, s, "Manrope-Regular", 6.1, ink)

    # flavour notes pill
    pw = L.width(f["notes"], "Manrope-Bold", 5.6, .16) + 9
    L.rect(cx - pw / 2, 59.6, pw, 5.6, fill=acc, r=2.8)
    L.text(cx, 63.45, f["notes"], "Manrope-Bold", 5.6, f["pill_ink"], track=.16)

    # footer row: veg mark | heat meter | net weight
    fy = 73.4
    L.line(x0 + 4, 68.6, x1 - 4, 68.6, muted, .15)
    veg_mark(L, x0 + 4, fy - 3.1, 3.4)
    L.text(x0 + 9.4, fy - .2, "100% VEG", "Manrope-Bold", 4.8, ink, "start", .12)
    hw = L.width("HEAT", "Manrope-Bold", 4.8, .18)
    hx = cx - (hw + 2.2 + 3 * 2.4) / 2
    L.text(hx, fy - .2, "HEAT", "Manrope-Bold", 4.8, ink, "start", .18)
    for i in range(3):
        px = hx + hw + 2.6 + i * 2.4
        if i < f["heat"]:
            L.circle(px, fy - 1.0, .8, fill=acc)
        else:
            L.circle(px, fy - 1.0, .75, stroke=acc, lw=.22)
    L.text(x1 - 4, fy - .2, "NET WT. 200 g", "Manrope-Bold", 4.8, ink, "end", .12)


def build(slug, f, path, ai):
    c = canvas.Canvas(path, pagesize=((W + 2 * B) * mm, (H + 2 * B) * mm),
                      initialFontName="Manrope-Regular", initialFontSize=6)
    c.setTitle(f"Ashvena {f['name']} Cashews - label 174 x 80 mm")
    c.setAuthor("Ashvena")
    c.setSubject("Direction F - Modern Botanical")
    trim = (B * mm, B * mm, (B + W) * mm, (B + H) * mm)
    c.setTrimBox(trim)
    c.setBleedBox((0, 0, (W + 2 * B) * mm, (H + 2 * B) * mm))
    if ai:
        # Illustrator sets the artboard from the crop box: make it the trim.
        c.setCropBox(trim)
        c.setArtBox(trim)
    draw(c, f)
    c.showPage()
    c.save()


def main():
    os.makedirs(OUT, exist_ok=True)
    for slug, f in LABELS.items():
        base = os.path.join(OUT, f"ashvena-{slug}-cashews_label")
        build(slug, f, base + ".ai", ai=True)
        build(slug, f, base + ".pdf", ai=False)
        # preview of the trim area (the .ai crop box) at 300 dpi
        subprocess.run(["pdftoppm", "-png", "-r", "300", "-singlefile", "-cropbox",
                        base + ".ai", base], check=True)
        print("built", os.path.relpath(base, OUT))


if __name__ == "__main__":
    main()
