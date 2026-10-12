#!/usr/bin/env python3
"""Render the Ashvena 1953 logo reveal (1080 x 1920, 9:16).

  Frame 1  0-3 s    ribbon is cut               (Kling 2.5 clip from the tin photo)
  Frame 2  3-6 s    tin lid opens, gold glow    (same clip)
  Frame 3  6-11 s   sparkles stream out of the tin and build the logo in gold
  Frame 4  11-15 s  plain Dispensary-blue background, final logo in brand colours

Frames 3-4 are drawn here, particle by particle, from the vector logo in
logo-reveal/source/ashvena-logo-final.pdf so the mark is exact.

    pip install numpy pillow scipy cairosvg     (plus ffmpeg and poppler-utils)
    python3 scripts/render_logo_reveal.py
    python3 scripts/render_logo_reveal.py --still 9.5    # one preview frame

Without logo-reveal/source/kling-ribbon-tin-open.mp4 the tin photo stands in
for frames 1-2 so the timing can still be previewed.
"""
import argparse
import io
import math
import os
import re
import subprocess
import tempfile
from multiprocessing import Pool

import cairosvg
import numpy as np
from PIL import Image
from scipy.ndimage import convolve1d, gaussian_filter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logo-reveal")
SRC = os.path.join(ROOT, "source")
LOGO_PDF = os.path.join(SRC, "ashvena-logo-final.pdf")
CLIP = os.path.join(SRC, "kling-ribbon-tin-open.mp4")
PHOTO = os.path.join(SRC, "tin-ribbon.jpg")

W, H, FPS = 1080, 1920, 30
T_CLIP_CUT = 6.0      # frames 1-2 end, coded sparkles take over
T_CLIP_END = 10.0     # Kling clip length; its last frame is held after this
T_LOGO_DONE = 10.4    # every sparkle has landed, gold logo solid
T_SCENE4 = 11.0       # blue reveal starts
T_END = 15.0

# Brand palette (from the logo PDF)
DISPENSARY = np.array([203, 233, 241]) / 255
BRICK = np.array([148, 21, 40]) / 255
DEEP_LAC = np.array([53, 7, 15]) / 255
GOLD_HI = np.array([0.99, 0.84, 0.48])
GOLD_LO = np.array([0.72, 0.46, 0.14])
SPARK = np.array([1.00, 0.80, 0.42])

LOGO_W = 620          # lockup width on the 1080 px frame
LOGO_CY = 0.50 * H
EMIT = (0.52 * W, 0.255 * H)   # mouth of the open tin in the clip's last frame


