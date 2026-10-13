#!/usr/bin/env python3
"""Generate the Ashvena society-stall layout sheet (front view + top view).

Writes stall/ashvena-stall-layout.svg and renders a PNG preview next to it.
Requires: pip install playwright (Chromium). Fonts: Cinzel, Montserrat.
"""
import glob
import os

from playwright.sync_api import sync_playwright

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stall")
CHROME = "/opt/pw-browsers/chromium"

W, H = 1640, 1130
MID, MID2 = "#0f1a40", "#1d3a66"
GOLD, IVORY, MAROON = "#c9a24a", "#f1e6cf", "#7a1f1a"
RED, GREEN, WOOD = "#b3301c", "#2f7a3b", "#7a5a22"
SERIF = "Cinzel, 'Times New Roman', serif"
SANS = "Montserrat, Arial, sans-serif"

o = []


def add(s):
    o.append(s)


def text(x, y, s, size=14, fill=MID, anchor="start", weight=500, font=SANS, ls=0):
    add(f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}">{s}</text>')


def badge(x, y, n):
    add(f'<circle cx="{x}" cy="{y}" r="14" fill="{GOLD}" stroke="{MID}" stroke-width="2"/>')
    text(x, y + 5, n, 14, MID, "middle", 700)


def carton(x, y, w, h, col):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="{col}" stroke="{GOLD}" stroke-width="1.5"/>')
    add(f'<ellipse cx="{x + w / 2}" cy="{y + h * 0.45}" rx="{w * 0.28}" ry="{h * 0.2}" fill="{IVORY}" stroke="{GOLD}"/>')
    add(f'<rect x="{x + 4}" y="{y + h - 9}" width="{w - 8}" height="3" fill="{GOLD}"/>')


def peacock(cx, base, flip=1, scale=1.0):
    g = f'translate({cx},{base}) scale({flip * scale},{scale})'
    add(f'<g transform="{g}">')
    add(f'<path d="M-6,0 C-30,40 -34,110 -14,150 C-8,110 -4,60 6,0Z" fill="{GREEN}" stroke="{GOLD}" stroke-width="1"/>')
    for i, (dx, dy) in enumerate([(-18, 70), (-14, 100), (-20, 120), (-12, 135)]):
        add(f'<circle cx="{dx}" cy="{dy}" r="5" fill="#1fa09a" stroke="{GOLD}"/>')
    add(f'<ellipse cx="4" cy="-8" rx="16" ry="12" fill="#1e6fb0"/>')
    add(f'<path d="M8,-12 C18,-30 16,-46 10,-54" stroke="#1e6fb0" stroke-width="9" fill="none" stroke-linecap="round"/>')
    add(f'<circle cx="10" cy="-58" r="6" fill="#1e6fb0"/><path d="M14,-58 l9,2 l-9,3z" fill="{GOLD}"/>')
    add('</g>')


def jaali(x, y, w, h):
    add(f'<defs><pattern id="jaali" width="26" height="26" patternUnits="userSpaceOnUse">'
        f'<path d="M13,2 L24,13 L13,24 L2,13Z" fill="none" stroke="{GOLD}" stroke-opacity=".25"/></pattern></defs>')
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#jaali)"/>')


def dim_h(x1, x2, y, label):
    add(f'<path d="M{x1},{y} H{x2} M{x1},{y - 6} v12 M{x2},{y - 6} v12" stroke="{MAROON}" stroke-width="1.5" fill="none"/>')
    text((x1 + x2) / 2, y - 9, label, 13, MAROON, "middle", 700)


