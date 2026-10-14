#!/usr/bin/env python3
"""Ashvena 1953 stall standees - 6 x 9 in inserts for an acrylic T-stand.

Built to the Ashvena Brand & Packaging Guidelines 2026 (v1.0):

  * stacked logo (mark + "Ashvena" + "1953") in original colours, centred on
    a light wall, never on a coloured panel; veg mark top-left
  * Fraunces (9 pt optical size) for titles of modern ranges, taglines and
    the sign-off; Bricolage Grotesque (14 pt) for functional text; Lobster
    for titles of the heritage ranges only (candies, dry fruits)
  * approved watercolour + gold-ink art only (see prepare_standee_art.py),
    titles in the darkest range colour, copy from the copy library

  1  Real Fruit Candies    Amla, Khatti-Meethi Amla, Carrot (heritage, Dadi scene)
  2  Masalas & Dry Fruits  Cutting Chai + Chatpata Chaat, 73-year-old recipe
                           (modern, brass bowls) and the premium dry fruits
                           (heritage, Papa scene)

Artboard: 158.4 x 234.6 mm = 152.4 x 228.6 mm (6 x 9 in) trim + 3 mm bleed,
4 px = 1 mm. Text is live and every region is a named group. The bottom
~10 mm of the trim sits behind the stand's lip, so it carries no key copy.

The menus carry no prices or pack sizes: names, one short line each, art.

Usage:  python3 scripts/prepare_standee_art.py <guidelines.pdf>   # once
        python3 scripts/generate_standees.py
"""
import base64
import os
import re
import subprocess

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(BASE, "signage", "stall-standees")
ART = os.path.join(OUT, "art")
LOGO = os.path.join(BASE, "signage", "brand", "ashvena-logo-stacked.svg")

MM = 4                                   # px per mm
BLEED = 3
TW, TH = 152.4, 228.6                    # trim: 6 x 9 in
W, H = (TW + 2 * BLEED) * MM, (TH + 2 * BLEED) * MM
PT = 25.4 / 72                           # 1 pt in mm
CX = TW / 2

# core palette (guidelines p. 5)
RED, INK, STORY, VEG = "#941528", "#35070F", "#4B403B", "#1E8E3E"
RULE = "#B9A98C"

FONTS = {
    "fraunces": ("Fraunces", "Fraunces, 'Fraunces 9pt', Georgia, serif"),
    "bricolage": ("Bricolage Grotesque", "'Bricolage Grotesque', 'Bricolage Grotesque 14pt', Helvetica, Arial, sans-serif"),
    "lobster": ("Lobster", "Lobster, cursive"),
}

CANDIES = [
    dict(key="amla", name="Amla Candy", title="#2D6C4C", line="Sweet, soft and chewy."),
    dict(key="khatti-meethi", name="Khatti-Meethi Amla Candy", title="#1C6467",
         line="Sweet, sour, with rock salt and spices."),
    dict(key="carrot", name="Carrot Candy", title="#A85325", line="Made with real carrot."),
]
MASALAS = [
    dict(key="cutting-chai", name="Cutting Chai", title="#81461F", art="cutting-chai-bowl.jpg",
         line="Brewed strong. Poured slow."),
    dict(key="chatpata-chaat", name="Chatpata Chaat", title="#982820", art="chatpata-chaat-bowl.jpg",
         line="Tangy, salty, a little wild."),
]
DRY_FRUITS = [
    dict(key="whole-cashews", name="Whole Cashews", title="#6C5020"),
    dict(key="akbari-pistachios", name="Akbari Pistachios", title="#414A27"),
    dict(key="california-almonds", name="California Almonds", title="#985E31"),
    # raisin title #D3992C is too pale at list size on cream: use the darkest range colour (head)
    dict(key="seedless-raisins", name="Seedless Raisins", title="#6D441B"),
    dict(key="walnut-kernels", name="Walnut Kernels", title="#9A7040"),
]
DRY_FRUIT_LINE = "Papa’s rule: whole ones for the guests."

