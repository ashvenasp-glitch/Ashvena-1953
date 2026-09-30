#!/usr/bin/env python3
"""Ashvena "Royal Cashew Collection" festive gift-box lid - Direction E.

Ornamental Indian vector artwork: jaali lattice, lotus-petal border,
corner mandala rosettes, a cusped Mughal jharokha arch, twin peacocks
(Peri Peri + Kadi Patta) and a brass urn heaped with cashews.

Artboard: 250 x 250 mm lid top (4 px = 1 mm), two colourways.
Output: packaging/E-royal-collection/ashvena-royal-collection_lid-<colourway>.svg
"""
import math
import os

from generate_packaging import DEFS, bowl_scene, esc
from generate_wrap_labels import peacock

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packaging", "E-royal-collection")
S = 1000
C = S / 2

F_DISPLAY = "Cinzel, 'Trajan Pro', serif"
F_SERIF = "'Cormorant Garamond', Garamond, Georgia, serif"
F_SANS = "Montserrat, Helvetica, Arial, sans-serif"

COLOURWAYS = {
    "midnight": dict(bg="#0f1a33", bg2="#16264a", arch0="#1d4a5c", arch1="#0a1f33",
                     lattice_op=.14, sub="#e9dcc0", ink="#e9dcc0"),
    "ivory": dict(bg="#f3ead8", bg2="#e8dcc2", arch0="#7a1f2b", arch1="#3f0c15",
                  lattice_op=.22, sub="#5a1420", ink="#3a2a1c"),
}

PETAL = "M 0,0 C -8,-6 -7,-16 0,-24 C 7,-16 8,-6 0,0 Z"


def text(x, y, s, size, fill, family=F_SANS, weight=400, ls=0, italic=False):
    it = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="middle" letter-spacing="{ls}"{it}>{esc(s)}</text>')


def g(gid, body, extra=""):
    return f'<g id="{gid}"{extra}>\n{body}\n</g>'


