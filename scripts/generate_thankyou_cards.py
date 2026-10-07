#!/usr/bin/env python3
"""Ashvena stall thank-you cards (A6, with bleed).

Fronts: six Gen Z one-liners set big, stacked and two-tone in Bricolage
Grotesque Condensed ExtraBold, on the brand brick red and dispensary blue.
Back: khadi cream, the stacked logo, a short note from the family story
and a QR code.

Artboard: 111 x 154 mm = A6 105 x 148 mm trim + 3 mm bleed (4 px = 1 mm).
Output: packaging/G-thank-you-cards/ashvena-thankyou-<front-NN|back>.svg
Run render_previews.py G-thank-you-cards, then this script with --export
for the duplex print PDF and the Illustrator .ai files.
"""
import glob
import os
import re
import sys

import qrcode
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "packaging", "G-thank-you-cards")
BRAND = os.path.join(HERE, "..", "packaging", "brand")

BLEED = 12                              # 3 mm
W, H = 111 * 4, 154 * 4                 # 444 x 616 px
TX0, TY0, TX1, TY1 = BLEED, BLEED, W - BLEED, H - BLEED
SAFE = 22                               # 5.5 mm inside the trim

# brand palette (from Ashvena logo final.pdf)
BRICK, BLUE, LAC, KHADI, WHITE = "#941528", "#cbe9f1", "#350710", "#fce4cd", "#ffffff"

F_PUNCH = "'Bricolage Grotesque 96pt Condensed', 'Bricolage Grotesque', 'Arial Narrow', sans-serif"
F_SERIF = "Fraunces, Georgia, serif"
F_SANS = "'Bricolage Grotesque', Helvetica, Arial, sans-serif"

QR_URL = "https://wa.me/917988626068"   # Ashvena customer care (WhatsApp)

# (background, highlight colour, base colour, lines); "*" marks a highlighted line
FRONTS = [
    (BRICK, BLUE, KHADI, ["*YOU ATE.", "AND LEFT", "NO CRUMBS.", "*THANK YOU!"]),
    (BLUE, BRICK, LAC, ["*NO CAP,", "YOU JUST", "MADE OUR", "WHOLE", "*DAY."]),
    (BRICK, KHADI, BLUE, ["ELITE", "SNACK", "TASTE", "*DETECTED.", "THANKS,", "*BESTIE."]),
    (BLUE, LAC, BRICK, ["*IT'S GIVING", "73-YEAR-OLD", "RECIPE", "*ENERGY."]),
    (BRICK, BLUE, KHADI, ["*LOW-KEY", "*OBSESSED", "WITH YOU", "FOR STOPPING", "BY."]),
    (BLUE, BRICK, LAC, ["*YOUR", "*SNACK ERA", "STARTS", "NOW.", "*THANK YOU!"]),
]

BACK_NOTE = [
    "In 1947, when our family crossed the border, they carried one thing with them: "
    "a promise to do everything with purity. With honesty. No shortcuts. Ever.",
    "Since 1953, that promise has gone into everything we make. "
    "Today, a little of it goes home with you.",
    "We hope it tastes like home.",
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def font_file(family, style):
    for f in glob.glob(os.path.expanduser("~/.fonts/*.ttf")):
        n = TTFont(f, lazy=True)["name"]
        if (n.getDebugName(16) or n.getDebugName(1)) == family and (n.getDebugName(17) or n.getDebugName(2)) == style:
            return f
    raise SystemExit(f"font not installed: {family} {style}")


class Metrics:
    def __init__(self, path):
        t = TTFont(path)
        self.cmap, self.hmtx, self.upm = t.getBestCmap(), t["hmtx"], t["head"].unitsPerEm

    def width(self, s, size, ls=0):
        adv = sum(self.hmtx[self.cmap.get(ord(c), self.cmap[ord("?")])][0] for c in s)
        return adv * size / self.upm + ls * max(0, len(s) - 1)


def wrap(text, m, size, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if cur and m.width(trial, size) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur] if cur else lines


def text(x, y, s, size, fill, family, weight=400, anchor="start", ls=0, italic=False):
    it = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size:.1f}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}"{it}>{esc(s)}</text>')


def g(gid, body, extra=""):
    return f'<g id="{gid}"{extra}>\n{body}\n</g>'


