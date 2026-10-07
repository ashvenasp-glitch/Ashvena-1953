#!/usr/bin/env python3
"""Ashvena 1953 - logo-reveal film ("revealed from the tin"), ~8 s, 1920x1080.

  0.00-3.75  opening: the old tin opens and light spills out. Either the AI
             tin clip (--opening-clip, Nano Banana keyframes animated with
             Seedance) or, without one, an animatic built from a tin photo
             (--still) so timing can be reviewed.
  3.25-4.25  the camera pushes into the light; warm light settles into pale
             sea-green sampled from the tin.
  3.95-6.10  the अ draws itself in crimson, stroke by stroke in calligraphic
             order, with brush-like speed (slow press-in, slower in tight
             turns, a quick dry-brush flick on the tail). Wet ink settles.
  5.95-7.05  the camera eases back to the full lockup; "Ashvena" and "1953"
             are revealed beneath the mark.
  7.05-8.00  hold.

The mark, wordmark and year are taken from the vector master (logo_final.ai,
page 1) and are never redrawn or approximated - only revealed.

Usage:
  python3 scripts/render_logo_reveal.py --logo logo_final.ai --still tin.jpg -o out.mp4
  python3 scripts/render_logo_reveal.py --logo logo_final.ai --opening-clip tin_ai.mp4 -o out.mp4
"""
import argparse
import json
import math
import os
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage
from scipy.spatial import cKDTree

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STROKES = os.path.join(ROOT, "motion", "a_strokes.json")

W, H, FPS, DUR = 1920, 1080, 30, 8.0

# Brand colours (sampled from the vector master) and the tin.
DISPENSARY = (203, 233, 241)       # logo master background
BRICK = np.array([148, 21, 40], np.float32)   # the mark and the year
DEEP_LAC = np.array([53, 7, 15], np.float32)  # the wordmark
TIN_GREEN = np.array([207, 228, 221], np.float32)  # pale sea-green: hue of the tin enamel (photo), lifted to a clean field
WARM_LIGHT = np.array([255, 241, 214], np.float32)

# Timeline (seconds)
T_OPEN_END = 3.75     # opening fully bloomed into light
T_BLOOM = 3.25        # push into the light starts
T_SETTLE = 4.25       # light has settled into sea-green
T_DRAW = 3.95         # first touch of the brush
T_PULL = (5.95, 7.05)  # camera eases back to the full lockup
T_WORD = (6.12, 6.92)  # "Ashvena" reveal
T_YEAR = (6.42, 7.12)  # "1953" reveal

# Logo master geometry, px at 400 dpi on page 1 of logo_final.ai.
DPI = 400
CROP = (800, 1110, 3470, 4110)  # lockup canvas taken from the page render
MARK_ORIGIN = (980, 1100)       # origin of the coordinates in a_strokes.json
MARK_ROWS = (1100, 3200)        # crimson rows that belong to the mark (the rest is the year)
WORK = 0.5                      # working scale relative to the 400 dpi render
FINAL_LOCKUP_H = 700            # lockup height on the final frame, px
ZOOM_DRAW = 1.30                # extra zoom on the mark while it is drawn


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, np.float64) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


# --------------------------------------------------------------------------- logo layers

def load_logo_layers(ai_path, cache_dir):
    """Render page 1 of the .ai (a PDF) and unmix it into exact alpha layers."""
    png = os.path.join(cache_dir, "logo_p1.png")
    if not os.path.exists(png):
        subprocess.run(["pdftocairo", "-png", "-r", str(DPI), "-f", "1", "-l", "1", "-singlefile",
                        ai_path, png[:-4]], check=True)
    im = np.asarray(Image.open(png).convert("RGB")).astype(np.float32)
    bg = np.array(DISPENSARY, np.float32)

    def unmix(fg):
        d = fg - bg
        t = np.clip(((im - bg) @ d) / (d @ d), 0, 1)
        res = np.linalg.norm(im - (bg + t[..., None] * d), axis=-1)
        return t, res

    tc, rc = unmix(BRICK)
    td, rd = unmix(DEEP_LAC)
    crimson = np.where(rc <= rd, tc, 0)
    dark = np.where(rc > rd, td, 0)
    rows = np.arange(im.shape[0])[:, None]
    mark = np.where((rows >= MARK_ROWS[0]) & (rows < MARK_ROWS[1]), crimson, 0)
    year = np.where(rows >= MARK_ROWS[1], crimson, 0)

    x0, y0, x1, y1 = CROP
    cw, ch = int((x1 - x0) * WORK), int((y1 - y0) * WORK)

    def work(a):
        return np.asarray(Image.fromarray((a[y0:y1, x0:x1] * 255).astype(np.uint8))
                          .resize((cw, ch), Image.LANCZOS)).astype(np.float32) / 255

    return work(mark), work(dark), work(year)


