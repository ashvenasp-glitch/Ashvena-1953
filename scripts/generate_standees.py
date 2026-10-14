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

Prices: fill MRP below (e.g. "amla": "180"); empty ones print a write-in line.

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

MRP = {}                                 # product key -> price, e.g. {"amla": "180"}

CANDIES = [
    dict(key="amla", name="Amla Candy", title="#2D6C4C", lid="lid-amla.png", net="250 g",
         lines=["Dried amla with sugar. Sweet, soft and chewy."]),
    dict(key="khatti-meethi", name="Khatti-Meethi Amla Candy", title="#1C6467", lid="lid-khatti-meethi.png",
         net="250 g", lines=["Dried amla with sugar, rock salt and spices."]),
    dict(key="carrot", name="Carrot Candy", title="#A85325", lid="lid-carrot.png", net="250 g",
         lines=["Because Dadi always said carrots are good for your eyes."], claim="MADE WITH REAL CARROT"),
]
MASALAS = [
    dict(key="cutting-chai", name="Cutting Chai", title="#81461F", art="cutting-chai-bowl.jpg", net="100 g",
         line="Brewed strong. Poured slow."),
    dict(key="chatpata-chaat", name="Chatpata Chaat", title="#982820", art="chatpata-chaat-bowl.jpg", net="100 g",
         line="Tangy, salty, a little wild."),
]
DRY_FRUITS = [
    dict(key="whole-cashews", name="Whole Cashews", title="#6C5020", net="250 g",
         line="Papa’s rule: whole ones for the guests. We only pack whole ones."),
    dict(key="akbari-pistachios", name="Akbari Pistachios", title="#414A27", net="250 g",
         line="Papa’s rule: crack them open yourself. They taste better."),
    dict(key="california-almonds", name="California Almonds", title="#985E31", net="250 g",
         line="Mum’s rule: soak five at night, eat them at sunrise."),
    # raisin title #D3992C is too pale at list size on cream: use the darkest range colour (head)
    dict(key="seedless-raisins", name="Seedless Raisins", title="#6D441B", net="250 g",
         line="Papa’s rule: one handful a day. Papa has big hands."),
    dict(key="walnut-kernels", name="Walnut Kernels", title="#9A7040", net="250 g",
         line="Papa’s rule: walnuts look like brains for a reason."),
]

CLAIMS = "MADE WITH REAL FRUIT  ·  73-YEAR-OLD RECIPE  ·  NO ADDED COLOUR"
SIGN_OFF = "Heirloom, remixed. · Since 1953"
CARE = "MRP incl. of all taxes  ·  Customer care +91 79886 26068 (WhatsApp)"

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


def mrp(key):
    return f"MRP ₹ {MRP[key]}" if MRP.get(key) else "MRP ₹ ________"


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


def lid(name, cx, cy, d):
    img, _ = image(name, cx - d / 2, cy - d / 2, d, d, gid="Lid_" + name.split(".")[0].replace("lid-", ""))
    return img


def footer(y):
    return g("Footer",
             rule(6, TW - 6, y),
             t(CX, y + 7, SIGN_OFF, 11, INK, "fraunces", 400, italic=True),
             t(CX, y + 12.5, CARE, 6.5, STORY, "bricolage", 400, track=20, maxw=TW - 16))


def svg_doc(body, title, wall):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W / MM:.1f}mm" height="{H / MM:.1f}mm" viewBox="0 0 {W:.1f} {H:.1f}">\n'
            f'<title>{esc(title)}</title>\n'
            f'<g id="Background"><rect width="{W:.1f}" height="{H:.1f}" fill="{wall}"/></g>\n'
            f'{body}\n'
            f'<g id="Guides" opacity="0">'
            f'<rect id="Trim" x="{px(0)}" y="{px(0)}" width="{TW * MM:.1f}" height="{TH * MM:.1f}" fill="none" stroke="#ff00ff"/>'
            f'<rect id="Safe_6mm" x="{px(6)}" y="{px(6)}" width="{(TW - 12) * MM:.1f}" height="{(TH - 16) * MM:.1f}" '
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
        r = [lid(c["lid"], 13, y + 10.5, 14),
             t(25, y + 8.5, c["name"], 18, c["title"], "lobster", anchor="start", maxw=88),
             t(TW - 6, y + 4.6, "NET WT.", 5.2, STORY, "bricolage", 500, "end", 100),
             t(TW - 6, y + 10.2, c["net"], 14, c["title"], "fraunces", 600, "end"),
             t(TW - 6, y + 15.6, mrp(c["key"]), 7.5, STORY, "bricolage", 400, "end")]
        for j, line in enumerate(c["lines"]):
            r.append(t(25, y + 14 + j * 4.4, line, 8.5, STORY, italic=True, anchor="start", maxw=92))
        if c.get("claim"):
            r.append(t(25, y + 14 + len(c["lines"]) * 4.4, c["claim"], 5.6, STORY, "bricolage", 500, "start", 100))
        if i < len(CANDIES) - 1:
            r.append(rule(25, TW - 6, y + step - 1))
        o.append(g("Product_" + c["key"].replace("-", "_"), *r))
    o.append(footer(FOOTER_Y))
    return svg_doc("\n".join(o), "Ashvena 1953 stall standee - Real Fruit Candies", WALL_CANDY)


