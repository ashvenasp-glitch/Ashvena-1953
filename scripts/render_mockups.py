#!/usr/bin/env python3
"""Render a presentation board of 3D carton mockups from the flat PNG previews."""
import glob
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packaging")
CHROME = "/opt/pw-browsers/chromium"

DIRS = [("A-heritage-ivory", "A · Heritage Ivory", "#efe6d4"),
        ("B-noir-royale", "B · Noir Royale", "#d9d2c5"),
        ("C-spice-coast", "C · Spice Coast", "#e4efe9")]
FLAVS = ["peri-peri", "kadi-patta"]

# carton face sizes in px: front 240 x 340, side 90 x 340 (image is 660 x 680 px -> scale .5)
CSS = """
body{margin:0;font-family:Montserrat,sans-serif;background:#f6f1e7;color:#3a2a1c}
h1{font-family:Cinzel,serif;font-weight:600;letter-spacing:8px;text-align:center;margin:36px 0 4px;font-size:34px}
p.sub{text-align:center;margin:0 0 28px;letter-spacing:3px;font-size:12px;color:#8a765a}
.row{display:flex;align-items:center;margin:0 40px 28px;border-radius:18px;padding:28px 30px}
.label{width:190px;font-family:Cinzel,serif;font-size:20px;letter-spacing:2px}
.stage{flex:1;display:flex;justify-content:space-around;perspective:1400px}
.box{position:relative;width:240px;height:340px;transform-style:preserve-3d;transform:rotateY(28deg) rotateX(-4deg)}
.face{position:absolute;top:0;height:340px;background-size:330px 340px;backface-visibility:hidden}
.front{left:0;width:240px;background-position:-90px 0;transform:translateZ(45px)}
.side{left:75px;width:90px;background-position:0 0;transform:rotateY(-90deg) translateZ(120px);filter:brightness(.82)}
.shadow{position:absolute;left:-30px;right:-10px;bottom:-26px;height:30px;border-radius:50%;
        background:radial-gradient(rgba(0,0,0,.35),transparent 70%);transform:translateZ(-60px) rotateX(90deg)}
.back img{height:340px;box-shadow:0 12px 30px rgba(0,0,0,.25)}
"""


def main():
    rows = []
    for d, label, bg in DIRS:
        boxes = []
        for fl in FLAVS:
            img = os.path.abspath(os.path.join(ROOT, d, f"ashvena-{fl}-cashews_front-side.png"))
            boxes.append(f'<div class="box"><div class="shadow"></div>'
                         f'<div class="face side" style="background-image:url(file://{img})"></div>'
                         f'<div class="face front" style="background-image:url(file://{img})"></div></div>')
        backs = sorted(glob.glob(os.path.join(ROOT, d, "*_back.png")))
        if backs:
            boxes.append(f'<div class="back"><img src="file://{os.path.abspath(backs[0])}"></div>')
        rows.append(f'<div class="row" style="background:{bg}"><div class="label">{label}</div>'
                    f'<div class="stage">{"".join(boxes)}</div></div>')
    html = (f"<html><head><style>{CSS}</style></head><body><h1>ASHVENA</h1>"
            f"<p class='sub'>PERI PERI &amp; KADI PATTA CASHEWS · PACKAGING DIRECTIONS</p>"
            f"{''.join(rows)}</body></html>")
    kw = {}
    exe = glob.glob(CHROME + "*/chrome-linux/chrome")
    if exe:
        kw["executable_path"] = exe[0]
    with sync_playwright() as p:
        b = p.chromium.launch(**kw, args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1400, "height": 800}, device_scale_factor=1.5)
        path = os.path.join(ROOT, "_board.html")
        open(path, "w").write(html)
        pg.goto("file://" + os.path.abspath(path))
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        pg.screenshot(path=os.path.join(ROOT, "ashvena-cashew-packaging-board.png"), full_page=True)
        os.remove(path)
        b.close()


if __name__ == "__main__":
    main()