def bbox(a, thr=0.5):
    ys, xs = np.nonzero(a > thr)
    return xs.min(), ys.min(), xs.max(), ys.max()


# --------------------------------------------------------------------------- brush timing

def catmull_rom(pts, n=24):
    P = np.asarray(pts, np.float64)
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out)


def resample(path, step):
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    L = s[-1]
    q = np.arange(0, L, step)
    return np.stack([np.interp(q, s, path[:, 0]), np.interp(q, s, path[:, 1])], 1), L


def stroke_schedule(spec, t0):
    """Sample every stroke centreline and give each sample its brush time."""
    samples, t = [], t0
    for st in spec:
        t += st["gap"]
        ox, oy = MARK_ORIGIN[0] - CROP[0], MARK_ORIGIN[1] - CROP[1]
        pts = [((x + ox) * WORK, (y + oy) * WORK) for x, y in st["pts"]]
        path, L = resample(catmull_rom(pts), 1.5)
        u = np.linspace(0, 1, len(path))
        # curvature: brush slows in tight turns
        d = np.gradient(path, axis=0)
        ang = np.unwrap(np.arctan2(d[:, 1], d[:, 0]))
        kappa = ndimage.gaussian_filter1d(np.abs(np.gradient(ang)) / 1.5, 6)
        v = 1.0 / (1.0 + 55.0 * kappa)
        if st.get("ease_in"):
            v *= 0.32 + 0.68 * smoothstep(0.0, 0.16, u)   # pressing the brush down
        if st["end"] == "settle":
            v *= 1.0 - 0.45 * smoothstep(0.80, 1.0, u)   # slows into the lift
        elif st["end"] == "flick":
            v *= 1.0 + 1.1 * smoothstep(0.80, 1.0, u)    # fast dry-brush release
        tt = np.concatenate([[0], np.cumsum(1.0 / v[:-1])])
        tt = t + tt / tt[-1] * st["dur"]
        samples.append((path, tt))
        t = tt[-1]
    return samples, t


def time_map(mark, samples):
    """Arrival time of the brush for every pixel of the mark.

    Each pixel belongs to the stroke whose centreline is nearest. Within that
    stroke it takes the earliest brush sample whose footprint covers it, so
    where a stroke crosses itself (crossbar and stem) the first pass lays the
    ink. The footprint is the glyph half-width along the stroke, median-smoothed
    so junction bulges do not leak into neighbouring strokes. Pixels outside
    every footprint (dry-brush flecks) take the nearest sample of their stroke."""
    hgt, wid = mark.shape
    inside = mark > 0.02
    ys, xs = np.nonzero(inside)
    pix = np.stack([xs, ys], 1).astype(np.float64)
    trees = [cKDTree(path) for path, _ in samples]
    dist = np.stack([tr.query(pix)[0] for tr in trees], 1)
    owner = np.argmin(dist, 1)
    edt = ndimage.maximum_filter(ndimage.distance_transform_edt(mark > 0.5), 7)
    T = np.full(mark.shape, 1e9, np.float32)
    for si, (path, tt) in enumerate(samples):
        mine = np.zeros(mark.shape, bool)
        mine[ys[owner == si], xs[owner == si]] = True
        hw = edt[np.clip(path[:, 1].astype(int), 0, hgt - 1), np.clip(path[:, 0].astype(int), 0, wid - 1)]
        hw = ndimage.median_filter(hw, size=41, mode="nearest")
        Ts = np.full(mark.shape, np.inf, np.float32)
        for (x, y), t, h in zip(path, tt, hw):
            r = h * 1.15 + 3
            x0, x1 = int(max(x - r, 0)), int(min(x + r + 1, wid))
            y0, y1 = int(max(y - r, 0)), int(min(y + r + 1, hgt))
            if x0 >= x1 or y0 >= y1:
                continue
            yy, xx = np.mgrid[y0:y1, x0:x1]
            hit = ((xx - x) ** 2 + (yy - y) ** 2 <= r * r) & mine[y0:y1, x0:x1]
            sub = Ts[y0:y1, x0:x1]
            sub[hit] = np.minimum(sub[hit], t)
        miss = mine & ~np.isfinite(Ts)
        if miss.any():
            my, mx = np.nonzero(miss)
            _, idx = trees[si].query(np.stack([mx, my], 1))
            Ts[my, mx] = tt[idx]
        T[mine] = Ts[mine]
    return T


