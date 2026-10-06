#!/usr/bin/env python3
"""Ashvena 1953 visiting card: front in Dispensary blue, back in Brick red.

Uses the vector lockup in brand/ashvena-logo.svg (extracted from logo_final.ai).

Card: 3.5 x 2 in (88.9 x 50.8 mm) trim + 3 mm bleed on every side,
so each artboard is 94.9 x 56.8 mm at 10 px = 1 mm.

Output (stationery/visiting-card/):
  ashvena-visiting-card_front.ai / _back.ai     Illustrator files (PDF-compatible .ai, with bleed)
  ashvena-visiting-card_print.pdf               2-page print PDF (front, back), with bleed
  ashvena-visiting-card_front.svg / _back.svg   editable SVG masters (named layers, live text)
  ashvena-visiting-card_front.png / _back.png   previews cropped to trim
  ashvena-visiting-card-board.png               both sides on one board

Requires: pip install playwright, plus Cormorant Garamond and Montserrat installed.
"""
import base64
import glob
import os
import re
from xml.sax.saxutils import escape as esc

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "..", "brand", "ashvena-logo.svg")
OUT = os.path.join(HERE, "..", "stationery", "visiting-card")

MM = 10
BLEED = 3 * MM
TW, TH = 889, 508                       # trim, px
W, H = TW + 2 * BLEED, TH + 2 * BLEED   # artboard incl. bleed
X0, Y0 = BLEED, BLEED                   # trim origin

BRICK = "#941528"
LAC = "#35070F"
DISPENSARY = "#CBE9F1"
DISPENSARY_DEEP = "#B5DCE8"
SAGE = "#BFD9D6"                        # mark colour when reversed on brick
KHADI = "#FCE4CD"

F_SERIF = "'Cormorant Garamond', Garamond, Georgia, serif"
F_SANS = "Montserrat, Helvetica, Arial, sans-serif"

# Placeholder details: replace before print.
CARD = dict(
    name="Your Name",
    title="Designation",
    phone="+91 00000 00000",
    email="name@yourdomain.com",
    web="www.yourwebsite.com",
    address="Address line, City 000 000",
)


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


def lockup(gid, cx, top, height, mark, word, year, names=("Mark", "Wordmark", "Year")):
    """Place the stacked lockup (or a subset of it) centred on cx, scaled to `height`."""
    bx, by, bw, bh = union(*names)
    s = height / bh
    tx, ty = cx - (bx + bw / 2) * s, top - by * s
    fills = {"Mark": mark, "Wordmark": word, "Year": year}
    body = "".join(f'<path id="{gid}_{n}" fill="{fills[n]}" d="{LOGO_PARTS[n][1]}"/>' for n in names)
    return f'<g id="{gid}" transform="translate({tx:.2f} {ty:.2f}) scale({s:.5f})">{body}</g>'


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


def icon(kind, x, y, c):
    """Tiny line icons (about 2.4 mm), drawn centred on (x, y)."""
    sw = 'fill="none" stroke="{}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"'.format(c)
    if kind == "phone":
        return (f'<path transform="translate({x - 11} {y - 11})" {sw} '
                f'd="M7 3 L10 3 L12 8 L9.5 10 C10.8 12.8 13.2 15.2 16 16.5 L18 14 L23 16 L23 19 '
                f'C23 21 21.5 22.5 19.5 22.3 C11 21.5 4.5 15 3.7 6.5 C3.5 4.5 5 3 7 3 Z"/>')
    if kind == "email":
        return (f'<g transform="translate({x - 12} {y - 9})" {sw}><rect x="1" y="1" width="22" height="16" rx="2"/>'
                f'<path d="M2 3 L12 10.5 L22 3"/></g>')
    if kind == "web":
        return (f'<g transform="translate({x - 11} {y - 11})" {sw}><circle cx="11" cy="11" r="10"/>'
                f'<ellipse cx="11" cy="11" rx="4.5" ry="10"/><path d="M1.5 8 H20.5 M1.5 14 H20.5"/></g>')
    if kind == "pin":
        return (f'<g transform="translate({x - 9} {y - 12})" {sw}>'
                f'<path d="M9 23 C9 23 1 14.5 1 9 A8 8 0 0 1 17 9 C17 14.5 9 23 9 23 Z"/>'
                f'<circle cx="9" cy="9" r="3"/></g>')
    return ""


