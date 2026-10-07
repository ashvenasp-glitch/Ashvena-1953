#!/usr/bin/env python3
"""Ashvena logo reveal: golden sparkles rise out of the spice tin, gather into the
brush mark, and fuse into the solid logo as it zooms toward camera.

Timeline (24 fps, 1080x1920, 9.25 s):
  0.0-1.25s  push-in (clip from its frame 12), latch lifts, light spills out
  1.25-4.0s  golden sparkles stream out of the opening and gather into the mark,
             written left to right; the tin's glow dims as its light leaves
             (second half of the clip slowed 2.5x with motion interpolation)
  4.0-4.7s   the sparkle mark hovers and glitters
  4.7-6.2s   it zooms toward camera; the sparkles melt together into the solid
             mark, gold cooling to brick, while the light over-exposes the frame
  6.2-6.8s   the flood settles into the background colour
  6.75-8.0s  "Ashvena" wipes in, "1953" follows; hold on the lockup to 9.25 s

Usage:
  python3 scripts/render_logo_reveal.py --video tin.mov --logo Ashvena_logo_final.pdf \
      --out motion/ashvena-logo-reveal.mp4 [--bg blue|cream] [--preview 60,100,140]
"""
import argparse
import os
import subprocess

import numpy as np
import pypdfium2 as pdfium
from PIL import Image

W, H, FPS = 1080, 1920, 24
TOTAL = 222

BRICK = np.array([148, 21, 40], np.float32) / 255
DEEP_LAC = np.array([53, 7, 15], np.float32) / 255
BACKGROUNDS = {  # (background, mark, wordmark, year) from the logo PDF
    "blue": ((203, 233, 241), BRICK, DEEP_LAC, BRICK),   # primary: brick on dispensary
    "cream": ((252, 228, 205), BRICK, DEEP_LAC, BRICK),  # brick on khadi cream
}
FLOOD_WHITE = np.array([255, 251, 244], np.float32) / 255
SPARK_CORE = np.array([255, 248, 228], np.float32) / 255
SPARK_GLOW = np.array([255, 196, 104], np.float32) / 255
SPARK_WIDE = np.array([255, 146, 52], np.float32) / 255
FUSE_GOLD = np.array([236, 178, 84], np.float32) / 255
EMBER_TINT = np.array([0.62, 0.52, 0.42], np.float32)   # the tin's glow once dimmed

# Plate geometry (after scaling the 1076x1926 source to 1080 wide and cropping to 1920)
RIM_Y = 644.0            # top edge of the tin's front wall
TIN_CX = 547.0           # horizontal centre of the opening
LIGHT_SRC = (547.0, 560.0)
PLATE_START, PLATE_SLOW_FROM, PLATE_SLOW = 12, 60, 2.5

# Logo layout: page-1 lockup in PDF points, mapped onto the frame
PX_PER_PT = 1.36          # wordmark ~620 px wide
LOCKUP_PT_CENTRE = (380.0, 469.65)
LOCKUP_FRAME_CENTRE = (540.0, 880.0)
HOVER_SCALE = (0.53, 0.56)            # x PX_PER_PT, while the sparkles gather
HOVER_CENTRE_Y = (428.0, 412.0)       # in front of the open lid

# Key frames
F_EMIT0 = 30              # first sparkles leave the tin
F_ZOOM0, F_ZOOM1 = 112, 148
F_FUSE0, F_FUSE1 = 116, 144
F_COOL0, F_COOL1 = 124, 150
F_FLOOD0, F_FLOOD1 = 122, 148
F_SETTLE1 = 164
F_WORD0, F_WORD1 = 162, 184
F_YEAR0, F_YEAR1 = 174, 192


def clamp01(x):
    return np.clip(x, 0.0, 1.0)


def prog(f, a, b):
    return float(clamp01((f - a) / (b - a)))


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_in_out_cubic(t):
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def smoothstep(e0, e1, x):
    t = clamp01((x - e0) / (e1 - e0))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def screen(img, light_rgb):
    return 1 - (1 - img) * (1 - clamp01(light_rgb))


# ---------------------------------------------------------------- logo layers