def logo(kind, x, y, w, recolour=None):
    """Place the vector logo (stacked|horizontal) with its top-left at x, y, w px wide."""
    s = open(os.path.join(BRAND, f"ashvena-logo-{kind}.svg")).read()
    vb = re.search(r'viewBox="([^"]+)"', s).group(1)
    vx, vy, vw, vh = map(float, vb.split())
    paths = "\n".join(re.findall(r"<path\b[^>]*/>", s))
    for a, b in (recolour or {}).items():
        paths = paths.replace(f'fill="{a}"', f'fill="{b}"')
    h = w * vh / vw
    return (f'<svg x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" viewBox="{vb}">{paths}</svg>', h)


def doc(body, title):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W / 4:.0f}mm" height="{H / 4:.0f}mm" viewBox="0 0 {W} {H}">\n'
            f'<title>{esc(title)}</title>\n{body}\n</svg>\n')


# ---------------------------------------------------------------------------
# front
# ---------------------------------------------------------------------------

def front(i, spec, m):
    bg, hi, base, lines = spec
    x0, x1 = TX0 + SAFE, TX1 - SAFE
    words = [ln.lstrip("*") for ln in lines]
    # one size for the block: widest line fills the safe width, capped so short messages stay tall-ish
    top_room, bottom = TY0 + SAFE + 6, TY1 - SAFE - 34 - 26
    # widest line fills the safe width; the whole block must also fit above the logo row
    size = min(118, min((x1 - x0) / m.width(w, 1) for w in words),
               (bottom - top_room) / (.72 + .9 * (len(lines) - 1)))
    lead = size * .9
    cap = size * .72                                   # cap height of the condensed cut
    block_h = cap + lead * (len(lines) - 1)
    logo_svg, logo_h = logo("horizontal", x0, TY1 - SAFE - 34, 118,
                            {BRICK: BLUE, LAC: KHADI} if bg == BRICK else None)
    y = max(top_room + cap, bottom - block_h + cap)   # sit the block low, like a poster
    t = []
    for k, ln in enumerate(lines):
        col = hi if ln.startswith("*") else base
        t.append(text(x0 - size * .02, y + k * lead, ln.lstrip("*"), size, col, F_PUNCH, 800))
    heart = (f'<path d="M 0,4 C -6,-3 -14,2 -9,9 L 0,17 L 9,9 C 14,2 6,-3 0,4 Z" '
             f'transform="translate({x1 - 10:.1f} {TY1 - SAFE - 25:.1f}) scale(1.05)" fill="{hi}"/>')
    body = [g("Background", f'<rect width="{W}" height="{H}" fill="{bg}"/>'),
            g("Message", "\n".join(t)),
            g("Logo", logo_svg),
            g("Heart", heart)]
    return doc("\n".join(body), f"Ashvena thank-you card - front {i:02d}")


# ---------------------------------------------------------------------------
# back
# ---------------------------------------------------------------------------

def qr_svg(x, y, size, data, fill):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
    q.add_data(data)
    q.make(fit=True)
    mtx = q.get_matrix()
    n = len(mtx)
    c = size / n
    d = "".join(f"M{x + j * c:.2f},{y + i * c:.2f}h{c:.2f}v{c:.2f}h{-c:.2f}z"
                for i, row in enumerate(mtx) for j, v in enumerate(row) if v)
    return f'<path d="{d}" fill="{fill}"/>'