def front():
    o = [f'<rect id="Background" width="{W}" height="{H}" fill="{DISPENSARY}"/>']
    # Oversized mark bleeding off the right edge as a quiet watermark.
    o.append('<g id="Watermark" opacity=".5">'
             + lockup("Watermark_Mark", X0 + TW + 70, Y0 - 150, 660, DISPENSARY_DEEP, "", "", names=("Mark",))
             + '</g>')

    # Left panel: stacked lockup.
    panel = 360
    o.append(lockup("Logo", X0 + panel / 2 + 10, Y0 + 92, 324, BRICK, LAC, BRICK))
    o.append(f'<line id="Divider" x1="{X0 + panel + 20}" y1="{Y0 + 92}" x2="{X0 + panel + 20}" '
             f'y2="{Y0 + TH - 92}" stroke="{BRICK}" stroke-width="1.6" opacity=".7"/>')

    # Right panel: name and contact details.
    x = X0 + panel + 62
    c = CARD
    o.append('<g id="Name_Block">'
             + text(x, Y0 + 158, c["name"], 52, LAC, F_SERIF, 600)
             + text(x + 2, Y0 + 196, c["title"].upper(), 19, BRICK, F_SANS, 600, ls=3.2)
             + f'<line x1="{x + 2}" y1="{Y0 + 226}" x2="{x + 62}" y2="{Y0 + 226}" stroke="{BRICK}" stroke-width="2.4"/>'
             + '</g>')
    rows = [("phone", c["phone"]), ("email", c["email"]), ("web", c["web"]), ("pin", c["address"])]
    lines = []
    for i, (k, v) in enumerate(rows):
        y = Y0 + 286 + i * 42
        lines.append(icon(k, x + 12, y - 8, BRICK))
        lines.append(text(x + 40, y, v, 21, LAC, F_SANS, 500, ls=.3))
    o.append('<g id="Contact_Details">' + "".join(lines) + '</g>')
    o.append(guides())
    return svg("\n".join(o))


def back():
    o = [f'<rect id="Background" width="{W}" height="{H}" fill="{BRICK}"/>']
    inset = 40
    o.append(f'<rect id="Frame" x="{X0 + inset}" y="{Y0 + inset}" width="{TW - 2 * inset}" '
             f'height="{TH - 2 * inset}" fill="none" stroke="{KHADI}" stroke-width="1.6" opacity=".45"/>')
    o.append(f'<rect id="Frame_Inner" x="{X0 + inset + 8}" y="{Y0 + inset + 8}" width="{TW - 2 * inset - 16}" '
             f'height="{TH - 2 * inset - 16}" fill="none" stroke="{KHADI}" stroke-width=".8" opacity=".3"/>')
    o.append(lockup("Logo_Reversed", X0 + TW / 2, Y0 + 92, 324, SAGE, KHADI, SAGE))
    o.append(guides())
    return svg("\n".join(o))


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
        f, bk = ("data:image/png;base64," + base64.b64encode(open(s[:-4] + ".png", "rb").read()).decode()
                 for s in paths)
        pg = b.new_page(viewport={"width": 2100, "height": 1200})
        pg.set_content(board_html(f, bk), wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.screenshot(path=os.path.join(OUT, "ashvena-visiting-card-board.png"))
        print("rendered ashvena-visiting-card-board.png")
        b.close()
    package([s[:-4] + ".pdf" for s in paths])


def package(pdfs):
    """Write each side as a PDF-compatible .ai and merge both into one print PDF."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import RectangleObject
    pt = 72 / 25.4 / MM
    merged = PdfWriter()
    for pdf in pdfs:
        side = "Front" if pdf.endswith("_front.pdf") else "Back"
        w = PdfWriter(clone_from=PdfReader(pdf))
        # Chromium rounds the page up to whole points; crop back to the exact bleed size
        # (content is anchored top-left) and mark the trim for the printer.
        page = w.pages[0]
        top = float(page.mediabox.top)
        page.mediabox = page.cropbox = page.bleedbox = RectangleObject([0, top - H * pt, W * pt, top])
        page.trimbox = RectangleObject([BLEED * pt, top - (BLEED + TH) * pt, (BLEED + TW) * pt, top - BLEED * pt])
        w.write(pdf)
        w = PdfWriter(clone_from=PdfReader(pdf))
        w.add_metadata({"/Title": f"Ashvena 1953 Visiting Card - {side}", "/Creator": "generate_visiting_card.py"})
        with open(pdf[:-4] + ".ai", "wb") as fh:
            w.write(fh)
        merged.append(pdf)
        os.remove(pdf)
        print("wrote", os.path.basename(pdf[:-4] + ".ai"))
    merged.add_metadata({"/Title": "Ashvena 1953 Visiting Card"})
    with open(os.path.join(OUT, "ashvena-visiting-card_print.pdf"), "wb") as fh:
        merged.write(fh)
    print("wrote ashvena-visiting-card_print.pdf")


def main():
    os.makedirs(OUT, exist_ok=True)
    paths = []
    for side, fn in (("front", front), ("back", back)):
        p = os.path.join(OUT, f"ashvena-visiting-card_{side}.svg")
        open(p, "w").write(fn())
        paths.append(p)
        print("wrote", os.path.basename(p))
    render(paths)


if __name__ == "__main__":
    main()
