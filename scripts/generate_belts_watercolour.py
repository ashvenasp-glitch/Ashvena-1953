#!/usr/bin/env python3
"""Ashvena box belts, v4 "Watercolour" - the house watercolour + gold-ink look.

The artwork is a painted panorama from Magnific (Nano Banana Pro, styled on
the existing Ashvena band art): brass bowl hero, faint arch and palm, palace
garden either side. This script lays the live vector layer over it - logo,
product name, sign-off, candy strip, border bands, veg mark, net weight -
so the type stays editable in Illustrator.

Art goes in packaging/F-palace-garden/art/ashvena-<flavour>-watercolour.png
(4096 x 1032 px, the belt's 3.97:1 ratio, full bleed under the bands).
Until it is there, the art layer shows a labelled placeholder.

Artboard: 297.04 x 74.8 mm (4 px = 1 mm).
Output: packaging/F-palace-garden/ashvena-<flavour>-v4_belt.svg
"""
import os

import generate_belts as gb
from generate_belts import esc, g
from generate_belts_heritage import (BAND, BY, F_SANS, F_SCRIPT, F_SERIF, FLAVOURS, H, SIGNOFF, W, W_MM, H_MM,
                                     logo, strip_band, t, top_band)

ROOT = gb.ROOT
ART_DIR = "art"


def art_layer(key, f):
    rel = f"{ART_DIR}/ashvena-{key}-watercolour.png"
    if os.path.exists(os.path.join(ROOT, rel)):
        return g("Watercolour_Art", f'<image href="{rel}" x="0" y="0" width="{W:.2f}" height="{H:.2f}" '
                                    f'preserveAspectRatio="xMidYMid slice"/>')
    return g("Watercolour_Art_PLACEHOLDER",
             f'<rect width="{W:.2f}" height="{H:.2f}" fill="{f["field"]}"/>'
             f'<rect x="8" y="{BY + 8}" width="{W - 16:.2f}" height="{H - 2 * BY - 16:.2f}" fill="none" '
             f'stroke="{f["ink"]}" stroke-width="1" stroke-dasharray="6 6" opacity=".4"/>'
             + t(150, H - BY - 20, f"WATERCOLOUR ART: place {rel}", 9, f["ink"], F_SANS, 700, "start", ls=1.5))


def title_block(f):
    cx = W / 2
    o = [  # soft cream glow so the type reads on any part of the painting
        f'<radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{f["field"]}" stop-opacity=".92"/>'
        f'<stop offset=".6" stop-color="{f["field"]}" stop-opacity=".7"/><stop offset="1" stop-color="{f["field"]}" stop-opacity="0"/></radialGradient>',
        f'<ellipse cx="{cx:.1f}" cy="{BY + 72}" rx="190" ry="78" fill="url(#glow)"/>',
        logo(cx, BY + 2),
        g("Product_Name", t(cx, BY + 106, f["name"], f["name_size"], f["head"], F_SCRIPT, 400, ls=.4)),
        g("Signoff", t(cx, BY + 122, SIGNOFF, 8.5, f["ink"], F_SERIF, 400, italic=True, ls=.4))]
    return g("Title_Type", "".join(o))


def marks(f):
    x0, x1, y = 22, W - 22, BY + 10
    plaque = f'fill="{f["field"]}" opacity=".85"'
    return (g("Veg_Mark", f'<rect x="{x0 - 4}" y="{y - 4}" width="20" height="20" rx="3" {plaque}/>'
                          f'<rect x="{x0}" y="{y}" width="12" height="12" fill="#fff" stroke="#138a36" stroke-width="1.2"/>'
                          f'<circle cx="{x0 + 6}" cy="{y + 6}" r="3.2" fill="#138a36"/>')
            + g("Net_Wt_PLACEHOLDER", f'<rect x="{x1 - 78}" y="{y - 4}" width="82" height="20" rx="3" {plaque}/>'
                + t(x1 - 2, y + 9.5, "NET WT. XXX g", 7.5, f["ink"], F_SANS, 700, "end", ls=1)))


def belt(key):
    f = FLAVOURS[key]
    gb.CREAM, gb.GOLD = f["cream"], f["gold"]
    o = [art_layer(key, f), title_block(f), marks(f),
         g("Border_Bands", top_band(f) + strip_band(f))]
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_MM}mm" height="{H_MM}mm" viewBox="0 0 {W:.2f} {H:.2f}">\n'
            f'<title>Ashvena {esc(f["name"])} - box belt (watercolour)</title>\n' + "\n".join(o) + "\n</svg>\n")


def main():
    os.makedirs(os.path.join(ROOT, ART_DIR), exist_ok=True)
    for key in FLAVOURS:
        p = os.path.join(ROOT, f"ashvena-{key}-v4_belt.svg")
        open(p, "w").write(belt(key))
        print(os.path.relpath(p, os.path.join(ROOT, "..", "..")))


if __name__ == "__main__":
    main()
