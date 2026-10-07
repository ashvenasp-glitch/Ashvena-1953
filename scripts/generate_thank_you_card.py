#!/usr/bin/env python3
"""Ashvena "thank you for your purchase" insert card - Direction F.

Modelled on the clean "Say hello to your new favorite" retail insert:
Front: solid Ashvena red with a giant tone-on-tone emblem merging into the
field, the wordmark, bold sans + script headline and a peacock-blue foot.
Back: cream card, bold sans heading with a script line, a short heartfelt
note, and a scannable Instagram QR code.

Artboard: 150 x 100 mm (4 px = 1 mm), landscape.
Output: packaging/F-thank-you-card/ashvena-thank-you-card_<side>.svg

Usage: python3 scripts/generate_thank_you_card.py [--insta HANDLE]
"""
import argparse
import os

import segno

from generate_packaging import CASHEW, esc

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packaging", "F-thank-you-card")
W, H = 600, 400

INSTAGRAM = "ashvena.1953"  # PLACEHOLDER - confirm the real handle before print

F_DISPLAY = "Cinzel, 'Trajan Pro', serif"
F_SANS = "Montserrat, Helvetica, Arial, sans-serif"
F_SCRIPT = "'Pinyon Script', 'Great Vibes', cursive"

RED = "#7d1a26"
RED_DEEP = "#5e111c"
RED_LIGHT = "#8f2533"
BLUE = "#1b4f8a"
BLUE_DEEP = "#123a6b"
CREAM = "#f2ecdf"
IVORY = "#f6efe2"
GOLD = "#c9a45c"

DEFS = f"""
<radialGradient id="redBg" cx=".7" cy=".4" r=".9">
  <stop offset="0" stop-color="{RED_LIGHT}"/><stop offset=".6" stop-color="{RED}"/><stop offset="1" stop-color="{RED_DEEP}"/>
</radialGradient>
<clipPath id="cardClip"><rect width="{W}" height="{H}"/></clipPath>
"""


def text(x, y, s, size, fill, family=F_SANS, weight=400, ls=0, anchor="middle", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}"{extra}>{s}</text>')


def g(gid, body):
    return f'<g id="{gid}">\n{body}\n</g>'


def emblem(cx, cy, r, col, sw=1.5, op=1):
    """Ashvena roundel: double ring, diamond finial, Cinzel 'A' and a cashew."""
    s = r / 70
    return (f'<g opacity="{op}">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="{sw}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * .93:.1f}" fill="none" stroke="{col}" stroke-width="{sw * .45:.2f}"/>'
            f'<path d="M {cx},{cy - r * .78:.1f} l {r * .07:.1f},{r * .09:.1f} l {-r * .07:.1f},{r * .09:.1f} '
            f'l {-r * .07:.1f},{-r * .09:.1f} Z" fill="{col}"/>'
            f'<text x="{cx}" y="{cy + r * .14:.1f}" font-family="{F_DISPLAY}" font-size="{r * .82:.1f}" '
            f'font-weight="600" fill="{col}" text-anchor="middle">A</text>'
            f'<path d="{CASHEW}" transform="translate({cx} {cy + r * .42:.1f}) scale({s:.3f})" fill="{col}"/>'
            f'</g>')


def monogram(cx, cy, r, col, op=1):
    """Oversized emblem ring + 'A' for the merged watermark (cashew left out at this scale)."""
    return (f'<g opacity="{op}">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="7"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * .93:.1f}" fill="none" stroke="{col}" stroke-width="2"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 1.08:.1f}" fill="none" stroke="{col}" stroke-width="1.2"/>'
            f'<path d="M {cx},{cy - r * .82:.1f} l {r * .06:.1f},{r * .08:.1f} l {-r * .06:.1f},{r * .08:.1f} '
            f'l {-r * .06:.1f},{-r * .08:.1f} Z" fill="{col}"/>'
            f'<text x="{cx}" y="{cy + r * .4:.1f}" font-family="{F_DISPLAY}" font-size="{r * 1.2:.1f}" '
            f'font-weight="600" fill="{col}" text-anchor="middle">A</text>'
            f'</g>')


