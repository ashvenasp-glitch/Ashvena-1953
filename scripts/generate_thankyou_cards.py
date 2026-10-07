#!/usr/bin/env python3
"""Ashvena stall thank-you cards (A6, with bleed).

Fronts: four Gen Z "Heirloom, remixed" one-liners set big and stacked in
Bricolage Grotesque Condensed ExtraBold, each playing with the brand brick
red and dispensary blue (split card, highlight + notification, checkboxes,
trend-line split).
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
DEEP_RED, ROSE, BLUSH = "#5e0b19", "#d0566a", "#f6d3d8"
DEEP_BLUE, MID_BLUE, ICE = "#2b6a7c", "#8fc6d6", "#eef8fb"

F_PUNCH = "'Bricolage Grotesque 96pt Condensed', 'Bricolage Grotesque', 'Arial Narrow', sans-serif"
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

X0, X1 = TX0 + SAFE, TX1 - SAFE                 # safe text column
LOGO_Y = TY1 - SAFE - 34                         # logo row


def fit(m, lines, width, height, cap=118):
    """One size for a block: widest line fills `width`, all lines fit `height`."""
    return min(cap, min(width / m.width(t, 1) for t in lines),
               height / (.72 + .9 * (len(lines) - 1)))


def stack(m, x, top, lines, size, extra_w=None):
    """Lines of (text, colour) top-down from cap-top `top`; returns svg and the baselines."""
    out, base = [], []
    for k, (t, col) in enumerate(lines):
        y = top + size * .72 + k * size * .9
        out.append(text(x - size * .02, y, t, size, col, F_PUNCH, 800))
        base.append(y)
    return "\n".join(out), base


def foot(bg_bottom, heart):
    dark = bg_bottom in (BRICK, DEEP_RED, DEEP_BLUE)
    rec = {BRICK: BLUE, LAC: KHADI} if bg_bottom in (BRICK, DEEP_RED) else {BRICK: BLUSH, LAC: ICE}
    lg, _ = logo("horizontal", X0, LOGO_Y, 118, rec if dark else None)
    hp = (f'<path d="M 0,4 C -6,-3 -14,2 -9,9 L 0,17 L 9,9 C 14,2 6,-3 0,4 Z" '
          f'transform="translate({X1 - 10:.1f} {TY1 - SAFE - 25:.1f}) scale(1.05)" fill="{heart}"/>')
    return g("Logo", lg) + "\n" + g("Heart", hp)


def tag(x, y, label, bg, fg, anchor="start"):
    """Small rounded label, e.g. EST. 1953."""
    w = len(label) * 6.4 + 16
    x0 = x - w if anchor == "end" else x
    return (f'<rect x="{x0:.1f}" y="{y:.1f}" width="{w:.1f}" height="17" rx="8.5" fill="{bg}"/>'
            + text(x0 + w / 2, y + 12.2, label, 9, fg, F_SANS, 800, "middle", ls=1.4))


def outline(x, y, t, size, col, bg):
    """Hollow letters: stroke painted under a background-coloured fill, so overlapping contours don't show."""
    return (f'<text x="{x - size * .02:.1f}" y="{y:.1f}" font-family="{F_PUNCH}" font-size="{size:.1f}" font-weight="800" '
            f'fill="{bg}" stroke="{col}" stroke-width="{size * .056:.1f}" stroke-linejoin="round" '
            f'paint-order="stroke">{esc(t)}</text>')


def sparkle(x, y, r, col):
    k = r * .28
    return (f'<path d="M {x},{y - r} Q {x + k},{y - k} {x + r},{y} Q {x + k},{y + k} {x},{y + r} '
            f'Q {x - k},{y + k} {x - r},{y} Q {x - k},{y - k} {x},{y - r} Z" fill="{col}"/>')


