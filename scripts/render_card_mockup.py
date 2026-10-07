#!/usr/bin/env python3
"""Render a styled flat-lay mockup of the thank-you card (back over front), like the reference photo."""
import glob
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packaging", "F-thank-you-card")
CHROME = "/opt/pw-browsers/chromium"

CSS = """
body{margin:0;width:1100px;height:1300px;overflow:hidden;
     background:radial-gradient(circle at 30% 20%,#efe9df,#d9d0c2 70%,#cbc1b1)}
.card{position:absolute;width:900px;height:600px;background-size:cover;border-radius:3px}
.front{left:120px;top:600px;transform:rotate(13deg);
       box-shadow:0 30px 60px rgba(40,20,10,.35),0 6px 14px rgba(40,20,10,.25)}
.back{left:60px;top:120px;transform:rotate(7deg);
      box-shadow:0 34px 70px rgba(40,20,10,.38),0 8px 16px rgba(40,20,10,.22)}
.light{position:absolute;inset:0;pointer-events:none;
       background:linear-gradient(115deg,rgba(255,255,255,.18),transparent 40%,rgba(0,0,0,.08))}
"""


def main():
    img = {s: "file://" + os.path.abspath(os.path.join(ROOT, f"ashvena-thank-you-card_{s}.png")) for s in ("front", "back")}
    html = (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='card front' style=\"background-image:url('{img['front']}')\"></div>"
            f"<div class='card back' style=\"background-image:url('{img['back']}')\"></div>"
            f"<div class='light'></div></body></html>")
    kw = {}
    exe = glob.glob(CHROME + "*/chrome-linux/chrome")
    if exe:
        kw["executable_path"] = exe[0]
    with sync_playwright() as p:
        b = p.chromium.launch(**kw, args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1100, "height": 1300})
        path = os.path.join(ROOT, "_mockup.html")
        open(path, "w").write(html)
        pg.goto("file://" + os.path.abspath(path))
        pg.wait_for_timeout(300)
        pg.screenshot(path=os.path.join(ROOT, "ashvena-thank-you-card_mockup.png"))
        os.remove(path)
        b.close()


if __name__ == "__main__":
    main()
