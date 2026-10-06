#!/usr/bin/env python3
"""Ashvena 1953 visiting card: front in Dispensary blue, back in Brick red.

Front: horizontal logo lockup, name, labelled contact rows and a dotted
Instagram QR code; a line-art palm leans in from the right edge.
Back: the reversed logo inside a cusped jharokha arch, banana leaves and a
faint interlocking-circle lattice (after the botanical / jharokha references).

Uses the vector lockup in brand/ashvena-logo.svg (extracted from logo_final.ai).
Card: 3.5 x 2 in (88.9 x 50.8 mm) trim + 3 mm bleed, at 10 px = 1 mm.

One front is made per Instagram handle in HANDLES so each QR can be test-scanned.

Output (stationery/visiting-card/):
  ashvena-visiting-card_back.ai / .svg / .png
  ashvena-visiting-card_front_<handle>.ai / .svg / .png
  ashvena-visiting-card_print_<handle>.pdf     2 pages (front, back), with bleed
  ashvena-visiting-card-board.png

Requires: pip install playwright pypdf segno, plus Cormorant Garamond and Montserrat.
"""
import base64
import glob
import math
import os
import re
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
BRICK_DARK = "#7E0F20"
LAC = "#35070F"
DISPENSARY = "#CBE9F1"
BLUE_LINE = "#7DB3C6"
BLUE_FILL = "#BCDFEA"
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
HANDLES = ["ashvena1953", "ashvena.sp"]


def instagram_url(handle):
    return f"https://instagram.com/{handle}"


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


def lockup_stacked(gid, cx, top, height, mark, word, year):
    bx, by, bw, bh = union("Mark", "Wordmark", "Year")
    s = height / bh
    tx, ty = cx - (bx + bw / 2) * s, top - by * s
    body = logo_path(gid, "Mark", mark) + logo_path(gid, "Wordmark", word) + logo_path(gid, "Year", year)
    return f'<g id="{gid}" transform="translate({tx:.2f} {ty:.2f}) scale({s:.5f})">{body}</g>'


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


def bezier(p0, p1, p2, t):
    a = (1 - t) ** 2
    b = 2 * (1 - t) * t
    c = t * t
    x = a * p0[0] + b * p1[0] + c * p2[0]
    y = a * p0[1] + b * p1[1] + c * p2[1]
    dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
    dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
    n = math.hypot(dx, dy) or 1
    return x, y, dx / n, dy / n


# ---------------------------------------------------------------- QR

def qr_code(gid, url, x, y, size, ink, paper):
    """Dotted QR (round modules, rounded finders) with an Instagram glyph in the centre."""
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
                 f'rx="{.5 * u:.2f}" fill="none" stroke="{ink}" stroke-width="{u:.2f}"/>')
        o.append(f'<rect x="{fx + 2 * u:.2f}" y="{fy + 2 * u:.2f}" width="{3 * u:.2f}" height="{3 * u:.2f}" '
                 f'rx="{.3 * u:.2f}" fill="{ink}"/>')
    cx, cy = x + size / 2, y + size / 2
    o.append(f'<rect x="{cx - hole * u / 2 + u * .3:.2f}" y="{cy - hole * u / 2 + u * .3:.2f}" '
             f'width="{hole * u - u * .6:.2f}" height="{hole * u - u * .6:.2f}" rx="{u * 1.6:.2f}" fill="{paper}"/>')
    o.append(instagram_glyph(cx, cy, hole * u * .62, ink, u * .62))
    o.append('</g>')
    return "".join(o)


# ---------------------------------------------------------------- botanicals