def svg_doc(body, title):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W / 4:.0f}mm" height="{H / 4:.0f}mm" '
            f'viewBox="0 0 {W} {H}">\n<title>{esc(title)}</title>\n<defs>{DEFS}</defs>\n'
            f'<g clip-path="url(#cardClip)">\n{body}\n</g>\n</svg>\n')


# ---------------------------------------------------------------------------
# Front
# ---------------------------------------------------------------------------

def front():
    o = [g("Background", f'<rect width="{W}" height="{H}" fill="url(#redBg)"/>')]

    # giant emblem bleeding off the top-right corner, tone-on-tone so it merges into the red
    o.append(g("Logo_Watermark",
               monogram(462, 170, 250, "#a33545", op=.55)))

    o.append(g("Ashvena_Logo",
               emblem(64, 66, 22, IVORY, sw=1.3)
               + text(98, 63, "ASHVENA", 17, IVORY, F_DISPLAY, 600, 5, anchor="start")
               + text(99, 77, "EST. 1953", 6.5, GOLD, F_SANS, 600, 3, anchor="start")))

    o.append(g("Headline",
               text(46, 272, "Say", 44, IVORY, F_SANS, 700, 1, anchor="start")
               + text(152, 268, "hello", 92, IVORY, F_SCRIPT, 400, anchor="start")
               + text(46, 322, "to your new favourite.", 44, IVORY, F_SANS, 700, .5, anchor="start")))

    # peacock-blue foot with a fine gold rule
    o.append(g("Blue_Foot",
               f'<rect x="0" y="{H - 30}" width="{W}" height="30" fill="{BLUE_DEEP}"/>'
               f'<rect x="0" y="{H - 30}" width="{W}" height="1.6" fill="{GOLD}"/>'
               + text(W / 2, H - 11.5, "PREMIUM CASHEWS  ·  SINCE 1953", 7.5, IVORY, F_SANS, 600, 4)))
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


def back(handle):
    cx = W / 2
    o = [g("Background", f'<rect width="{W}" height="{H}" fill="{CREAM}"/>')]
    o.append(g("Heading",
               text(cx, 70, "Thank you for choosing us for", 25, RED, F_SANS, 700, .2)
               + text(cx, 116, "your special moments", 50, BLUE, F_SCRIPT, 400)))
    o.append(g("Message", "".join(text(cx, 153 + i * 16, s, 11.5, RED, F_SANS, 500) for i, s in enumerate(BODY))))
    o.append(g("Offer", "".join(text(cx, 215 + i * 16, s, 11.5, RED, F_SANS, 500) for i, s in enumerate(OFFER))))

    # Instagram row: QR on the left, call to action on the right, centred as a unit
    url = f"https://www.instagram.com/{handle}/"
    qs, qx, qy = 84, 190, 270
    o.append(g("Instagram",
               qr_code(qx, qy, qs, url, RED_DEEP)
               + f'<line x1="{qx + qs + 18}" y1="{qy + 6}" x2="{qx + qs + 18}" y2="{qy + qs - 6}" stroke="{RED}" '
                 f'stroke-width=".8" opacity=".35"/>'
               + text(qx + qs + 34, qy + 22, "SCAN TO FOLLOW", 8, BLUE, F_SANS, 700, 2.5, anchor="start")
               + text(qx + qs + 34, qy + 38, "our story on Instagram", 11.5, RED, F_SANS, 500, anchor="start")
               + insta_glyph(qx + qs + 41, qy + 59, 13, RED)
               + text(qx + qs + 54, qy + 63, f"@{esc(handle)}", 11, RED, F_SANS, 600, .3, anchor="start")))
    return svg_doc("\n".join(o), "Ashvena thank-you card - back")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insta", default=INSTAGRAM, help="Instagram handle without @")
    a = ap.parse_args()
    os.makedirs(ROOT, exist_ok=True)
    for side, svg in [("front", front()), ("back", back(a.insta.lstrip("@")))]:
        p = os.path.join(ROOT, f"ashvena-thank-you-card_{side}.svg")
        open(p, "w").write(svg)
        print(os.path.relpath(p, os.path.join(ROOT, "..", "..")))


if __name__ == "__main__":
    main()