def front_old_new(m, top_bg, bot_bg, old_cols, new_cols, tag1, tag2, hollow_old=False, heart=BRICK):
    """OLD SCHOOL RECIPE. on the top half, NEW SCHOOL CRAVINGS. on the bottom half."""
    split = H * .48
    size = fit(m, ["OLD SCHOOL", "NEW SCHOOL"], X1 - X0, 200)
    top = split - 30 - size * (.72 + .9)
    if hollow_old:
        t1 = "\n".join(outline(X0, top + size * .72 + k * size * .9, t, size, c, top_bg)
                       for k, (t, c) in enumerate(zip(["OLD SCHOOL", "RECIPE."], old_cols)))
    else:
        t1, _ = stack(m, X0, top, list(zip(["OLD SCHOOL", "RECIPE."], old_cols)), size)
    t2, _ = stack(m, X0, split + 34, list(zip(["NEW SCHOOL", "CRAVINGS."], new_cols)), size)
    return [g("Background", f'<rect width="{W}" height="{split:.1f}" fill="{top_bg}"/>'
                            f'<rect y="{split:.1f}" width="{W}" height="{H - split:.1f}" fill="{bot_bg}"/>'),
            g("Tags", tag(X1, TY0 + SAFE, "EST. 1953", *tag1, "end") + tag(X1, split + 12, "EST. TODAY", *tag2, "end")),
            g("Message", t1 + "\n" + t2), foot(bot_bg if bot_bg != DEEP_BLUE else BRICK, heart)]


def front_viral(m, bg, cols, hl, note_bg, note_fg, note_accent, heart):
    """VIRAL in a highlight block; the punchline as a phone notification."""
    lines = [("WE'VE BEEN", cols[0]), ("VIRAL", cols[1]), ("SINCE 1953.", cols[2])]
    size = fit(m, [t for t, _ in lines], X1 - X0, 300)
    msg, base = stack(m, X0, TY0 + SAFE + 22, lines, size)
    vw = m.width("VIRAL", size)
    hlr = (f'<rect x="{X0 - 8:.1f}" y="{base[1] - size * .8:.1f}" width="{vw + 14:.1f}" height="{size * .9:.1f}" '
           f'fill="{hl}" transform="rotate(-2 {X0:.1f} {base[1]:.1f})"/>')
    ny = base[2] + 34
    note = (f'<g transform="rotate(-3 {X0 + 150:.1f} {ny + 30:.1f})">'
            f'<rect x="{X0:.1f}" y="{ny:.1f}" width="{X1 - X0:.1f}" height="62" rx="16" fill="{note_bg}"/>'
            f'<rect x="{X0 + 12:.1f}" y="{ny + 13:.1f}" width="36" height="36" rx="9" fill="{note_accent}"/>'
            + logo("stacked", X0 + 17, ny + 16, 26, {BRICK: BLUE, LAC: BLUE})[0]
            + text(X0 + 60, ny + 27, "ASHVENA  ·  NOW", 9.5, note_accent, F_SANS, 800, ls=1.2)
            + text(X0 + 60, ny + 47, "The internet just found out.", 15, note_fg, F_SANS, 700)
            + f'<circle cx="{X1 - 16:.1f}" cy="{ny + 16:.1f}" r="5" fill="{note_accent}"/></g>')
    return [g("Background", f'<rect width="{W}" height="{H}" fill="{bg}"/>'),
            g("Highlight", hlr), g("Message", msg), g("Notification", note), foot(bg, heart)]


