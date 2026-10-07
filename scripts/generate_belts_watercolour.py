#!/usr/bin/env python3
"""Ashvena box belts, v4 "Watercolour" - the house watercolour + gold-ink look.

The artwork is a painted panorama from Magnific (Nano Banana Pro, styled on
the existing Ashvena band art): brass bowl hero, faint arch and palm, palace
garden either side. This script lays the live vector layer over it - logo,
product name, sign-off, candy strip, border bands, veg mark, net weight -
so the type stays editable in Illustrator.

Art goes in packaging/F-palace-garden/art/ashvena-<flavour>-watercolour.png
(3.97:1, full bleed under the bands; 4096 x 1032 px for print).
Until it is there, the art layer shows a labelled placeholder.

Artboard: 297.04 x 74.8 mm (4 px = 1 mm).
Output: packaging/F-palace-garden/ashvena-<flavour>-v4_belt.svg
"""
import os

import generate_belts as gb
from generate_belts import esc, g
from generate_belts_heritage import (BAND, BY, F_DEVA, F_SANS, F_SCRIPT, F_SERIF, FLAVOURS, H, LOGO_DARK, LOGO_RED,
                                     SIGNOFF, W, W_MM, H_MM, strip_band, t, top_band)

WC_NAME_SIZE = {"aam-papad": 36, "fruit-cocktail": 30}   # fits the clear space above the bowl

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
    """Logo, name and sign-off in the clear space above the bowl (about 54 mm wide)."""
    cx = W / 2
    o = [  # soft glow over the faint arch and palm so the type reads cleanly
        f'<radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{f["field"]}" stop-opacity=".9"/>'
        f'<stop offset=".65" stop-color="{f["field"]}" stop-opacity=".6"/><stop offset="1" stop-color="{f["field"]}" stop-opacity="0"/></radialGradient>',
        f'<ellipse cx="{cx:.1f}" cy="{BY + 66}" rx="122" ry="72" fill="url(#glow)"/>',
        g("Logo_PLACEHOLDER_replace_with_Ashvena_logo_final",
          t(cx, BY + 23, "अ", 22, LOGO_RED, F_DEVA, 400)
          + t(cx, BY + 39, "Ashvena", 15.5, LOGO_DARK, F_SERIF, 600, ls=.5)
          + t(cx, BY + 47.5, "1953", 6.5, LOGO_RED, F_SANS, 700, ls=2)),
        g("Product_Name", t(cx, BY + 84, f["name"], f["wc_name_size"], f["head"], F_SCRIPT, 400, ls=.3)),
        g("Signoff", t(cx, BY + 99, SIGNOFF, 7, f["ink"], F_SERIF, 400, italic=True, ls=.3))]
    return g("Title_Type", "".join(o))


def marks(f):
    """Veg mark and net weight as one small row under the sign-off, on the front face."""
    cx, y = W / 2, BY + 106
    return (g("Veg_Mark", f'<rect x="{cx - 38}" y="{y}" width="9" height="9" fill="#fff" stroke="#138a36" stroke-width="1"/>'
                          f'<circle cx="{cx - 33.5}" cy="{y + 4.5}" r="2.4" fill="#138a36"/>')
            + g("Net_Wt_PLACEHOLDER", t(cx - 25, y + 7.2, "NET WT. XXX g", 6.5, f["ink"], F_SANS, 700, "start", ls=.8)))


def belt(key):
    f = dict(FLAVOURS[key], wc_name_size=WC_NAME_SIZE[key])
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
