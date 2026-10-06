#!/usr/bin/env python3
"""Ashvena 1953 visiting card: front in Dispensary blue, back in Brick red.

Front: horizontal logo lockup, name, labelled contact rows and a dotted
Instagram QR code on plain blue.
Back: an oversized tone-on-tone (debossed) mark bleeding off the edge, with
the wordmark in Khadi Cream.

Uses the vector lockup in brand/ashvena-logo.svg (extracted from logo_final.ai).
Card: 3.5 x 2 in (88.9 x 50.8 mm) trim + 3 mm bleed, at 10 px = 1 mm.

Output (stationery/visiting-card/):
  ashvena-visiting-card.ai                    front + back as two artboards (PDF-compatible), with bleed
  ashvena-visiting-card_print.pdf             the same two pages for the printer
  ashvena-visiting-card_coreldraw-curves.pdf  the same two pages, text converted to outlines
  ashvena-visiting-card_front.svg / .png      editable SVG master + preview
  ashvena-visiting-card_back.svg  / .png
  ashvena-visiting-card-board.png

Requires: pip install playwright pypdf segno cairosvg, poppler-utils (pdftocairo), plus Cormorant Garamond and Montserrat.
"""
import base64
import glob
import os
import re
import subprocess
import tempfile
from xml.sax.saxutils import escape as esc

import segno

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "..", "brand", "ashvena-logo.svg")
OUT = os.path.join(HERE, "..", "stationery", "visiting-card")

MM = 10
BLEED = 3 * MM
TW, TH = 889, 508                       # trim, px
W, H = TW + 2 * BLEED, TH + 2 * BLEED   # artboard incl. bleed
X0, Y0 = BLEED, BLEED                   # trim origin

BRICK = "#941528"
EMBOSS_FACE = "#8B1326"
EMBOSS_SHADOW = "#6F0C1C"
EMBOSS_LIGHT = "#A8293E"
LAC = "#35070F"
DISPENSARY = "#CBE9F1"
SAGE = "#BFD9D6"                        # mark colour when reversed on brick
KHADI = "#FCE4CD"

F_SERIF = "'Cormorant Garamond', Garamond, Georgia, serif"
F_SANS = "Montserrat, Helvetica, Arial, sans-serif"

CARD = dict(
    name="Krishana Arora",
    mobile=["+91 79886 26068", "+91 81684 72560"],
    email="ashvena.sp@gmail.com",
    address="8 Marla, Sonipat, Haryana",
)
# Link taken verbatim from the QR code Instagram generated for the account.
INSTAGRAM = dict(
    handle="ashvena_1953",
    url="https://www.instagram.com/ashvena_1953?utm_source=qr&stkn=ZHF3cnhwemdkc3Bu",
)


# ---------------------------------------------------------------- logo

def load_logo():
    src = open(LOGO).read()
    parts = {}
    for pid, bbox, d in re.findall(r'<path id="(\w+)" data-bbox="([^"]+)" fill="[^"]+" d="([^"]+)"', src):
        parts[pid] = (tuple(map(float, bbox.split())), d)
    return parts


LOGO_PARTS = load_logo()


def union(*names):
    boxes = [LOGO_PARTS[n][0] for n in names]
    x0 = min(b[0] for b in boxes)
    y0 = min(b[1] for b in boxes)
    x1 = max(b[0] + b[2] for b in boxes)
    y1 = max(b[1] + b[3] for b in boxes)
    return x0, y0, x1 - x0, y1 - y0


def logo_path(gid, name, fill):
    return f'<path id="{gid}_{name}" fill="{fill}" d="{LOGO_PARTS[name][1]}"/>'


def lockup_horizontal(gid, x, y, mark_h, mark, word, year):
    """Mark on the left, wordmark and year to its right (as on the logo's landscape artboard)."""
    (mx, my, mw, mh), _ = LOGO_PARTS["Mark"]
    (wx, wy, ww, wh), _ = LOGO_PARTS["Wordmark"]
    (yx, yy, yw, yh), _ = LOGO_PARTS["Year"]
    s = mark_h / mh
    o = [f'<g id="{gid}">',
         f'<g transform="translate({x - mx * s:.2f} {y - my * s:.2f}) scale({s:.5f})">{logo_path(gid, "Mark", mark)}</g>']
    s2 = s * .82
    wx0, wy0 = x + mw * s * .76, y + mh * s * .24
    o.append(f'<g transform="translate({wx0 - wx * s2:.2f} {wy0 - wy * s2:.2f}) scale({s2:.5f})">'
             f'{logo_path(gid, "Wordmark", word)}</g>')
    yy0 = wy0 + wh * s2 + 6
    o.append(f'<g transform="translate({wx0 + 4 - yx * s2:.2f} {yy0 - yy * s2:.2f}) scale({s2:.5f})">'
             f'{logo_path(gid, "Year", year)}</g>')
    o.append('</g>')
    return "".join(o)


