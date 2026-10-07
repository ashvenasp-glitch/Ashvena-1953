#!/usr/bin/env python3
"""Ashvena logo reveal: 1080 x 1920 (9:16), 24 fps, ~10.5 s.

Story: the antique sea-green spice tin opens, its golden light floods the
frame and settles into a sea-green plate (the tin's enamel colour). The
crimson brush "અ" (the tin's red lettering colour) then paints itself in the
storyboard stroke order: upper bowl first, then lower bowl, rising diagonal,
top loop, stem and the dry-brush tail flick. ASHVENA and EST. 1953 follow.

The brush mark is lifted from the last storyboard frame (src/brush-storyboard_a.webp),
cleaned and upscaled 6x, and revealed along hand-placed centre lines so the
stroke front behaves like a round brush tip.

    pip install numpy pillow scipy opencv-python-headless
    python3 motion/logo-reveal/render_logo_reveal.py             # full render (silent)
    python3 motion/logo-reveal/render_logo_reveal.py --preview   # contact sheet only

Needs ffmpeg on PATH. Fonts (Cinzel, Montserrat) are fetched from the
google/fonts repo into ~/.cache/ashvena-fonts on first run.
"""
import argparse
import subprocess
import urllib.request
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
TIN_CLIP = SRC / "spice-tin_push-in.mov"
OUT_MP4 = HERE / "ashvena-logo-reveal_9x16.mp4"
OUT_POSTER = HERE / "ashvena-logo-reveal_poster.png"
OUT_MARK = HERE / "ashvena-brush-mark.png"
FONT_DIR = Path.home() / ".cache" / "ashvena-fonts"
FONTS = {
    "cinzel": "ofl/cinzel/Cinzel%5Bwght%5D.ttf",
    "montserrat": "ofl/montserrat/Montserrat%5Bwght%5D.ttf",
}

W, H, FPS = 1080, 1920, 24
DUR = 10.5
NF = round(DUR * FPS)
CX, CY = W / 2, H / 2

# Timeline (seconds)
T_ZOOM = 2.5            # extra push toward the glowing lid
T_WHITE_UP = 3.5        # golden light starts flooding the frame
T_CUT = 4.1             # tin -> plate, under full light
T_CLEAR = 4.95          # plate fully settled
T_A, DUR_A = 4.55, 0.90                  # stroke 1: upper bowl
T_B, DUR_B = T_A + DUR_A + 0.12, 1.95    # stroke 2: lower bowl -> loop -> stem -> tail
T_WORD = 7.35           # ASHVENA letters
T_EST = 8.0             # rules + EST. 1953
T_SHEEN = 8.75          # enamel light sweep

# Palette (0-1 sRGB)
CRIMSON = np.array([139, 9, 26], np.float32) / 255      # storyboard ink, matches the tin lettering
TEAL = np.array([38, 76, 72], np.float32) / 255
GOLD = np.array([168, 128, 56], np.float32) / 255
LIGHT = np.array([255, 243, 218], np.float32) / 255     # warm flash
PLATE_IN = np.array([206, 236, 234], np.float32) / 255  # sea-green enamel, centre
PLATE_OUT = np.array([140, 186, 182], np.float32) / 255  # edges

# Brush centre lines, in 2x storyboard-crop pixels (crop = 446 x 354 px around the glyph)
PATH_A = [(55, 322), (50, 275), (62, 215), (92, 155), (132, 103), (180, 63), (235, 48), (290, 52),
          (330, 82), (345, 130), (333, 178), (298, 212), (252, 235), (200, 250)]
SPEED_A = [0.4, 0.8, 1, 1, 1, 1, 1, 1, 1, 0.95, 0.95, 0.9, 0.75, 0.5]
PATH_B = [(205, 262), (255, 278), (310, 282), (352, 298), (385, 330), (400, 372), (400, 420), (385, 465),
          (345, 500), (285, 507), (232, 500), (196, 470), (190, 425), (198, 388), (215, 362), (262, 350),
          (322, 328), (382, 300), (432, 285), (472, 262), (495, 205), (512, 150), (528, 100), (545, 60),
          (568, 33), (598, 35), (620, 62), (628, 105), (616, 152), (592, 195), (560, 232), (530, 265),
          (508, 305), (496, 355), (494, 410), (500, 470), (520, 528), (555, 575), (605, 607), (670, 630),
          (745, 648), (820, 655), (865, 650)]