CLAIMS = "MADE WITH REAL FRUIT  ·  73-YEAR-OLD RECIPE  ·  NO ADDED COLOUR"
SIGN_OFF = "Heirloom, remixed. · Since 1953"

FOOTER_Y = 203                           # same on both cards, clear of the stand's lip
WALL_CANDY = "#e0efe1"                   # matches the faded edges baked into the art
WALL_PANTRY = "#f9f3e1"

# Display-message cards: the pair mirrors the Amla (red / light-blue mark) and
# Khatti-Meethi (light blue / red mark) candy lids, guidelines p. 19.
CREAM = "#F3E6C6"                        # Heirloom Cream: one-colour logo + text on a dark ground
LID_BLUE = "#CBE9F1"
MESSAGES = {
    "red": dict(kicker="73 YEARS IN", display=["No shortcuts.", "Ever."],
                story="In 1947, when our family crossed the border, they carried one thing with them. "
                      "An intention to do everything with purity. With honesty.",
                close="That’s why everything we make feels like home."),
    "blue": dict(kicker="THE HOUSE RULE", display=["Nobody leaves", "without tasting."],
                 by="Dadi, every single day",
                 body=["Ask us for a taste of our", "candies, masalas and dry fruits."],
                 range="CANDIES  ·  MASALAS  ·  DRY FRUITS"),
}


# ---------------------------------------------------------------------------
# units, metrics, text
# ---------------------------------------------------------------------------

def px(v):
    """Trim-relative mm -> artboard px."""
    return (BLEED + v) * MM


_METRICS = {}
FC_WEIGHT = {400: 80, 500: 100, 600: 180}


def _metrics(font, weight, italic):
    key = (font, weight, italic)
    if key not in _METRICS:
        _METRICS[key] = None
        try:
            from fontTools.ttLib import TTFont
            fam = FONTS[font][0]
            q = f"{fam}:weight={FC_WEIGHT[weight]}" + (":slant=100" if italic else "")
            path = subprocess.run(["fc-match", "-f", "%{file}", q], capture_output=True, text=True).stdout
            f = TTFont(path)
            if fam.lower() in f["name"].getDebugName(1).lower():
                _METRICS[key] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
        except Exception:
            pass
    return _METRICS[key]


def measure(s, font, pt, weight=400, italic=False, track=0):
    """Width in mm of `s` at `pt`, tracking in 1/1000 em (as in Illustrator)."""
    size = pt * PT
    m = _metrics(font, weight, italic)
    if m:
        cmap, hmtx, upm = m
        adv = sum(hmtx[cmap[ord(c)]][0] if ord(c) in cmap else upm * .5 for c in s) / upm
    else:
        adv = len(s) * .52
    return adv * size + len(s) * size * track / 1000


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def t(x, y, s, pt, fill, font="fraunces", weight=400, anchor="middle", track=0, italic=False, maxw=None, gid=None):
    """Live text at trim-relative mm. Auto-shrinks to `maxw` mm."""
    if maxw:
        while pt > 4.4 and measure(s, font, pt, weight, italic, track) > maxw:
            pt -= .25
    size = pt * PT * MM
    ls = size * track / 1000
    shift = {"start": 0, "middle": ls / 2, "end": ls}[anchor]     # trailing letter-space
    it = ' font-style="italic"' if italic else ""
    idattr = f' id="{gid}"' if gid else ""
    return (f'<text{idattr} x="{px(x) + shift:.2f}" y="{px(y):.2f}" font-family="{FONTS[font][1]}" '
            f'font-size="{size:.2f}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" '
            f'letter-spacing="{ls:.2f}"{it}>{esc(s)}</text>')


def g(gid, *body):
    return f'<g id="{gid}">\n' + "\n".join(body) + "\n</g>"


def rule(x0, x1, y, col=RULE, w=.6):
    return f'<line x1="{px(x0):.1f}" y1="{px(y):.1f}" x2="{px(x1):.1f}" y2="{px(y):.1f}" stroke="{col}" stroke-width="{w}"/>'


