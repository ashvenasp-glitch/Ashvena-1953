# Ashvena: Motion

## Logo reveal: spice tin (`ashvena-logo-reveal_tin.mp4`)

9.25 s, 1080 × 1920 (9:16), 24 fps, H.264. No audio.

| Time | What happens |
|---|---|
| 0.0–1.25 s | Push-in on the antique sea-green tin. The latch lifts and light spills out. |
| 1.25–4.0 s | Golden sparkles stream out of the opening and gather into the **अ** mark, written left to right. The tin's glow dims to amber as its light leaves. |
| 4.0–4.7 s | The sparkle mark hovers and glitters. |
| 4.7–6.2 s | The mark zooms toward camera. The sparkles melt together into the solid mark (gold → copper → brick) while the light over-exposes the frame. |
| 6.2–6.8 s | The light settles into Dispensary Blue. |
| 6.75–9.25 s | "Ashvena" wipes in and "1953" follows. The video holds on the final lockup. |

The end frame is the primary lockup from page 1 of `brand/Ashvena_logo_final.pdf`, in the same colours (Brick, Deep Lac, Dispensary Blue) and the same proportions. The sparkles are sampled from the mark's own outline, so they form its exact shape.

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
- `--preview 70,120,221` saves those frames as PNGs instead of rendering the video.
