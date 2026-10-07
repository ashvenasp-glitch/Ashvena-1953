# Ashvena 1953: logo reveal ("revealed from the tin")

An 8-second, 1920×1080, 30 fps logo reveal. The old tin opens, warm light spills
out, the camera moves into the light, and the अ draws itself in crimson. The
wordmark settles in beneath it.

| Time | What happens | Source |
|---|---|---|
| 0.00–1.00 | Closed tin, close-up, soft warm light, slow push-in | AI shot: Nano Banana keyframes animated with Seedance |
| 1.00–3.25 | The lid lifts slowly. Warm light spills out with a faint drift of spice dust | AI shot |
| 3.25–4.25 | The camera pushes into the light. The light settles into pale sea-green sampled from the tin | `render_logo_reveal.py` |
| 3.95–6.10 | The अ draws itself stroke by stroke in calligraphic order (below) | `render_logo_reveal.py`, from the vector master |
| 5.95–7.05 | The camera eases back to the full lockup. "Ashvena" and then "1953" ink in from left to right | `render_logo_reveal.py` |
| 7.05–8.00 | Hold | |

## Files

- `ashvena-1953_logo-reveal_logo-section.mp4`: the finished logo section, starting from the light. This part is final.
- `ashvena-1953_logo-reveal_animatic.mp4`: the full 8 s timing. The opening is a **placeholder** built from a tin photo (push-in, light from above, spice dust) and is labelled as such. It gets replaced by the AI tin shot.
- `a_strokes.json`: stroke centrelines, order, pauses and durations for the अ.
- `../scripts/render_logo_reveal.py`: the renderer and compositor.

## How the अ is drawn

The mark is never redrawn. The exact vector mark from `logo_final.ai` is
revealed along hand-placed brush centrelines, in this order:

1. **Upper hook** (0.62 s): enters at the dry tail on the lower left, sweeps up and over the top, and curls down into the centre. The brush slows into the lift.
2. Brush lifts (0.10 s).
3. **Lower bowl** (0.48 s): presses in at the right, runs down and around the bowl, and rises on the left...
4. ...then flows without lifting into the **crossbar, top loop, stem and tail** (0.95 s): it climbs to the top loop, comes down the stem and releases in a quick dry-brush flick.

Brush speed varies along each stroke. It starts slowly as the brush presses
down, slows in tight turns and accelerates through the final flick. Fresh ink
is slightly darker and settles to Brick (#941528) over about 0.3 s. Where the
stem crosses the crossbar, the first pass lays the ink.

Colours: the mark and "1953" use Brick #941528, and "Ashvena" uses Deep Lac #35070F. The
pale sea-green field is #CFE4DD, the hue of the tin enamel lifted to a clean
field. It carries faint enamel texture, vignette and grain.

## The AI tin shot (pending)

Nano Banana and Seedance run on Magnific. From the build session, Magnific's
upload host (`ak-data.magnific.com`) and output CDN (`pikaso.cdnpk.net`) were
blocked by the environment's network policy. Allowing those two hosts unblocks
the step. These are the planned calls:

**Keyframe A, closed tin.** Nano Banana Pro (`imagen-nano-banana-2`), 16:9, 2k.
References: the full photo of the tin (for form) and the crimson-lettered close-up (for lettering).

> Photorealistic cinematic still. The exact antique spice tin from the first reference: same tall rectangular body, same flat hinged lid with the bent-wire hasp and diamond hasp plate, same dents, chipped edges and rust spots, in pale sea-green enamel. On its front face, hand-brushed crimson Urdu lettering copied exactly from the second reference (لاجونتی), same strokes, centred. No paper label, no marker writing, no other text. The tin is closed, standing on an old dark teak counter in a traditional pansari shop, background soft out-of-focus darkness of wooden drawers. Soft warm tungsten key light from the left, gentle rim light, shallow depth of field, 50 mm at eye level, front-on, tin centred and filling about 70% of frame height, slight film grain, nostalgic and quiet. No hands, no people.

**Keyframe B, lid open.** Nano Banana Pro, with keyframe A as its reference.

> Same photograph, same camera, framing and lighting. Only change: the hinged lid is open, swung up and back about 70° so its underside shows. Warm golden light glows from inside the tin and spills over the rim, lighting the lid's underside; a faint drift of fine golden spice dust floats up through the light. Surroundings slightly darker so the glow reads. Lettering unchanged.

**Animation.** Seedance 2.5 (`bytedance-seedance-pro-2.5`), with A as the start frame and B as the end frame, 4 s, 1080p, 16:9.

> Slow cinematic push-in on an antique sea-green spice tin on a teak counter. For the first second only the slow push-in. Then the hinged lid lifts open by itself, slowly and smoothly; warm golden light swells from inside and spills over the rim; a faint drift of spice dust rises and glints in the light. The camera keeps gently pushing in toward the glowing opening. Calm, nostalgic, hand-made. Lettering stays exactly as is. No people, no hands, no fast motion, no cuts.

**Final composite**

```
python3 scripts/render_logo_reveal.py --logo motion/source/logo_final.ai \
    --opening-clip tin_open.mp4 -o motion/ashvena-1953_logo-reveal.mp4
```

The clip is retimed to 0–3.75 s, then blooms into the light and the logo section.

## Re-rendering the parts that exist now

```
python3 scripts/render_logo_reveal.py --logo motion/source/logo_final.ai --logo-only \
    -o motion/ashvena-1953_logo-reveal_logo-section.mp4
python3 scripts/render_logo_reveal.py --logo motion/source/logo_final.ai --still <tin photo> \
    -o motion/ashvena-1953_logo-reveal_animatic.mp4
```

Requirements: Python 3 with numpy, Pillow and scipy, plus `pdftocairo` (poppler) and `ffmpeg`.