def palm_frond(base, ctrl, tip, leaflets, length, stroke, fill, sw=1.2, droop=.35, side=1):
    """Feathery palm frond: curved rachis with narrow drooping leaflets on both sides."""
    o = [f'<path d="M{base[0]:.1f},{base[1]:.1f} Q{ctrl[0]:.1f},{ctrl[1]:.1f} {tip[0]:.1f},{tip[1]:.1f}" '
         f'fill="none" stroke="{stroke}" stroke-width="{sw * 1.6:.2f}" stroke-linecap="round"/>']
    for i in range(leaflets):
        t = .08 + .92 * i / (leaflets - 1)
        px, py, dx, dy = bezier(base, ctrl, tip, t)
        L = length * (1 - .72 * t) * (0.75 + .25 * math.sin(math.pi * min(t * 1.3, 1)))
        for s in (-1, 1):
            a = math.atan2(dy, dx) + s * math.radians(38 - 12 * t)
            ex, ey = px + L * math.cos(a), py + L * math.sin(a) + L * droop
            mx, my = px + L * .5 * math.cos(a), py + L * .5 * math.sin(a)
            nx, ny = -(ey - py), ex - px
            nn = math.hypot(nx, ny) or 1
            wv = L * .07
            o.append(f'<path d="M{px:.1f},{py:.1f} Q{mx + nx / nn * wv:.1f},{my + ny / nn * wv:.1f} {ex:.1f},{ey:.1f} '
                     f'Q{mx - nx / nn * wv:.1f},{my - ny / nn * wv:.1f} {px:.1f},{py:.1f} Z" '
                     f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:.2f}" stroke-linejoin="round"/>')
    return "".join(o)


def palm_tree(gid, top, foot, ctrl, stroke, fill, scale=1.0):
    """Curved trunk with ring marks and a crown of fronds."""
    o = [f'<g id="{gid}">']
    # trunk
    n = 22
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        x, y, dx, dy = bezier(foot, ctrl, top, t)
        w = (13 - 6 * t) * scale
        left.append((x - dy * w, y + dx * w))
        right.append((x + dy * w, y - dx * w))
    pts = left + right[::-1]
    o.append('<path d="M' + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + f' Z" fill="{fill}" stroke="{stroke}" '
             f'stroke-width="1.3" stroke-linejoin="round"/>')
    for i in range(2, n - 1, 2):
        (ax, ay), (bx, by) = left[i], right[i]
        o.append(f'<path d="M{ax:.1f},{ay:.1f} Q{(ax + bx) / 2:.1f},{(ay + by) / 2 + 3:.1f} {bx:.1f},{by:.1f}" '
                 f'fill="none" stroke="{stroke}" stroke-width=".9"/>')
    # crown
    cx, cy = top
    for ang, ln, bend in [(-168, 175, 40), (-140, 190, 30), (-110, 170, 25), (-75, 165, -25), (-40, 185, -30),
                          (-10, 175, -40), (20, 140, -40), (190, 150, 45)]:
        a = math.radians(ang)
        ln *= scale
        tip = (cx + ln * math.cos(a), cy + ln * math.sin(a) + ln * .25)
        c = (cx + ln * .55 * math.cos(a) - bend * scale * math.sin(a) * .3,
             cy + ln * .55 * math.sin(a) - abs(bend) * scale * .5)
        o.append(palm_frond((cx, cy), c, tip, 16, 58 * scale, stroke, fill, sw=1.0, droop=.3))
    o.append('</g>')
    return "".join(o)


def banana_leaf(base, ctrl, tip, width, stroke, fill):
    """Broad banana leaf: outline from a width profile along the midrib, oblique parallel veins."""
    n = 30
    left, right, mid = [], [], []
    for i in range(n + 1):
        t = i / n
        x, y, dx, dy = bezier(base, ctrl, tip, t)
        w = width * (math.sin(math.pi * min(t * 1.05, 1)) ** .7) * (1 - .15 * t)
        mid.append((x, y, dx, dy))
        left.append((x - dy * w, y + dx * w))
        right.append((x + dy * w, y - dx * w))
    outline = "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in left + right[::-1]) + " Z"
    o = [f'<path d="{outline}" fill="{fill}" stroke="{stroke}" stroke-width="1.4" stroke-linejoin="round"/>']
    o.append(f'<path d="M{base[0]:.1f},{base[1]:.1f} Q{ctrl[0]:.1f},{ctrl[1]:.1f} {tip[0]:.1f},{tip[1]:.1f}" '
             f'fill="none" stroke="{stroke}" stroke-width="2.2"/>')
    for i in range(2, n - 1):
        x, y, dx, dy = mid[i]
        for edge, sgn in ((left, 1), (right, -1)):
            j = min(i + 1, n)
            ex, ey = edge[j]
            o.append(f'<path d="M{x:.1f},{y:.1f} Q{(x + ex) / 2 + dx * 4:.1f},{(y + ey) / 2 + dy * 4:.1f} {ex:.1f},{ey:.1f}" '
                     f'fill="none" stroke="{stroke}" stroke-width=".6" opacity=".75"/>')
    return "".join(o)


