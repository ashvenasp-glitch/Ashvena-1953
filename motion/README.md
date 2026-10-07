# Ashvena: Motion

## Logo reveal: spice tin (`ashvena-logo-reveal_tin.mp4`)

6.5 s, 1080 × 1920 (9:16), 24 fps, H.264. No audio.

| Time | What happens |
|---|---|
| 0.0–1.3 s | Push-in on the antique sea-green tin. The latch lifts and light spills out. |
| 1.3–2.6 s | The brick **अ** mark rises out of the opening, lit from behind, while dust drifts up. |
| 2.6–3.8 s | The mark flies toward camera, and the tin's light over-exposes the frame. |
| 3.8–4.3 s | The light settles into Dispensary Blue. |
| 4.2–6.5 s | "Ashvena" wipes in and "1953" follows. The video holds on the final lockup. |

The end frame is the primary lockup from page 1 of `brand/Ashvena_logo_final.pdf`, in the same colours (Brick, Deep Lac, Dispensary Blue) and the same proportions.

Source clip: `source/spice-tin-pushin.mov` (Seedance, 4 s).

## Regenerate
```
pip install numpy pillow pypdfium2      # plus ffmpeg on PATH
python3 scripts/render_logo_reveal.py \
    --video motion/source/spice-tin-pushin.mov \
    --logo brand/Ashvena_logo_final.pdf \
    --out motion/ashvena-logo-reveal_tin.mp4
```
- `--bg cream` ends on Khadi Cream instead of Dispensary Blue.
- `--preview 40,72,155` saves those frames as PNGs instead of rendering the video.