# ---------------------------------------------------------------------------
# Standee 2 - Masalas (73-year-old recipe) & Premium Dry Fruits
# ---------------------------------------------------------------------------

def standee_pantry():
    o = [veg_mark(6, 6), logo(CX, 7, 24)]
    o.append(g("Masala_Head",
               t(CX, 41, "Recipe from 1953", 20, INK, italic=True),
               t(CX, 46.5, "MASALAS", 7, "#3D2313", "bricolage", 500, track=320)))
    for i, m in enumerate(MASALAS):
        cx = TW / 4 + i * TW / 2
        art, h = image(m["art"], cx - 37, 47.5, 74, gid="Art_" + m["key"].replace("-", "_"))
        y = 47.5 + h
        o.append(g("Product_" + m["key"].replace("-", "_"),
                   art,
                   t(cx, y + 7, m["name"], 17, m["title"], italic=True, maxw=68),
                   t(cx, y + 11.5, "MASALA", 6.5, "#3D2313", "bricolage", 500, track=320),
                   t(cx, y + 16.5, m["line"], 8.5, STORY, italic=True, maxw=68),
                   t(cx, y + 22, f"NET WT. {m['net']}   ·   {mrp(m['key'])}", 7, STORY, "bricolage", 400, maxw=70)))
    y_div = 47.5 + h + 27
    o.append(rule(6, TW - 6, y_div))

    yt = y_div + 11
    o.append(g("Dry_Fruit_Head", t(6, yt, "Premium Dry Fruits", 22, "#6C5020", "lobster", anchor="start")))
    ah = art_height("papa-family-scene.jpg", 78)
    art, _ = image("papa-family-scene.jpg", TW + BLEED - 78, FOOTER_Y - 3.5 - ah, 78, gid="Art_Papa_Scene")
    o.append(g("Illustration", art))
    rows, ly, rx = [], yt + 7, 76
    step = (FOOTER_Y - 2 - ly) / len(DRY_FRUITS)
    for i, d in enumerate(DRY_FRUITS):
        y = ly + i * step
        rows.append(g("Product_" + d["key"].replace("-", "_"),
                      t(6, y + 4.8, d["name"], 13, d["title"], "lobster", anchor="start", maxw=50),
                      t(rx, y + 4.4, f"{d['net']}  ·  {mrp(d['key']).replace('MRP ', '')}", 6.8, STORY, "bricolage",
                        400, "end"),
                      t(6, y + 9.2, d["line"], 6.6, STORY, italic=True, anchor="start", maxw=rx - 6)))
        if i < len(DRY_FRUITS) - 1:
            rows.append(rule(6, rx, y + step - 1.3))
    o.append(g("Dry_Fruit_List", *rows))
    o.append(footer(FOOTER_Y))
    return svg_doc("\n".join(o), "Ashvena 1953 stall standee - Masalas & Dry Fruits", WALL_PANTRY)


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


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in [("ashvena-standee_real-fruit-candies", standee_candies),
                     ("ashvena-standee_masalas-dry-fruits", standee_pantry),
                     ("ashvena-display_red-no-shortcuts", message_red),
                     ("ashvena-display_blue-house-rule", message_blue)]:
        path = os.path.join(OUT, name + ".svg")
        with open(path, "w") as fh:
            fh.write(fn())
        print(os.path.relpath(path, BASE))


if __name__ == "__main__":
    main()
