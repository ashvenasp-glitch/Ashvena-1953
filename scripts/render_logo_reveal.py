#!/usr/bin/env python3
"""Ashvena 1953 - logo-reveal film ("revealed from the tin"), ~8 s, 1920x1080
(or 1080x1920 for Instagram Reels with --aspect 9:16).

  0.00-3.75  opening: the old tin opens and light spills out. Either the AI
             tin clip (--opening-clip, Nano Banana keyframes animated with
             Seedance) or, without one, an animatic built from a tin photo
             (--still) so timing can be reviewed.
  3.25-4.25  the camera pushes into the light; warm light settles into pale
             sea-green sampled from the tin.
  3.95-6.10  the अ draws itself in crimson in one continuous brush stroke,
             moving like a writing hand (a gentle press-in, slower in tight
             turns and broad strokes, a quick dry-brush flick on the tail).
             Wet ink settles; where the brush crosses ink it laid earlier,
             it re-wets it.
  5.95-7.05  the camera eases back to the full lockup; "Ashvena" and "1953"
             are revealed beneath the mark.
  7.05-8.00  hold.

The mark, wordmark and year are taken from the vector master (logo_final.ai,
page 1) and are never redrawn or approximated - only revealed.

Usage:
  python3 scripts/render_logo_reveal.py --logo logo_final.ai --still tin.jpg -o out.mp4
  python3 scripts/render_logo_reveal.py --logo logo_final.ai --opening-clip tin_ai.mp4 -o out.mp4
  python3 scripts/render_logo_reveal.py --logo logo_final.ai --opening-clip tin_ai_9x16.mp4 --aspect 9:16 -o out.mp4
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
SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920)}

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
#
# The brush is moved the way a hand writes. Its speed along the centreline
# follows the two-thirds power law of human drawing movements (tangential
# speed ~ curvature^(-1/3), Lacquaniti, Terzuolo & Viviani 1983), computed on
# the smoother path of the hand rather than on the ink outline, with a
# saturation for near-straight runs. Where the brush is pressed into a broad
# stroke it moves more slowly, and it moves quickly through light hairlines.
# The press-in at the first touch and the release at the flick are
# minimum-jerk speed ramps (Flash & Hogan 1985). Brush time is the integral of
# ds / v along arc length, so the speed never jumps.

DS = 1.0                 # centreline sample spacing, work px
KIN = dict(              # defaults; a stroke may override any of them under "kinematics"
    beta=1 / 3,          # power-law exponent: v ~ (curvature + 1/r_sat)^-beta
    r_sat=260.0,         # radius (work px) beyond which a run counts as straight
    v_floor=0.30,        # slowest speed, as a fraction of the straight-run speed
    sigma_geom=4.0,      # smoothing of the brush centreline, work px
    sigma_hand=16.0,     # smoothing of the hand's path for curvature, work px
    sigma_speed=50.0,    # smoothing of the speed profile along the stroke, work px
    pressure=0.5,        # v ~ width^-pressure: a broad, pressed stroke moves slower
    press=0.30,          # speed at the first touch, as a fraction of the cruise speed
    press_dur=0.20,      # minimum-jerk press-in ramp, s
    release=0.35,        # extra speed gained through the flick
    release_dur=0.22,    # minimum-jerk release ramp, s
)
WET_DECAY = 0.28         # s, fresh ink settles from dark to Brick
WET_DARK = 0.22          # fresh ink is this much darker
SHUTTER = 1.0            # exposure per frame, in frame intervals (360-degree shutter)
TIP_RAMP = 0.010         # s, softness of the brush tip as it passes a pixel
FRONT_ROUND = 0.45       # the edges of the brush trail its centre by this many half-widths


def min_jerk(x):
    """Minimum-jerk transition 10x^3 - 15x^4 + 6x^5 on [0, 1]: zero velocity and
    acceleration at both ends."""
    x = np.clip(x, 0.0, 1.0)
    return x * x * x * (10 - 15 * x + 6 * x * x)


def catmull_rom(pts, n=48, alpha=0.5):
    """Centripetal Catmull-Rom spline through the points (no cusps or overshoot
    where the points bunch up, as in the curl's rounded turn)."""
    P = np.asarray(pts, np.float64)
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        k1 = np.linalg.norm(p1 - p0) ** alpha
        k2 = k1 + np.linalg.norm(p2 - p1) ** alpha
        k3 = k2 + np.linalg.norm(p3 - p2) ** alpha
        t = np.linspace(k1, k2, n, endpoint=False)[:, None]
        a1 = ((k1 - t) * p0 + t * p1) / k1
        a2 = ((k2 - t) * p1 + (t - k1) * p2) / (k2 - k1)
        a3 = ((k3 - t) * p2 + (t - k2) * p3) / (k3 - k2)
        b1 = ((k2 - t) * a1 + t * a2) / k2
        b2 = ((k3 - t) * a2 + (t - k1) * a3) / (k3 - k1)
        out.append(((k2 - t) * b1 + (t - k1) * b2) / (k2 - k1))
    out.append(P[-2][None])
    return np.vstack(out)


def resample(path, step):
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    L = s[-1]
    q = np.append(np.arange(0, L, step), L)
    return np.stack([np.interp(q, s, path[:, 0]), np.interp(q, s, path[:, 1])], 1), s


def smooth_open(P, sigma):
    """Gaussian smoothing of an open polyline sampled at even spacing. The ends
    are padded by point reflection, so the end points and end tangents stay."""
    if sigma <= 0:
        return P.copy()
    n = min(int(3 * sigma) + 1, len(P) - 1)
    pre = 2 * P[0] - P[1:n + 1][::-1]
    post = 2 * P[-1] - P[-n - 1:-1][::-1]
    Q = ndimage.gaussian_filter1d(np.vstack([pre, P, post]), sigma, axis=0, mode="nearest")
    return Q[n:len(Q) - n]


def curvature(P):
    d1 = np.gradient(P, DS, axis=0)
    d2 = np.gradient(d1, DS, axis=0)
    num = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0])
    return num / np.maximum(np.linalg.norm(d1, axis=1), 1e-9) ** 3