# ---------------------------------------------------------------- helpers

def text(x, y, s, size, fill, family=F_SANS, weight=400, ls=0, anchor="start", italic=False):
    it = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" letter-spacing="{ls}" text-anchor="{anchor}"{it}>{esc(s)}</text>')


def svg(body):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W / MM}mm" height="{H / MM}mm" '
            f'viewBox="0 0 {W} {H}">\n{body}\n</svg>\n')


def guides():
    """Trim line, hidden by default; switch on the layer in Illustrator to check placement."""
    return (f'<g id="Trim_Guide" display="none"><rect x="{X0}" y="{Y0}" width="{TW}" height="{TH}" '
            f'fill="none" stroke="#00a0e9" stroke-width="1"/></g>')


def instagram_glyph(cx, cy, size, c, sw):
    r = size / 2
    return (f'<g fill="none" stroke="{c}" stroke-width="{sw}">'
            f'<rect x="{cx - r:.2f}" y="{cy - r:.2f}" width="{size:.2f}" height="{size:.2f}" rx="{size * .28:.2f}"/>'
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{size * .23:.2f}"/></g>'
            f'<circle cx="{cx + size * .27:.2f}" cy="{cy - size * .27:.2f}" r="{size * .06:.2f}" fill="{c}"/>')


# ---------------------------------------------------------------- QR

def qr_code(gid, url, x, y, size, ink, paper):
    """Dotted QR in Instagram's style (round modules, rounded rings with round centres), glyph in the middle."""
    qr = segno.make(url, error="h")
    m = [list(r) for r in qr.matrix]
    n = len(m)
    u = size / n
    finders = [(0, 0), (n - 7, 0), (0, n - 7)]

    def in_finder(r, c):
        return any(fr <= r < fr + 7 and fc <= c < fc + 7 for fc, fr in finders)

    hole = int(n * .27) | 1
    h0 = (n - hole) // 2

    def in_hole(r, c):
        return h0 <= r < h0 + hole and h0 <= c < h0 + hole

    o = [f'<g id="{gid}">']
    for r in range(n):
        for c in range(n):
            if m[r][c] and not in_finder(r, c) and not in_hole(r, c):
                o.append(f'<circle cx="{x + (c + .5) * u:.2f}" cy="{y + (r + .5) * u:.2f}" r="{u * .48:.2f}" fill="{ink}"/>')
    for fc, fr in finders:
        fx, fy = x + fc * u, y + fr * u
        o.append(f'<rect x="{fx + u / 2:.2f}" y="{fy + u / 2:.2f}" width="{6 * u:.2f}" height="{6 * u:.2f}" '
                 f'rx="{1.7 * u:.2f}" fill="none" stroke="{ink}" stroke-width="{u:.2f}"/>')
        o.append(f'<circle cx="{fx + 3.5 * u:.2f}" cy="{fy + 3.5 * u:.2f}" r="{1.55 * u:.2f}" fill="{ink}"/>')
    cx, cy = x + size / 2, y + size / 2
    o.append(f'<rect x="{cx - hole * u / 2 + u * .3:.2f}" y="{cy - hole * u / 2 + u * .3:.2f}" '
             f'width="{hole * u - u * .6:.2f}" height="{hole * u - u * .6:.2f}" rx="{u * 1.6:.2f}" fill="{paper}"/>')
    o.append(instagram_glyph(cx, cy, hole * u * .62, ink, u * .62))
    o.append('</g>')
    return "".join(o)


# ---------------------------------------------------------------- sides

def place(gid, name, x, y, height, fill, anchor="start"):
    """One logo part scaled to `height`; (x, y) is its top-left, or top-right with anchor='end'."""
    (bx, by, bw, bh), d = LOGO_PARTS[name]
    s = height / bh
    if anchor == "end":
        x -= bw * s
    return (f'<g id="{gid}" transform="translate({x - bx * s:.2f} {y - by * s:.2f}) scale({s:.5f})">'
            f'<path fill="{fill}" d="{d}"/></g>')