def front_checklist(m, bg, q_col, a_col, box_col, tick_col, box_fill="none", heart=BLUE):
    """TRADITION? [x] CHECK.  VIBES? [x][x] DOUBLE CHECK."""
    rows = [("TRADITION?", q_col, 0), ("CHECK.", a_col, 1), ("VIBES?", q_col, 0), ("DOUBLE", a_col, 2), ("CHECK.", a_col, 0)]
    probe = max(m.width(t, 1) + n * .82 for t, _, n in rows)
    size = min(110, (X1 - X0) / probe, (LOGO_Y - 30 - TY0 - SAFE) / (.72 + .9 * 4))
    top = LOGO_Y - 26 - size * (.72 + .9 * 4)
    o, boxes = [], []
    for k, (t, col, n) in enumerate(rows):
        y = top + size * .72 + k * size * .9
        x, b = X0, size * .66
        for j in range(n):
            bx, by = x + j * b * 1.24, y - b
            boxes.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{b:.1f}" height="{b:.1f}" rx="{b * .14:.1f}" '
                         f'fill="{box_fill}" stroke="{box_col}" stroke-width="{b * .12:.1f}"/>'
                         f'<path d="M {bx + b * .2:.1f},{by + b * .52:.1f} L {bx + b * .42:.1f},{by + b * .74:.1f} '
                         f'L {bx + b * .84:.1f},{by + b * .22:.1f}" fill="none" stroke="{tick_col}" stroke-width="{b * .15:.1f}" '
                         f'stroke-linecap="round" stroke-linejoin="round"/>')
        if n:
            x += n * b * 1.24 + b * .2
        o.append(text(x - size * .02, y, t, size, col, F_PUNCH, 800))
    return [g("Background", f'<rect width="{W}" height="{H}" fill="{bg}"/>'),
            g("Checkboxes", "".join(boxes)), g("Message", "\n".join(o)), foot(bg, heart)]


def front_elders(m, bg, elder_cols, you_cols, style, accent, accent2, heart):
    """OUR ELDERS MADE IT. / YOU MADE IT TRENDY.
    style: 'sticker' = TRENDY on a tilted block with sparkles,
           'tone'    = elders tone-on-tone (quiet), you bright (loud),
           'stamp'   = a vintage EST. 1953 stamp vs a NEW sticker."""
    lines = [("OUR ELDERS", elder_cols[0]), ("MADE IT.", elder_cols[1]), ("YOU MADE IT", you_cols[0]), ("TRENDY.", you_cols[1])]
    size = fit(m, [t for t, _ in lines], X1 - X0, LOGO_Y - 40 - TY0 - SAFE)
    top = LOGO_Y - 30 - size * (.72 + .9 * 3)
    msg, base = stack(m, X0, top, lines, size)
    o = [g("Background", f'<rect width="{W}" height="{H}" fill="{bg}"/>')]
    deco = []
    tw = m.width("TRENDY.", size)
    if style == "sticker":
        deco.append(f'<rect x="{X0 - 9:.1f}" y="{base[3] - size * .78:.1f}" width="{tw + 16:.1f}" height="{size * .84:.1f}" '
                    f'fill="{accent}" transform="rotate(-3 {X0:.1f} {base[3]:.1f})"/>')
        deco += [sparkle(X0 + tw + 34, base[3] - size * .62, 15, accent2), sparkle(X0 + tw + 58, base[3] - size * .2, 9, accent2)]
    elif style == "tone":
        deco += [sparkle(X0 + tw + 30, base[3] - size * .55, 16, accent), sparkle(X0 + tw + 56, base[3] - size * .15, 10, accent),
                 sparkle(X1 - 20, base[2] - size * .9, 8, accent)]
    elif style == "stamp":
        cx, cy, r = X1 - 46, TY0 + SAFE + 46, 40
        deco.append(f'<g transform="rotate(-12 {cx} {cy})"><circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{accent}" stroke-width="2.5"/>'
                    f'<circle cx="{cx}" cy="{cy}" r="{r - 6}" fill="none" stroke="{accent}" stroke-width="1"/>'
                    + text(cx, cy - 4, "EST.", 11, accent, F_SANS, 800, "middle", ls=2)
                    + text(cx, cy + 14, "1953", 17, accent, F_PUNCH, 800, "middle", ls=1) + "</g>")
        sx, sy = X0 + tw + 14, base[3] - size * .78
        deco.append(f'<g transform="rotate(10 {sx + 34} {sy + 16})"><rect x="{sx}" y="{sy}" width="68" height="30" rx="15" fill="{accent2}"/>'
                    + text(sx + 34, sy + 21, "NEW!", 15, bg, F_SANS, 800, "middle", ls=1.5) + "</g>")
    o += [g("Decoration", "".join(deco)), g("Message", msg), foot(bg, heart)]
    return o


