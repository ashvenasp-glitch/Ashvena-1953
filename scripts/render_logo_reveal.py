#!/usr/bin/env python3
"""Ashvena logo reveal: the brush mark rises out of the glowing spice tin.

Timeline (24 fps, 1080x1920, 6.5 s):
  0.0-1.3s  push-in (clip starts at its frame 18), latch lifts, light spills out
  1.3-2.6s  the mark rises out of the opening, backlit, dust drifting up
            (second half of the clip slowed 1.4x with motion interpolation)
  2.6-3.8s  the mark flies toward camera while the light over-exposes the frame
  3.8-4.3s  the flood settles into the background colour
  4.2-5.3s  "Ashvena" wipes in, "1953" follows; hold on the lockup to 6.5s

Usage:
  python3 scripts/render_logo_reveal.py --video tin.mov --logo Ashvena_logo_final.pdf \
      --out motion/ashvena-logo-reveal.mp4 [--bg blue|cream] [--preview 66,100,130]
"""
import argparse
import os
import subprocess

import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageFilter

W, H, FPS = 1080, 1920, 24
TOTAL = 156

BRICK = np.array([148, 21, 40], np.float32) / 255
DEEP_LAC = np.array([53, 7, 15], np.float32) / 255
BACKGROUNDS = {  # (background, mark, wordmark, year) from the logo PDF
    "blue": ((203, 233, 241), BRICK, DEEP_LAC, BRICK),   # primary: brick on dispensary
    "cream": ((252, 228, 205), BRICK, DEEP_LAC, BRICK),  # brick on khadi cream
}
FLOOD_WHITE = np.array([255, 251, 244], np.float32) / 255
GOLD = np.array([255, 196, 110], np.float32) / 255

# Plate geometry (after scaling the 1076x1926 source to 1080 wide and cropping to 1920)
RIM_Y = 644.0            # top edge of the tin's front wall
TIN_CX = 547.0           # horizontal centre of the opening
LIGHT_SRC = (547.0, 560.0)
RAY_CENTRE = (547.0, 780.0)  # inside the tin, so rays fan upward
PLATE_START, PLATE_SLOW_FROM, PLATE_SLOW = 18, 60, 1.4

# Logo layout: page-1 lockup in PDF points, mapped onto the frame
PX_PER_PT = 1.36          # wordmark ~620 px wide
LOCKUP_PT_CENTRE = (380.0, 469.65)
LOCKUP_FRAME_CENTRE = (540.0, 880.0)

# Key frames
F_RISE0, F_RISE1 = 32, 62
F_FLY1 = 88
F_FLOOD0, F_FLOOD1 = 70, 92
F_SETTLE1 = 104
F_WORD0, F_WORD1 = 100, 120
F_YEAR0, F_YEAR1 = 110, 126


def clamp01(x):
    return np.clip(x, 0.0, 1.0)


def prog(f, a, b):
    return float(clamp01((f - a) / (b - a)))


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_out_quad(t):
    return 1 - (1 - t) ** 2


def ease_in_out_cubic(t):
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def smoothstep(e0, e1, x):
    t = clamp01((x - e0) / (e1 - e0))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


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


def lockup_pos(pt):
    return (LOCKUP_FRAME_CENTRE[0] + (pt[0] - LOCKUP_PT_CENTRE[0]) * PX_PER_PT,
            LOCKUP_FRAME_CENTRE[1] + (pt[1] - LOCKUP_PT_CENTRE[1]) * PX_PER_PT)


# ---------------------------------------------------------------- helpers