class Layer:
    """One logo element rendered from the PDF, kept as an alpha pyramid."""

    RENDER_SCALE = 6.0

    def __init__(self, pdf_path, obj_index):
        pdf = pdfium.PdfDocument(pdf_path)
        page = pdf[0]
        page_h = page.get_size()[1]
        objs = list(page.get_objects())
        left, bottom, right, top = objs[obj_index].get_bounds()
        for i, o in enumerate(objs):
            if i != obj_index:
                page.remove_obj(o)
        page.gen_content()
        s = self.RENDER_SCALE
        img = page.render(scale=s, fill_color=(0, 0, 0, 0)).to_pil().convert("RGBA")
        alpha = img.getchannel("A")
        pad = 4
        box = (int(left * s) - pad, int((page_h - top) * s) - pad,
               int(np.ceil(right * s)) + pad, int(np.ceil((page_h - bottom) * s)) + pad)
        alpha = alpha.crop(box)
        self.alpha = alpha
        self.origin_pt = (box[0] / s, box[1] / s)          # top-left of crop, in points
        self.centre_pt = ((left + right) / 2, page_h - (top + bottom) / 2)
        self.size_pt = (right - left, top - bottom)
        self.levels = []                                   # (px per pt, image)
        level, scale = alpha, s
        while scale > 0.25:
            self.levels.append((scale, level))
            scale /= np.sqrt(2)
            level = alpha.resize((max(1, round(alpha.width * scale / s)),
                                  max(1, round(alpha.height * scale / s))), Image.LANCZOS)

    def place(self, px_per_pt, centre, rot_deg=0.0):
        """Full-frame float alpha with the layer centre at `centre` (frame px)."""
        lvl_scale, img = self.levels[0]
        for sc, im in self.levels:
            if sc >= px_per_pt:
                lvl_scale, img = sc, im
        k = px_per_pt / lvl_scale
        th = np.radians(rot_deg)
        cos, sin = np.cos(th), np.sin(th)
        uc = (self.centre_pt[0] - self.origin_pt[0]) * lvl_scale
        vc = (self.centre_pt[1] - self.origin_pt[1]) * lvl_scale
        cx, cy = centre
        a, b = cos / k, sin / k
        d, e = -sin / k, cos / k
        c = uc - (a * cx + b * cy)
        f = vc - (d * cx + e * cy)
        out = img.transform((W, H), Image.AFFINE, (a, b, c, d, e, f), resample=Image.BICUBIC)
        return np.asarray(out, np.float32) / 255

    def sample_points(self, n, rng):
        """n points inside the shape (alpha-weighted), in points relative to its centre."""
        a = np.asarray(self.alpha, np.float64).ravel()
        idx = rng.choice(a.size, size=n, replace=False, p=a / a.sum())
        py, px = np.divmod(idx, self.alpha.width)
        s = self.RENDER_SCALE
        u = (px + rng.random(n)) / s + self.origin_pt[0] - self.centre_pt[0]
        v = (py + rng.random(n)) / s + self.origin_pt[1] - self.centre_pt[1]
        return u.astype(np.float32), v.astype(np.float32)

    def area_pt2(self):
        return float(np.asarray(self.alpha, np.float64).sum() / 255 / self.RENDER_SCALE ** 2)


def lockup_pos(pt):
    return (LOCKUP_FRAME_CENTRE[0] + (pt[0] - LOCKUP_PT_CENTRE[0]) * PX_PER_PT,
            LOCKUP_FRAME_CENTRE[1] + (pt[1] - LOCKUP_PT_CENTRE[1]) * PX_PER_PT)


# ---------------------------------------------------------------- image helpers

def _box(a, r, axis):
    """Mean filter of width 2r+1 along one axis, edges clamped."""
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float32)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return (hi - lo) / (2 * r + 1)


