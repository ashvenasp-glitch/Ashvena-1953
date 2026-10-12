# Ashvena 1953: Logo Reveal

A 15-second vertical reveal (1080 × 1920, 30 fps) for Reels, Shorts and Stories.

| Frame | Time | What happens | Made with |
|---|---|---|---|
| 1 · Ribbon cut | 0–3 s | Brass scissors snip the organza ribbon, and it falls off the tin | Kling 2.5 image-to-video from `source/tin-ribbon.jpg` (Magnific) |
| 2 · Tin opens | 3–6 s | The lid lifts, warm gold light and sparkles rise from the tin | same clip |
| 3 · Sparkles build the logo | 6–11 s | Sparkles stream out of the tin and arc over. The brush mark अ, then *Ashvena*, then *1953*, build in gold while the room darkens and defocuses | `scripts/render_logo_reveal.py` |
| 4 · Final logo | 11–15 s | A circle of Dispensary blue opens out from the logo. The gold turns Brick and Deep Lac, a light glint passes, and the logo holds | same script |

Frames 3 and 4 are built from the vector paths in `source/ashvena-logo-final.pdf`, so the logo matches the master artwork exactly.

**Colours:** Dispensary `#CBE9F1`, Brick `#941528`, Deep Lac `#35070F`.

## Files
- `ashvena-logo-reveal.mp4` is the finished video.
- `source/tin-ribbon.jpg` is the start frame, cropped to 9:16.
- `source/kling-ribbon-tin-open.mp4` is the 10 s Kling 2.5 clip (frames 1–2).
- `source/ashvena-logo-final.pdf` is the logo master.

## Re-render
```
pip install numpy pillow scipy cairosvg      # also needs ffmpeg and poppler-utils
python3 scripts/render_logo_reveal.py                # writes ashvena-logo-reveal.mp4
python3 scripts/render_logo_reveal.py --still 9.5    # a single preview frame
```
Timings, logo size and colours are constants at the top of the script. Without the Kling clip in `source/`, the tin photo stands in for frames 1–2.

The video has no sound. Add music or a sparkle sound effect in your editor.