def ease(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def ease_out(u):
    u = np.clip(u, 0, 1)
    return 1 - (1 - u) ** 3


# ---------------------------------------------------------------- logo layers

def logo_layers():
    """Return (mark, word, year) alpha masks placed on the W x H frame."""
    svg = subprocess.run(["pdftocairo", "-svg", "-f", "1", "-l", "1", LOGO_PDF, "-"],
                         capture_output=True, check=True).stdout.decode()
    head = re.search(r"<svg[^>]*>", svg).group(0)
    vw, vh = map(float, re.search(r'viewBox="0 0 (\S+) (\S+)"', head).groups())
    paths = re.findall(r"<path[^>]*/>", svg)   # mark, "Ashvena", "1953"
    scale = 4
    masks = []
    for p in paths:
        one = p.replace(re.search(r'fill="[^"]+"', p).group(0), 'fill="#000"')
        doc = f'<svg xmlns="http://www.w3.org/2000/svg" width="{vw * scale}" height="{vh * scale}" viewBox="0 0 {vw} {vh}">{one}</svg>'
        png = cairosvg.svg2png(bytestring=doc.encode())
        masks.append(np.asarray(Image.open(io.BytesIO(png)).split()[-1], np.float32) / 255)
    union = np.maximum.reduce(masks)
    ys, xs = np.nonzero(union > 0.02)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    k = LOGO_W / (x1 - x0)
    tw, th = round((x1 - x0) * k), round((y1 - y0) * k)
    ox, oy = round((W - tw) / 2), round(LOGO_CY - th / 2)
    out = []
    for m in masks:
        im = Image.fromarray((m[y0:y1, x0:x1] * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
        full = np.zeros((H, W), np.float32)
        full[oy:oy + th, ox:ox + tw] = np.asarray(im, np.float32) / 255
        out.append(full)
    return out, (ox, oy, tw, th)


# ------------------------------------------------------------------ particles

def build_particles(layers, box, seed=1953):
    rng = np.random.default_rng(seed)
    ox, oy, tw, th = box
    counts = (5200, 2600, 700)
    windows = ((7.4, 9.4), (8.3, 9.9), (9.0, 10.2))   # landing sweep per layer
    tx, ty, ta = [], [], []
    for m, n, (a, b) in zip(layers, counts, windows):
        ys, xs = np.nonzero(m > 0.5)
        pick = rng.choice(len(xs), n, replace=len(xs) < n)
        x = xs[pick] + rng.random(n) - 0.5
        y = ys[pick] + rng.random(n) - 0.5
        sweep = (x - ox) / tw                          # write left to right
        tx.append(x), ty.append(y)
        ta.append(a + (b - a) * sweep + rng.normal(0, 0.12, n))
    tx, ty, ta = map(np.concatenate, (tx, ty, ta))
    n = len(tx)
    # most rise out of the tin mouth; a share drift in from the gold trail above it
    from_trail = rng.random(n) < 0.25
    sx = np.where(from_trail, rng.uniform(0.15, 0.55, n) * W, EMIT[0] + rng.normal(0, 45, n))
    sy = np.where(from_trail, rng.uniform(0.06, 0.22, n) * H, EMIT[1] + rng.normal(0, 12, n))
    te = np.where(from_trail, rng.uniform(5.6, 7.0, n), rng.uniform(5.8, 7.8, n))
    ta = np.maximum(ta, te + 1.3)
    # fountain path: up out of the tin, arc over, settle down onto the target
    c1x = sx + rng.normal(0, 160, n)
    c1y = sy - rng.uniform(250, 650, n)
    c2x = tx + rng.normal(0, 260, n)
    c2y = ty - rng.uniform(120, 480, n)
    return dict(n=n, sx=sx, sy=sy, c1x=c1x, c1y=c1y, c2x=c2x, c2y=c2y, tx=tx, ty=ty,
                te=te, ta=ta, freq=rng.uniform(2, 7, n), phase=rng.uniform(0, 2 * np.pi, n),
                big=rng.random(n) < 0.12, rng_seed=seed)


def particle_state(P, t):
    u = np.clip((t - P["te"]) / (P["ta"] - P["te"]), 0, 1)
    e = ease(u)
    a, b = (1 - e), e
    x = a ** 3 * P["sx"] + 3 * a * a * b * P["c1x"] + 3 * a * b * b * P["c2x"] + b ** 3 * P["tx"]
    y = a ** 3 * P["sy"] + 3 * a * a * b * P["c1y"] + 3 * a * b * b * P["c2y"] + b ** 3 * P["ty"]
    alive = t >= P["te"]
    landed = t >= P["ta"]
    tw = 0.55 + 0.45 * np.sin(2 * np.pi * P["freq"] * t + P["phase"])
    fade_in = np.clip((t - P["te"]) / 0.25, 0, 1)
    after = np.clip((t - P["ta"]) / 0.8, 0, 1)
    bright = np.where(landed, 1.0 - 0.7 * after, 1.0) * tw * fade_in
    bright *= 1.0 - ease((t - T_SCENE4 - 0.4) / 1.2)          # glitter fades in frame 4
    return x, y, np.where(alive, bright, 0.0), landed


def splat(buf, x, y, v):
    xi, yi = np.round(x).astype(int), np.round(y).astype(int)
    ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H) & (v > 0)
    np.add.at(buf, (yi[ok], xi[ok]), v[ok])


def blur(img, sigma, down):
    """Cheap wide gaussian: blur at reduced size, then scale back up."""
    if img.ndim == 3:
        return np.stack([blur(img[..., c], sigma, down) for c in range(img.shape[2])], -1)
    img = img.astype(np.float32)
    if down == 1:
        return gaussian_filter(img, sigma)
    h, w = img.shape
    small = img.reshape(h // down, down, w // down, down).mean((1, 3))
    small = gaussian_filter(small, sigma / down)
    return np.asarray(Image.fromarray(small, "F").resize((w, h), Image.BILINEAR))


def sparkle_light(P, t):
    """Additive RGB light of every sparkle at time t."""
    x, y, v, _ = particle_state(P, t)
    core = np.zeros((H, W), np.float32)
    splat(core, x, y, v.astype(np.float32))
    stars = np.zeros((H, W), np.float32)
    splat(stars, x[P["big"]], y[P["big"]], 2.2 * v[P["big"]].astype(np.float32))
    light = (gaussian_filter(core, 0.9) * 5.0 + gaussian_filter(stars, 1.6) * 7.0
             + blur(core + stars, 7, 4) * 9.0 + blur(core + stars, 28, 8) * 14.0)
    rays = star_rays(stars)
    light = light + rays
    hot = 1 - np.exp(-light)                                   # tone map
    rgb = hot[..., None] * SPARK + (hot ** 3)[..., None] * (1 - SPARK)   # white-hot centres
    return rgb.astype(np.float32)


def star_rays(stars):
    """Four-point glints on the bright sparkles."""
    s = gaussian_filter(stars, 1.2)
    k = 18
    ray = 1 - np.abs(np.arange(-k, k + 1)) / k
    ray[k] = 0
    return (convolve1d(s, ray, 1) + convolve1d(s, ray, 0)) * 0.9


# ----------------------------------------------------------------- background

class Background:
    def __init__(self):
        self.frames = None
        if os.path.exists(CLIP):
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", CLIP, "-vf",
                                  f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                 capture_output=True, check=True).stdout
            self.frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
        else:
            print("! no Kling clip yet, using the tin photo as a stand-in")
            self.still = np.asarray(Image.open(PHOTO).convert("RGB").resize((W, H), Image.LANCZOS))

    def at(self, t):
        if self.frames is None:
            return self.still
        i = min(int(round(t * FPS)), len(self.frames) - 1)
        return self.frames[i]

    def clip_seconds(self):
        return T_CLIP_END if self.frames is None else len(self.frames) / FPS


def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - W / 2) / (W * 0.62), (yy - LOGO_CY) / (H * 0.55))
    return np.clip(1.15 - 0.55 * r ** 2, 0.25, 1)[..., None]