# ---------------------------------------------------------------------------
# brand elements
# ---------------------------------------------------------------------------

def art_height(name, w):
    from PIL import Image
    iw, ih = Image.open(os.path.join(ART, name)).size
    return w * ih / iw


def image(name, x, y, w, h=None, gid=None):
    """Embedded art at trim-relative mm; height follows the file's aspect unless given."""
    data = base64.b64encode(open(os.path.join(ART, name), "rb").read()).decode()
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    h = h or art_height(name, w)
    return (f'<image id="{gid or name.split(".")[0]}" x="{px(x):.2f}" y="{px(y):.2f}" width="{w * MM:.2f}" '
            f'height="{h * MM:.2f}" preserveAspectRatio="xMidYMid meet" xlink:href="data:{mime};base64,{data}"/>'), h


def logo(cx, top, height, one_colour=None):
    """Stacked logo, original colours. Clear space x = word height = 16 % of logo height.

    `one_colour` (Heirloom Cream) is for solid dark grounds only, as on the guidelines cover.
    """
    src = open(LOGO).read()
    vx, vy, vw, vh = map(float, re.search(r'viewBox="([^"]+)"', src).group(1).split())
    s = height * MM / vh
    body = "\n".join(re.findall(r'<g id="(?:Mark|Word|Year)".*?</g>', src, re.S))
    if one_colour:
        body = re.sub(r'fill="#[0-9A-Fa-f]{6}"', f'fill="{one_colour}"', body)
    x0 = px(cx) - vw * s / 2
    return f'<g id="Logo_Stacked" transform="translate({x0:.2f} {px(top):.2f}) scale({s:.5f}) translate({-vx} {-vy})">\n{body}\n</g>'


def veg_mark(x, y, size=5.0):
    sw = size * .08
    return g("Veg_Mark",
             f'<rect x="{px(x) + sw * MM / 2:.2f}" y="{px(y) + sw * MM / 2:.2f}" width="{(size - sw) * MM:.2f}" '
             f'height="{(size - sw) * MM:.2f}" fill="#FFFFFF" stroke="{VEG}" stroke-width="{sw * MM:.2f}"/>',
             f'<circle cx="{px(x + size / 2):.2f}" cy="{px(y + size / 2):.2f}" r="{size * .25 * MM:.2f}" fill="{VEG}"/>')


def footer(y, line=RULE, col=INK):
    return g("Footer",
             rule(6, TW - 6, y, line),
             t(CX, y + 8, SIGN_OFF, 12, col, "fraunces", 400, italic=True))


def arch_window(gid, x, apex, w, h, rise, wall, line, art):
    """Light jharokha-style window (arched top) holding art painted on that wall colour."""
    def shape(x0, y0, ww, hh, a):
        ya, yb, r = y0 + a, y0 + hh, 2.5
        return (f"M {px(x0):.2f},{px(yb - r):.2f} L {px(x0):.2f},{px(ya):.2f} "
                f"A {ww / 2 * MM:.2f} {a * MM:.2f} 0 0 1 {px(x0 + ww):.2f},{px(ya):.2f} "
                f"L {px(x0 + ww):.2f},{px(yb - r):.2f} Q {px(x0 + ww):.2f},{px(yb):.2f} {px(x0 + ww - r):.2f},{px(yb):.2f} "
                f"L {px(x0 + r):.2f},{px(yb):.2f} Q {px(x0):.2f},{px(yb):.2f} {px(x0):.2f},{px(yb - r):.2f} Z")
    o = 1.8
    return g(gid,
             f'<path d="{shape(x - o, apex - o, w + 2 * o, h + 2 * o, rise + o)}" fill="none" stroke="{line}" '
             f'stroke-width="1.1"/>',
             f'<path d="{shape(x, apex, w, h, rise)}" fill="{wall}"/>',
             art)