def blur(arr, radius, down=2):
    """Gaussian blur of a float HxW or HxWx3 array (done at reduced resolution)."""
    h, w = arr.shape[:2]
    small = (w // down, h // down)
    chans = [arr] if arr.ndim == 2 else [arr[..., i] for i in range(arr.shape[2])]
    out = []
    for ch in chans:
        im = Image.fromarray(np.clip(ch * 255, 0, 255).astype(np.uint8))
        im = im.resize(small, Image.BILINEAR).filter(ImageFilter.GaussianBlur(radius / down))
        out.append(np.asarray(im.resize((w, h), Image.BILINEAR), np.float32) / 255)
    return out[0] if arr.ndim == 2 else np.stack(out, -1)


def god_rays(source, centre, length=0.42, samples=28, down=4):
    """Radial streaks from `source` (HxW float) pointing away from `centre`."""
    h, w = source.shape
    sw, sh = w // down, h // down
    src = Image.fromarray(source.astype(np.float32), "F").resize((sw, sh), Image.BILINEAR)
    cx, cy = centre[0] / down, centre[1] / down
    acc = np.zeros((sh, sw), np.float32)
    wsum = 0.0
    for i in range(samples):
        t = 1.0 - length * i / (samples - 1)
        wgt = (1 - i / samples) ** 1.5
        im = src.transform((sw, sh), Image.AFFINE,
                           (t, 0, cx * (1 - t), 0, t, cy * (1 - t)), resample=Image.BILINEAR)
        acc += np.asarray(im, np.float32) * wgt
        wsum += wgt
    acc /= wsum
    return np.asarray(Image.fromarray(acc, "F").resize((w, h), Image.BILINEAR), np.float32)


class Dust:
    """Warm dust motes drifting up out of the tin."""

    def __init__(self, seed=1953, n=420):
        rng = np.random.default_rng(seed)
        self.t0 = rng.uniform(F_RISE0 - 6, F_FLOOD1 - 4, n)
        self.life = rng.uniform(26, 60, n)
        self.x0 = rng.normal(TIN_CX, 120, n).clip(260, 830)
        self.y0 = rng.uniform(560, RIM_Y - 4, n)
        self.vy = -rng.uniform(1.2, 4.2, n)
        self.vx = rng.normal(0, 0.9, n)
        self.wob = rng.uniform(4, 22, n)
        self.wfreq = rng.uniform(0.04, 0.12, n)
        self.phase = rng.uniform(0, 2 * np.pi, n)
        bokeh = rng.random(n) < 0.12
        self.sigma = np.where(bokeh, rng.uniform(4, 8, n), rng.uniform(0.7, 2.0, n))
        self.amp = np.where(bokeh, rng.uniform(0.10, 0.25, n), rng.uniform(0.35, 1.0, n))
        self.sprites = {}

    def sprite(self, sigma):
        key = round(sigma * 2) / 2
        if key not in self.sprites:
            r = int(np.ceil(key * 3))
            yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
            self.sprites[key] = np.exp(-(xx ** 2 + yy ** 2) / (2 * key ** 2)).astype(np.float32)
        return self.sprites[key]

    def render(self, f):
        layer = np.zeros((H, W), np.float32)
        age = f - self.t0
        live = (age > 0) & (age < self.life)
        for i in np.nonzero(live)[0]:
            a = age[i]
            x = self.x0[i] + self.vx[i] * a + self.wob[i] * np.sin(self.wfreq[i] * a + self.phase[i])
            y = self.y0[i] + self.vy[i] * a - 0.012 * a * a
            lifefade = min(1.0, a / 8) * min(1.0, (self.life[i] - a) / 20)
            flick = 0.75 + 0.25 * np.sin(0.7 * a + self.phase[i] * 3)
            spr = self.sprite(self.sigma[i])
            r = spr.shape[0] // 2
            xi, yi = int(round(x)), int(round(y))
            x0, x1, y0, y1 = xi - r, xi + r + 1, yi - r, yi + r + 1
            if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H:
                continue
            sx0, sy0 = max(0, -x0), max(0, -y0)
            sx1 = spr.shape[1] - max(0, x1 - W)
            sy1 = spr.shape[0] - max(0, y1 - H)
            layer[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] += \
                spr[sy0:sy1, sx0:sx1] * self.amp[i] * lifefade * flick
        return layer


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
        self.dust = Dust()
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.dist = np.hypot(xx - LIGHT_SRC[0], yy - LIGHT_SRC[1])
        self.above_rim = smoothstep(RIM_Y + 2, RIM_Y - 2, yy)
        self.rise_start = None

    def mark_state(self, f):
        """Scale (px/pt), centre and rotation of the mark at frame f."""
        final_c = lockup_pos(self.mark.centre_pt)
        mh = self.mark.size_pt[1]
        s_r0, s_r1 = 0.40 * PX_PER_PT, 0.54 * PX_PER_PT
        cx_rise = TIN_CX + 8
        if f <= F_RISE1:
            t = ease_out_quad(prog(f, F_RISE0, F_RISE1))
            s = lerp(s_r0, s_r1, t)
            y_start = RIM_Y + mh * s_r0 / 2 + 6
            y_end = RIM_Y - 18 - mh * s_r1 / 2
            return s, (cx_rise, lerp(y_start, y_end, t)), lerp(-6.0, -2.0, t)
        t = ease_in_out_cubic(prog(f, F_RISE1, F_FLY1))
        y_end = RIM_Y - 18 - mh * s_r1 / 2
        s = lerp(s_r1, PX_PER_PT, t)
        c = (lerp(cx_rise, final_c[0], t), lerp(y_end, final_c[1], t))
        return s, c, lerp(-2.0, 0.0, t)

    def frame(self, f, plate):
        img = plate.copy()

        # ---- mark geometry
        mark_a = np.zeros((H, W), np.float32)
        if f >= F_RISE0:
            s, c, rot = self.mark_state(f)
            hold = 1 + 0.012 * prog(f, F_FLY1, TOTAL)       # slow breathe on the end card
            if hold > 1:
                lc = LOCKUP_FRAME_CENTRE
                c = (lc[0] + (c[0] - lc[0]) * hold, lc[1] + (c[1] - lc[1]) * hold)
            mark_a = self.mark.place(s * hold, c, rot)
            if f <= F_RISE1:
                mark_a *= self.above_rim                     # still inside the tin

        # ---- light: swell in the opening, god-rays, flood
        swell = smoothstep(F_RISE0 - 8, F_RISE0 + 8, f) * (1 - prog(f, F_FLOOD1, F_FLOOD1 + 1))
        flood_t = prog(f, F_FLOOD0, F_FLOOD1)
        if f < F_FLOOD1 + 1:
            lum = img.mean(-1)
            bright = clamp01((lum - 0.62) / 0.3) * self.above_rim
            if swell > 0:
                # rays: the mark blocks light, so it carves shadows into them
                src = bright * (1 - clamp01(mark_a * 1.4))
                rays = god_rays(src, RAY_CENTRE)
                ray_amt = (0.55 + 0.9 * ease_in_out_cubic(flood_t)) * swell
                glow = blur(bright, 60, down=4)
                light = clamp01(rays * ray_amt + glow * 0.35 * swell)
                img = 1 - (1 - img) * (1 - light[..., None] * GOLD)    # screen

            # backlit halo behind the rising mark
            if f >= F_RISE0:
                halo = blur(mark_a, 28, down=2) * 0.4 * (1 - flood_t)
                img = 1 - (1 - img) * (1 - halo[..., None] * GOLD)

            # flood: the light over-exposes the frame, nearest the opening first
            if flood_t > 0:
                g_peak = 1 + 60 * flood_t ** 2.2
                radial = np.exp(-self.dist / lerp(260, 1500, flood_t))
                g = (1 + (g_peak - 1) * (0.25 + 0.75 * radial))[..., None]
                bloom = blur(img, lerp(30, 120, flood_t), down=4)
                x = clamp01(1 - (1 - img) * (1 - bloom * 0.8 * flood_t))
                img = x * g / (1 + x * (g - 1))
                img = lerp(img, FLOOD_WHITE, smoothstep(0.72, 1.0, flood_t))
        else:
            img = np.broadcast_to(FLOOD_WHITE, img.shape).copy()

        # flood settles into the brand background
        settle = ease_in_out_cubic(prog(f, F_FLOOD1, F_SETTLE1))
        if f >= F_FLOOD1:
            img = lerp(img, self.c_bg, settle)

        # ---- dust in front of the light, gone once the flood takes over
        if F_RISE0 - 6 <= f < F_FLOOD1:
            dust = self.dust.render(f) * (1 - flood_t) * smoothstep(F_RISE0 - 8, F_RISE0 + 4, f)
            img = 1 - (1 - img) * (1 - clamp01(dust)[..., None] * GOLD)

        # ---- the mark, with light wrapping its edges while it's backlit
        if mark_a.any():
            wrap_amt = 0.55 * (1 - prog(f, F_FLOOD0, F_FLOOD0 + 14))
            colour = np.broadcast_to(self.c_mark, img.shape)
            if wrap_amt > 0:
                edge = clamp01((1 - blur(mark_a, 3, down=1)) * 2.5) * mark_a
                behind = blur(img, 8, down=2)
                colour = colour + (behind - colour) * (edge * wrap_amt)[..., None]
            img = lerp(img, colour, mark_a[..., None])

        # ---- wordmark and year
        hold = 1 + 0.012 * prog(f, F_FLY1, TOTAL)
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
