#!/usr/bin/env python3
"""Render presentation boards: the stall cards in clear acrylic T-stands.

Reads the PNG previews (run render_previews.py signage first), trims the 3 mm
bleed and writes one board per entry in BOARDS to signage/stall-standees/.
"""
import base64
import glob
import io
import os

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "signage", "stall-standees")
CHROME = "/opt/pw-browsers/chromium"
BOARDS = {
    "ashvena-standees-board": (["ashvena-standee_real-fruit-candies", "ashvena-standee_masalas-dry-fruits"],
                               "REAL FRUIT CANDIES · MASALAS &amp; DRY FRUITS"),
    "ashvena-display-cards-board": (["ashvena-display_red-no-shortcuts", "ashvena-display_blue-house-rule"],
                                    "DISPLAY MESSAGES · ASHVENA RED · LID BLUE"),
}
BLEED_PX = 3 * 8                          # previews are 8 px per mm

CSS = """
body{margin:0;width:1500px;background:#f3ecdc;font-family:'Bricolage Grotesque',sans-serif;color:#35070F}
.wall{height:640px;background:linear-gradient(#f8f3e7,#efe5d0)}
.table{height:330px;background:linear-gradient(#d9c7a6,#c9b28b);box-shadow:inset 0 14px 22px -12px rgba(60,30,10,.35)}
h1{position:absolute;top:34px;width:100%;text-align:center;margin:0;font:italic 400 40px Fraunces,serif}
p.sub{position:absolute;top:92px;width:100%;text-align:center;margin:0;font-size:12px;letter-spacing:4px;color:#4B403B}
.stage{position:absolute;top:150px;left:0;right:0;display:flex;justify-content:center;gap:150px;perspective:1800px}
.stand{position:relative;width:440px;transform-style:preserve-3d}
.stand.l{transform:rotateY(9deg)} .stand.r{transform:rotateY(-9deg)}
.card{display:block;width:440px;height:660px;box-shadow:0 2px 3px rgba(0,0,0,.15)}
.acrylic{position:absolute;left:-9px;right:-9px;top:-9px;height:678px;border:1px solid rgba(255,255,255,.85);
  border-radius:3px;background:linear-gradient(112deg,rgba(255,255,255,.42) 0%,rgba(255,255,255,0) 20%,
  rgba(255,255,255,0) 63%,rgba(255,255,255,.2) 72%,rgba(255,255,255,0) 80%);
  box-shadow:inset 0 0 0 1px rgba(170,190,200,.35),0 26px 40px -24px rgba(40,20,5,.55)}
.lip{position:absolute;left:-16px;right:-16px;top:640px;height:32px;border-radius:2px;
  background:linear-gradient(rgba(255,255,255,.55),rgba(215,228,232,.38));border:1px solid rgba(255,255,255,.9);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.9)}
.base{position:absolute;left:-30px;right:-30px;top:670px;height:26px;border-radius:3px;
  background:linear-gradient(rgba(235,242,244,.75),rgba(190,205,210,.55));border:1px solid rgba(255,255,255,.8)}
.shadow{position:absolute;left:-10px;right:-10px;top:690px;height:30px;border-radius:50%;
  background:radial-gradient(rgba(60,30,10,.35),transparent 70%)}
"""


def card_uri(name):
    im = Image.open(os.path.join(ROOT, name + ".png")).convert("RGB")
    im = im.crop((BLEED_PX, BLEED_PX, im.width - BLEED_PX, im.height - BLEED_PX))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def board_html(cards, sub):
    stands = "".join(f'<div class="stand {side}"><div class="shadow"></div><div class="base"></div>'
                     f'<img class="card" src="{card_uri(n)}"><div class="acrylic"></div><div class="lip"></div></div>'
                     for n, side in zip(cards, ["l", "r"]))
    return (f"<html><head><style>{CSS}</style></head><body><div class='wall'></div><div class='table'></div>"
            f"<h1>Ashvena 1953 · Stall standees</h1>"
            f"<p class='sub'>6 × 9 IN ACRYLIC T-STAND · {sub}</p>"
            f"<div class='stage'>{stands}</div></body></html>")


def main():
    kw = {}
    exe = glob.glob(CHROME + "*/chrome-linux/chrome")
    if exe:
        kw["executable_path"] = exe[0]
    with sync_playwright() as p:
        b = p.chromium.launch(**kw)
        pg = b.new_page(viewport={"width": 1500, "height": 970}, device_scale_factor=1.5)
        for name, (cards, sub) in BOARDS.items():
            pg.set_content(board_html(cards, sub), wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(200)
            out = os.path.join(ROOT, name + ".png")
            pg.screenshot(path=out, full_page=True)
            print(os.path.relpath(out, os.path.join(ROOT, "..", "..")))
        b.close()


if __name__ == "__main__":
    main()
