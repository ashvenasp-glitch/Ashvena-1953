#!/usr/bin/env python3
"""Ashvena "thank you for your purchase" insert card - Direction F.

Modelled on the clean "Say hello to your new favorite" retail insert, in the
colours and style of the official logo (brand/ashvena-logo_final.ai):
brush-stroke "अ" mark, high-contrast serif wordmark, Brick + Dispensary blue.

Front: Brick field with the brush mark blown up and merged tone-on-tone into
the background, the horizontal logo lockup and a serif / italic headline.
Back: Dispensary-blue card with a heartfelt note and a scannable Instagram QR.

Artboard: 150 x 100 mm (4 px = 1 mm), landscape.
Output: packaging/F-thank-you-card/ashvena-thank-you-card_<side>.svg

Usage: python3 scripts/generate_thank_you_card.py [--insta HANDLE] [--phone NUMBER]
"""
import argparse
import json
import os

import segno

from generate_packaging import esc

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "packaging", "F-thank-you-card")
LOGO = json.load(open(os.path.join(HERE, "..", "brand", "ashvena-logo-parts.json")))
W, H = 600, 400

INSTAGRAM = "ashvena.1953"  # PLACEHOLDER - confirm the real handle before print
PHONE = "+91 79886 26068"

F_SERIF = "'Bodoni Moda', 'Libre Caslon Display', Didot, serif"
F_SANS = "Montserrat, Helvetica, Arial, sans-serif"

# logo palette (see brand/ashvena-logo-parts.json)
BRICK = LOGO["palette"]["brick"]
DEEP_LAC = LOGO["palette"]["deep_lac"]
DISPENSARY = LOGO["palette"]["dispensary"]
KHADI = LOGO["palette"]["khadi_cream"]

DEFS = f"""
<radialGradient id="brickBg" cx=".72" cy=".38" r=".95">
  <stop offset="0" stop-color="#a11a2f"/><stop offset=".55" stop-color="{BRICK}"/><stop offset="1" stop-color="#7a0f20"/>
</radialGradient>
<clipPath id="cardClip"><rect width="{W}" height="{H}"/></clipPath>
"""


def text(x, y, s, size, fill, family=F_SANS, weight=400, ls=0, anchor="middle", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}"{extra}>{s}</text>')


def g(gid, body):
    return f'<g id="{gid}">\n{body}\n</g>'


def logo_part(name, x, y, h, fill, op=1, rot=0):
    """Place a logo path so its bounding box top-left sits at (x, y) with height h."""
    x0, y0, x1, y1 = LOGO[name]["bbox"]
    k = h / (y1 - y0)
    r = f" rotate({rot} {(x0 + x1) / 2:.1f} {(y0 + y1) / 2:.1f})" if rot else ""
    o = f' opacity="{op}"' if op != 1 else ""
    return (f'<path fill="{fill}"{o} transform="translate({x:.2f} {y:.2f}) scale({k:.4f}) '
            f'translate({-x0:.2f} {-y0:.2f}){r}" d="{LOGO[name]["d"]}"/>')


def part_width(name, h):
    x0, y0, x1, y1 = LOGO[name]["bbox"]
    return (x1 - x0) * h / (y1 - y0)


def lockup_horizontal(x, y, h, mark_col, word_col, year_col):
    """Mark + 'Ashvena' / '1953' side by side (logo artboard 2 arrangement)."""
    o = [logo_part("mark", x, y, h, mark_col)]
    wx = x + part_width("mark", h) + h * .22
    wh = h * .36
    o.append(logo_part("wordmark", wx, y + h * .22, wh, word_col))
    o.append(logo_part("year", wx + h * .02, y + h * .22 + wh + h * .06, wh * .5, year_col))
    return "".join(o)


def svg_doc(body, title):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W / 4:.0f}mm" height="{H / 4:.0f}mm" '
            f'viewBox="0 0 {W} {H}">\n<title>{esc(title)}</title>\n<defs>{DEFS}</defs>\n'
            f'<g clip-path="url(#cardClip)">\n{body}\n</g>\n</svg>\n')


# ---------------------------------------------------------------------------
# Front
# ---------------------------------------------------------------------------

def front():
    o = [g("Background", f'<rect width="{W}" height="{H}" fill="url(#brickBg)"/>')]
    # the brush mark, blown up and bleeding off the right edge, inked tone-on-tone into the brick
    o.append(g("Logo_Watermark", logo_part("mark", 262, -22, 440, DEEP_LAC, op=.28)))
    o.append(g("Ashvena_Logo", lockup_horizontal(44, 40, 58, DISPENSARY, KHADI, DISPENSARY)))
    o.append(g("Headline",
               text(44, 286, "Say", 50, KHADI, F_SERIF, 500, anchor="start")
               + text(138, 286, "hello", 64, DISPENSARY, F_SERIF, 400, anchor="start", extra=' font-style="italic"')
               + text(44, 344, "to your new favourite.", 50, KHADI, F_SERIF, 500, anchor="start")))
    return svg_doc("\n".join(o), "Ashvena thank-you card - front")