def lattice(x0, y0, x1, y1, step, op):
    """Jaali: eight-point stars with connecting diamonds."""
    o = []
    y, row = y0, 0
    while y <= y1:
        x = x0 + (step / 2 if row % 2 else 0)
        while x <= x1:
            r, r2 = step * .32, step * .14
            pts = []
            for k in range(16):
                rr = r if k % 2 == 0 else r2
                a = math.pi / 8 * k
                pts.append(f"{x + rr * math.cos(a):.1f},{y + rr * math.sin(a):.1f}")
            o.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="url(#gold)" stroke-width="1"/>')
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{step * .06:.1f}" fill="url(#gold)"/>')
            x += step
        y += step / 2
        row += 1
    return f'<g opacity="{op}">{"".join(o)}</g>'


def rosette(cx, cy, r, rings=3, fill="url(#gold)", op=1):
    o = [f'<g transform="translate({cx} {cy})" opacity="{op}">']
    for i in range(rings, 0, -1):
        n = 8 * (i + 1)
        sc = r / 24 * i / rings
        for k in range(n):
            o.append(f'<path d="{PETAL}" transform="rotate({360 / n * k + (i % 2) * 180 / n:.2f}) scale({sc:.3f})" '
                     f'fill="{fill}" stroke="#7a5a22" stroke-width="{.6 / sc:.2f}" opacity="{.55 + .15 * (rings - i)}"/>')
    o.append(f'<circle r="{r * .16:.1f}" fill="{fill}" stroke="#7a5a22" stroke-width=".8"/>')
    o.append(f'<circle r="{r * .07:.1f}" fill="#b3301c"/>')
    o.append("</g>")
    return "".join(o)


def petal_border(inset, spacing, scale):
    o = []
    L0, L1 = inset + 40, S - inset - 40
    n = int((L1 - L0) / spacing)
    for side in range(4):
        for i in range(n + 1):
            p = L0 + (L1 - L0) * i / n
            if side == 0:
                x, y, r = p, inset, 180
            elif side == 1:
                x, y, r = S - inset, p, 270
            elif side == 2:
                x, y, r = p, S - inset, 0
            else:
                x, y, r = inset, p, 90
            o.append(f'<path d="{PETAL}" transform="translate({x:.1f} {y:.1f}) rotate({r}) scale({scale})" '
                     f'fill="url(#gold)" opacity=".9"/>')
    return "".join(o)


def arch_points(cx, top, w, spring, n):
    """Points along an ogee arch from left spring to right spring."""
    L, R = cx - w / 2, cx + w / 2
    segs = [((L, spring), (L, spring - 150), (cx - 60, top + 70), (cx, top)),
            ((cx, top), (cx + 60, top + 70), (R, spring - 150), (R, spring))]
    pts = []
    for p0, p1, p2, p3 in segs:
        for i in range(n):
            u = i / n
            a = [(1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u ** 2, u ** 3]
            pts.append((sum(c * p[0] for c, p in zip(a, (p0, p1, p2, p3))),
                        sum(c * p[1] for c, p in zip(a, (p0, p1, p2, p3)))))
    pts.append((R, spring))
    return pts


def arch_path(cx, top, w, spring, base, cusped=False):
    pts = arch_points(cx, top, w, spring, 6 if cusped else 30)
    d = f"M {cx - w / 2:.1f},{base} L {pts[0][0]:.1f},{pts[0][1]:.1f}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if cusped:
            r = math.hypot(x1 - x0, y1 - y0) * .55
            d += f" A {r:.1f} {r:.1f} 0 0 0 {x1:.1f},{y1:.1f}"
        else:
            d += f" L {x1:.1f},{y1:.1f}"
    return d + f" L {cx + w / 2:.1f},{base} Z"


def lid(cw_key):
    cw = COLOURWAYS[cw_key]
    extra_defs = (f'<linearGradient id="archFill" x1="0" y1="0" x2="0" y2="1">'
                  f'<stop offset="0" stop-color="{cw["arch0"]}"/><stop offset="1" stop-color="{cw["arch1"]}"/></linearGradient>'
                  f'<radialGradient id="lidBg" cx=".5" cy=".45" r=".75">'
                  f'<stop offset="0" stop-color="{cw["bg2"]}"/><stop offset="1" stop-color="{cw["bg"]}"/></radialGradient>'
                  f'<clipPath id="lidClip"><rect x="60" y="60" width="{S - 120}" height="{S - 120}"/></clipPath>')
    o = [g("Background", f'<rect width="{S}" height="{S}" fill="url(#lidBg)"/>')]
    o.append(g("Jaali_Lattice", f'<g clip-path="url(#lidClip)">{lattice(60, 60, S - 60, S - 60, 56, cw["lattice_op"])}</g>'))

    # frame
    fr = [f'<rect x="22" y="22" width="{S - 44}" height="{S - 44}" fill="none" stroke="url(#gold)" stroke-width="3"/>',
          f'<rect x="30" y="30" width="{S - 60}" height="{S - 60}" fill="none" stroke="url(#gold)" stroke-width="1"/>',
          f'<rect x="58" y="58" width="{S - 116}" height="{S - 116}" fill="none" stroke="url(#gold)" stroke-width="1.2"/>',
          petal_border(44, 22, .5)]
    for x, y in [(44, 44), (S - 44, 44), (44, S - 44), (S - 44, S - 44)]:
        fr.append(f'<circle cx="{x}" cy="{y}" r="30" fill="{cw["bg"]}"/>')
        fr.append(rosette(x, y, 30, 2))
    o.append(g("Border", "".join(fr)))

    # brand
    o.append(g("Brand",
               text(C, 132, "ASHVENA", 58, "url(#gold)", F_DISPLAY, 600, 16)
               + f'<line x1="{C - 170}" y1="152" x2="{C - 62}" y2="152" stroke="url(#gold)" stroke-width="1"/>'
               + f'<line x1="{C + 62}" y1="152" x2="{C + 170}" y2="152" stroke="url(#gold)" stroke-width="1"/>'
               + text(C, 157, "EST. 1953", 13, cw["sub"], F_SANS, 600, 5)))

    # arch
    cx, top, w, spring, base = C, 238, 560, 440, 800
    ar = [rosette(cx, top + 20, 80, 3, op=.3),
          f'<path d="{arch_path(cx, top - 16, w + 44, spring, base + 12)}" fill="none" stroke="url(#gold)" stroke-width="2"/>',
          f'<path d="{arch_path(cx, top, w, spring, base)}" fill="url(#gold)"/>',
          f'<path d="{arch_path(cx, top + 14, w - 28, spring, base)}" fill="url(#archFill)"/>',
          f'<path d="{arch_path(cx, top + 30, w - 60, spring + 4, base, cusped=True)}" fill="none" '
          f'stroke="url(#gold)" stroke-width="2.2" stroke-linejoin="round"/>']
    # finial
    ar.append(f'<path d="M {cx},{top - 70} C {cx + 10},{top - 50} {cx + 12},{top - 36} {cx},{top - 22} '
              f'C {cx - 12},{top - 36} {cx - 10},{top - 50} {cx},{top - 70} Z" fill="url(#gold)"/>')
    ar.append(f'<circle cx="{cx}" cy="{top - 78}" r="5" fill="url(#gold)"/>')
    # pillars
    for px in (cx - w / 2 - 22, cx + w / 2 + 22):
        ar.append(f'<rect x="{px - 9}" y="{spring - 40}" width="18" height="{base - spring + 52}" fill="url(#gold)"/>')
        ar.append(f'<rect x="{px - 15}" y="{spring - 52}" width="30" height="12" rx="3" fill="url(#gold)"/>')
        ar.append(f'<rect x="{px - 15}" y="{base}" width="30" height="12" rx="3" fill="url(#gold)"/>')
        for k in range(6):
            yy = spring - 20 + k * 60
            ar.append(f'<path d="M {px},{yy} l 5,8 l -5,8 l -5,-8 Z" fill="{cw["bg"]}" opacity=".6"/>')
    # hanging bead garland under the arch crown
    pts = arch_points(cx, top + 42, w - 90, spring + 8, 6)
    for x, y in pts[2:-2]:
        ar.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y + 26:.1f}" stroke="url(#gold)" stroke-width="1"/>')
        ar.append(f'<circle cx="{x:.1f}" cy="{y + 30:.1f}" r="4" fill="url(#gold)"/>')
        ar.append(f'<path d="M {x:.1f},{y + 34:.1f} l 3,6 l -3,6 l -3,-6 Z" fill="#b3301c"/>')
    o.append(g("Jharokha_Arch", "\n".join(ar)))

    # scene inside arch
    sc = [f'<clipPath id="archClip"><path d="{arch_path(cx, top + 14, w - 28, spring, base)}"/></clipPath>',
          '<g clip-path="url(#archClip)">',
          rosette(cx, 470, 150, 3, op=.18),
          peacock("peri", cx - 150, 520, .6).replace('id="Peacock_Mascot"', 'id="Peacock_PeriPeri"'),
          f'<g transform="translate({2 * (cx + 150)} 0) scale(-1 1)">'
          + peacock("kadi", cx + 150, 520, .6).replace('id="Peacock_Mascot"', 'id="Peacock_KadiPatta"') + "</g>",
          # urn pedestal
          f'<path d="M {cx - 40},{782} L {cx + 40},{782} L {cx + 26},{752} L {cx - 26},{752} Z" fill="url(#gold)"/>',
          f'<rect x="{cx - 60}" y="782" width="120" height="14" rx="4" fill="url(#gold)"/>',
          f'<rect x="{cx - 18}" y="728" width="36" height="26" fill="url(#gold)"/>',
          bowl_scene({"style": "plain"}, cx, 668, 9),
          # lotus base
          "".join(f'<path d="{PETAL}" transform="translate({cx + dx} 800) rotate({rot}) scale({s})" '
                  f'fill="#e9a3a8" stroke="#8a2f3a" stroke-width="1.5"/>'
                  for dx, rot, s in [(-120, -60, 1.3), (-95, -35, 1.5), (-70, -12, 1.7),
                                     (120, 60, 1.3), (95, 35, 1.5), (70, 12, 1.7)]),
          "</g>"]
    o.append(g("Arch_Scene", "\n".join(sc)))

    # title
    o.append(g("Title",
               text(C, 858, "The Royal Cashew Collection", 40, "url(#gold)", F_SERIF, 600, italic=True)
               + text(C, 890, "PERI PERI  ·  KADI PATTA  ·  CLASSIC ROASTED", 12, cw["sub"], F_SANS, 600, 4)
               + f'<path d="M {C - 90},910 L {C - 12},910 M {C + 12},910 L {C + 90},910" stroke="url(#gold)" stroke-width="1"/>'
               + f'<path d="M {C},904 l 6,6 l -6,6 l -6,-6 Z" fill="url(#gold)"/>'
               + text(C, 935, "FESTIVE EDITION  ·  3 × 200 g", 10, cw["sub"], F_SANS, 600, 3)))

    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{S / 4:.0f}mm" height="{S / 4:.0f}mm" viewBox="0 0 {S} {S}">\n'
            f'<title>Ashvena Royal Cashew Collection - lid ({cw_key})</title>\n'
            f'<defs>{DEFS}{extra_defs}</defs>\n' + "\n".join(o) + "\n</svg>\n")


def main():
    os.makedirs(ROOT, exist_ok=True)
    for k in COLOURWAYS:
        p = os.path.join(ROOT, f"ashvena-royal-collection_lid-{k}.svg")
        open(p, "w").write(lid(k))
        print(os.path.relpath(p, os.path.join(ROOT, "..", "..")))


if __name__ == "__main__":
    main()
