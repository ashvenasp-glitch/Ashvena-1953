# Ashvena: Logo Reveal (9:16)

`ashvena-logo-reveal_9x16.mp4`: 1080 × 1920, 24 fps, 10.5 s, H.264, no audio.

| Time | Shot |
|---|---|
| 0.0 – 3.5 s | The antique sea-green spice tin (`src/spice-tin_push-in.mov`) fades up from black, the lid opens and golden light spills out. |
| 2.5 – 4.1 s | The camera pushes toward the glowing lid, the bloom builds, motes rise, and warm light fills the frame. |
| 4.1 – 4.9 s | The light settles into a sea-green enamel plate (the tin's colour) with drifting spice dust. |
| 4.55 – 7.5 s | The crimson brush **અ** paints itself in the storyboard order: upper bowl, then lower bowl, rising diagonal, top loop, stem and dry-brush tail flick. |
| 7.35 – 8.6 s | **ASHVENA** (Cinzel) rises in letter by letter, then gold rules and **EST. 1953** (Montserrat). |
| 8.75 – 10.5 s | A soft enamel sheen sweeps across the lockup, then the lockup holds. |

## Files
- `ashvena-logo-reveal_9x16.mp4` is the final video.
- `ashvena-logo-reveal_poster.png` is the end frame (thumbnail or cover).
- `ashvena-brush-mark.png` is the cleaned brush mark: crimson `#8B091A` on transparency, 2676 × 2124. It was lifted from the last storyboard frame and upscaled 6×.
- `src/` holds the source clip and the two brush storyboards.

## Regenerate
```
pip install numpy pillow scipy opencv-python-headless
python3 motion/logo-reveal/render_logo_reveal.py             # video + poster + brush mark
python3 motion/logo-reveal/render_logo_reveal.py --preview   # contact sheet only
```
Timings, colours and the brush centre lines (`PATH_A`, `PATH_B`) are constants at the top of the script.