def svg_doc(body, title, wall, tw=TW, th=TH):
    w, h = (tw + 2 * BLEED) * MM, (th + 2 * BLEED) * MM
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w / MM:.1f}mm" height="{h / MM:.1f}mm" viewBox="0 0 {w:.1f} {h:.1f}">\n'
            f'<title>{esc(title)}</title>\n'
            f'<g id="Background"><rect width="{w:.1f}" height="{h:.1f}" fill="{wall}"/></g>\n'
            f'{body}\n'
            f'<g id="Guides" opacity="0">'
            f'<rect id="Trim" x="{px(0)}" y="{px(0)}" width="{tw * MM:.1f}" height="{th * MM:.1f}" fill="none" stroke="#ff00ff"/>'
            f'<rect id="Safe_6mm" x="{px(6)}" y="{px(6)}" width="{(tw - 12) * MM:.1f}" height="{(th - 16) * MM:.1f}" '
            f'fill="none" stroke="#00aaff" stroke-dasharray="6 4"/></g>\n</svg>\n')


# ---------------------------------------------------------------------------
# Standee 1 - Real Fruit Candies (heritage)
# ---------------------------------------------------------------------------

def standee_candies():
    o = [veg_mark(6, 6), logo(CX, 8, 28)]
    o.append(g("Title",
               t(CX, 49, "Real Fruit Candies", 30, "#1C6467", "lobster", maxw=TW - 20),
               t(CX, 55.5, "Dadi never asked if we wanted amla.", 11, STORY, italic=True),
               t(CX, 60.5, "She just handed it over.", 11, STORY, italic=True)))
    art, h = image("dadi-family-scene.jpg", -BLEED, 61, TW + 2 * BLEED, gid="Art_Dadi_Scene")
    o.append(g("Illustration", art))
    o.append(g("Claims_Strip", t(CX, 61 + h + 4.5, CLAIMS, 7, STORY, "bricolage", 500, track=100, maxw=TW - 14)))

    top = 61 + h + 9
    step = (FOOTER_Y - 1 - top) / len(CANDIES)
    for i, c in enumerate(CANDIES):
        y = top + i * step
        r = [t(CX, y + step / 2 - 1, c["name"], 22, c["title"], "lobster", maxw=TW - 16),
             t(CX, y + step / 2 + 5.5, c["line"], 10.5, STORY, italic=True, maxw=TW - 16)]
        if i < len(CANDIES) - 1:
            r.append(rule(CX - 30, CX + 30, y + step - .5))
        o.append(g("Product_" + c["key"].replace("-", "_"), *r))
    o.append(footer(FOOTER_Y))
    return svg_doc("\n".join(o), "Ashvena 1953 stall standee - Real Fruit Candies", WALL_CANDY)


# ---------------------------------------------------------------------------
# Standee 2 - Masalas (73-year-old recipe) & Premium Dry Fruits
# ---------------------------------------------------------------------------

def standee_pantry():
    o = [veg_mark(6, 6), logo(CX, 8, 28)]
    o.append(g("Masala_Head",
               t(CX, 48, "Recipe from 1953", 22, INK, italic=True),
               t(CX, 54, "MASALAS", 7.5, "#3D2313", "bricolage", 500, track=320)))
    for i, m in enumerate(MASALAS):
        cx = TW / 4 + i * TW / 2
        art, h = image(m["art"], cx - 37, 56, 74, gid="Art_" + m["key"].replace("-", "_"))
        y = 56 + h
        o.append(g("Product_" + m["key"].replace("-", "_"),
                   art,
                   t(cx, y + 7.5, m["name"], 19, m["title"], italic=True, maxw=68),
                   t(cx, y + 12.5, "MASALA", 7, "#3D2313", "bricolage", 500, track=320),
                   t(cx, y + 18, m["line"], 10, STORY, italic=True, maxw=68)))
    y_div = 56 + h + 25
    o.append(rule(6, TW - 6, y_div))

    yt = y_div + 12
    o.append(g("Dry_Fruit_Head",
               t(6, yt, "Premium Dry Fruits", 24, "#6C5020", "lobster", anchor="start"),
               t(6, yt + 6.5, DRY_FRUIT_LINE, 10, STORY, italic=True, anchor="start")))
    ah = art_height("papa-family-scene.jpg", 78)
    art, _ = image("papa-family-scene.jpg", TW + BLEED - 78, FOOTER_Y - 3.5 - ah, 78, gid="Art_Papa_Scene")
    o.append(g("Illustration", art))
    rows, ly, rx = [], yt + 11, 72
    step = (FOOTER_Y - 2 - ly) / len(DRY_FRUITS)
    for i, d in enumerate(DRY_FRUITS):
        y = ly + i * step
        rows.append(g("Product_" + d["key"].replace("-", "_"),
                      t(6, y + step / 2 + 2.2, d["name"], 17, d["title"], "lobster", anchor="start", maxw=rx - 6)))
        if i < len(DRY_FRUITS) - 1:
            rows.append(rule(6, rx, y + step))
    o.append(g("Dry_Fruit_List", *rows))
    o.append(footer(FOOTER_Y))
    return svg_doc("\n".join(o), "Ashvena 1953 stall standee - Masalas & Dry Fruits", WALL_PANTRY)