SPEED_B = [0.35, 0.7, 0.95, 0.95, 0.95, 1.05, 1.05, 1.05, 1.05, 1.05, 1.0, 1.0, 1.0, 1.0, 1.15, 1.3,
           1.3, 1.3, 1.3, 1.0, 1.0, 1.0, 0.75, 0.75, 0.75, 0.75, 0.95, 0.95, 0.95, 0.95, 1.2, 1.2, 1.2,
           1.2, 1.2, 1.2, 1.35, 1.35, 1.35, 1.8, 1.8, 1.8, 2.4]

GLYPH_W2 = 1520         # glyph canvas width at 2x (760 px in the final frame)
LOCK_Y0, LOCK_Y1 = 380, 1540   # final-frame rows covered by the 2x lockup canvas


def smooth(e0, e1, x):
    t = np.clip((np.asarray(x, np.float32) - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def ease_out(x):
    x = np.clip(x, 0, 1)
    return 1 - (1 - x) ** 3


def font(name, size, wght):
    path = FONT_DIR / Path(FONTS[name]).name
    if not path.exists():
        FONT_DIR.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve("https://raw.githubusercontent.com/google/fonts/main/" + FONTS[name], path)
    f = ImageFont.truetype(str(path), size)
    f.set_variation_by_axes([wght])
    return f


# ---------------------------------------------------------------- brush mark
def extract_glyph():
    """Soft alpha of the brush mark from the last storyboard frame, upscaled 6x."""
    panel = Image.open(SRC / "brush-storyboard_a.webp").convert("RGB").crop((1006, 755, 1504, 1125))
    a = np.asarray(panel, np.float32)
    bg = np.median(a[:20].reshape(-1, 3), 0)
    dist = np.linalg.norm(a - bg, axis=2)
    ink = np.median(a[dist > np.percentile(dist, 97)], 0)
    v = ink - bg
    al = np.clip(((a - bg) @ v) / (v @ v), 0, 1)[12:366, 25:471]
    k = 6
    up = Image.fromarray((al * 255).astype(np.uint8)).resize((al.shape[1] * k, al.shape[0] * k), Image.LANCZOS)
    up = ndi.gaussian_filter(np.asarray(up, np.float32) / 255, 2.2)
    m = 1 / (1 + np.exp(-(up - 0.5) / 0.035))
    lab, n = ndi.label(m > 0.5)
    sizes = ndi.sum(np.ones_like(m), lab, range(1, n + 1))
    keep = ndi.binary_dilation(np.isin(lab, 1 + np.flatnonzero(sizes >= 60)), iterations=3)
    return (m * keep).astype(np.float32)


def catmull(pts, n=16):
    p = np.array(pts, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out, par = [], []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1:i + 3]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
            par.append(i - 1 + t)
    out.append(p[-2])
    par.append(len(pts) - 1)
    return np.array(out), np.array(par)


def stroke_track(pts, speeds, t0, dur, scale, step=2.0):
    """Uniform-arc samples of a centre line with absolute paint times."""
    xy, par = catmull(pts)
    xy = xy * scale
    v = np.interp(par, np.arange(len(pts)), speeds)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))])
    su = np.arange(0, s[-1], step)
    p = np.stack([np.interp(su, s, xy[:, 0]), np.interp(su, s, xy[:, 1])], 1)
    vu = np.interp(su, s, v)
    tt = np.concatenate([[0], np.cumsum(np.diff(su) / (0.5 * (vu[1:] + vu[:-1])))])
    tt = t0 + dur * tt / tt[-1]
    tan = np.gradient(p, axis=0)
    tan /= np.linalg.norm(tan, axis=1, keepdims=True) + 1e-9
    return dict(p=p, t=tt, s=su, frac=su / su[-1], tan=tan, speed=step / np.gradient(tt))


