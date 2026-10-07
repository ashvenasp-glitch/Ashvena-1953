#!/usr/bin/env python3
"""Retouch the v4 watercolour paintings: remove stray motifs, add corner trees.

Works on the untouched paintings in packaging/F-palace-garden/art/src/ and
writes the retouched versions to art/ (where generate_belts_watercolour.py
reads them). All coordinates are given on a 2000 px wide reference and
scaled, so the same edits apply to Magnific's full-size 4096 px exports:
drop those into art/src/ under the same names and rerun.

Edits
- remove: patch a box with clean paper taken from elsewhere in the painting.
- floor: carry the faint floor line out to both ends of the belt.
- corner trees: clone a palm already in the painting (watercolour multiplies
  onto paper, so it is lifted as paper-relative colour and multiplied back),
  one at each end, mirrored on the right so both lean towards the centre.
- tint: the white paper becomes a soft coloured wash from the belt palette.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packaging", "F-palace-garden", "art")
REF_W = 2000

EDITS = {
    "fruit-cocktail": dict(
        # stray post and melon pot at the left end
        remove=[dict(box=(296, 40, 437, 480), paper_from=(110, 20), keep_from_x=404, keep_rows=(180, 262))],
        floor=dict(y=388, sample=(1210, 1250)),
        palm=dict(box=(636, 36, 836, 396),
                  mask=[[(636, 36), (836, 36), (836, 216), (636, 216)],
                        [(684, 210), (730, 210), (684, 396), (642, 396)]],
                  base=(662, 388)),
        corners=(70, 1930), flat_paper=True,
        tint="#e7e9c9"),                                   # pale lime-sage (palette lime)
    "aam-papad": dict(
        remove=[],
        floor=dict(y=427, sample=(1600, 1640)),
        palm=dict(box=(1170, 28, 1396, 434),
                  mask=[[(1170, 28), (1396, 28), (1396, 222), (1170, 222)],
                        [(1238, 216), (1282, 216), (1232, 434), (1204, 434)]],
                  base=(1212, 427)),
        corners=(80, 1920),
        tint="#f6eedc",                                    # warm cream
        paper_sat=(26, 6)),                                # warm cream washes count as paper too
}


def paper_tone(a):
    """Median colour of the plain paper (the brightest, most common tone)."""
    flat = a.reshape(-1, 3)
    bright = flat[flat.mean(1) > np.percentile(flat.mean(1), 60)]
    return np.median(bright, 0)


def retouch(key, e):
    src = Image.open(os.path.join(ART, "src", f"ashvena-{key}-watercolour.png")).convert("RGB")
    k = src.width / REF_W
    a = np.asarray(src).astype(np.float32)
    paper = paper_tone(a)
    S = lambda v: int(round(v * k))                                   # noqa: E731

    # 1. remove stray motifs with clean paper from the same rows
    for r in e["remove"]:
        # cover the motif (and the floor line under it - step 3 redraws it), feathered into the paper
        x0, y0, x1, y1 = map(S, r["box"])
        px, py = map(S, r["paper_from"])
        patch = a[py:py + (y1 - y0), px:px + (x1 - x0)].copy()
        # match the patch to the open paper beside the box (the motif had a pale halo round it)
        ring = np.concatenate([a[y0:y1, x0 - S(40):x0 - S(10)], a[y0:y1, x1 + S(10):x1 + S(40)]], 1).reshape(-1, 3)
        ring = ring[ring.mean(1) > 240]
        if len(ring):
            patch *= np.median(ring, 0) / np.median(patch.reshape(-1, 3), 0)
        f = S(10)
        m = Image.new("L", (x1 - x0 + 2 * f, y1 - y0 + 2 * f), 0)
        ImageDraw.Draw(m).rectangle((f, f, f + x1 - x0 - 1, f + y1 - y0 - 1), fill=255)
        m = np.asarray(m.filter(ImageFilter.GaussianBlur(f / 2)), np.float32)[f:-f, f:-f, None] / 255
        cur = a[y0:y1, x0:x1]
        if "keep_from_x" in r:                     # leaves overhanging from the neighbour: keep them, outline and all
            keep = np.zeros(cur.shape[:2], np.float32)
            kx = S(r["keep_from_x"]) - x0
            ky0, ky1 = (S(v) - y0 for v in r["keep_rows"])
            keep[ky0:ky1, kx:] = (cur[ky0:ky1, kx:].mean(2) < 228).astype(np.float32)
            keep = np.asarray(Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(k)),
                              np.float32)[..., None] / 255
            m = m * (1 - keep)
        a[y0:y1, x0:x1] = cur * (1 - m) + patch * m

    # plain flat-white paper: even out its tone so patched areas leave no seam
    if e.get("flat_paper"):
        plain = (a.min(2) >= 249)[..., None]
        a = np.where(plain, paper, a)

    # 2. lift the palm as paper-relative colour (1 = paper) inside its mask
    bx0, by0, bx1, by1 = map(S, e["palm"]["box"])
    crop = a[by0:by1, bx0:bx1] / paper
    m = Image.new("L", (bx1 - bx0, by1 - by0), 0)
    d = ImageDraw.Draw(m)
    for poly in e["palm"]["mask"]:
        d.polygon([(S(x) - bx0, S(y) - by0) for x, y in poly], fill=255)
    m = np.asarray(m.filter(ImageFilter.GaussianBlur(2 * k)), np.float32)[..., None] / 255
    tree = np.clip(1 - (1 - np.minimum(crop, 1)) * m, 0, 1)        # outside mask -> 1 (no change)
    base_x, base_y = S(e["palm"]["base"][0]) - bx0, S(e["palm"]["base"][1]) - by0

    # 3. floor line out to both ends (multiply a faint sample strip across)
    fy = S(e["floor"]["y"])
    sx0, sx1 = map(S, e["floor"]["sample"])
    band = a[fy - S(4):fy + S(4), sx0:sx1] / paper
    reps = int(np.ceil(a.shape[1] / band.shape[1]))
    strip = np.tile(np.minimum(band, 1), (1, reps, 1))[:, :a.shape[1]]
    region = a[fy - S(4):fy + S(4)]
    a[fy - S(4):fy + S(4)] = np.minimum(region, paper * strip)

    # 4. one palm at each corner, standing on the floor line
    for i, cx in enumerate(e["corners"]):
        t = tree if i == 0 else tree[:, ::-1]
        bx = base_x if i == 0 else t.shape[1] - 1 - base_x
        x0, y0 = S(cx) - bx, fy - base_y
        xa, xb = max(0, x0), min(a.shape[1], x0 + t.shape[1])
        a[y0:y0 + t.shape[0], xa:xb] *= t[:, xa - x0:xb - x0]

    # 5. coloured paper: the white paper takes the wash colour, with a soft
    #    low-frequency mottle so it reads as a watercolour wash
    tint = np.array([int(e["tint"][i:i + 2], 16) for i in (1, 3, 5)], np.float32)
    rng = np.random.default_rng(7)
    h, w = a.shape[:2]
    noise = Image.fromarray((rng.random((max(2, h // 60), max(2, w // 60))) * 255).astype(np.uint8))
    noise = np.asarray(noise.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(20 * k)), np.float32) / 255
    mottle = 1 - 0.035 * (noise[..., None] - .5)
    # only where the pixel is paper: painted motifs keep their own colours
    # paper = light and neutral (includes the pale halos and paper streaks; keeps cream and pale leaves)
    lum = a.mean(2, keepdims=True)
    sat = a.max(2, keepdims=True) - a.min(2, keepdims=True)
    s0, sw = e.get("paper_sat", (7, 10))
    paperness = np.clip((lum - 215) / 20, 0, 1) * np.clip(1 - (sat - s0) / sw, 0, 1)
    # soften the paper/wash boundary (also hides compression blocks in small copies)
    pm = Image.fromarray((paperness[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5 * k))
    paperness = np.minimum(paperness, np.asarray(pm, np.float32)[..., None] / 255 + .15)
    a = a * (1 - paperness) + a * (tint / paper) * mottle * paperness
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    out = os.path.join(ART, f"ashvena-{key}-watercolour.png")
    img.save(out, optimize=True)
    print(os.path.relpath(out, os.path.join(ART, "..", "..", "..")))


def main():
    for key, e in EDITS.items():
        retouch(key, e)


if __name__ == "__main__":
    main()