# ---------------------------------------------------------------------------
# Red menus (the stall's two side stands): Ashvena Red ground, one-colour cream
# logo, cream / lid-blue type, art held in light arched windows.
# ---------------------------------------------------------------------------

def standee_candies_red():
    o = [veg_mark(6, 6), logo(CX, 8, 28, one_colour=CREAM)]
    o.append(g("Title",
               t(CX, 49, "Real Fruit Candies", 30, CREAM, "lobster", maxw=TW - 20),
               t(CX, 55.5, "Dadi never asked if we wanted amla.", 11, LID_BLUE, italic=True),
               t(CX, 60.5, "She just handed it over.", 11, LID_BLUE, italic=True)))
    apex, bottom, aw = 65, 134, 132
    h = art_height("dadi-family-scene.jpg", aw)
    art, _ = image("dadi-family-scene.jpg", CX - aw / 2, bottom - 1.5 - h, aw, gid="Art_Dadi_Scene")
    o.append(arch_window("Window_Dadi", 8, apex, TW - 16, bottom - apex, 14, WALL_CANDY, LID_BLUE, art))
    o.append(g("Claims_Strip", t(CX, bottom + 7.5, CLAIMS, 7, CREAM, "bricolage", 500, track=100, maxw=TW - 14)))

    top = bottom + 11
    step = (FOOTER_Y - 1 - top) / len(CANDIES)
    for i, c in enumerate(CANDIES):
        y = top + i * step
        r = [t(CX, y + step / 2 - .5, c["name"], 21, CREAM, "lobster", maxw=TW - 16),
             t(CX, y + step / 2 + 5.5, c["line"], 10.5, LID_BLUE, italic=True, maxw=TW - 16)]
        if i < len(CANDIES) - 1:
            r.append(rule(CX - 30, CX + 30, y + step - .3, LID_BLUE))
        o.append(g("Product_" + c["key"].replace("-", "_"), *r))
    o.append(footer(FOOTER_Y, LID_BLUE, LID_BLUE))
    return svg_doc("\n".join(o), "Ashvena 1953 stall standee - Real Fruit Candies (red)", RED)