class BrushMark:
    def __init__(self):
        hi = extract_glyph()
        self.hi = hi
        h2 = round(hi.shape[0] * GLYPH_W2 / hi.shape[1])
        self.mask = np.asarray(Image.fromarray(hi).resize((GLYPH_W2, h2), Image.LANCZOS), np.float32).clip(0, 1)
        scale = GLYPH_W2 / hi.shape[1] * 3   # 2x-crop px -> glyph canvas px
        self.dt = ndi.distance_transform_edt(self.mask > 0.5)
        self.strokes = [stroke_track(self._centre(PATH_A, scale), SPEED_A, T_A, DUR_A, scale),
                        stroke_track(self._centre(PATH_B, scale), SPEED_B, T_B, DUR_B, scale)]
        self._time_map(scale)
        self._paint_colour()

    def _centre(self, pts, scale, passes=2, reach=16):
        """Slide hand-placed points along their normals onto the stroke's medial axis."""
        dt = self.dt / scale
        p = np.array(pts, float)
        for _ in range(passes):
            q = p.copy()
            for i in range(len(p)):
                tng = p[min(i + 1, len(p) - 1)] - p[max(i - 1, 0)]
                tng /= np.linalg.norm(tng)
                ts = np.arange(-reach, reach + 0.5, 0.5)
                cand = p[i] + ts[:, None] * np.array([-tng[1], tng[0]])
                iy = np.clip((cand[:, 1] * scale).astype(int), 0, dt.shape[0] - 1)
                ix = np.clip((cand[:, 0] * scale).astype(int), 0, dt.shape[1] - 1)
                v = dt[iy, ix]
                if v.max() > 0:
                    q[i] = cand[np.argmax(v - 0.15 * np.abs(ts))]
            p = q
        return p

    def _time_map(self, scale):
        """Each pixel gets the earliest time a round brush tip on the centre line covers it."""
        m = self.mask
        dt = self.dt
        tmap = np.full(m.shape, np.inf, np.float32)
        hh, ww = m.shape
        for st in self.strokes:
            p = st["p"]
            iy = np.clip(p[:, 1].round().astype(int), 0, hh - 1)
            ix = np.clip(p[:, 0].round().astype(int), 0, ww - 1)
            # robust half-width: long running median, so merged junction blobs don't inflate the tip
            r = np.clip(ndi.median_filter(dt[iy, ix], 31, mode="nearest") * 1.02, 4 * scale, 40 * scale)
            st["r"] = r
            for (x, y), t, rad in zip(p, st["t"], r):
                x0, x1 = max(int(x - rad), 0), min(int(x + rad) + 2, ww)
                y0, y1 = max(int(y - rad), 0), min(int(y + rad) + 2, hh)
                if x0 >= x1 or y0 >= y1:
                    continue
                yy, xx = np.ogrid[y0:y1, x0:x1]
                inside = (xx - x) ** 2 + (yy - y) ** 2 <= rad * rad
                sub = tmap[y0:y1, x0:x1]
                sub[inside] = np.minimum(sub[inside], t)
        pts = np.concatenate([s["p"] for s in self.strokes])
        times = np.concatenate([s["t"] for s in self.strokes])
        self.sid = np.concatenate([np.full(len(s["p"]), i) for i, s in enumerate(self.strokes)])
        self.tree = cKDTree(pts)
        ys, xs = np.nonzero(m > 0.005)
        _, nn = self.tree.query(np.stack([xs, ys], 1))
        self.nn = (ys, xs, nn)
        miss = ~np.isfinite(tmap[ys, xs])
        tmap[ys[miss], xs[miss]] = times[nn[miss]]   # splinters and dry streaks: nearest centre point
        tmap[~np.isfinite(tmap)] = 99
        self.tmap = tmap
        self.t_end = times.max()

    def _paint_colour(self):
        """Crimson enamel with faint bristle streaks along the stroke and darker pooled edges."""
        rng = np.random.default_rng(1953)
        noise = ndi.gaussian_filter1d(rng.standard_normal(8192), 1.2)
        noise /= noise.std()
        slow = ndi.gaussian_filter1d(rng.standard_normal(8192), 6.0)
        slow /= slow.std()
        ys, xs, nn = self.nn
        pts = np.concatenate([s["p"] for s in self.strokes])
        tan = np.concatenate([s["tan"] for s in self.strokes])
        arc = np.concatenate([s["s"] for s in self.strokes])
        frac = np.concatenate([s["frac"] for s in self.strokes])
        sid = self.sid[nn]
        off = (xs - pts[nn, 0]) * -tan[nn, 1] + (ys - pts[nn, 1]) * tan[nn, 0]
        idx = np.arange(8192)
        streak = np.interp(off / 1.3 + 4096 + sid * 977, idx, noise)
        along = np.interp(arc[nn] / 70 + 300 + sid * 1311, idx, slow)
        lum = 1 + 0.018 * streak + 0.025 * along
        dry = smooth(0.9, 1.0, frac[nn]) * (sid == 1)          # tail thins out
        grain = 1 + 0.015 * rng.standard_normal(len(xs))
        col = np.ones(self.mask.shape + (3,), np.float32) * CRIMSON
        c = CRIMSON[None] * (lum * grain)[:, None]
        c = c + (np.array([0.70, 0.16, 0.22]) - c) * (0.35 * dry)[:, None]
        col[ys, xs] = c
        rim = np.clip((1 - ndi.gaussian_filter(self.mask, 2.0)) * 2.2, 0, 1)
        col *= (1 - 0.10 * rim)[..., None]
        self.col = col.clip(0, 1)

    def frame(self, t):
        """(premultiplied rgb, alpha) of the mark at time t, with 180-degree shutter blur."""
        age = t - self.tmap
        if t > self.t_end + 0.1:
            cov = 1.0
        else:
            cov = np.zeros_like(age)
            for d in np.linspace(-1 / 96, 1 / 96, 5):
                cov += smooth(0, 0.012, age + d)
            cov /= 5
        a = self.mask * cov
        wet = np.exp(-np.clip(age, 0, None) / 0.45) * (age > 0)
        col = self.col * (1 - 0.28 * wet)[..., None]
        return col * a[..., None], a

    def save_master(self, path):
        hi = self.hi
        rgba = np.zeros(hi.shape + (4,), np.uint8)
        rgba[..., :3] = (CRIMSON * 255).round().astype(np.uint8)
        rgba[..., 3] = (hi * 255).round().astype(np.uint8)
        Image.fromarray(rgba, "RGBA").save(path, optimize=True)