def gblur(a, sigma, down=1, axes=(0, 1)):
    """Approximate Gaussian blur of a float HxW array (three box passes)."""
    h, w = a.shape
    small = a if down == 1 else a.reshape(h // down, down, w // down, down).mean((1, 3))
    s = sigma / down
    r = max(1, int(round((np.sqrt(4 * s * s + 1) - 1) / 2)))
    for _ in range(3):
        for ax in axes:
            small = _box(small, r, ax)
    if down == 1:
        return small
    return np.asarray(Image.fromarray(small.astype(np.float32), "F")
                      .resize((w, h), Image.BILINEAR), np.float32)


def binomial3(a):
    """[1 2 1]/4 blur in both directions: turns splatted points into soft dots."""
    p = np.pad(a, 1, mode="constant")
    p = (p[:-2] + 2 * p[1:-1] + p[2:]) / 4
    return (p[:, :-2] + 2 * p[:, 1:-1] + p[:, 2:]) / 4


def splat(xs, ys, ws):
    """Bilinear-splat weighted points into an HxW float image."""
    x0 = np.floor(xs).astype(np.int64)
    y0 = np.floor(ys).astype(np.int64)
    fx, fy = xs - x0, ys - y0
    idx, wts = [], []
    for dx, dy, wt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)),
                       (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xi, yi = x0 + dx, y0 + dy
        ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
        idx.append(yi[ok] * W + xi[ok])
        wts.append((ws * wt)[ok])
    out = np.bincount(np.concatenate(idx), np.concatenate(wts), minlength=W * H)
    return out.reshape(H, W).astype(np.float32)


# ---------------------------------------------------------------- sparkles

class Sparkles:
    """Golden sparkles that fly out of the tin and settle onto points of the mark."""

    def __init__(self, mark, n=3600, seed=1953):
        rng = np.random.default_rng(seed)
        self.n = n
        self.tu, self.tv = mark.sample_points(n, rng)
        # written left to right: particles bound for the left of the mark launch first
        rank = np.argsort(np.argsort(self.tu + rng.normal(0, 12, n))) / (n - 1)
        self.t0 = F_EMIT0 + 34 * rank + rng.uniform(0, 10, n)
        self.dur = rng.uniform(26, 38, n)
        self.sx = rng.normal(TIN_CX, 110, n).clip(275, 815).astype(np.float32)
        self.sy = (RIM_Y + rng.uniform(15, 60, n)).astype(np.float32)
        self.c1 = np.stack([rng.normal(0, 50, n), -rng.uniform(230, 430, n)])   # up out of the tin
        self.c2 = np.stack([rng.normal(0, 110, n), -rng.uniform(50, 170, n)])  # land from above
        big = rng.random(n) < 0.05
        self.base = np.where(big, rng.uniform(1.4, 2.0, n), rng.uniform(0.45, 1.0, n))
        self.omega = rng.uniform(0.15, 0.45, n)
        self.phase = rng.uniform(0, 2 * np.pi, n)
        self.glint = rng.random(n) < 0.08
        self.jit = rng.uniform(0, 2 * np.pi, (2, n))
        self.stray = rng.random(n) < 0.12
        ang = rng.normal(0, 0.5, n)
        self.stray_turn = np.stack([np.cos(ang), np.sin(ang)])
        self.stray_speed = rng.uniform(1.2, 3.6, n)

    def positions(self, f, state):
        """World positions, weights and launch progress of every sparkle at time f."""
        s, (cx, cy), rot = state
        th = np.radians(rot)
        cos, sin = np.cos(th), np.sin(th)
        jx = 0.6 * np.sin(0.21 * f + self.jit[0])
        jy = 0.6 * np.sin(0.17 * f + self.jit[1])
        dx = s * (cos * self.tu - sin * self.tv)
        dy = s * (sin * self.tu + cos * self.tv)
        tx, ty = cx + dx + jx, cy + dy + jy

        u = clamp01((f - self.t0) / self.dur)
        e = 1 - (1 - u) ** 3
        b0, b1, b2, b3 = (1 - e) ** 3, 3 * (1 - e) ** 2 * e, 3 * (1 - e) * e ** 2, e ** 3
        x = b0 * self.sx + b1 * (self.sx + self.c1[0]) + b2 * (tx + self.c2[0]) + b3 * tx
        y = b0 * self.sy + b1 * (self.sy + self.c1[1]) + b2 * (ty + self.c2[1]) + b3 * ty

        # during the zoom some sparkles break away and stream past the camera
        z = max(0.0, f - F_ZOOM0)
        if z > 0:
            norm = np.hypot(dx, dy) + 1e-3
            ux, uy = dx / norm, dy / norm
            vx = ux * self.stray_turn[0] - uy * self.stray_turn[1]
            vy = ux * self.stray_turn[1] + uy * self.stray_turn[0]
            d = self.stray_speed * z ** 1.5 * self.stray
            x, y = x + vx * d, y + vy * d

        tw = (0.5 + 0.5 * np.sin(self.omega * f + self.phase)) ** 4
        w = self.base * (0.45 + 0.75 * tw) * smoothstep(0.0, 0.08, u) * (u > 0)
        w = w * np.where(u < 1, 1.3, 1.0)                       # brighter in flight
        if f < F_ZOOM0:                                          # hidden while inside the tin
            w = w * smoothstep(RIM_Y + 3, RIM_Y - 3, y)
        fuse = smoothstep(F_FUSE0, F_FUSE0 + 22, f)
        w = w * np.where(self.stray, 1 - prog(f, F_ZOOM0, F_ZOOM0 + 34), 1 - fuse)
        return x, y, w, u, tw

    def render(self, f, state_at):
        """Light (HxWx3) added by the sparkles, plus the unweighted point density."""
        xs, ys, ws = [], [], []
        for j in range(4):                                      # motion blur: 4 sub-frames
            x, y, w, u, tw = self.positions(f - 0.4 * j / 3, state_at(f - 0.4 * j / 3))
            xs.append(x)
            ys.append(y)
            ws.append(w / 4)
        x, y, w = np.concatenate(xs), np.concatenate(ys), np.concatenate(ws)
        pts = splat(x, y, w)
        core = binomial3(pts) * 3.2
        glow = gblur(pts, 3.5, down=2) * 4.5
        wide = gblur(pts, 26, down=4) * 3.5

        # four-point star glints on the brightest twinkles
        x0, y0, w0, u0, tw0 = self.positions(f, state_at(f))
        g = w0 * self.glint * clamp01((tw0 - 0.75) / 0.25)
        light = core[..., None] * SPARK_CORE + glow[..., None] * SPARK_GLOW + \
            wide[..., None] * SPARK_WIDE
        if g.any():
            gp = splat(x0, y0, g)
            star = gblur(gp, 9, axes=(1,)) + gblur(gp, 9, axes=(0,))
            light += (star * 9.0)[..., None] * SPARK_CORE
        settled = (u0 >= 1) & ~self.stray
        return light, (x0[settled], y0[settled])


class Dust:
    """Loose gold motes that drift up out of the tin and never join the mark."""

    def __init__(self, seed=7, n=260):
        rng = np.random.default_rng(seed)
        self.t0 = rng.uniform(F_EMIT0 - 4, F_FLOOD1 - 4, n)
        self.life = rng.uniform(30, 70, n)
        self.x0 = rng.normal(TIN_CX, 130, n).clip(260, 830)
        self.y0 = rng.uniform(560, RIM_Y - 4, n)
        self.vy = -rng.uniform(1.0, 3.6, n)
        self.vx = rng.normal(0, 0.8, n)
        self.wob = rng.uniform(4, 22, n)
        self.wfreq = rng.uniform(0.04, 0.12, n)
        self.phase = rng.uniform(0, 2 * np.pi, n)
        self.amp = rng.uniform(0.3, 0.9, n)

    def render(self, f):
        a = f - self.t0
        live = (a > 0) & (a < self.life)
        x = self.x0 + self.vx * a + self.wob * np.sin(self.wfreq * a + self.phase)
        y = self.y0 + self.vy * a - 0.01 * a * a
        fade = clamp01(a / 8) * clamp01((self.life - a) / 20)
        w = self.amp * fade * live * (0.7 + 0.3 * np.sin(0.7 * a + self.phase * 3))
        pts = splat(x, y, w)
        return binomial3(pts) * 2.2 + gblur(pts, 4, down=2) * 3.0


# ---------------------------------------------------------------- plate

def plate_frames(video, cache=None):
    """Yield float RGB frames: the clip from PLATE_START, its tail slowed with interpolation."""
    src = cache if cache and os.path.exists(cache) else video
    if src == video:
        graph = (
            f"[0:v]scale=1080:1933:flags=lanczos,crop=1080:1920:0:6,split=2[a][b];"
            f"[a]trim=start_frame={PLATE_START}:end_frame={PLATE_SLOW_FROM},setpts=PTS-STARTPTS[s1];"
            f"[b]trim=start_frame={PLATE_SLOW_FROM},setpts=(PTS-STARTPTS)*{PLATE_SLOW},"
            f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1[s2];"
            f"[s1][s2]concat=n=2:v=1[out]")
        cmd = ["ffmpeg", "-v", "error", "-i", video, "-filter_complex", graph, "-map", "[out]"]
    else:
        cmd = ["ffmpeg", "-v", "error", "-i", src]
    cmd += ["-f", "rawvideo", "-pix_fmt", "rgb48le", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = W * H * 6
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        try:
            yield np.frombuffer(buf, np.uint16).reshape(H, W, 3).astype(np.float32) / 65535
        except GeneratorExit:
            proc.kill()
            raise
    proc.wait()


# ---------------------------------------------------------------- compositor

class Reveal:
    def __init__(self, logo_pdf, bg):
        self.mark = Layer(logo_pdf, 1)
        self.word = Layer(logo_pdf, 2)
        self.year = Layer(logo_pdf, 3)
        bg_rgb, self.c_mark, self.c_word, self.c_year = BACKGROUNDS[bg]
        self.c_bg = np.array(bg_rgb, np.float32) / 255
        self.sparkles = Sparkles(self.mark)
        self.dust = Dust()
        self.mark_area = self.mark.area_pt2()
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.dist = np.hypot(xx - LIGHT_SRC[0], yy - LIGHT_SRC[1])
        self.above_rim = smoothstep(RIM_Y + 2, RIM_Y - 2, yy)

    def hold(self, f):
        return 1 + 0.012 * prog(f, F_ZOOM1, TOTAL)     # slow breathe on the end card

    def mark_state(self, f):
        """Scale (px/pt), centre and rotation of the mark at frame f."""
        th = prog(f, F_EMIT0, F_ZOOM0)
        s_h = lerp(*HOVER_SCALE, th) * PX_PER_PT
        c_h = (TIN_CX + 8, lerp(*HOVER_CENTRE_Y, th))
        r_h = lerp(-3.0, -1.5, th)
        if f <= F_ZOOM0:
            return s_h, c_h, r_h
        t = ease_in_out_cubic(prog(f, F_ZOOM0, F_ZOOM1))
        final_c = lockup_pos(self.mark.centre_pt)
        k = self.hold(f)
        lc = LOCKUP_FRAME_CENTRE
        c = (lerp(c_h[0], final_c[0], t), lerp(c_h[1], final_c[1], t))
        c = (lc[0] + (c[0] - lc[0]) * k, lc[1] + (c[1] - lc[1]) * k)
        return lerp(s_h, PX_PER_PT, t) * k, c, lerp(r_h, 0.0, t)

    def frame(self, f, plate):
        img = plate.copy()
        flood_t = prog(f, F_FLOOD0, F_FLOOD1)

        if f < F_FLOOD1 + 1:
            # the tin's glow dims as its light leaves as sparkles
            dim = smoothstep(F_EMIT0, F_EMIT0 + 44, f) * (1 - flood_t)
            if dim > 0:
                bright = gblur(clamp01((img.mean(-1) - 0.45) / 0.3), 20, down=4) * self.above_rim
                img = img * (1 - dim * (0.18 + 0.82 * bright[..., None] * (1 - EMBER_TINT)))

            # flood: the light over-exposes the frame, nearest the opening first
            if flood_t > 0:
                g_peak = 1 + 60 * flood_t ** 2.2
                radial = np.exp(-self.dist / lerp(260, 1500, flood_t))
                g = (1 + (g_peak - 1) * (0.25 + 0.75 * radial))[..., None]
                bloom = np.stack([gblur(img[..., i], lerp(30, 120, flood_t), down=4)
                                  for i in range(3)], -1)
                x = screen(img, bloom * 0.8 * flood_t)
                img = x * g / (1 + x * (g - 1))
                img = lerp(img, FLOOD_WHITE, smoothstep(0.72, 1.0, flood_t))
        else:
            img = np.broadcast_to(FLOOD_WHITE, img.shape).copy()

        # flood settles into the brand background
        settle = ease_in_out_cubic(prog(f, F_FLOOD1, F_SETTLE1))
        if f >= F_FLOOD1:
            img = lerp(img, self.c_bg, settle)

        if F_EMIT0 - 4 <= f < F_FLOOD1:
            dust = self.dust.render(f) * (1 - flood_t)
            img = screen(img, dust[..., None] * SPARK_GLOW)

        # ---- the solid mark: sparkles melt together into it during the zoom
        state = self.mark_state(f)
        fuse = prog(f, F_FUSE0, F_FUSE1)
        sparkles_on = F_EMIT0 <= f < F_FUSE1 + 2
        if sparkles_on:
            light, (sx, sy) = self.sparkles.render(f, self.mark_state)
        if fuse > 0:
            s, c, rot = state
            mark_a = self.mark.place(s, c, rot)
            if fuse < 1:
                count = splat(sx, sy, np.ones_like(sx))
                sigma = lerp(1.5, 9.0, ease_in_out_cubic(fuse)) * s / (HOVER_SCALE[1] * PX_PER_PT)
                expected = len(sx) / (self.mark_area * s * s)
                dens = gblur(count, sigma, down=2 if sigma > 4 else 1) / expected
                meta = smoothstep(0.5, 0.95, dens * lerp(0.35, 2.4, fuse))
                fill = mark_a * np.maximum(meta, smoothstep(0.65, 1.0, fuse))
            else:
                fill = mark_a
            cool = ease_in_out_cubic(prog(f, F_COOL0, F_COOL1))
            if cool < 1:
                halo = gblur(fill, 12, down=2) * 0.6 * (1 - cool)
                img = screen(img, halo[..., None] * SPARK_GLOW)
            colour = lerp(FUSE_GOLD, self.c_mark, cool)
            img = lerp(img, np.broadcast_to(colour, img.shape), fill[..., None])
        if sparkles_on:
            img = screen(img, light)

        # ---- wordmark and year
        hold = self.hold(f)
        for layer, colour, a0, a1, rise in ((self.word, self.c_word, F_WORD0, F_WORD1, 16),
                                            (self.year, self.c_year, F_YEAR0, F_YEAR1, 12)):
            t = prog(f, a0, a1)
            if t <= 0:
                continue
            te = ease_out_cubic(t)
            cx, cy = lockup_pos(layer.centre_pt)
            lc = LOCKUP_FRAME_CENTRE
            cx, cy = lc[0] + (cx - lc[0]) * hold, lc[1] + (cy - lc[1]) * hold
            a = layer.place(PX_PER_PT * hold, (cx, cy + rise * (1 - te)))
            if layer is self.word:
                half = layer.size_pt[0] * PX_PER_PT * hold / 2
                soft = 140.0
                front = lerp(cx - half - soft, cx + half + soft, ease_in_out_cubic(t))
                xs = np.arange(W, dtype=np.float32)
                a = a * clamp01((front - xs) / soft)[None, :]
            else:
                a = a * te
            img = lerp(img, np.broadcast_to(colour, img.shape), a[..., None])

        return clamp01(img)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--video", required=True)
    ap.add_argument("--logo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bg", default="blue", choices=sorted(BACKGROUNDS))
    ap.add_argument("--plate-cache", help="pre-rendered plate (skips interpolation)")
    ap.add_argument("--preview", help="comma-separated frame numbers to save as PNG instead")
    args = ap.parse_args()

    reveal = Reveal(args.logo, args.bg)
    previews = {int(x) for x in args.preview.split(",")} if args.preview else None

    enc = None
    if previews is None:
        enc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
             "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p",
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
             "-movflags", "+faststart", args.out], stdin=subprocess.PIPE)

    plates = plate_frames(args.video, args.plate_cache)
    plate = None
    for f in range(TOTAL):
        nxt = next(plates, None)
        if nxt is not None:
            plate = nxt
        if previews is not None and f not in previews:
            continue
        out = (reveal.frame(f, plate) * 255 + 0.5).astype(np.uint8)
        if previews is not None:
            Image.fromarray(out).save(f"{args.out}_{f:03d}.png")
            if f == max(previews):
                break
        else:
            enc.stdin.write(out.tobytes())
        if f % 24 == 0:
            print(f"frame {f}/{TOTAL}", flush=True)
    plates.close()
    if enc:
        enc.stdin.close()
        enc.wait()


if __name__ == "__main__":
    main()
