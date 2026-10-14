#!/usr/bin/env python3
"""Pull the approved Ashvena artwork and logo out of the brand guidelines PDF.

The standees reuse the finished pack illustrations (watercolour + gold ink,
Brand & Packaging Guidelines 2026, p. 8 and p. 19) instead of new art. The
PDF only holds the printed fronts, so each scene is cropped clear of the
baked-in type, any stray glyphs are painted out with the wall colour, and the
crop edges are faded into the standee wall in software (guidelines p. 11:
"extend the wall in software", never AI expand). Bowls and figures are never
cropped.

Writes:
  signage/brand/ashvena-logo-stacked.svg     vector stacked logo (p. 4)
  signage/stall-standees/art/*.jpg|png       cropped scenes and candy lids

Usage:  python3 scripts/prepare_standee_art.py <Ashvena-Brand-Packaging-Guidelines-2026.pdf>
Needs:  poppler-utils (pdfimages, pdftocairo) and Pillow.
"""
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFilter

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ART = os.path.join(BASE, "signage", "stall-standees", "art")
BRAND = os.path.join(BASE, "signage", "brand")

WALL_CANDY = (0xe0, 0xef, 0xe1)     # Khatti-Meethi wall as printed (#DCE9E1 in the book)
WALL_PANTRY = (0xf9, 0xf3, 0xe1)    # warm cream between the chai, chaat and Papa walls

# name: (page, image index, crop box, painted-out boxes + plain-wall sample box (crop px),
#        fades l/t/r/b in source px, wall the edges fade into)
SCENES = {
    "dadi-family-scene": (8, 5, (4, 438, 945, 818), ([], None), (40, 70, 30, 18), WALL_CANDY),
    "cutting-chai-bowl": (8, 3, (2, 196, 594, 550), ([(80, 0, 385, 44)], (130, 56, 250, 80)),
                          (70, 60, 60, 30), WALL_PANTRY),
    "chatpata-chaat-bowl": (8, 4, (2, 196, 594, 550), ([(180, 0, 225, 12), (226, 12, 372, 46)], (190, 50, 300, 72)),
                            (70, 40, 60, 30), WALL_PANTRY),
    "papa-family-scene": (8, 6, (455, 112, 1013, 537), ([], None), (60, 56, 22, 10), WALL_PANTRY),
}
LIDS = {"lid-khatti-meethi": (19, 0), "lid-amla": (19, 2), "lid-carrot": (19, 3)}


def extract(pdf, page, tmp):
    prefix = os.path.join(tmp, f"p{page}")
    if not os.path.exists(prefix + "-000.png"):
        subprocess.run(["pdfimages", "-f", str(page), "-l", str(page), "-png", pdf, prefix], check=True)
    return prefix


def fade_mask(size, l, t, r, b):
    """White where the art stays, ramping to black over the given edge widths."""
    w, h = size
    m = Image.new("L", size, 255)
    px = m.load()
    for y in range(h):
        fy = min(1, y / t if t else 1, (h - 1 - y) / b if b else 1)
        for x in range(w):
            fx = min(1, x / l if l else 1, (w - 1 - x) / r if r else 1)
            f = max(0.0, min(fx, fy))
            px[x, y] = int(255 * f * f * (3 - 2 * f))
    return m


def paint_out(im, boxes, wall_from):
    """Cover leftover glyph fragments with the local wall colour, feathered."""
    if not boxes:
        return im
    m = Image.new("L", im.size, 0)
    d = ImageDraw.Draw(m)
    for box in boxes:
        d.rectangle(box, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(4))
    patch = Image.new("RGB", im.size, im.crop(wall_from).resize((1, 1), Image.Resampling.BOX).getpixel((0, 0)))
    return Image.composite(patch, im, m)


def scene(pdf, tmp, name, spec):
    page, idx, box, wipes, fades, wall = spec
    src = Image.open(f"{extract(pdf, page, tmp)}-{idx:03d}.png").convert("RGB").crop(box)
    src = paint_out(src, *wipes)
    big = src.resize((src.width * 2, src.height * 2), Image.Resampling.LANCZOS)
    big = big.filter(ImageFilter.UnsharpMask(radius=1.4, percent=35, threshold=2))
    mask = fade_mask(src.size, *fades).resize(big.size, Image.Resampling.BILINEAR)
    out = Image.composite(big, Image.new("RGB", big.size, wall), mask)
    path = os.path.join(ART, name + ".jpg")
    out.save(path, quality=90, optimize=True)
    return path


def lid(pdf, tmp, name, spec):
    page, idx = spec
    im = Image.open(f"{extract(pdf, page, tmp)}-{idx:03d}.png").convert("RGB")
    s = 4 * im.width
    m = Image.new("L", (s, s), 0)
    ImageDraw.Draw(m).ellipse((6, 6, s - 7, s - 7), fill=255)
    m = m.resize(im.size, Image.Resampling.LANCZOS)
    im.putalpha(m)
    im = im.resize((360, 360), Image.Resampling.LANCZOS)
    path = os.path.join(ART, name + ".png")
    im.save(path, optimize=True)
    return path


def logo(pdf, tmp):
    svg = os.path.join(tmp, "p4.svg")
    subprocess.run(["pdftocairo", "-svg", "-f", "4", "-l", "4", pdf, svg], check=True)
    body = open(svg).read().split("</defs>", 1)[1]
    paths = [p for p in re.findall(r'<path[^>]*>', body) if len(re.search(r' d="([^"]*)"', p).group(1)) > 2000]
    mark, word, year = [re.search(r' d="([^"]*)"', p).group(1) for p in paths[:3]]
    # bounding box measured from the page-4 master (pt): mark + word + year, proportions 67 / 16 / 9 %
    vb = "122.39 149.82 155.64 174.79"
    out = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="55mm" height="61.7mm">\n'
           f'<title>Ashvena 1953 - stacked logo</title>\n'
           f'<g id="Mark" fill="#941528"><path d="{mark}"/></g>\n'
           f'<g id="Word" fill="#35070F"><path d="{word}"/></g>\n'
           f'<g id="Year" fill="#941528"><path d="{year}"/></g>\n</svg>\n')
    path = os.path.join(BRAND, "ashvena-logo-stacked.svg")
    open(path, "w").write(out)
    return path


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    pdf = sys.argv[1]
    os.makedirs(ART, exist_ok=True)
    os.makedirs(BRAND, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        written = [logo(pdf, tmp)]
        written += [scene(pdf, tmp, k, v) for k, v in SCENES.items()]
        written += [lid(pdf, tmp, k, v) for k, v in LIDS.items()]
    for p in written:
        print(os.path.relpath(p, BASE))


if __name__ == "__main__":
    main()