# ---------------------------------------------------------------- lockup (mark + wordmark) at 2x
class Lockup:
    def __init__(self, mark):
        self.mark = mark
        self.h2 = (LOCK_Y1 - LOCK_Y0) * 2
        m = mark.mask
        ys, xs = np.nonzero(m > 0.5)
        bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
        w = m[ys, xs]
        x_vis = 0.55 * (xs * w).sum() / w.sum() + 0.45 * (bx0 + bx1) / 2
        self.gx = int(round(W - x_vis))

        self.f_word = font("cinzel", 196, 600)
        self.f_est = font("montserrat", 58, 500)
        cap_w = -self.f_word.getbbox("H", anchor="ls")[1] / 2
        cap_e = -self.f_est.getbbox("H", anchor="ls")[1] / 2
        hg = (by1 - by0) / 2
        gap1, gap2 = 92, 60
        total = hg + gap1 + cap_w + gap2 + cap_e
        top = 935 - total / 2
        self.gy = int(round((top - LOCK_Y0) * 2 - by0))
        self.word_base = (top + hg + gap1 + cap_w - LOCK_Y0) * 2
        self.est_base = self.word_base + (gap2 + cap_e) * 2
        self.est_mid = self.est_base - cap_e   # vertical middle of the EST caps (2x)
        self.letters = [self._letter(ch, self.f_word) for ch in "ASHVENA"]
        self.est = self._tracked("EST. 1953", self.f_est, 0.42)
        self.sheen_box = (self.gx + bx0, self.gy + by0, self.gx + bx1, self.word_base)

    @staticmethod
    def _letter(ch, f):
        l, t, r, b = f.getbbox(ch, anchor="ls")
        img = Image.new("L", (r - l + 8, b - t + 8))
        ImageDraw.Draw(img).text((4 - l, 4 - t), ch, font=f, fill=255, anchor="ls")
        return dict(a=np.asarray(img, np.float32) / 255, ox=l - 4, oy=t - 4, adv=f.getlength(ch))

    def _tracked(self, text, f, track):
        size = f.size
        glyphs = [self._letter(c, f) for c in text]
        width = sum(g["adv"] for g in glyphs) + track * size * (len(glyphs) - 1)
        top = min(g["oy"] for g in glyphs)
        bot = max(g["oy"] + g["a"].shape[0] for g in glyphs)
        out = np.zeros((bot - top, int(np.ceil(width)) + 16), np.float32)
        x = 8.0
        for g in glyphs:
            xi = int(round(x + g["ox"]))
            hh, ww = g["a"].shape
            out[g["oy"] - top:g["oy"] - top + hh, xi:xi + ww] = np.maximum(
                out[g["oy"] - top:g["oy"] - top + hh, xi:xi + ww], g["a"])
            x += g["adv"] + track * size
        return dict(a=out, top=top, width=width)

    @staticmethod
    def _stamp(canvas, patch, x, y, op=1.0):
        """Add an alpha patch at a sub-pixel position."""
        xi, yi = int(np.floor(x)), int(np.floor(y))
        fx, fy = x - xi, y - yi
        hh, ww = patch.shape
        shifted = cv2.warpAffine(patch, np.float32([[1, 0, fx], [0, 1, fy]]), (ww + 1, hh + 1),
                                 flags=cv2.INTER_LINEAR)
        y0, x0 = max(yi, 0), max(xi, 0)
        y1, x1 = min(yi + hh + 1, canvas.shape[0]), min(xi + ww + 1, canvas.shape[1])
        if y1 <= y0 or x1 <= x0:
            return
        sub = shifted[y0 - yi:y1 - yi, x0 - xi:x1 - xi] * op
        canvas[y0:y1, x0:x1] = np.maximum(canvas[y0:y1, x0:x1], sub)

    def frame(self, t):
        rgb = np.zeros((self.h2, W * 2, 3), np.float32)
        alpha = np.zeros((self.h2, W * 2), np.float32)
        if t < T_A - 0.05:
            return rgb, alpha
        gp, ga = self.mark.frame(t)
        hh, ww = ga.shape
        rgb[self.gy:self.gy + hh, self.gx:self.gx + ww] = gp
        alpha[self.gy:self.gy + hh, self.gx:self.gx + ww] = ga

        if t >= T_WORD:
            # ASHVENA: letters rise in one by one while the tracking settles
            word = np.zeros_like(alpha)
            size = self.f_word.size
            track = (0.26 + 0.10 * (1 - ease_out((t - T_WORD) / 1.3))) * size
            width = sum(g["adv"] for g in self.letters) + track * (len(self.letters) - 1)
            x = W - width / 2
            for i, g in enumerate(self.letters):
                p = ease_out((t - T_WORD - 0.065 * i) / 0.6)
                if p > 0:
                    self._stamp(word, g["a"], x + g["ox"], self.word_base + g["oy"] + (1 - p) * 52, p)
                x += g["adv"] + track
            rgb += word[..., None] * CRIMSON
            alpha += word
        if t >= T_EST:
            est = np.zeros_like(alpha)
            e = self.est
            p = ease_out((t - T_EST - 0.1) / 0.6)
            if p > 0:
                self._stamp(est, e["a"], W - e["width"] / 2 - 8, self.est_base + e["top"], p)
            rgb += est[..., None] * TEAL
            alpha += est
            # gold rules growing outward from the text
            g = ease_out((t - T_EST) / 0.75)
            rule = np.zeros_like(alpha)
            inner, length = e["width"] / 2 + 46, 150 * g
            for sgn in (-1, 1):
                xa, xb = sorted((W + sgn * inner, W + sgn * (inner + length)))
                if xb - xa > 0.5:
                    self._rule(rule, xa, xb, self.est_mid, 3.0)
            rgb += rule[..., None] * GOLD
            alpha += rule
        if T_SHEEN <= t <= T_SHEEN + 1.0:
            x0, y0, x1, y1 = self.sheen_box
            yy, xx = np.mgrid[0:self.h2, 0:W * 2].astype(np.float32)
            d = ((xx - x0) * 0.82 + (yy - y0) * 0.57) / ((x1 - x0) * 0.82 + (y1 - y0) * 0.57)
            c = -0.25 + 1.5 * smooth(T_SHEEN, T_SHEEN + 1.0, t)
            hl = 0.22 * np.exp(-((d - c) / 0.05) ** 2)
            sheen = np.array([1.0, 0.90, 0.86], np.float32)
            rgb = rgb * (1 - hl[..., None]) + sheen * (alpha * hl)[..., None]
        return rgb, np.clip(alpha, 0, 1)

    @staticmethod
    def _rule(canvas, xa, xb, yc, thick):
        xs = np.arange(int(xa) - 1, int(np.ceil(xb)) + 2)
        ys = np.arange(int(yc - thick) - 1, int(np.ceil(yc + thick)) + 2)
        cov_x = np.clip(np.minimum(xs + 1 - xa, xb - xs), 0, 1)
        cov_y = np.clip(np.minimum(ys + 1 - (yc - thick / 2), (yc + thick / 2) - ys), 0, 1)
        canvas[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1] = np.maximum(
            canvas[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1], cov_y[:, None] * cov_x[None])

    def to_frame(self, t, z):
        """Warp the 2x canvas into the 1080 x 1920 frame with the plate push-in z."""
        rgb, a = self.frame(t)
        if not a.any():
            return None, None
        rgb = cv2.GaussianBlur(rgb, (0, 0), 0.55)
        a = cv2.GaussianBlur(a, (0, 0), 0.55)
        m = np.float32([[z / 2, 0, CX * (1 - z)], [0, z / 2, z * LOCK_Y0 + CY * (1 - z)]])
        rgb = cv2.warpAffine(rgb, m, (W, H), flags=cv2.INTER_LINEAR)
        a = cv2.warpAffine(a, m, (W, H), flags=cv2.INTER_LINEAR)
        return rgb, a