def front():
    c = CARD
    o = [f'<rect id="Background" width="{W}" height="{H}" fill="{DISPENSARY}"/>']
    x = X0 + 64
    o.append(lockup_horizontal("Logo", x, Y0 + 52, 88, BRICK, LAC, BRICK))
    o.append('<g id="Name_Block">'
             + text(x, Y0 + 238, c["name"], 54, LAC, F_SERIF, 600)
             + f'<line x1="{x + 2}" y1="{Y0 + 264}" x2="{x + 56}" y2="{Y0 + 264}" stroke="{BRICK}" stroke-width="2"/>'
             + '</g>')
    lx, vx = x + 2, x + 128
    rows = [("MOBILE", c["mobile"][0], Y0 + 318), ("", c["mobile"][1], Y0 + 350),
            ("EMAIL", c["email"], Y0 + 396), ("ADDRESS", c["address"], Y0 + 442)]
    lines = []
    for label, value, y in rows:
        if label:
            lines.append(text(lx, y - 1, label, 15, BRICK, F_SANS, 600, ls=2.4))
        lines.append(text(vx, y, value, 23, LAC, F_SANS, 500, ls=.2))
    o.append('<g id="Contact_Details">' + "".join(lines) + '</g>')

    q, handle = 216, INSTAGRAM["handle"]
    qx, qy = X0 + TW - 64 - q, Y0 + 442 - 44 - q
    o.append(qr_code("QR_Instagram", INSTAGRAM["url"], qx, qy, q, BRICK, DISPENSARY))
    o.append('<g id="QR_Caption">'
             + instagram_glyph(qx + q / 2 - 2 - len(handle) * 6.6, qy + q + 37, 18, LAC, 1.8)
             + text(qx + q / 2 + 12, qy + q + 44, handle, 20, LAC, F_SANS, 500, ls=.4, anchor="middle")
             + '</g>')
    o.append(guides())
    return svg("\n".join(o))


def back():
    o = [f'<rect id="Background" width="{W}" height="{H}" fill="{BRICK}"/>']
    # Oversized mark, tone on tone, bleeding off the left and bottom edges. Drawn as a soft
    # deboss (light edge top-left, shadow bottom-right); the Emboss_Mark layer can also go
    # to the printer as a blind-deboss or spot-UV plate.
    mh, mx, my = 600, X0 - 120, Y0 + 40
    o.append('<g id="Emboss_Mark">'
             + place("Emboss_Lit_Edge", "Mark", mx + 1.6, my + 1.6, mh, EMBOSS_LIGHT)
             + place("Emboss_Shade_Edge", "Mark", mx - 1.6, my - 1.6, mh, EMBOSS_SHADOW)
             + place("Emboss_Face", "Mark", mx, my, mh, EMBOSS_FACE)
             + '</g>')
    rx = X0 + TW - 70
    o.append('<g id="Wordmark">'
             + place("Wordmark_Ashvena", "Wordmark", rx, Y0 + 205, 50, KHADI, anchor="end")
             + place("Wordmark_Year", "Year", rx, Y0 + 269, 24, SAGE, anchor="end")
             + '</g>')
    o.append(guides())
    return svg("\n".join(o))


# ---------------------------------------------------------------- render

def board_html(front_png, back_png):
    card = "width:889px;height:508px;border-radius:6px;box-shadow:0 30px 60px rgba(53,7,15,.28),0 6px 14px rgba(53,7,15,.18)"
    return f"""<html><body style="margin:0;width:2100px;height:1200px;background:linear-gradient(135deg,#f6efe6,#e9dfd2);
position:relative;font-family:Montserrat">
<img src="{back_png}" style="position:absolute;left:160px;top:150px;{card};transform:rotate(-6deg)">
<img src="{front_png}" style="position:absolute;left:1000px;top:480px;{card};transform:rotate(4deg)">
<div style="position:absolute;left:160px;bottom:70px;color:#35070F;font-size:20px;letter-spacing:4px">
ASHVENA 1953 &middot; VISITING CARD &middot; 3.5 &times; 2 IN</div>
</body></html>"""