def stroke_schedule(spec, t0):
    """Sample every stroke centreline and give each sample its brush time.

    Returns one dict per stroke: the centreline (work px), the brush time and
    speed at every sample, the tangents and normals, and the overlap passes
    (index ranges along the centreline; time_map lets the earlier pass lay the
    ink where two passes of the brush cross)."""
    samples, t = [], t0
    ox, oy = MARK_ORIGIN[0] - CROP[0], MARK_ORIGIN[1] - CROP[1]
    for st in spec:
        k = dict(KIN, **st.get("kinematics", {}))
        pts = [((x + ox) * WORK, (y + oy) * WORK) for x, y in st["pts"]]
        n_seg = 48
        raw = catmull_rom(pts, n_seg)
        path, s_raw = resample(raw, DS)
        geom = smooth_open(path, k["sigma_geom"])          # where the brush tip runs
        hand = smooth_open(path, k["sigma_hand"])          # the smoother movement of the hand
        kap = curvature(hand)
        # brush width (pressure) along the stroke, from the widths at the points
        knot_s = s_raw[np.arange(len(pts)) * n_seg]
        s_path = np.arange(len(geom)) * DS
        width = np.interp(s_path, knot_s, np.asarray(st["w"], np.float64) * WORK)
        width = ndimage.gaussian_filter1d(width, 20 / DS, mode="nearest")
        # two-thirds power law, saturating on near-straight runs
        v = (kap + 1.0 / k["r_sat"]) ** (-k["beta"])
        v_max = k["r_sat"] ** k["beta"]
        v = np.maximum(v, k["v_floor"] * v_max)
        # a pressed (broad) brush moves more slowly than a light one
        v = v * np.clip(width / np.median(width), 0.6, 1.6) ** (-k["pressure"])
        v = np.exp(ndimage.gaussian_filter1d(np.log(v), k["sigma_speed"] / DS, mode="nearest"))
        # minimum-jerk press-in and release, in brush time (fixed point: the ramps
        # depend on time, which depends on the ramped speed)
        dur = st["dur"]
        g = np.ones_like(v)
        for _ in range(6):
            vv = v * g
            tt = np.concatenate([[0], np.cumsum(2 * DS / (vv[1:] + vv[:-1]))])
            tt *= dur / tt[-1]
            g = np.ones_like(v)
            if st.get("ease_in", True):
                g *= k["press"] + (1 - k["press"]) * min_jerk(tt / k["press_dur"])
            if st.get("end") == "flick":
                g *= 1 + k["release"] * min_jerk((tt - (dur - k["release_dur"])) / k["release_dur"])
            elif st.get("end") == "settle":
                g *= 1 - 0.4 * min_jerk((tt - (dur - k["release_dur"])) / k["release_dur"])
        vv = v * g
        tt = np.concatenate([[0], np.cumsum(2 * DS / (vv[1:] + vv[:-1]))])
        scale = dur / tt[-1]
        tt *= scale
        t += st.get("gap", 0.0)
        tan = np.gradient(geom, axis=0)
        tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-9)
        nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
        # overlap passes: break the centreline at the listed control points
        breaks = [0] + [int(round(knot_s[i] / DS)) for i in st.get("pass_breaks", [])] + [len(geom)]
        samples.append(dict(path=geom, t=t + tt, v=vv / scale, tan=tan, nrm=nrm, kappa=kap, hw=width / 2,
                            passes=list(zip(breaks[:-1], breaks[1:]))))
        t = t + tt[-1]
    return samples, t