# ---------------------------------------------------------------- plate, light and dust
def make_plate():
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - CX) / 900, (yy - 880) / 1250)
    k = np.clip(r, 0, 1.4) ** 1.6
    plate = PLATE_IN + (PLATE_OUT - PLATE_IN) * np.clip(k, 0, 1)[..., None]
    warm = np.exp(-(((xx - CX) / 620) ** 2 + ((yy - 760) / 780) ** 2))
    plate += (LIGHT - plate) * (0.08 * warm)[..., None]
    # enamel/paper tooth: soft mottling + fine grain
    mott = ndi.gaussian_filter(rng.standard_normal((H // 4, W // 4)), 10)
    mott = cv2.resize(mott / mott.std(), (W, H), interpolation=cv2.INTER_CUBIC)
    fine = ndi.gaussian_filter(rng.standard_normal((H, W)), 0.8)
    fine /= fine.std()
    plate *= (1 + 0.006 * mott + 0.006 * fine)[..., None]
    vig = 1 - 0.20 * np.clip(np.hypot((xx - CX) / 760, (yy - CY) / 1180), 0, 1.5) ** 2.4
    return (plate * vig[..., None]).astype(np.float32)


def sprite(radius, soft):
    n = int(np.ceil(radius * 2 + 6))
    yy, xx = np.mgrid[0:n, 0:n] - (n - 1) / 2
    d = np.hypot(xx, yy)
    if soft:   # out-of-focus disc
        return np.clip((radius - d) / max(radius * 0.35, 1) + 0.5, 0, 1).astype(np.float32)
    return np.exp(-(d / max(radius, 0.6)) ** 2).astype(np.float32)


def draw(img, spr, x, y, colour, alpha, additive=False):
    n = spr.shape[0]
    xi, yi = int(round(x - n / 2)), int(round(y - n / 2))
    y0, x0 = max(yi, 0), max(xi, 0)
    y1, x1 = min(yi + n, H), min(xi + n, W)
    if y1 <= y0 or x1 <= x0:
        return
    a = spr[y0 - yi:y1 - yi, x0 - xi:x1 - xi, None] * alpha
    if additive:
        img[y0:y1, x0:x1] += a * colour
    else:
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + colour * a


class Dust:
    """Spice dust thrown up by the flash, drifting over the plate."""
    PALETTE = np.array([[214, 148, 38], [219, 102, 31], [158, 56, 26], [230, 184, 90]], np.float32) / 255

    def __init__(self):
        rng = np.random.default_rng(11)
        n_s, n_b = 150, 10
        n = n_s + n_b
        self.big = np.arange(n) >= n_s
        self.x0 = rng.uniform(-40, W + 40, n)
        self.y0 = H * (0.2 + 0.85 * rng.beta(2.2, 1.4, n))
        self.vb = -rng.uniform(80, 260, n)        # initial burst (px/s)
        self.vx = rng.normal(0, 40, n)
        self.vd = -rng.uniform(6, 26, n)          # terminal drift
        self.sw_a = rng.uniform(5, 22, n)
        self.sw_f = rng.uniform(0.12, 0.4, n)
        self.sw_p = rng.uniform(0, 6.3, n)
        self.rad = np.where(self.big, rng.uniform(10, 34, n), rng.uniform(0.9, 3.2, n))
        self.alpha = np.where(self.big, rng.uniform(0.03, 0.06, n), rng.uniform(0.25, 0.65, n))
        self.col = self.PALETTE[rng.integers(0, 4, n)]
        self.flick = rng.uniform(0, 6.3, n)
        self.sprites = [sprite(r, b) for r, b in zip(self.rad, self.big)]

    def render(self, img, t):
        dt = t - T_CUT
        if dt < 0:
            return
        tau = 0.8
        burst = tau * (1 - np.exp(-dt / tau))
        x = self.x0 + self.vx * burst + self.sw_a * np.sin(2 * np.pi * self.sw_f * dt + self.sw_p)
        y = self.y0 + self.vb * burst + self.vd * dt
        fade = 1 - 0.4 * smooth(T_CUT, DUR, t)
        tw = 0.85 + 0.15 * np.sin(5 * dt + self.flick)
        warm = np.array([1.0, 0.86, 0.58], np.float32)
        for i in range(len(x)):
            if self.big[i]:   # out-of-focus motes catch the light
                draw(img, self.sprites[i], x[i], y[i], warm, self.alpha[i] * fade * tw[i], additive=True)
            else:
                draw(img, self.sprites[i], x[i], y[i], self.col[i], self.alpha[i] * fade * tw[i])


class Glints:
    """Bright motes rising out of the open tin (scene space, follows the push-in)."""

    def __init__(self):
        rng = np.random.default_rng(5)
        n = 80
        self.t0 = rng.uniform(2.7, 4.05, n)
        self.x = np.clip(rng.normal(540, 120, n), 300, 780)
        self.y = rng.uniform(560, 640, n)
        self.vy = -rng.uniform(90, 230, n)
        self.vx = rng.normal(0, 30, n)
        self.rad = rng.uniform(0.8, 2.4, n)
        self.amp = rng.uniform(0.4, 1.0, n)
        self.sprites = [sprite(r, False) for r in self.rad]

    def render(self, img, t, m):
        col = np.array([1.0, 0.78, 0.40], np.float32)
        for i in range(len(self.t0)):
            age = t - self.t0[i]
            if not 0 <= age <= 1.3:
                continue
            sx = self.x[i] + self.vx[i] * age + 8 * np.sin(4 * age + i)
            sy = self.y[i] + self.vy[i] * age
            px = m[0, 0] * sx + m[0, 2]
            py = m[1, 1] * sy + m[1, 2]
            life = smooth(0, 0.15, age) * (1 - smooth(0.8, 1.3, age))
            draw(img, self.sprites[i], px, py, col, self.amp[i] * life * 1.4, additive=True)


# ---------------------------------------------------------------- tin clip
def load_tin():
    w0, h0 = 1076, 1926
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(TIN_CLIP), "-vf", "scale=in_color_matrix=bt709:in_range=tv",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h0, w0, 3)


def tin_matrix(t, w0=1076, h0=1926):
    e = smooth(T_ZOOM, T_CUT + 0.05, t) ** 1.6
    s = max(W / w0, H / h0) * (1 + 0.32 * e)
    fx, fy = w0 / 2 + (540 - w0 / 2) * e, h0 / 2 + (445 - h0 / 2) * e   # toward the glowing lid
    ox, oy = CX, CY + (800 - CY) * e
    return np.float32([[s, 0, ox - s * fx], [0, s, oy - s * fy]])


def bloom(img, k):
    lum = img @ np.float32([0.2126, 0.7152, 0.0722])
    bright = img * smooth(0.5, 0.95, lum)[..., None]
    small = cv2.resize(bright, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    b = 0.6 * cv2.GaussianBlur(small, (0, 0), 4) + 0.4 * cv2.GaussianBlur(small, (0, 0), 16)
    b = cv2.resize(b, (W, H), interpolation=cv2.INTER_LINEAR)
    return img + k * b * np.float32([1.0, 0.86, 0.62])


def light_level(t):
    """0 -> 1 golden flood toward the cut, then back to 0 as the plate settles."""
    if t < T_CUT:
        return float(smooth(T_WHITE_UP, T_CUT, t)) ** 2.2
    return 1 - float(ease_out((t - T_CUT) / (T_CLEAR - T_CUT)))


# ---------------------------------------------------------------- renderer
class Renderer:
    def __init__(self):
        self.tin = load_tin()
        self.mark = BrushMark()
        self.lockup = Lockup(self.mark)
        self.plate = make_plate()
        self.dust = Dust()
        self.glints = Glints()
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.vig = (1 - 0.14 * np.clip(np.hypot((xx - CX) / 760, (yy - CY) / 1180), 0, 1.5) ** 2.2)[..., None]

    def frame(self, f):
        t = f / FPS
        wl = light_level(t)
        if t < T_CUT:
            src = self.tin[min(f, len(self.tin) - 1)].astype(np.float32) / 255
            m = tin_matrix(t)
            img = cv2.warpAffine(src, m, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
            k = 0.25 + 0.5 * float(smooth(1.4, 3.0, t)) + 3.2 * float(smooth(3.2, T_CUT, t)) ** 2
            img = bloom(img, k)
            self.glints.render(img, t, m)
            img *= 1 + 0.9 * wl
            img *= self.vig
            img *= float(smooth(0, 0.6, t))
        else:
            z = 1 + 0.05 * float(np.sin(0.5 * np.pi * min((t - T_CUT) / (DUR - T_CUT), 1)))
            mz = np.float32([[z, 0, CX * (1 - z)], [0, z, CY * (1 - z)]])
            img = cv2.warpAffine(self.plate, mz, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            img = img * (1 + 0.25 * wl)
            prem, a = self.lockup.to_frame(t, z)
            if a is not None:
                shadow = np.roll(cv2.GaussianBlur(a, (0, 0), 3.2), 3, axis=0)
                img *= (1 - 0.11 * shadow)[..., None]
                img = img * (1 - a[..., None]) + prem
            self.dust.render(img, t)
        img = img + (LIGHT - img) * wl
        g = cv2.GaussianBlur(np.random.default_rng(f).standard_normal((H, W)).astype(np.float32), (0, 0), 0.7)
        img += (0.022 * g)[..., None]
        return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="write a contact sheet instead of the video")
    ap.add_argument("--out", type=Path, default=OUT_MP4)
    args = ap.parse_args()
    r = Renderer()
    r.mark.save_master(OUT_MARK)

    if args.preview:
        times = [0.5, 2.0, 3.0, 3.7, 4.0, 4.3, 4.7, 5.0, 5.4, 5.9, 6.4, 6.9, 7.3, 7.6, 8.0, 8.5, 9.1, 10.4]
        thumbs = [Image.fromarray(r.frame(round(s * FPS))).resize((270, 480), Image.LANCZOS) for s in times]
        sheet = Image.new("RGB", (270 * 6, 480 * 3), "white")
        for i, im in enumerate(thumbs):
            sheet.paste(im, ((i % 6) * 270, (i // 6) * 480))
        sheet.save(args.out.with_name("preview_contact-sheet.png"))
        return

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
         "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-profile:v", "high", "-x264-params", "aq-mode=3",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-an", "-movflags", "+faststart", str(args.out)],
        stdin=subprocess.PIPE)
    last = None
    for f in range(NF):
        last = r.frame(f)
        enc.stdin.write(last.tobytes())
        if f % 24 == 0:
            print(f"frame {f}/{NF}", flush=True)
    enc.stdin.close()
    enc.wait()
    Image.fromarray(last).save(OUT_POSTER, optimize=True)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