def scene3_bg(bg, t, held_from, vig):
    """Clip keeps playing, then holds its last frame with a slow push-in;
    the tin sinks back into a warm, dark, defocused room so the gold reads."""
    frame = bg.at(min(t, held_from - 1 / FPS)).astype(np.float32) / 255
    if t > held_from:
        z = 1 + 0.035 * ease((t - held_from) / (T_SCENE4 - held_from + 1))
        im = Image.fromarray((frame * 255).astype(np.uint8))
        cw, ch = W / z, H / z
        frame = np.asarray(im.resize((W, H), Image.BICUBIC,
                                     box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)),
                           np.float32) / 255
    k = ease((t - 7.0) / 2.2)
    if k > 0:
        soft = blur(frame, 2 + 14 * k, 4)
        frame = frame * (1 - k) + soft * k
        frame = frame * (1 - 0.72 * k * (1 - vig * 0.4))
        frame = frame * (1 - 0.15 * k) + 0.15 * k * frame * np.array([1.10, 0.92, 0.75])
    return frame


# ------------------------------------------------------------------ logo look

def gold_fill(mask, ox, oy, th):
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    g = np.clip((yy - oy) / th, 0, 1)
    grad = GOLD_HI * (1 - g) + GOLD_LO * g
    rng = np.random.default_rng(7)
    glitter = gaussian_filter(rng.random((H, W)).astype(np.float32), 0.7)
    glitter = (0.88 + 0.5 * (glitter - glitter.mean()))[..., None]
    return np.clip(grad * glitter, 0, 1).astype(np.float32)


def glint(mask_all, t, box):
    """Soft diagonal light sweep across the finished logo."""
    ox, oy, tw, th = box
    u = (t - 12.7) / 0.9
    if not 0 <= u <= 1:
        return 0
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    pos = ox - 200 + (tw + 400) * ease(u)
    d = (xx + 0.45 * (yy - LOGO_CY)) - pos
    return (np.exp(-(d / 55) ** 2) * mask_all * 0.55)[..., None]