def standee_pantry_red():
    o = [veg_mark(6, 6), logo(CX, 8, 28, one_colour=CREAM)]
    o.append(g("Masala_Head",
               t(CX, 48, "Recipe from 1953", 22, CREAM, italic=True),
               t(CX, 54, "MASALAS", 7.5, LID_BLUE, "bricolage", 500, track=320)))
    apex, bottom, ww, aw = 58, 105, 66, 62
    for i, m in enumerate(MASALAS):
        cx = TW / 4 + i * TW / 2 + (1 if i == 0 else -1)
        h = art_height(m["art"], aw)
        art, _ = image(m["art"], cx - aw / 2, bottom - 1.5 - h, aw, gid="Art_" + m["key"].replace("-", "_"))
        o.append(g("Product_" + m["key"].replace("-", "_"),
                   arch_window("Window_" + m["key"].replace("-", "_"), cx - ww / 2, apex, ww, bottom - apex, 8,
                               WALL_PANTRY, LID_BLUE, art),
                   t(cx, bottom + 10.5, m["name"], 19, CREAM, italic=True, maxw=68),
                   t(cx, bottom + 15.5, "MASALA", 7, LID_BLUE, "bricolage", 500, track=320),
                   t(cx, bottom + 21, m["line"], 10, CREAM, italic=True, maxw=68)))
    y_div = bottom + 26.5
    o.append(rule(6, TW - 6, y_div, LID_BLUE))

    yt = y_div + 12
    o.append(g("Dry_Fruit_Head",
               t(6, yt, "Premium Dry Fruits", 21, CREAM, "lobster", anchor="start"),
               t(6, yt + 6.3, DRY_FRUIT_LINE, 9.5, LID_BLUE, italic=True, anchor="start")))
    px0, pw, paw = 76, TW - 6 - 76, 66
    papex, pbottom = y_div + 5, FOOTER_Y - 4
    ah = art_height("papa-family-scene.jpg", paw)
    art, _ = image("papa-family-scene.jpg", px0 + (pw - paw) / 2, pbottom - 1 - ah, paw, gid="Art_Papa_Scene")
    o.append(arch_window("Window_Papa", px0, papex, pw, pbottom - papex, 9, WALL_PANTRY, LID_BLUE, art))
    rows, ly, rx = [], yt + 10, 70
    step = (FOOTER_Y - 2 - ly) / len(DRY_FRUITS)
    for i, d in enumerate(DRY_FRUITS):
        y = ly + i * step
        rows.append(g("Product_" + d["key"].replace("-", "_"),
                      t(6, y + step / 2 + 2, d["name"], 16, CREAM, "lobster", anchor="start", maxw=rx - 6)))
        if i < len(DRY_FRUITS) - 1:
            rows.append(rule(6, rx, y + step, LID_BLUE, .5))
    o.append(g("Dry_Fruit_List", *rows))
    o.append(footer(FOOTER_Y, LID_BLUE, LID_BLUE))
    return svg_doc("\n".join(o), "Ashvena 1953 stall standee - Masalas & Dry Fruits (red)", RED)


# ---------------------------------------------------------------------------
# Display-message cards (type only: Fraunces display, Bricolage kickers)
# ---------------------------------------------------------------------------

def wrap_mm(s, font, pt, weight, maxw, italic=False):
    lines, cur = [], ""
    for word in s.split():
        nxt = (cur + " " + word).strip()
        if cur and measure(nxt, font, pt, weight, italic) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = nxt
    return lines + ([cur] if cur else [])


def short_rule(y, col, w=24):
    return rule(CX - w / 2, CX + w / 2, y, col, 1.2)


def sign_off(col, sub_col):
    return g("Sign_Off",
             t(CX, FOOTER_Y + 6, SIGN_OFF, 12, col, italic=True),
             t(CX, FOOTER_Y + 12, "SONIPAT, INDIA", 6, sub_col, "bricolage", 500, track=240))


def message_red():
    m = MESSAGES["red"]
    o = [logo(CX, 16, 32, one_colour=CREAM),
         g("Kicker", t(CX, 76, m["kicker"], 8, LID_BLUE, "bricolage", 500, track=320)),
         g("Display", *[t(CX, 100 + i * 21, line, 56, CREAM, italic=True, maxw=TW - 18)
                        for i, line in enumerate(m["display"])]),
         short_rule(137, LID_BLUE)]
    lines = wrap_mm(m["story"], "fraunces", 12.5, 400, 116)
    o.append(g("Story", *[t(CX, 152 + i * 6.6, line, 12.5, CREAM) for i, line in enumerate(lines)],
               t(CX, 152 + len(lines) * 6.6 + 5, m["close"], 12.5, LID_BLUE, italic=True, maxw=TW - 20)))
    o.append(sign_off(LID_BLUE, CREAM))
    return svg_doc("\n".join(o), "Ashvena 1953 display card - No shortcuts. Ever. (red)", RED)