# ---------------------------------------------------------------------------
# Back
# ---------------------------------------------------------------------------

BODY = [
    "We’re truly honoured to be part of your celebrations.",
    "Every cashew is slow-roasted to our family recipe from 1953,",
    "bringing heritage, warmth and flavour to your table.",
]
OFFER = [
    "As a small token of appreciation,",
    'please enjoy <tspan font-weight="800">15% off</tspan> your next purchase.',
    "Your trust means the world to us.",
]


def qr_code(x, y, size, url, col):
    m = list(segno.make(url, error="q").matrix)
    c = size / len(m)
    d = "".join(f"M{x + i * c:.2f},{y + j * c:.2f}h{c:.2f}v{c:.2f}h{-c:.2f}z"
                for j, row in enumerate(m) for i, v in enumerate(row) if v)
    return f'<g id="Instagram_QR"><title>{esc(url)}</title><path d="{d}" fill="{col}" shape-rendering="crispEdges"/></g>'


def insta_glyph(x, y, s, col):
    return (f'<g transform="translate({x} {y}) scale({s / 14:.3f})">'
            f'<rect x="-7" y="-7" width="14" height="14" rx="4" fill="none" stroke="{col}" stroke-width="1.5"/>'
            f'<circle r="3.3" fill="none" stroke="{col}" stroke-width="1.5"/>'
            f'<circle cx="3.9" cy="-3.9" r=".9" fill="{col}"/></g>')


def phone_glyph(x, y, s, col):
    """Mobile phone outline, centred on (x, y), s px tall."""
    k = s / 14
    return (f'<g transform="translate({x} {y}) scale({k:.3f})">'
            f'<rect x="-4.5" y="-7" width="9" height="14" rx="1.8" fill="none" stroke="{col}" stroke-width="1.4"/>'
            f'<line x1="-1.5" y1="-5" x2="1.5" y2="-5" stroke="{col}" stroke-width="1"/>'
            f'<circle cy="4.6" r=".9" fill="{col}"/></g>')


def back(handle, phone):
    cx = W / 2
    o = [g("Background", f'<rect width="{W}" height="{H}" fill="{DISPENSARY}"/>')]
    o.append(g("Logo_Mark", logo_part("mark", cx - part_width("mark", 34) / 2, 24, 34, BRICK)))
    o.append(g("Heading",
               text(cx, 96, "Thank you for choosing us for", 25, DEEP_LAC, F_SERIF, 500)
               + text(cx, 136, "your special moments", 38, BRICK, F_SERIF, 400, extra=' font-style="italic"')))
    o.append(g("Message", "".join(text(cx, 166 + i * 15.5, s, 11, DEEP_LAC, F_SANS, 500) for i, s in enumerate(BODY))))
    o.append(g("Offer", "".join(text(cx, 222 + i * 15.5, s, 11, DEEP_LAC, F_SANS, 500) for i, s in enumerate(OFFER))))

    # Instagram row: QR on the left, call to action on the right, centred as a unit
    url = f"https://www.instagram.com/{handle}/"
    qs, qx, qy = 82, 192, 278
    o.append(g("Instagram",
               qr_code(qx, qy, qs, url, DEEP_LAC)
               + f'<line x1="{qx + qs + 18}" y1="{qy + 6}" x2="{qx + qs + 18}" y2="{qy + qs - 6}" stroke="{BRICK}" '
                 f'stroke-width=".8" opacity=".45"/>'
               + text(qx + qs + 34, qy + 12, "SCAN TO FOLLOW", 8, BRICK, F_SANS, 700, 2.5, anchor="start")
               + text(qx + qs + 34, qy + 28, "our story on Instagram", 11, DEEP_LAC, F_SANS, 500, anchor="start")
               + insta_glyph(qx + qs + 41, qy + 50, 13, BRICK)
               + text(qx + qs + 54, qy + 54, f"@{esc(handle)}", 11, BRICK, F_SANS, 600, .3, anchor="start")
               + phone_glyph(qx + qs + 41, qy + 70, 13, BRICK)
               + text(qx + qs + 54, qy + 74, esc(phone), 11, BRICK, F_SANS, 600, .3, anchor="start")))
    return svg_doc("\n".join(o), "Ashvena thank-you card - back")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insta", default=INSTAGRAM, help="Instagram handle without @")
    ap.add_argument("--phone", default=PHONE, help="mobile number as printed, e.g. '+91 98765 43210'")
    a = ap.parse_args()
    os.makedirs(ROOT, exist_ok=True)
    for side, svg in [("front", front()), ("back", back(a.insta.lstrip("@"), a.phone))]:
        p = os.path.join(ROOT, f"ashvena-thank-you-card_{side}.svg")
        open(p, "w").write(svg)
        print(os.path.relpath(p, os.path.join(ROOT, "..", "..")))


if __name__ == "__main__":
    main()