def _project(pix, P, a, b, tree):
    """Nearest point of the centreline samples a..b-1 for every pixel, refined
    onto the polyline: the fractional sample index and the distance."""
    d, j = tree.query(pix)
    j = j + a
    best_f = j.astype(np.float64)
    best_d = d
    for lo in (j - 1, j):
        hi = lo + 1
        ok = (lo >= a) & (hi <= b - 1)
        lo_, hi_ = np.clip(lo, a, b - 1), np.clip(hi, a, b - 1)
        e = P[hi_] - P[lo_]
        ee = np.maximum((e * e).sum(1), 1e-12)
        u = np.clip(((pix - P[lo_]) * e).sum(1) / ee, 0, 1)
        q = P[lo_] + u[:, None] * e
        dd = np.linalg.norm(pix - q, axis=1)
        better = ok & (dd < best_d)
        best_d = np.where(better, dd, best_d)
        best_f = np.where(better, lo_ + u, best_f)
    return best_f, best_d


def _through_ink(ink, a, b, n=16):
    """True where the straight line from a to b stays on ink."""
    hgt, wid = ink.shape
    ok = np.ones(len(a), bool)
    for k in range(1, n):
        q = a + (b - a) * (k / n)
        ok &= ink[np.clip(np.rint(q[:, 1]).astype(int), 0, hgt - 1),
                  np.clip(np.rint(q[:, 0]).astype(int), 0, wid - 1)]
    return ok


_REVEAL_CACHE = {}   # id(T) -> the time map's companions (re-wet times, ink pixels)