add(f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add(f'<rect width="{W}" height="{H}" fill="#f6efe0"/>')
add(f'<rect x="14" y="14" width="{W - 28}" height="{H - 28}" fill="none" stroke="{GOLD}" stroke-width="2"/>')
text(W / 2, 74, "ASHVENA", 40, MID, "middle", 700, SERIF, 14)
text(W / 2, 108, "SOCIETY STALL LAYOUT  ·  6 ft TABLE  ·  FRONT VIEW + TOP VIEW", 15, MAROON, "middle", 600, SANS, 3)

# ---------------------------------------------------------------- FRONT VIEW
GY = 800  # ground line
text(450, 160, "FRONT VIEW  (what visitors see)", 17, MID, "middle", 700, SANS, 2)
add(f'<line x1="40" y1="{GY}" x2="860" y2="{GY}" stroke="{MID}" stroke-width="2"/>')

# backdrop banner 6 ft x 6.5 ft
bx, by, bw, bh = 235, 335, 420, 455
add(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{MID}" stroke="{GOLD}" stroke-width="3"/>')
jaali(bx, by, bw, bh)
add(f'<path d="M{bx + 60},{by + 330} V{by + 150} C{bx + 60},{by + 80} {bx + 210},{by + 40} {bx + 210},{by + 40} '
    f'C{bx + 210},{by + 40} {bx + 360},{by + 80} {bx + 360},{by + 150} V{by + 330}Z" fill="{MID2}" stroke="{GOLD}" stroke-width="3"/>')
text(bx + 210, by + 36, "ASHVENA", 30, GOLD, "middle", 700, SERIF, 8)
text(bx + 210, by + 56, "EST. 1953", 11, IVORY, "middle", 600, SANS, 4)
text(bx + 210, by + 96, "Roasted · Spiced · Royal", 13, IVORY, "middle", 600, SERIF, 2)
badge(bx + 14, by + 14, "1")

# table + cloth
tx, tw, ty = 235, 420, 615
add(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{GY - ty}" fill="{IVORY}" stroke="{GOLD}" stroke-width="2"/>')
add(f'<rect x="{tx}" y="{GY - 28}" width="{tw}" height="28" fill="{MID}"/>')
add(f'<rect x="{tx - 6}" y="{ty - 6}" width="{tw + 12}" height="10" fill="{WOOD}"/>')
text(tx + 112, ty + 62, "TRY BEFORE YOU BUY", 12, MAROON, "middle", 700, SANS, 2)
text(tx + 112, ty + 82, "free samples", 12, MAROON, "middle", 500, SANS, 1)
badge(tx + 14, ty + 36, "2")

# QR / price card pinned on the cloth
add(f'<rect x="{tx + 258}" y="{ty + 30}" width="92" height="104" rx="4" fill="#fff" stroke="{GOLD}" stroke-width="2"/>')
for r in range(5):
    for c in range(5):
        if (r * 3 + c * 5) % 4 != 1:
            add(f'<rect x="{tx + 274 + c * 12}" y="{ty + 44 + r * 12}" width="10" height="10" fill="{MID}"/>')
text(tx + 304, ty + 122, "SCAN TO ORDER", 9, MAROON, "middle", 700, SANS, 1)
badge(tx + 358, ty + 34, "7")

# product towers (pyramids of cartons on a small riser)
def tower(cx, col):
    add(f'<rect x="{cx - 54}" y="{ty - 22}" width="108" height="22" fill="{WOOD}" stroke="{GOLD}"/>')
    for row, n in enumerate([3, 2, 1]):
        w = 34
        y = ty - 22 - 46 * (row + 1)
        x0 = cx - n * w / 2
        for i in range(n):
            carton(x0 + i * w, y, w - 3, 46, col)


tower(333, RED)
tower(557, GREEN)
text(333, ty - 7, "PERI PERI", 9, IVORY, "middle", 700, SANS, 1)
text(557, ty - 7, "KADI PATTA", 9, IVORY, "middle", 700, SANS, 1)
badge(333, ty - 196, "4")
badge(557, ty - 196, "4")

# hero gift box on riser at centre
add(f'<rect x="405" y="{ty - 50}" width="80" height="50" fill="{WOOD}" stroke="{GOLD}"/>')
add(f'<rect x="404" y="{ty - 134}" width="82" height="82" fill="{MID}" stroke="{GOLD}" stroke-width="3"/>')
add(f'<path d="M418,{ty - 62} V{ty - 100} C418,{ty - 115} 445,{ty - 124} 445,{ty - 124} C445,{ty - 124} 472,{ty - 115} 472,{ty - 100} V{ty - 62}Z" '
    f'fill="{MAROON}" stroke="{GOLD}" stroke-width="2"/>')
text(445, ty - 7, "ROYAL", 9, IVORY, "middle", 700, SANS, 1)
badge(445, ty - 156, "3")

# sample tray (left front corner)
add(f'<rect x="240" y="{ty - 6}" width="42" height="6" fill="{GOLD}"/>')
for i in range(5):
    add(f'<rect x="{243 + i * 8}" y="{ty - 16}" width="6" height="10" fill="#fff" stroke="{MID}" stroke-width=".8"/>')
badge(261, ty - 32, "5")

# vote board (right front corner): tent sign + two jars
add(f'<path d="M614,{ty - 52} h38 l-3,38 h-32Z" fill="#fff" stroke="{MID}" stroke-width="1.5"/>')
text(633, ty - 32, "VOTE!", 10, MAROON, "middle", 700, SANS, 1)
for x, col in [(616, RED), (636, GREEN)]:
    add(f'<rect x="{x}" y="{ty - 28}" width="16" height="24" rx="3" fill="{col}" fill-opacity=".85" stroke="{MID}"/>')
badge(633, ty - 70, "6")

# side standees 2 ft x 6 ft
def standee(x, headline, sub, num):
    add(f'<rect x="{x}" y="{GY - 420}" width="130" height="420" fill="{MID}" stroke="{GOLD}" stroke-width="3"/>')
    jaali(x, GY - 420, 130, 420)
    text(x + 65, GY - 380, "ASHVENA", 17, GOLD, "middle", 700, SERIF, 4)
    peacock(x + 65, GY - 300, 1, 0.8)
    text(x + 65, GY - 170, headline, 15, IVORY, "middle", 700, SERIF, 1)
    text(x + 65, GY - 146, sub, 10, IVORY, "middle", 500, SANS, 1)
    add(f'<rect x="{x + 15}" y="{GY - 112}" width="100" height="30" rx="15" fill="{GOLD}"/>')
    text(x + 65, GY - 92, "ASK ME", 12, MID, "middle", 700, SANS, 2)
    badge(x + 16, GY - 404, num)


standee(55, "FREE SAMPLES", "Peri Peri · Kadi Patta", "8")
standee(705, "FESTIVE DUO", "Pre-order · flat delivery", "8")

dim_h(tx, tx + tw, GY + 36, "6 ft table")
dx = tx + tw + 26
add(f'<path d="M{dx},{ty} V{GY} M{dx - 6},{ty} h12 M{dx - 6},{GY} h12" stroke="{MAROON}" stroke-width="1.5" fill="none"/>')
add(f'<text transform="translate({dx - 8},{(ty + GY) / 2}) rotate(-90)" font-family="{SANS}" font-size="13" font-weight="700" '
    f'fill="{MAROON}" text-anchor="middle">2.5 ft</text>')

# ---------------------------------------------------------------- TOP VIEW
text(1220, 160, "TOP VIEW  (10 × 8 ft pitch)", 17, MID, "middle", 700, SANS, 2)
S = 55  # px per ft
px, py, pw, ph = 930, 190, 10 * S, 8 * S  # stall boundary
add(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="#fbf6ea" stroke="{MID}" stroke-width="2" stroke-dasharray="9 6"/>')
text(px + 8, py - 8, "BACK  (wall / fence)", 11, MID, "start", 600, SANS, 1)

# backdrop 6 ft along the back
add(f'<rect x="{px + 2 * S}" y="{py + 4}" width="{6 * S}" height="8" fill="{MID}" stroke="{GOLD}"/>')
badge(px + 2 * S - 18, py + 8, "1")
# standees flank the table, angled slightly outward
for sx, sy, ang in [(px + 6, py + 70, -14), (px + pw - 2 * S - 6, py + 70, 14)]:
    add(f'<g transform="rotate({ang} {sx + S} {sy})"><rect x="{sx}" y="{sy - 4}" width="{2 * S}" height="8" fill="{MID}" stroke="{GOLD}"/></g>')
badge(px + 30, py + 112, "8")
badge(px + pw - 30, py + 112, "8")

# seller zone + stock boxes
text(px + 5 * S, py + 2.2 * S, "SELLER ZONE (3 ft)", 11, MAROON, "middle", 700, SANS, 2)
add(f'<circle cx="{px + 5 * S}" cy="{py + 2.8 * S}" r="17" fill="{GOLD}" stroke="{MID}" stroke-width="2"/>')
text(px + 5 * S, py + 2.8 * S + 4, "YOU", 11, MID, "middle", 700)
add(f'<circle cx="{px + 6.4 * S}" cy="{py + 2.8 * S}" r="17" fill="#fff" stroke="{MID}" stroke-width="2"/>')
text(px + 6.4 * S, py + 2.8 * S + 4, "HELP", 10, MID, "middle", 700)
add(f'<rect x="{px + 2.2 * S}" y="{py + 22}" width="{1.6 * S}" height="30" fill="#e2c995" stroke="{WOOD}"/>')
text(px + 3 * S, py + 42, "STOCK BOXES", 9, WOOD, "middle", 700, SANS, 1)

# table 6 ft x 2.5 ft
ttx, tty, ttw, tth = px + 2 * S, py + 3.3 * S, 6 * S, 2.5 * S
add(f'<rect x="{ttx}" y="{tty}" width="{ttw}" height="{tth}" fill="{IVORY}" stroke="{WOOD}" stroke-width="3"/>')
badge(ttx - 18, tty + 14, "2")
cy = tty + tth * 0.42
add(f'<rect x="{ttx + 1.1 * S}" y="{cy - 22}" width="{1.3 * S}" height="44" rx="3" fill="{RED}" stroke="{GOLD}"/>')
add(f'<rect x="{ttx + 3.6 * S}" y="{cy - 22}" width="{1.3 * S}" height="44" rx="3" fill="{GREEN}" stroke="{GOLD}"/>')
add(f'<rect x="{ttx + 2.55 * S}" y="{cy - 26}" width="{1.0 * S}" height="52" fill="{MID}" stroke="{GOLD}" stroke-width="2"/>')
text(ttx + 1.75 * S, cy + 4, "PERI", 10, "#fff", "middle", 700)
text(ttx + 4.25 * S, cy + 4, "KADI", 10, "#fff", "middle", 700)
text(ttx + 3.05 * S, cy + 4, "ROYAL", 10, GOLD, "middle", 700)
badge(ttx + 1.75 * S, cy - 36, "4")
badge(ttx + 3.05 * S, cy - 40, "3")
add(f'<rect x="{ttx + 0.12 * S}" y="{tty + tth - 26}" width="{0.9 * S}" height="18" rx="3" fill="#fff" stroke="{GOLD}" stroke-width="2"/>')
badge(ttx + 0.55 * S, tty + tth - 38, "5")
for i, col in enumerate([RED, GREEN]):
    add(f'<circle cx="{ttx + 5.15 * S + i * 22}" cy="{tty + tth - 18}" r="9" fill="{col}" stroke="{MID}"/>')
badge(ttx + 5.5 * S, tty + tth - 38, "6")
add(f'<rect x="{ttx + 2.7 * S}" y="{tty + tth - 4}" width="{0.7 * S}" height="8" fill="#fff" stroke="{GOLD}" stroke-width="2"/>')
badge(ttx + 3.05 * S, tty + tth + 22, "7")

# customer flow
fy = py + ph + 36
add(f'<defs><marker id="arr" markerUnits="userSpaceOnUse" markerWidth="14" markerHeight="14" refX="10" refY="7" orient="auto">'
    f'<path d="M0,0 L14,7 L0,14Z" fill="{MAROON}"/></marker></defs>')
ay = py + ph - 28
add(f'<path d="M{px + 0.6 * S},{fy + 62} L{px + 1.4 * S},{ay} H{px + 8.6 * S} L{px + 9.4 * S},{fy + 62}" '
    f'stroke="{MAROON}" stroke-width="3" fill="none" stroke-dasharray="2 7" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arr)"/>')
text(px + 5 * S, py + ph - 42, "visitors queue at the sides, never in front of the table", 11, MAROON, "middle", 600, SANS)
add(f'<rect x="{px - 4}" y="{fy + 62}" width="{pw + 8}" height="22" fill="#e9dcc0"/>')
text(px + pw / 2, fy + 78, "SOCIETY WALKWAY", 11, WOOD, "middle", 700, SANS, 5)

# ---------------------------------------------------------------- LEGEND
ly = 960
add(f'<line x1="40" y1="{ly - 36}" x2="{W - 40}" y2="{ly - 36}" stroke="{GOLD}" stroke-width="1.5"/>')
legend = [
    ("1", "Backdrop banner", "6 × 6.5 ft, midnight + gold arch art"),
    ("2", "Table, 6 × 2.5 ft", "Ivory cloth, midnight skirt, brand line"),
    ("3", "Hero gift box", "Royal Collection at eye level (4–5 ft)"),
    ("4", "Flavour towers", "Peri Peri left, Kadi Patta right, on risers"),
    ("5", "Sampling tray", "Front corner, covered, with toothpicks"),
    ("6", "Vote board", "Two jars: drop a cashew in your favourite"),
    ("7", "QR + price card", "Scan to order / pre-order via WhatsApp"),
    ("8", "Side standees", "Free samples · Festive duo offer"),
]
for i, (n, t, d) in enumerate(legend):
    col, row = i % 4, i // 4
    x = 60 + col * 395
    y = ly + row * 62
    badge(x, y, n)
    text(x + 26, y - 1, t, 14, MID, "start", 700)
    text(x + 26, y + 17, d, 12, "#4a4a4a", "start", 500)

text(W / 2, H - 38, "Rule of thumb: hero product at eye level · trial packs at hand level · samples at the front corner · price and QR always visible",
     12, MAROON, "middle", 600, SANS, 1)
add("</svg>")


def main():
    os.makedirs(OUT, exist_ok=True)
    svg_path = os.path.join(OUT, "ashvena-stall-layout.svg")
    src = "\n".join(o)
    with open(svg_path, "w") as f:
        f.write(src)
    kw = {}
    exe = glob.glob(CHROME + "*/chrome-linux/chrome")
    if exe:
        kw["executable_path"] = exe[0]
    with sync_playwright() as p:
        b = p.chromium.launch(**kw)
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1.5)
        body = src.split("?>", 1)[1]
        pg.set_content(f"<html><body style='margin:0'>{body}</body></html>", wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.screenshot(path=svg_path[:-4] + ".png", clip={"x": 0, "y": 0, "width": W, "height": H})
        b.close()
    print("wrote", svg_path)


if __name__ == "__main__":
    main()
