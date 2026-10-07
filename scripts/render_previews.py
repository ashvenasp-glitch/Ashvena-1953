#!/usr/bin/env python3
"""Render PNG previews and print-ready PDFs for every packaging SVG.

Usage: python3 scripts/render_previews.py [FOLDER ...]  (default: all folders)

Requires: pip install playwright  (uses Chromium) and the Cinzel,
Cormorant Garamond and Montserrat fonts installed locally.
"""
import glob
import os
import re
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packaging")
CHROME = "/opt/pw-browsers/chromium"


def main():
    dirs = sys.argv[1:] or ["*"]  # optional: only these direction folders
    svgs = sorted(f for d in dirs for f in glob.glob(os.path.join(ROOT, d, "*.svg")))
    kw = {}
    exe = glob.glob(CHROME + "*/chrome-linux/chrome")
    if exe:
        kw["executable_path"] = exe[0]
    with sync_playwright() as p:
        b = p.chromium.launch(**kw)
        for s in svgs:
            src = open(s).read()
            w, h = map(float, re.search(r'viewBox="0 0 (\S+) (\S+)"', src).groups())
            pg = b.new_page(viewport={"width": int(w), "height": int(h)}, device_scale_factor=2)
            body = src.split("?>", 1)[1].replace("<svg ", "<svg style='display:block' ", 1)
            px = re.sub(r'width="[^"]+mm" height="[^"]+mm"', f'width="{w}" height="{h}"', body, 1)
            pg.set_content(f"<html><body style='margin:0'>{px}</body></html>", wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.screenshot(path=s[:-4] + ".png", clip={"x": 0, "y": 0, "width": w, "height": h})
            pg.set_content(f"<html><body style='margin:0'>{body}</body></html>", wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.pdf(path=s[:-4] + ".pdf", width=f"{w / 4}mm", height=f"{h / 4}mm",
                   print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            pg.close()
            print("rendered", os.path.relpath(s, ROOT))
        b.close()


if __name__ == "__main__":
    main()