def time_map(mark, samples):
    """Arrival time of the brush for every pixel of the mark.

    Every pixel is projected onto the nearest point of each overlap pass of the
    centreline, so the leading edge runs across the stroke like the edge of a
    brush, slightly rounded (the edges trail the centre). A pass covers the
    pixels within its band (half the brush width on each side of the
    centreline) that it reaches through ink. Where two passes cover a pixel
    (the crossings), the earlier pass lays the ink and the later one re-wets
    it (kept for mark_reveal as a second time). Pixels outside every band
    (junction fillets, corners, the dry-brush streaks of the tail) take the
    pass whose band is nearest, kept in step with the nearest banded ink."""
    inside = mark > 0
    ys, xs = np.nonzero(inside)
    pix = np.stack([xs, ys], 1).astype(np.float64)
    ink = mark > 0.3
    big = np.float64(1e9)
    cand_t, cand_ex, cand_in = [], [], []
    for smp in samples:
        P, tt, v, N = smp["path"], smp["t"], smp["v"], smp["nrm"]
        hw_s = smp["hw"]
        n_all = len(P)
        for a, b in smp["passes"]:
            tree = cKDTree(P[a:b])
            f, _ = _project(pix, P, a, b, tree)
            i0 = np.clip(np.floor(f).astype(int), 0, n_all - 1)
            i1 = np.clip(i0 + 1, 0, n_all - 1)
            w = f - i0
            foot = P[i0] * (1 - w[:, None]) + P[i1] * w[:, None]
            nn = N[i0] * (1 - w[:, None]) + N[i1] * w[:, None]
            off = pix - foot
            n_off = (off * nn).sum(1)
            tan_off = (off * (smp["tan"][i0])).sum(1)
            # a foot at the end of a pass that is not the end of the stroke only
            # counts for pixels beside it, not for those ahead of or behind it
            valid = np.ones(len(pix), bool)
            if a > 0:
                valid &= ~((i0 <= a) & (tan_off < -1.5))
            if b < n_all:
                valid &= ~((i0 >= b - 2) & (tan_off > 1.5))
            hw = np.interp(f, np.arange(n_all), hw_s)
            t_here = np.interp(f, np.arange(n_all), tt)
            v_here = np.interp(f, np.arange(n_all), v)
            rel = np.minimum(np.abs(n_off) / hw, 1.0)
            t_here = t_here + FRONT_ROUND * rel * rel * hw / v_here
            excess = np.abs(n_off) - (1.05 * hw + 1.0)
            # the bristles only reach a pixel through ink: a pass does not cover
            # ink on the far side of bare paper (a notch, a gap between strokes)
            sees = _through_ink(ink, foot, pix)
            cand_t.append(t_here)
            cand_ex.append(np.where(valid, np.maximum(excess, 0) + np.where(sees, 0.0, 40.0), big))
            cand_in.append(valid & sees & (excess <= 0))
    cand_t, cand_ex, cand_in = np.array(cand_t), np.array(cand_ex), np.array(cand_in)
    t_in = np.where(cand_in, cand_t, np.inf)
    any_in = cand_in.any(0)
    first = np.argmin(t_in, 0)
    near = np.argmin(cand_ex, 0)
    pick = np.where(any_in, first, near)
    cols = np.arange(len(pix))
    Tv = cand_t[pick, cols]
    # ink outside every band (junction fillets, corners, flecks) is laid with the
    # nearest banded ink: no later or earlier than the brush needs to get there
    if (~any_in).any() and any_in.any():
        inb = np.zeros(mark.shape, bool)
        inb[ys[any_in], xs[any_in]] = True
        Tb = np.zeros(mark.shape, np.float64)
        Tb[ys[any_in], xs[any_in]] = Tv[any_in]
        dist, (iy, ix) = ndimage.distance_transform_edt(~inb, return_indices=True)
        out = ~any_in
        oy, ox_ = ys[out], xs[out]
        v_med = np.median(np.concatenate([smp["v"] for smp in samples]))
        slack = dist[oy, ox_] / v_med
        tq = Tb[iy[oy, ox_], ix[oy, ox_]]
        Tv[out] = np.clip(Tv[out], tq - slack, tq + slack)
    # re-wet: a later pass of the brush over ink that is already laid
    last = np.max(np.where(cand_in, cand_t, -np.inf), 0)
    T2v = np.where(any_in & (last > Tv + 0.06), last, np.inf)
    T = np.full(mark.shape, 1e9, np.float32)
    T[ys, xs] = Tv
    T2 = np.full(mark.shape, np.inf, np.float32)
    T2[ys, xs] = T2v
    _REVEAL_CACHE.clear()
    _REVEAL_CACHE[id(T)] = dict(T=T, T2=T2, idx=np.flatnonzero(inside))
    return T


