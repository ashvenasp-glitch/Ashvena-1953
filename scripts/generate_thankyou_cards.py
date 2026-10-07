#!/usr/bin/env python3
"""Ashvena stall thank-you cards (A6, with bleed).

Fronts: four Gen Z "Heirloom, remixed" one-liners, type only, in the style of
the client's reference cards: a tight stacked block of Anton caps centred on a
light brand background (pink, white or blue), the colour changing
phrase by phrase (brand red or deep blue with white or a lighter tint).
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
# darker / lighter tones of the brand red and blue
ROSE, PINK = "#d0566a", "#eea8b2"
DEEP_BLUE, SKY, ICE = "#2b6a7c", "#9fcfdd", "#eef8fb"

F_TYPE = "Anton, 'Bebas Neue', Impact, 'Arial Narrow', sans-serif"
F_SERIF = "Fraunces, Georgia, serif"
F_SANS = "'Bricolage Grotesque', Helvetica, Arial, sans-serif"

QR_URL = "https://wa.me/917988626068"   # Ashvena customer care (WhatsApp)

# the four final messages, three colour options each (see OPTIONS below);
# FRONTS is the print set: one chosen option per message
FRONTS = ["1A", "2A", "3A", "4A"]

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
# fronts
# ---------------------------------------------------------------------------

def front_type(m, bg, lines):
    """Type-only card in the reference style: a tight, stacked block of heavy condensed caps,
    centred with generous margins, colour changing phrase by phrase."""
    words = [t for t, _ in lines]
    bw = (TX1 - TX0) * .76                              # block width: ~3/4 of the card
    size = min(bw / max(m.width(t, 1) for t in words), (TY1 - TY0) * .64 / (.86 + 1.0 * (len(lines) - 1)))
    lead = size * 1.0                                   # tight, with a clear sliver between lines
    cap = size * .86                                    # Anton cap height (1760 / 2048)
    block_h = cap + lead * (len(lines) - 1)
    widest = max(m.width(t, size) for t in words)
    x = (W - widest) / 2
    top = (H - block_h) / 2 + 10                        # optically a touch below centre
    out = [text(x, top + cap + k * lead, t, size, c, F_TYPE, 400) for k, (t, c) in enumerate(lines)]
    return [g("Background", f'<rect width="{W}" height="{H}" fill="{bg}"/>'), g("Message", "\n".join(out))]


# id -> (background, [(line, colour)]); 1 = old/new, 2 = viral, 3 = checklist, 4 = elders;
# A/B light backgrounds as in the reference, C tone-on-tone brick
OPTIONS = {
    "1A": (PINK, [("OLD SCHOOL", BRICK), ("RECIPE.", BRICK), ("NEW SCHOOL", WHITE), ("CRAVINGS.", WHITE)]),
    "1B": (WHITE, [("OLD SCHOOL", BRICK), ("RECIPE.", BRICK), ("NEW SCHOOL", ROSE), ("CRAVINGS.", ROSE)]),
    "2A": (WHITE, [("WE'VE BEEN", BRICK), ("VIRAL SINCE", BRICK), ("1953.", BRICK), ("THE INTERNET", ROSE), ("JUST FOUND OUT.", ROSE)]),
    "2B": (SKY, [("WE'VE BEEN", DEEP_BLUE), ("VIRAL SINCE", DEEP_BLUE), ("1953.", DEEP_BLUE), ("THE INTERNET", WHITE), ("JUST FOUND OUT.", WHITE)]),
    "3A": (SKY, [("TRADITION?", DEEP_BLUE), ("CHECK.", WHITE), ("VIBES?", DEEP_BLUE), ("DOUBLE CHECK.", WHITE)]),
    "3B": (PINK, [("TRADITION?", BRICK), ("CHECK.", WHITE), ("VIBES?", BRICK), ("DOUBLE CHECK.", WHITE)]),
    "4A": (SKY, [("OUR ELDERS", BRICK), ("MADE IT.", BRICK), ("YOU MADE IT", WHITE), ("TRENDY.", WHITE)]),
    "4B": (WHITE, [("OUR ELDERS", DEEP_BLUE), ("MADE IT.", DEEP_BLUE), ("YOU MADE IT", BRICK), ("TRENDY.", BRICK)]),
    # C: tone-on-tone brick, the quieter phrase in rose, the punchline in blue
    "1C": (BRICK, [("OLD SCHOOL", ROSE), ("RECIPE.", ROSE), ("NEW SCHOOL", BLUE), ("CRAVINGS.", BLUE)]),
    "2C": (BRICK, [("WE'VE BEEN", ROSE), ("VIRAL SINCE", ROSE), ("1953.", ROSE), ("THE INTERNET", BLUE), ("JUST FOUND OUT.", BLUE)]),
    "3C": (BRICK, [("TRADITION?", ROSE), ("CHECK.", BLUE), ("VIBES?", ROSE), ("DOUBLE CHECK.", BLUE)]),
    "4C": (BRICK, [("OUR ELDERS", ROSE), ("MADE IT.", ROSE), ("YOU MADE IT", ICE), ("TRENDY.", ICE)]),
}


def front(i, oid, m):
    bg, lines = OPTIONS[oid]
    return doc("\n".join(front_type(m, bg, lines)), f"Ashvena thank-you card - front {i:02d} (option {oid})")


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
    m_punch = Metrics(font_file("Anton", "Regular"))
    m_serif = Metrics(font_file("Fraunces", "Regular"))
    m_ital = Metrics(font_file("Fraunces", "Italic"))
    for old in (glob.glob(os.path.join(ROOT, "ashvena-thankyou-front-*.*")) + glob.glob(os.path.join(ROOT, "ai", "*Front*.ai"))
                + glob.glob(os.path.join(ROOT, "options", "*"))):
        os.remove(old)                                     # the set changes size between rounds
    for i, oid in enumerate(FRONTS, 1):
        p = os.path.join(ROOT, f"ashvena-thankyou-front-{i:02d}.svg")
        open(p, "w").write(front(i, oid, m_punch))
        print(os.path.relpath(p, os.path.join(ROOT, "..", "..")))
    opt_dir = os.path.join(ROOT, "options")
    os.makedirs(opt_dir, exist_ok=True)
    for oid in OPTIONS:
        open(os.path.join(opt_dir, f"ashvena-thankyou-option-{oid}.svg"), "w").write(front(0, oid, m_punch))
    print("options:", ", ".join(OPTIONS))
    p = os.path.join(ROOT, "ashvena-thankyou-back.svg")
    open(p, "w").write(back(m_serif, m_ital))
    print(os.path.relpath(p, os.path.join(ROOT, "..", "..")))


if __name__ == "__main__":
    main()