def back(m_serif, m_ital):
    cx = W / 2
    x0, x1 = TX0 + SAFE + 4, TX1 - SAFE - 4
    o = [g("Background", f'<rect width="{W}" height="{H}" fill="{KHADI}"/>')]
    lg, lh = logo("stacked", cx - 52, TY0 + SAFE + 4, 104)
    o.append(g("Logo", lg))
    y = TY0 + SAFE + 4 + lh + 44
    o.append(g("Heading", text(cx, y, "Thank you for", 23, BRICK, F_SERIF, 600, "middle")
               + text(cx, y + 27, "bringing us home.", 23, BRICK, F_SERIF, 600, "middle")))
    y += 27 + 14
    o.append(f'<path d="M {cx - 40},{y} L {cx - 7},{y} M {cx + 7},{y} L {cx + 40},{y}" stroke="{BRICK}" stroke-width=".8"/>'
             f'<path d="M {cx},{y - 3.5} l 3.5,3.5 l -3.5,3.5 l -3.5,-3.5 Z" fill="{BRICK}"/>')
    y += 26
    size, lh_ = 12.8, 18.4
    note = []
    for k, para in enumerate(BACK_NOTE):
        last = k == len(BACK_NOTE) - 1
        m = m_ital if last else m_serif
        for ln in wrap(para, m, size, x1 - x0):
            note.append(text(cx, y, ln, size, LAC, F_SERIF, 400, "middle", italic=last))
            y += lh_
        y += 7
    o.append(g("Note", "\n".join(note)))
    o.append(g("Signature", text(cx, y + 6, "With love, the Ashvena family", 11, BRICK, F_SERIF, 600, "middle", italic=True)))

    # QR row
    qs = 78
    qy = TY1 - SAFE - qs - 18
    qx = x0 + 6
    o.append(g("QR_Code", f'<rect x="{qx - 5}" y="{qy - 5}" width="{qs + 10}" height="{qs + 10}" rx="6" fill="{WHITE}"/>'
               + qr_svg(qx, qy, qs, QR_URL, LAC)))
    tx = qx + qs + 16
    o.append(g("QR_Label",
               text(tx, qy + 18, "SCAN TO SAY HI", 10.5, BRICK, F_SANS, 800, ls=1.2)
               + text(tx, qy + 32, "& REORDER ON WHATSAPP", 10.5, BRICK, F_SANS, 800, ls=1.2)
               + text(tx, qy + 52, "+91 79886 26068", 11, LAC, F_SANS, 600, ls=.6)
               + text(tx, qy + 72, "Heirloom, remixed. · Since 1953", 9.5, LAC, F_SERIF, 400, italic=True)))
    return doc("\n".join(o), "Ashvena thank-you card - back")


# ---------------------------------------------------------------------------
# export: duplex print PDF + Illustrator files
# ---------------------------------------------------------------------------

def export():
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import RectangleObject
    trim = RectangleObject([BLEED * 72 / 25.4 / 4, BLEED * 72 / 25.4 / 4,
                            (W - BLEED) * 72 / 25.4 / 4, (H - BLEED) * 72 / 25.4 / 4])
    back_pdf = os.path.join(ROOT, "ashvena-thankyou-back.pdf")
    fronts = sorted(glob.glob(os.path.join(ROOT, "ashvena-thankyou-front-*.pdf")))
    duplex = PdfWriter()
    for f in fronts:                                       # front, back, front, back ... for duplex printing
        for src in (f, back_pdf):
            page = PdfReader(src).pages[0]
            page.trimbox = trim
            duplex.add_page(page)
    out = os.path.join(ROOT, "Ashvena-ThankYou-Cards-A6-duplex-print.pdf")
    with open(out, "wb") as fh:
        duplex.write(fh)
    print(os.path.relpath(out, os.path.join(ROOT, "..", "..")))
    ai_dir = os.path.join(ROOT, "ai")
    os.makedirs(ai_dir, exist_ok=True)
    for src in fronts + [back_pdf]:
        w = PdfWriter(clone_from=PdfReader(src))
        w.pages[0].trimbox = trim
        name = os.path.basename(src)[:-4].replace("ashvena-thankyou-", "Ashvena-ThankYou-A6-").title()
        with open(os.path.join(ai_dir, name.replace("Ashvena-Thankyou-A6-", "Ashvena-ThankYou-A6-") + ".ai"), "wb") as fh:
            w.write(fh)
    print(os.path.relpath(ai_dir, os.path.join(ROOT, "..", "..")), "(.ai)")


def main():
    if "--export" in sys.argv:
        return export()
    os.makedirs(ROOT, exist_ok=True)
    m_punch = Metrics(font_file("Bricolage Grotesque 96pt Condensed", "ExtraBold"))
    m_serif = Metrics(font_file("Fraunces", "Regular"))
    m_ital = Metrics(font_file("Fraunces", "Italic"))
    for i, spec in enumerate(FRONTS, 1):
        p = os.path.join(ROOT, f"ashvena-thankyou-front-{i:02d}.svg")
        open(p, "w").write(front(i, spec, m_punch))
        print(os.path.relpath(p, os.path.join(ROOT, "..", "..")))
    p = os.path.join(ROOT, "ashvena-thankyou-back.svg")
    open(p, "w").write(back(m_serif, m_ital))
    print(os.path.relpath(p, os.path.join(ROOT, "..", "..")))


if __name__ == "__main__":
    main()