# --------------------------------------------------------------------- render

class Reveal:
    def __init__(self):
        self.layers, self.box = logo_layers()
        self.mask_all = np.maximum.reduce(self.layers)
        self.P = build_particles(self.layers, self.box)
        self.bg = Background()
        self.held_from = min(self.bg.clip_seconds(), T_CLIP_END)
        self.vig = vignette()
        ox, oy, tw, th = self.box
        self.gold = gold_fill(self.mask_all, ox, oy, th)
        m, w, y = self.layers
        brand = BRICK * m[..., None] + DEEP_LAC * w[..., None] + BRICK * y[..., None]
        self.brand = (brand / np.maximum(self.mask_all, 1e-4)[..., None]).astype(np.float32)
        self.cache_t = None

    def reveal_map(self, t):
        """Where sparkles have landed, the gold logo materialises."""
        P = self.P
        landed = P["ta"] <= t
        stamp = np.zeros((H, W), np.float32)
        w = np.clip((t - P["ta"][landed]) / 0.35, 0, 1).astype(np.float32)
        splat(stamp, P["tx"][landed], P["ty"][landed], w)
        rev = np.clip(gaussian_filter(stamp, 4.0) * 60, 0, 1)
        rev = np.maximum(rev, ease((t - (T_LOGO_DONE - 0.6)) / 0.6))
        return rev * self.mask_all

    def frame(self, t):
        if t < T_CLIP_CUT:
            return self.bg.at(t)
        ox, oy, tw, th = self.box
        vig = self.vig
        if t < T_SCENE4:
            base = scene3_bg(self.bg, t, self.held_from, vig)
        else:
            dark = scene3_bg(self.bg, T_SCENE4, self.held_from, vig)
            # Dispensary blue opens out from the logo as a soft circle
            u = ease_out((t - T_SCENE4) / 0.9)
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            r = np.hypot(xx - W / 2, yy - LOGO_CY)
            rad = u * math.hypot(W / 2, H / 2) * 1.15
            inside = np.clip((rad - r) / 90 + 0.5, 0, 1)[..., None]
            ring = np.exp(-((r - rad) / 26) ** 2)[..., None] * (1 - u) * 1.6
            base = dark * (1 - inside) + DISPENSARY * inside
            base = base + ring * SPARK
        # logo: gold while forming, then turns to brick and deep lac on blue
        rev = self.reveal_map(t)[..., None]
        k = ease((t - T_SCENE4 - 0.25) / 0.8)
        fill = self.gold * (1 - k) + self.brand * k
        shimmer = 0
        if k < 1:
            halo = blur(rev[..., 0] * (1 - k), 10, 4)[..., None]
            shimmer = halo * SPARK * 0.35
        out = base * (1 - rev) + fill * rev + shimmer
        out = out + glint(self.mask_all, t, self.box) * (1 if k >= 1 else 0)
        out = 1 - (1 - out) * (1 - sparkle_light(self.P, t))   # screen the sparkles on
        return (np.clip(out, 0, 1) * 255).astype(np.uint8)


_R = None


def _init():
    global _R
    _R = Reveal()


def _render(i):
    return _R.frame(i / FPS).tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", type=float, nargs="*", help="render preview frames at these seconds")
    ap.add_argument("--out", default=os.path.join(ROOT, "ashvena-logo-reveal.mp4"))
    ap.add_argument("--start", type=float, default=0.0, help="first second to render")
    args = ap.parse_args()

    if args.still:
        r = Reveal()
        for t in args.still:
            p = os.path.join(tempfile.gettempdir(), f"reveal_{t:05.2f}.png")
            Image.fromarray(r.frame(t)).save(p)
            print(p)
        return

    first, last = round(args.start * FPS), round(T_END * FPS)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                           "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart", args.out], stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=_init) as pool:
        for n, buf in enumerate(pool.imap(_render, range(first, last), chunksize=2)):
            ff.stdin.write(buf)
            if n % 30 == 0:
                print(f"  {(first + n) / FPS:5.1f}s")
    ff.stdin.close()
    ff.wait()
    print("wrote", os.path.relpath(args.out))


if __name__ == "__main__":
    main()