def message_blue():
    m = MESSAGES["blue"]
    o = [logo(CX, 16, 32),
         g("Kicker", t(CX, 74, m["kicker"], 8, STORY, "bricolage", 500, track=320)),
         g("Quote_Mark", t(CX, 110, "“", 88, RED, italic=True)),
         g("Display", *[t(CX, 118 + i * 18, line, 46, RED, italic=True, maxw=TW - 16)
                        for i, line in enumerate(m["display"])]),
         g("Attribution", t(CX, 147.5, m["by"], 12.5, STORY, italic=True)),
         short_rule(157, RED)]
    lines = m["body"]
    o.append(g("Body", *[t(CX, 170 + i * 6.6, line, 12.5, INK) for i, line in enumerate(lines)]))
    o.append(g("Range", t(CX, 170 + len(lines) * 6.6 + 7, m["range"], 7, RED, "bricolage", 500, track=320)))
    o.append(sign_off(RED, STORY))
    return svg_doc("\n".join(o), "Ashvena 1953 display card - Nobody leaves without tasting. (blue)", LID_BLUE)


# ---------------------------------------------------------------------------
# A4 tasting counter (centre of the stall)
# ---------------------------------------------------------------------------
# A short, ordered flight converts better than an open spread (six-option
# tasting: ~30 % of tasters bought vs ~3 % with 24 options), so the card
# serves six samples, mild to bold, then hands off to gifting and WhatsApp.

A4W, A4H = 210, 297
WHATSAPP = "https://wa.me/917988626068"
TASTING = [
    ("Whole Cashews", "Start mild. 100% cashew, no added salt or oil."),
    ("Carrot Candy", "Made with real carrot."),
    ("Amla Candy", "Made with real fruit. Sweet and chewy."),
    ("Khatti-Meethi Amla Candy", "Sweet, sour, with rock salt and spices."),
    ("Chatpata Chaat Masala", "On fresh fruit. Tangy, salty, a little wild."),
    ("Cutting Chai Masala", "Finish with a cup. Brewed strong. Poured slow."),
]
ALLERGEN = ("ALLERGEN ADVICE  ·  Cashews and other dry fruits are tree nuts. Everything is packed in a "
            "facility that also handles tree nuts and peanuts.")
TASTING_THEMES = {
    # main = display + names, accent = kickers / rules / numbers, body = notes
    "red": dict(bg=RED, logo=CREAM, main=CREAM, accent=LID_BLUE, body=CREAM, num_ink=RED),
    "blue": dict(bg=LID_BLUE, logo=None, main=RED, accent=RED, body=INK, num_ink=LID_BLUE),
}


def qr_code(data, x, y, size, ink, paper):
    """Vector QR (segno) on a quiet-zone tile, at trim-relative mm."""
    import segno
    rows = [list(r) for r in segno.make(data, error="m").matrix]
    n = len(rows)
    cell = size / (n + 8)
    o = [f'<rect x="{px(x):.2f}" y="{px(y):.2f}" width="{size * MM:.2f}" height="{size * MM:.2f}" rx="{MM * 1.5}" '
         f'fill="{paper}"/>']
    d = []
    for j, row in enumerate(rows):
        for i, v in enumerate(row):
            if v:
                d.append(f"M{px(x + (i + 4) * cell):.2f},{px(y + (j + 4) * cell):.2f}h{cell * MM:.2f}v{cell * MM:.2f}"
                         f"h{-cell * MM:.2f}z")
    o.append(f'<path d="{"".join(d)}" fill="{ink}" shape-rendering="crispEdges"/>')
    return g("QR_WhatsApp", *o)