def render(paths):
    from playwright.sync_api import sync_playwright
    kw = {}
    exe = glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome")
    if exe:
        kw["executable_path"] = exe[0]
    with sync_playwright() as p:
        b = p.chromium.launch(**kw)
        for s in paths:
            body = open(s).read().split("?>", 1)[1]
            px = re.sub(r'width="[^"]+mm" height="[^"]+mm"', f'width="{W}" height="{H}"', body, count=1)
            pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
            pg.set_content(f"<html><body style='margin:0'>{px.replace('<svg ', '<svg style=\"display:block\" ', 1)}"
                           "</body></html>", wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.screenshot(path=s[:-4] + ".png", clip={"x": X0, "y": Y0, "width": TW, "height": TH})
            pg.set_content(f"<html><body style='margin:0'>{body}</body></html>", wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.pdf(path=s[:-4] + ".pdf", width=f"{W / MM}mm", height=f"{H / MM}mm", print_background=True,
                   margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            pg.close()
            print("rendered", os.path.basename(s))

        def data(s):
            return "data:image/png;base64," + base64.b64encode(open(s[:-4] + ".png", "rb").read()).decode()

        pg = b.new_page(viewport={"width": 2100, "height": 1200})
        pg.set_content(board_html(data(paths[0]), data(paths[1])), wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.screenshot(path=os.path.join(OUT, "ashvena-visiting-card-board.png"))
        print("rendered ashvena-visiting-card-board.png")
        b.close()


def crop(pdf):
    """Crop Chromium's rounded-up page back to the exact bleed size and mark the trim."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import RectangleObject
    pt = 72 / 25.4 / MM
    w = PdfWriter(clone_from=PdfReader(pdf))
    page = w.pages[0]
    top = float(page.mediabox.top)            # content is anchored top-left
    page.mediabox = page.cropbox = page.bleedbox = RectangleObject([0, top - H * pt, W * pt, top])
    page.trimbox = RectangleObject([BLEED * pt, top - (BLEED + TH) * pt, (BLEED + TW) * pt, top - BLEED * pt])
    w.write(pdf)


def package(paths):
    """Front and back as two artboards in one PDF-compatible .ai, plus the same pages as a print PDF."""
    from pypdf import PdfWriter
    pdfs = [s[:-4] + ".pdf" for s in paths]
    curves(pdfs)
    merged = PdfWriter()
    for pdf in pdfs:
        crop(pdf)
        merged.append(pdf)
    merged.add_metadata({"/Title": "Ashvena 1953 Visiting Card (front, back)", "/Creator": "generate_visiting_card.py"})
    for name in ("ashvena-visiting-card.ai", "ashvena-visiting-card_print.pdf"):
        with open(os.path.join(OUT, name), "wb") as fh:
            merged.write(fh)
        print("wrote", name)
    for pdf in pdfs:
        os.remove(pdf)


def curves(pdfs):
    """Same two pages with every glyph converted to outlines, for CorelDRAW (no fonts needed).

    pdftocairo writes each glyph as a vector path in SVG; cairosvg turns that back into PDF.
    Runs on Chromium's uncropped pages (content anchored top-left), then trims to the bleed size.
    """
    import cairosvg
    from pypdf import PdfWriter
    pt = 72 / 25.4 / MM
    merged = PdfWriter()
    with tempfile.TemporaryDirectory() as tmp:
        for i, pdf in enumerate(pdfs):
            svg_path = os.path.join(tmp, f"{i}.svg")
            subprocess.run(["pdftocairo", "-svg", pdf, svg_path], check=True)
            src = open(svg_path).read()
            src = re.sub(r'width="[^"]+" height="[^"]+" viewBox="[^"]+"',
                         f'width="{W * pt:.6f}pt" height="{H * pt:.6f}pt" viewBox="0 0 {W * pt:.6f} {H * pt:.6f}"',
                         src, count=1)
            out = os.path.join(tmp, f"{i}.pdf")
            cairosvg.svg2pdf(bytestring=src.encode(), write_to=out)
            crop(out)
            merged.append(out)
        merged.add_metadata({"/Title": "Ashvena 1953 Visiting Card (front, back) - text as curves",
                             "/Creator": "generate_visiting_card.py"})
        name = "ashvena-visiting-card_coreldraw-curves.pdf"
        with open(os.path.join(OUT, name), "wb") as fh:
            merged.write(fh)
        print("wrote", name)


def main():
    os.makedirs(OUT, exist_ok=True)
    paths = []
    for name, src in (("front", front()), ("back", back())):
        p = os.path.join(OUT, f"ashvena-visiting-card_{name}.svg")
        open(p, "w").write(src)
        paths.append(p)
        print("wrote", os.path.basename(p))
    render(paths)
    package(paths)


if __name__ == "__main__":
    main()
