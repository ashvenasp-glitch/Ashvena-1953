#!/usr/bin/env python3
"""Render PNG previews and print-ready PDFs for every packaging / signage SVG.

Requires: pip install playwright  (uses Chromium) and the Cinzel,
Cormorant Garamond and Montserrat fonts installed locally.

Usage:  python3 scripts/render_previews.py            # packaging + signage
        python3 scripts/render_previews.py signage    # only these folders
"""
import glob
import math
import os
import re
import sys

from playwright.sync_api import sync_playwright

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CHROME = "/opt/pw-browsers/chromium"


def main():
    roots = sys.argv[1:] or ["packaging", "signage"]
    svgs = sorted(s for r in roots for s in glob.glob(os.path.join(BASE, r, "*", "*.svg")))
    kw = {}
    exe = glob.glob(CHROME + "*/chrome-linux/chrome")
    if exe:
        kw["executable_path"] = exe[0]
    with sync_playwright() as p:
        b = p.chromium.launch(**kw)
        for s in svgs:
            src = open(s).read()
            wmm, hmm = map(float, re.search(r'width="([\d.]+)mm" height="([\d.]+)mm"', src).groups())
            w, h = wmm * 4, hmm * 4
            pg = b.new_page(viewport={"width": math.ceil(w), "height": math.ceil(h)}, device_scale_factor=2)
            body = src.split("?>", 1)[1].replace("<svg ", "<svg style='display:block' ", 1)
            px = re.sub(r'width="[^"]+mm" height="[^"]+mm"', f'width="{w}" height="{h}"', body, count=1)
            pg.set_content(f"<html><body style='margin:0'>{px}</body></html>", wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.screenshot(path=s[:-4] + ".png", clip={"x": 0, "y": 0, "width": w, "height": h})
            pg.set_content(f"<html><body style='margin:0'>{body}</body></html>", wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.pdf(path=s[:-4] + ".pdf", width=f"{wmm}mm", height=f"{hmm}mm",
                   print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            pg.close()
            print("rendered", os.path.relpath(s, BASE))
        b.close()


if __name__ == "__main__":
    main()
