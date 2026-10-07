# Ashvena 1953: logo reveal ("revealed from the tin")

An 8-second, 30 fps logo reveal. The final cut is a 1080×1920 (9:16) Instagram Reel;
the renderer also renders 1920×1080 (16:9). The old tin opens, warm light spills
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

- `ashvena-1953_logo-reveal.mp4`: **the final film**, 1080×1920 (9:16) for Instagram Reels, 8 s, no audio. AI tin shot + logo section.
- `source/tin/keyframe-a_closed.png`, `source/tin/keyframe-b_open.png`: the Nano Banana Pro keyframes (9:16).
- `source/tin/tin_open_seedance.mp4`: the raw Seedance clip (1076×1926, 24 fps, 4 s, HEVC, untouched original).
- `ashvena-1953_logo-reveal_logo-section.mp4`: the logo section in 16:9, 4.27 s, starting from the light.
- `ashvena-1953_logo-reveal_end-frame.png`: the closing lockup frame.
- `ashvena-1953_logo-reveal_animatic.mp4`: the full 8 s timing. The opening is a **placeholder** built from a tin photo (push-in, light from above, spice dust) and is labelled as such. Superseded by the final film; kept for reference.
- `a_strokes.json`: stroke centrelines, order, pauses and durations for the अ.
- `../scripts/render_logo_reveal.py`: the renderer and compositor.

## How the अ is drawn

The mark is never redrawn. The exact vector mark from `logo_final.ai` is
revealed along a hand-placed brush centreline as **one continuous stroke**,
in the order the client sketched: the अ is written like a "3" and then the stem.

1. Up from the dry tail at the lower left, over the top of the hook and down into the curl.
2. A rounded turn at the bottom of the curl, then out to the right through the joint.
3. Down the bowl's right side, round the bottom and up its left side.
4. Along the crossbar, up into the top loop, down the stem and out in a dry-brush flick.

The brush moves like a writing hand. Its speed follows the two-thirds power law
of handwriting: it slows smoothly in tight curves and runs faster on straight
stretches. It moves more slowly where the stroke is broad and quicker through
thin hairlines, and it eases in and out on the press-in and the final flick. Each pixel is
revealed when the brush tip passes it, so the leading edge is a clean line
across the stroke, with a closed-form 360° shutter blur for fluid 30 fps
playback. Where the stroke crosses ink it has already laid (the joint and the
stem over the crossbar), the first pass keeps the ink and the brush re-wets it
as it passes, so the movement never visibly stops. Fresh ink is darkest at the
tip and settles to Brick (#941528). It draws from 3.95 s to 6.10 s.

Colours: the mark and "1953" use Brick #941528, and "Ashvena" uses Deep Lac #35070F. The
pale sea-green field is #CFE4DD, the hue of the tin enamel lifted to a clean
field. It carries faint enamel texture, vignette and grain.

## The AI tin shot (done)

Generated on Magnific, vertical for the Reel. The prompts below are the ones
used; the vertical framing changed "filling about 70% of frame height" to
"centred horizontally and filling about 60% of frame height, with dark space
above the lid", and keyframe B and the animation got small additions noted
after each prompt.

| Step | Model | Settings | Credits |
|---|---|---|---|
| Keyframe A | Nano Banana Pro (`imagen-nano-banana-2`) | 9:16, 2k, 2 variants; refs: tin photo, then lettering close-up. Picked the variant with the hasp and diamond plate | 150 |
| Keyframe B | Nano Banana Pro | 9:16, 2k, 1 variant; ref: keyframe A | 75 |
| Animation | Seedance 2.5 (`bytedance-seedance-pro-2.5`) | start A, end B, 4 s, 1080p, 9:16, no sound effects | 3,160 |

**Keyframe A, closed tin.** Nano Banana Pro (`imagen-nano-banana-2`), 2k.
References: the full photo of the tin (for form) and the crimson-lettered close-up (for lettering).

> Photorealistic cinematic still. The exact antique spice tin from the first reference: same tall rectangular body, same flat hinged lid with the bent-wire hasp and diamond hasp plate, same dents, chipped edges and rust spots, in pale sea-green enamel. On its front face, hand-brushed crimson Urdu lettering copied exactly from the second reference (لاجونتی), same strokes, centred. No paper label, no marker writing, no other text. The tin is closed, standing on an old dark teak counter in a traditional pansari shop, background soft out-of-focus darkness of wooden drawers. Soft warm tungsten key light from the left, gentle rim light, shallow depth of field, 50 mm at eye level, front-on, tin centred and filling about 70% of frame height, slight film grain, nostalgic and quiet. No hands, no people.

**Keyframe B, lid open.** Nano Banana Pro, with keyframe A as its reference.

> Same photograph, same camera, framing and lighting. Only change: the hinged lid is open, swung up and back about 70° so its underside shows. Warm golden light glows from inside the tin and spills over the rim, lighting the lid's underside; a faint drift of fine golden spice dust floats up through the light. Surroundings slightly darker so the glow reads. Lettering unchanged.

(As run, it also said: "the wire hasp hanging free", "Tin body, dents, rust and the crimson lettering unchanged, in the same position. No hands, no people.")

**Animation.** Seedance 2.5 (`bytedance-seedance-pro-2.5`), with A as the start frame and B as the end frame, 4 s, 1080p, 9:16.

> Slow cinematic push-in on an antique sea-green spice tin on a teak counter. For the first second only the slow push-in. Then the hinged lid lifts open by itself, slowly and smoothly; warm golden light swells from inside and spills over the rim; a faint drift of spice dust rises and glints in the light. The camera keeps gently pushing in toward the glowing opening. Calm, nostalgic, hand-made. Lettering stays exactly as is. No people, no hands, no fast motion, no cuts.

(As run, it also said "the wire hasp slips free" and "The tin body keeps its exact shape".)

**Final composite**

```
python3 scripts/render_logo_reveal.py --logo motion/source/logo_final.ai \
    --opening-clip motion/source/tin/tin_open_seedance.mp4 --aspect 9:16 -o master.mp4
ffmpeg -i master.mp4 -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p \
    -movflags +faststart motion/ashvena-1953_logo-reveal.mp4
```

The clip is retimed to 0–3.75 s, then blooms into the light and the logo section.
Over 3.25–3.75 s the renderer pushes in (up to 2.4×) toward the brightest
region of the clip's last frame, the glowing lid, so the bloom reads as the
camera moving into the light rather than a crossfade. In 9:16 the lockup is 624×700 px, centred, inside the Reels safe area.

## Re-rendering the parts that exist now

```
python3 scripts/render_logo_reveal.py --logo motion/source/logo_final.ai --still <tin photo> \
    -o animatic_master.mp4            # CRF 15 master, about 9 min on 4 cores
ffmpeg -i animatic_master.mp4 -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p \
    -movflags +faststart motion/ashvena-1953_logo-reveal_animatic.mp4
ffmpeg -i animatic_master.mp4 -vf "trim=start_frame=112,setpts=PTS-STARTPTS" -c:v libx264 \
    -preset slow -crf 19 -pix_fmt yuv420p -movflags +faststart \
    motion/ashvena-1953_logo-reveal_logo-section.mp4
```

`--logo-only` renders the logo section on its own, starting at 3.6 s. Pass
`--frames 0,120,239` to also write review stills.

Requirements: Python 3 with numpy, Pillow and scipy, plus `pdftocairo` (poppler) and `ffmpeg`.