def tasting_counter(theme):
    th = TASTING_THEMES[theme]
    cx = A4W / 2
    o = [veg_mark(9, 9, 6), logo(cx, 14, 30, one_colour=th["logo"]),
         g("Kicker", t(cx, 60, "TASTING COUNTER", 10, th["accent"], "bricolage", 500, track=320)),
         g("Display", t(cx, 82, "Nobody leaves", 60, th["main"], italic=True, maxw=A4W - 24),
           t(cx, 103, "without tasting.", 60, th["main"], italic=True, maxw=A4W - 24)),
         g("Attribution", t(cx, 114, "Dadi’s house rule", 14, th["accent"], italic=True)),
         rule(cx - 15, cx + 15, 122, th["accent"], 1.4),
         g("Order_Head", t(cx, 134, "TASTE IN THIS ORDER, MILD TO BOLD", 8.5, th["accent"], "bricolage", 500,
                           track=260))]
    # centre the flight as a block: number disc + widest name / note
    text_w = max(max(measure(n, "fraunces", 17, 400, True), measure(d, "bricolage", 9)) for n, d in TASTING)
    x_num = cx - (8.8 + 5.6 + text_w) / 2 + 4.4
    x_txt, top, step = x_num + 10, 141, 13.6
    rows = []
    for i, (name, note) in enumerate(TASTING):
        y = top + i * step
        rows.append(g(f"Taste_{i + 1}",
                      f'<circle cx="{px(x_num):.2f}" cy="{px(y + 5.6):.2f}" r="{4.4 * MM:.2f}" fill="{th["accent"]}"/>',
                      t(x_num, y + 7.6, str(i + 1), 14, th["num_ink"], "fraunces", 600),
                      t(x_txt, y + 5.4, name, 17, th["main"], italic=True, anchor="start", maxw=A4W - x_txt - 30),
                      t(x_txt, y + 10.6, note, 9, th["body"], "bricolage", 400, "start", maxw=A4W - x_txt - 30)))
    o.append(g("Tasting_Flight", *rows))

    yb = top + len(TASTING) * step + 4
    o.append(rule(16, A4W - 16, yb, th["accent"], .8))
    qs = 30
    o.append(g("Take_Home",
               t(16, yb + 10, "LIKED IT?", 8.5, th["accent"], "bricolage", 500, "start", 260),
               t(16, yb + 19, "Take it home, or make it", 15, th["main"], italic=True, anchor="start"),
               t(16, yb + 26, "a Diwali gift. Ask us.", 15, th["main"], italic=True, anchor="start"),
               qr_code(WHATSAPP, A4W - 16 - qs, yb + 4, qs, INK, CREAM),
               t(A4W - 16 - qs - 5, yb + 12, "ORDER AGAIN", 8.5, th["accent"], "bricolage", 500, "end", 260),
               t(A4W - 16 - qs - 5, yb + 19, "Scan for WhatsApp", 11, th["main"], italic=True, anchor="end"),
               t(A4W - 16 - qs - 5, yb + 25, "+91 79886 26068", 11, th["main"], "fraunces", 600, "end")))
    o.append(g("Footer",
               t(cx, yb + 42, ALLERGEN, 7, th["body"], "bricolage", 400, maxw=A4W - 30),
               t(cx, yb + 50, SIGN_OFF, 12, th["accent"], italic=True)))
    return svg_doc("\n".join(o), f"Ashvena 1953 tasting counter A4 ({theme})", th["bg"], A4W, A4H)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in [("ashvena-standee_real-fruit-candies", standee_candies_red),
                     ("ashvena-standee_masalas-dry-fruits", standee_pantry_red),
                     ("ashvena-standee_real-fruit-candies-light", standee_candies),
                     ("ashvena-standee_masalas-dry-fruits-light", standee_pantry),
                     ("ashvena-display_red-no-shortcuts", message_red),
                     ("ashvena-display_blue-house-rule", message_blue),
                     ("ashvena-a4_tasting-counter-red", lambda: tasting_counter("red")),
                     ("ashvena-a4_tasting-counter-blue", lambda: tasting_counter("blue"))]:
        path = os.path.join(OUT, name + ".svg")
        with open(path, "w") as fh:
            fh.write(fn())
        print(os.path.relpath(path, BASE))


if __name__ == "__main__":
    main()