def lattice(x0, y0, x1, y1, r, stroke, op):
    """Interlocking circles (as on the Almanova pattern card)."""
    o = [f'<g id="Lattice" fill="none" stroke="{stroke}" stroke-width="1" opacity="{op}">']
    step = r
    y, row = y0, 0
    while y <= y1 + r:
        x = x0 + (step / 2 if row % 2 else 0)
        while x <= x1 + r:
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * .72:.1f}"/>')
            x += step
        y += step / 2
        row += 1
    o.append('</g>')
    return "".join(o)


def cusped_arch(cx, half, spring, apex, lobes):
    """Opening of a multifoil (cusped) pointed arch, returned as path commands from left spring to right spring."""
    rise = spring - apex
    a = (rise ** 2 - half ** 2) / (2 * half)          # pointed-arch centre offset
    R = half + a
    th_end = math.atan2(rise, -a) if a else math.pi / 2  # left arc: centre (cx + a, spring)
    pts = []
    for k in range(lobes + 1):                         # left half, spring -> apex
        th = math.pi - (math.pi - th_end) * k / lobes
        pts.append((cx + a + R * math.cos(th), spring - R * math.sin(th)))
    right = [(2 * cx - px, py) for px, py in pts[-2::-1]]
    pts += right
    d = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        ch = math.hypot(bx - ax, by - ay)
        d.append(f"A{ch * .58:.1f},{ch * .58:.1f} 0 0 1 {bx:.1f},{by:.1f}")
    return pts[0], " ".join(d)


def jharokha(gid, cx, top, stroke, bg):
    """Window frame after the reference: eave, frame, cusped arch opening, sill with scallop fringe."""
    o = [f'<g id="{gid}" fill="none" stroke="{stroke}" stroke-linejoin="round">']
    fw, ew = 150, 186                                  # frame / eave half widths
    eave_t, eave_b = top, top + 30
    f_top, f_bot = eave_b, top + 382
    o.append(f'<path d="M{cx - ew},{eave_t} H{cx + ew} V{eave_t + 9} H{cx - ew} Z" stroke-width="1.6"/>')
    o.append(f'<path d="M{cx - ew + 6},{eave_t + 9} L{cx - fw + 4},{eave_b} H{cx + fw - 4} L{cx + ew - 6},{eave_t + 9}" '
             f'stroke-width="1.6"/>')
    o.append(f'<path d="M{cx - ew + 6},{eave_t + 16} H{cx + ew - 6}" stroke-width=".8" opacity=".7"/>')
    o.append(f'<rect x="{cx - fw}" y="{f_top}" width="{2 * fw}" height="{f_bot - f_top}" stroke-width="1.6"/>')
    o.append(f'<rect x="{cx - fw + 10}" y="{f_top + 10}" width="{2 * fw - 20}" height="{f_bot - f_top - 20}" '
             f'stroke-width=".8" opacity=".7"/>')
    half, spring, apex = 112, f_top + 128, f_top + 34
    (sx, sy), arc = cusped_arch(cx, half, spring, apex, 4)
    bottom = f_bot - 22
    o.append(f'<path d="M{sx:.1f},{bottom} V{sy:.1f} {arc} V{bottom} Z" fill="{bg}" stroke-width="1.6"/>')
    # sill and scallop fringe
    sw2 = fw + 14
    o.append(f'<rect x="{cx - sw2}" y="{f_bot}" width="{2 * sw2}" height="12" stroke-width="1.6"/>')
    k = 12
    step = 2 * sw2 / k
    d = f"M{cx - sw2:.1f},{f_bot + 12}"
    for i in range(k):
        d += f" a{step / 2:.2f},{step / 2:.2f} 0 0 0 {step:.2f},0"
    o.append(f'<path d="{d}" stroke-width="1.2"/>')
    o.append('</g>')
    return "".join(o), (cx, apex, bottom)