# id -> (design, options); 1 = old/new, 2 = viral, 3 = checklist, 4 = elders
OPTIONS = {
    "1A": (front_old_new, dict(top_bg=BRICK, bot_bg=BLUE, old_cols=[BLUE, KHADI], new_cols=[BRICK, LAC],
                               tag1=(BLUE, BRICK), tag2=(BRICK, BLUE))),
    "1B": (front_old_new, dict(top_bg=DEEP_RED, bot_bg=ICE, old_cols=[BLUSH, BLUSH], new_cols=[BRICK, DEEP_BLUE],
                               tag1=(BLUSH, DEEP_RED), tag2=(DEEP_BLUE, ICE), hollow_old=True)),
    "1C": (front_old_new, dict(top_bg=BLUE, bot_bg=BRICK, old_cols=[DEEP_BLUE, DEEP_BLUE], new_cols=[BLUE, BLUSH],
                               tag1=(DEEP_BLUE, BLUE), tag2=(BLUSH, BRICK), hollow_old=True, heart=BLUE)),
    "2A": (front_viral, dict(bg=BLUE, cols=[LAC, BLUE, BRICK], hl=BRICK, note_bg=WHITE, note_fg=LAC, note_accent=BRICK, heart=BRICK)),
    "2B": (front_viral, dict(bg=DEEP_RED, cols=[BLUSH, DEEP_RED, MID_BLUE], hl=MID_BLUE, note_bg=ICE, note_fg=DEEP_RED,
                             note_accent=BRICK, heart=MID_BLUE)),
    "2C": (front_viral, dict(bg=ICE, cols=[DEEP_BLUE, WHITE, BRICK], hl=ROSE, note_bg=DEEP_BLUE, note_fg=WHITE,
                             note_accent=BRICK, heart=ROSE)),
    "3A": (front_checklist, dict(bg=BRICK, q_col=KHADI, a_col=BLUE, box_col=BLUE, tick_col=KHADI)),
    "3B": (front_checklist, dict(bg=BLUE, q_col=DEEP_BLUE, a_col=BRICK, box_col=BRICK, tick_col=WHITE, box_fill=BRICK, heart=BRICK)),
    "3C": (front_checklist, dict(bg=DEEP_BLUE, q_col=ICE, a_col=BLUSH, box_col=ROSE, tick_col=WHITE, box_fill=ROSE, heart=BLUSH)),
    "4A": (front_elders, dict(bg=BLUE, elder_cols=[BRICK, BRICK], you_cols=[LAC, BLUE], style="sticker",
                              accent=BRICK, accent2=ROSE, heart=BRICK)),
    "4B": (front_elders, dict(bg=BRICK, elder_cols=[ROSE, ROSE], you_cols=[BLUE, ICE], style="tone",
                              accent=BLUSH, accent2=BLUSH, heart=BLUE)),
    "4C": (front_elders, dict(bg=ICE, elder_cols=[DEEP_BLUE, DEEP_BLUE], you_cols=[BRICK, ROSE], style="stamp",
                              accent=DEEP_BLUE, accent2=BRICK, heart=BRICK)),
}


def front(i, oid, m):
    fn, kw = OPTIONS[oid]
    return doc("\n".join(fn(m, **kw)), f"Ashvena thank-you card - front {i:02d} (option {oid})")


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
    for old in glob.glob(os.path.join(ROOT, "ashvena-thankyou-front-*.*")) + glob.glob(os.path.join(ROOT, "ai", "*Front*.ai")):
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