def _shutter(x, ramp, shutter):
    """Brush coverage of a pixel averaged over the shutter: the tip covers it
    with a linear ramp of length `ramp` that starts at x = 0, and the frame
    integrates it over an exposure of length `shutter` centred on x."""
    def G(u):  # integral of clip(u, 0, 1)
        return np.where(u <= 0, 0.0, np.where(u >= 1, u - 0.5, 0.5 * u * u))
    lo, hi = (x - shutter / 2) / ramp, (x + shutter / 2) / ramp
    return np.where(lo >= 1, 1.0, np.clip((G(hi) - G(lo)) * ramp / shutter, 0.0, 1.0))


def mark_reveal(mark, T, t):
    """Alpha and colour of the mark at time t, from the brush arrival-time map T."""
    c = _REVEAL_CACHE.get(id(T))
    if c is None or c["T"] is not T:
        c = dict(T=T, T2=None, idx=np.flatnonzero(T < 1e8))
        _REVEAL_CACHE[id(T)] = c
    idx = c["idx"]
    Tv = T.ravel()[idx].astype(np.float64)
    sh = SHUTTER / FPS
    rev = _shutter(t - Tv, TIP_RAMP, sh)
    # freshly laid ink is darkest right at the brush tip and settles with age
    wet = np.where(rev > 0, np.exp(-np.clip(t - Tv, 0, None) / WET_DECAY), 0.0)
    if c["T2"] is not None:
        T2v = c["T2"].ravel()[idx].astype(np.float64)
        has = np.isfinite(T2v)
        if has.any():
            x2 = t - T2v[has]
            wet2 = _shutter(x2, TIP_RAMP, sh) * np.exp(-np.clip(x2, 0, None) / WET_DECAY)
            wet[has] = np.maximum(wet[has], wet2)
    alpha = np.zeros(mark.size, np.float32)
    alpha[idx] = mark.ravel()[idx] * rev
    wet_full = np.zeros(mark.size, np.float32)
    wet_full[idx] = wet
    ink = BRICK[None, None, :] * (1 - WET_DARK * wet_full.reshape(mark.shape)[..., None])
    return alpha.reshape(mark.shape), ink


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
    # the glow of the open tin: brightness-weighted centre of the hottest pixels in the last frame
    luma = frames[-1].astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    hot = np.clip(luma - np.percentile(luma, 97), 0, None)
    ys, xs = np.mgrid[0:H, 0:W]
    glow = np.array([(xs * hot).sum(), (ys * hot).sum()]) / hot.sum()

    def frame(i):
        f = frames[idx[min(i, n - 1)]]
        # the camera moves into the light: eased push toward the glowing opening under the bloom
        p = ease_io((i / FPS - T_BLOOM) / (T_OPEN_END - T_BLOOM))
        if p <= 0:
            return f.astype(np.float32)
        z = 1.0 + 1.4 * p
        cx, cy = np.array([W / 2, H / 2]) * (1 - p) + glow * p
        vw, vh = W / z, H / z
        cx, cy = min(max(cx, vw / 2), W - vw / 2), min(max(cy, vh / 2), H - vh / 2)
        box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
        return np.asarray(Image.fromarray(f).resize((W, H), Image.BICUBIC, box=box)).astype(np.float32)

    return frame, None


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
        cx = min(max(cx, vw / 2), bw - vw / 2)
        cy = min(max(cy, vh / 2), bh - vh / 2)
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
    ap.add_argument("--aspect", choices=sorted(SIZES), default="16:9",
                    help="16:9 (1920x1080) or 9:16 (1080x1920, Instagram Reels)")
    args = ap.parse_args()
    global W, H
    W, H = SIZES[args.aspect]

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
        a_mark, ink = mark_reveal(mark, T, t)

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