# ---------------------------------------------------------------- sides

def front(handle):
    c = CARD
    o = [f'<rect id="Background" width="{W}" height="{H}" fill="{DISPENSARY}"/>']
    o.append('<g id="Palm" opacity=".9">'
             + palm_tree("Palm_Tree", (X0 + TW - 46, Y0 + 74), (X0 + TW - 4, H + 20), (X0 + TW + 6, Y0 + 330),
                         BLUE_LINE, BLUE_FILL, scale=.6)
             + '</g>')

    x = X0 + 58
    o.append(lockup_horizontal("Logo", x, Y0 + 48, 92, BRICK, LAC, BRICK))
    o.append('<g id="Name_Block">'
             + text(x, Y0 + 236, c["name"], 54, LAC, F_SERIF, 600)
             + f'<line x1="{x + 2}" y1="{Y0 + 262}" x2="{x + 64}" y2="{Y0 + 262}" stroke="{BRICK}" stroke-width="2.4"/>'
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

    q, qx, qy = 196, X0 + 536, Y0 + 132
    o.append(f'<rect id="QR_Quiet_Zone" x="{qx - 14}" y="{qy - 14}" width="{q + 28}" height="{q + 28}" rx="14" '
             f'fill="{DISPENSARY}"/>')
    o.append(qr_code("QR_Instagram", instagram_url(handle), qx, qy, q, BRICK, DISPENSARY))
    o.append('<g id="QR_Caption">'
             + text(qx + q / 2, qy - 30, "SCAN · FOLLOW", 14, BRICK, F_SANS, 600, ls=3, anchor="middle")
             + text(qx + q / 2, qy + q + 44, "@" + handle, 21, LAC, F_SANS, 500, ls=.4, anchor="middle")
             + '</g>')
    o.append(guides())
    return svg("\n".join(o))


def back():
    o = [f'<rect id="Background" width="{W}" height="{H}" fill="{BRICK}"/>']
    o.append(lattice(0, 0, W, H, 64, KHADI, .07))
    cx = X0 + TW / 2
    frame, (ax, apex, bottom) = jharokha("Jharokha", cx, Y0 + 44, KHADI, BRICK)
    o.append(frame)
    o.append(lockup_stacked("Logo_Reversed", cx, apex + 40, bottom - apex - 58, SAGE, KHADI, SAGE))
    leaves = [((X0 + TW + 30, H + 10), (X0 + TW - 40, Y0 + 300), (X0 + TW - 150, Y0 + 150), 72),
              ((X0 + TW + 40, H - 10), (X0 + TW - 10, Y0 + 330), (X0 + TW - 40, Y0 + 70), 60),
              ((X0 + TW + 20, H + 20), (X0 + TW - 120, Y0 + 420), (X0 + TW - 250, Y0 + 330), 58)]
    o.append('<g id="Banana_Leaves">'
             + "".join(banana_leaf(b, c_, t, w, SAGE, BRICK_DARK) for b, c_, t, w in leaves)
             + '</g>')
    lf = [((X0 - 30, H + 10), (X0 + 40, Y0 + 300), (X0 + 120, Y0 + 170), 64),
          ((X0 - 40, H - 30), (X0 + 120, Y0 + 430), (X0 + 230, Y0 + 360), 54)]
    o.append('<g id="Banana_Leaves_Left">'
             + "".join(banana_leaf(b, c_, t, w, SAGE, BRICK_DARK) for b, c_, t, w in lf)
             + '</g>')
    o.append(guides())
    return svg("\n".join(o))


# ---------------------------------------------------------------- render

def board_html(back_png, fronts):
    card = "width:889px;height:508px;border-radius:6px;box-shadow:0 30px 60px rgba(53,7,15,.28),0 6px 14px rgba(53,7,15,.18)"
    lab = "position:absolute;color:#35070F;font-size:20px;letter-spacing:3px"
    imgs = [f'<img src="{back_png}" style="position:absolute;left:80px;top:300px;{card};transform:rotate(-4deg)">',
            f'<div style="{lab};left:90px;top:870px">BACK</div>']
    for i, (handle, png) in enumerate(fronts):
        top = 70 + i * 610
        imgs.append(f'<img src="{png}" style="position:absolute;left:1080px;top:{top}px;{card}">')
        imgs.append(f'<div style="{lab};left:1080px;top:{top + 528}px">FRONT, OPTION {"AB"[i]}: QR OPENS '
                    f'INSTAGRAM.COM/{handle.upper()}</div>')
    return (f'<html><body style="margin:0;width:2060px;height:1260px;background:linear-gradient(135deg,#f6efe6,#e9dfd2);'
            f'position:relative;font-family:Montserrat">{"".join(imgs)}</body></html>')


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

        pg = b.new_page(viewport={"width": 2060, "height": 1260})
        pg.set_content(board_html(data(paths[0]), [(h, data(s)) for h, s in zip(HANDLES, paths[1:])]),
                       wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.screenshot(path=os.path.join(OUT, "ashvena-visiting-card-board.png"))
        print("rendered ashvena-visiting-card-board.png")
        b.close()


def to_ai(pdf, title):
    """Crop Chromium's rounded page back to the exact bleed size, mark the trim, save as PDF-compatible .ai."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import RectangleObject
    pt = 72 / 25.4 / MM
    w = PdfWriter(clone_from=PdfReader(pdf))
    page = w.pages[0]
    top = float(page.mediabox.top)            # content is anchored top-left
    page.mediabox = page.cropbox = page.bleedbox = RectangleObject([0, top - H * pt, W * pt, top])
    page.trimbox = RectangleObject([BLEED * pt, top - (BLEED + TH) * pt, (BLEED + TW) * pt, top - BLEED * pt])
    w.add_metadata({"/Title": title, "/Creator": "generate_visiting_card.py"})
    ai = pdf[:-4] + ".ai"
    with open(ai, "wb") as fh:
        w.write(fh)
    os.remove(pdf)
    print("wrote", os.path.basename(ai))
    return ai


def package(paths):
    from pypdf import PdfWriter
    back_ai = to_ai(paths[0][:-4] + ".pdf", "Ashvena 1953 Visiting Card - Back")
    for handle, s in zip(HANDLES, paths[1:]):
        front_ai = to_ai(s[:-4] + ".pdf", f"Ashvena 1953 Visiting Card - Front (@{handle})")
        merged = PdfWriter()
        merged.append(front_ai)
        merged.append(back_ai)
        merged.add_metadata({"/Title": f"Ashvena 1953 Visiting Card (@{handle})"})
        out = os.path.join(OUT, f"ashvena-visiting-card_print_{handle}.pdf")
        with open(out, "wb") as fh:
            merged.write(fh)
        print("wrote", os.path.basename(out))


def main():
    os.makedirs(OUT, exist_ok=True)
    sides = [("back", back())] + [(f"front_{h}", front(h)) for h in HANDLES]
    paths = []
    for name, src in sides:
        p = os.path.join(OUT, f"ashvena-visiting-card_{name}.svg")
        open(p, "w").write(src)
        paths.append(p)
        print("wrote", os.path.basename(p))
    render(paths)
    package(paths)


if __name__ == "__main__":
    main()