# --------------------------------------------------------------------------- background

def make_background(rng):
    """Pale sea-green field with the quiet texture of old enamel and a soft vignette."""
    def noise(gw, gh, amp):
        n = rng.standard_normal((gh, gw)).astype(np.float32)
        return np.asarray(Image.fromarray(n).resize((W, H), Image.BICUBIC)) * amp
    base = np.ones((H, W, 3), np.float32) * TIN_GREEN
    tex = noise(24, 14, 1.7) + noise(96, 54, 0.9)
    brush = np.asarray(Image.fromarray(rng.standard_normal((40, 640)).astype(np.float32))
                       .resize((W, H), Image.BICUBIC)) * 0.8   # faint horizontal brushing in the enamel
    base += (tex + brush)[..., None]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vign = 1.0 - 0.075 * smoothstep(0.45, 1.45, r)
    glow = np.exp(-(((xx - W / 2) / (W * 0.42)) ** 2 + ((yy - H * 0.45) / (H * 0.5)) ** 2))
    return base * vign[..., None], glow.astype(np.float32)


# --------------------------------------------------------------------------- opening

def opening_frames_from_clip(path, n):
    """Decode the AI tin clip and retime it to n frames."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf",
                          f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    idx = np.linspace(0, len(frames) - 1, n).round().astype(int)
    return lambda i: frames[idx[min(i, n - 1)]].astype(np.float32), None


def opening_from_still(path, rng):
    """Animatic stand-in for the AI tin shot: slow push-in on a tin photo, warm
    light spilling down from the lid edge, spice dust drifting in the light."""
    src = Image.open(path).convert("RGB")
    sw, sh = src.size
    s = max(W / sw, H / sh) * 1.25
    big = src.resize((int(sw * s), int(sh * s)), Image.LANCZOS)
    arr = np.asarray(big).astype(np.float32)
    arr = arr * np.array([1.05, 1.0, 0.92]) * 0.86            # warm, low-key grade
    big = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    bw, bh = big.size
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    beam_shape = np.exp(-((xx - W / 2) / (W * 0.33)) ** 2) * np.exp(-(yy / (H * 0.55)) ** 2)
    vign = 1 - 0.35 * smoothstep(0.35, 1.3, np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2))
    n = 150
    dust = dict(x=rng.uniform(0, W, n), y=rng.uniform(0, H * 0.75, n), r=rng.uniform(0.8, 2.6, n),
                vx=rng.uniform(-8, 14, n), vy=rng.uniform(-22, -6, n), ph=rng.uniform(0, 6.3, n))

    def frame(i):
        t = i / FPS
        # slow push-in, then the camera moves into the light at the top of the frame
        z = 1.0 + 0.07 * ease_io(t / T_BLOOM) + 0.55 * ease_io((t - T_BLOOM) / (T_OPEN_END - T_BLOOM))
        cx, cy = bw / 2, bh / 2 - (bh * 0.18) * ease_io((t - T_BLOOM + 0.6) / 1.1)
        vw = bw / 1.25 / z
        vh = vw * H / W
        box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
        img = np.asarray(big.resize((W, H), Image.BICUBIC, box=box)).astype(np.float32) * vign[..., None]
        light = smoothstep(1.0, 3.0, t) * 0.75 + smoothstep(3.0, T_OPEN_END, t) * 0.25
        beam = beam_shape * light
        img = 255 - (255 - img) * (1 - beam[..., None] * (WARM_LIGHT / 255) * 0.85)  # screen
        lay = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(lay)
        for k in range(n):
            x = (dust["x"][k] + dust["vx"][k] * t + 6 * math.sin(t * 1.3 + dust["ph"][k])) % W
            y = (dust["y"][k] + dust["vy"][k] * t) % (H * 0.8)
            b = beam_shape[int(y), int(x)] * light
            if b < 0.04:
                continue
            r = dust["r"][k]
            dr.ellipse([x - r, y - r, x + r, y + r], fill=int(255 * min(1, b * 1.4)))
        dl = np.asarray(lay.filter(ImageFilter.GaussianBlur(1.1))).astype(np.float32)[..., None] / 255
        img = 255 - (255 - img) * (1 - dl * 0.9 * (WARM_LIGHT / 255))
        return img

    return frame, "PLACEHOLDER  ·  AI tin shot (Nano Banana + Seedance) pending"


# --------------------------------------------------------------------------- render

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logo", required=True, help="logo_final.ai (PDF-compatible Illustrator file)")
    ap.add_argument("--opening-clip", help="AI tin-opening clip (closed tin -> lid open, light spilling)")
    ap.add_argument("--still", help="tin photo for the animatic opening, used when no clip is given")
    ap.add_argument("--logo-only", action="store_true", help="render only the sea-green logo section")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--frames", help="also write these frame numbers as PNG (comma separated) for review")
    args = ap.parse_args()

    rng = np.random.default_rng(1953)
    cache = os.path.join(tempfile.gettempdir(), "ashvena_reveal_cache")
    os.makedirs(cache, exist_ok=True)
    mark, word, year = load_logo_layers(args.logo, cache)
    spec = json.load(open(STROKES))["strokes"]

    t_shift = -T_DRAW + 0.35 if args.logo_only else 0.0
    samples, t_end = stroke_schedule(spec, T_DRAW)
    T = time_map(mark, samples)

    k = FINAL_LOCKUP_H / (bbox(np.maximum(mark, year))[3] - bbox(np.maximum(mark, year))[1])
    mx0, my0, mx1, my1 = bbox(mark)
    lx0, ly0, lx1, ly1 = bbox(np.maximum(np.maximum(mark, year), word))
    c_mark = np.array([(mx0 + mx1) / 2, (my0 + my1) / 2])
    c_lock = np.array([(lx0 + lx1) / 2, (ly0 + ly1) / 2])
    wx0, _, wx1, _ = bbox(word)
    yx0, _, yx1, _ = bbox(year)
    ch, cw = mark.shape
    col_x = np.arange(cw, dtype=np.float32)[None, :]

    bg, glow = make_background(rng)
    if args.logo_only:
        get_open, label = None, None
    elif args.opening_clip:
        get_open, label = opening_frames_from_clip(args.opening_clip, int(T_OPEN_END * FPS) + 1)
    elif args.still:
        get_open, label = opening_from_still(args.still, rng)
    else:
        raise SystemExit("give --opening-clip, --still or --logo-only")

    dur = (DUR + t_shift) if args.logo_only else DUR
    nframes = int(round(dur * FPS))
    want = {int(f) for f in args.frames.split(",")} if args.frames else set()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", args.out], stdin=subprocess.PIPE)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except OSError:
        font = ImageFont.load_default()

    for i in range(nframes):
        t = i / FPS - t_shift
        # ---------------- sea-green field, warmed by the last of the light from the tin
        warm = 0.10 + 0.55 * (1 - smoothstep(T_SETTLE - 0.2, 5.6, t))
        field = bg + glow[..., None] * warm * (WARM_LIGHT - TIN_GREEN) * 0.6

        # ---------------- the mark: brush reveal, motion-blurred over the shutter
        rev = np.zeros_like(mark)
        for sub in (-1 / 3, 0, 1 / 3):
            rev += np.clip((t + sub / FPS - T) / 0.012, 0, 1)
        rev /= 3
        a_mark = mark * rev
        age = np.clip(t - T, 0, None)
        wet = np.exp(-age / 0.28) * (rev > 0)
        ink = BRICK[None, None, :] * (1 - 0.22 * wet[..., None])  # wet ink is darker, then settles

        # ---------------- wordmark and year: soft left-to-right ink wipe and a small rise
        pw = ease_io((t - T_WORD[0]) / (T_WORD[1] - T_WORD[0]))
        py = ease_io((t - T_YEAR[0]) / (T_YEAR[1] - T_YEAR[0]))
        feather = 0.35

        def wipe(p, x0, x1):
            u = (col_x - x0) / (x1 - x0)
            return np.clip((p * (1 + feather) - u) / feather, 0, 1)

        a_word = word * wipe(pw, wx0, wx1) * min(1, pw * 1.6)
        a_year = year * wipe(py, yx0, yx1) * min(1, py * 1.6)
        rise_w, rise_y = (1 - pw) * 14, (1 - py) * 12
        if rise_w > 0.05:
            a_word = ndimage.shift(a_word, (rise_w, 0), order=1)
        if rise_y > 0.05:
            a_year = ndimage.shift(a_year, (rise_y, 0), order=1)

        # premultiplied colour of the lockup layer
        A = np.clip(a_mark + a_word + a_year, 0, 1)
        RGB = ink * a_mark[..., None] + DEEP_LAC * a_word[..., None] + BRICK * a_year[..., None]
        layer = np.dstack([RGB, A[..., None] * 255]).astype(np.float32)

        # ---------------- camera: close on the mark while it is drawn, then ease back to the lockup
        p = ease_io((t - T_PULL[0]) / (T_PULL[1] - T_PULL[0]))
        z = (ZOOM_DRAW + 0.025 * (1 - smoothstep(T_DRAW, T_PULL[0], t))) * (1 - p) + p * (1.0 - 0.012 * smoothstep(T_PULL[1], DUR, t))
        c = c_mark * (1 - p) + c_lock * p
        s = k * z
        # frame = (W/2, H/2) + s * (canvas - c)  ->  canvas = (frame - (W/2,H/2)) / s + c
        aff = (1 / s, 0, c[0] - (W / 2) / s, 0, 1 / s, c[1] - (H / 2) / s)
        ss = 2  # supersample the transform for clean edges
        aff2 = (aff[0] / ss, 0, aff[2], 0, aff[4] / ss, aff[5])
        # premultiplied colour and alpha travel as separate 8-bit images so the
        # filters never re-premultiply them
        rgb_img = Image.fromarray(np.clip(layer[..., :3], 0, 255).astype(np.uint8), "RGB")
        a_img = Image.fromarray(np.clip(layer[..., 3], 0, 255).astype(np.uint8), "L")
        Lrgb, La = [np.asarray(im_.transform((W * ss, H * ss), Image.AFFINE, aff2, Image.BILINEAR)
                               .resize((W, H), Image.BOX)).astype(np.float32) for im_ in (rgb_img, a_img)]
        La = La[..., None] / 255
        logo_frame = field * (1 - La) + Lrgb

        # ---------------- opening and the move into the light
        if get_open is not None and t < T_SETTLE:
            if t < T_OPEN_END:
                o = get_open(i)
                b = float(smoothstep(T_BLOOM + 0.15, T_OPEN_END, t))
                o = 255 - (255 - o) * (1 - 0.7 * b * WARM_LIGHT / 255)   # light blooms over the shot
                frame = o * (1 - b) + WARM_LIGHT * b
            else:
                frame = WARM_LIGHT[None, None, :] * np.ones((H, W, 1), np.float32)
            m = smoothstep(T_OPEN_END - 0.02, T_SETTLE, t)
            frame = frame * (1 - m) + logo_frame * m
        elif get_open is None and t < T_SETTLE:
            m = smoothstep(T_OPEN_END - 0.02, T_SETTLE, t)
            frame = WARM_LIGHT * (1 - m) + logo_frame * m
        else:
            frame = logo_frame

        frame = frame + rng.normal(0, 1.6, (H, W, 1)).astype(np.float32)  # quiet film grain
        out = np.clip(frame, 0, 255).astype(np.uint8)
        if label and t < T_OPEN_END - 0.4:
            im = Image.fromarray(out)
            ImageDraw.Draw(im).text((36, H - 46), label, fill=(255, 255, 255), font=font)
            out = np.asarray(im)
        ff.stdin.write(out.tobytes())
        if i in want:
            Image.fromarray(out).save(os.path.splitext(args.out)[0] + f"_f{i:03d}.png")
    ff.stdin.close()
    ff.wait()
    print(f"wrote {args.out}: {nframes} frames, brush finishes at {t_end:.2f}s")


if __name__ == "__main__":
    main()
