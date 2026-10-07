# Watercolour art for the v4 belts

Painted in Magnific (Nano Banana Pro, 4096 × 1032 px), styled on the existing
Ashvena band art (curry-leaf and soul-of-tradition bands).

| Belt | Chosen painting | Save as |
|---|---|---|
| Aam Papad | Calmer take 1, more colourful version 1: https://www.magnific.com/app/creation/Lwnu0uMswO | `ashvena-aam-papad-watercolour.png` |
| Fruit Cocktail | Option A: https://www.magnific.com/app/creation/fHJprYlCDY | `ashvena-fruit-cocktail-watercolour.png` |

`src/` holds the untouched paintings: the 2000 × 504 px copies sent through chat
(about 171 dpi at belt size), fine for proofs but too soft for print. The files
in this folder are retouched from them by `scripts/edit_watercolour_art.py`:
the stray post and melon pot are removed from Fruit Cocktail, a palm is added at
each end of both belts, the floor line runs end to end, and the white paper
becomes a soft coloured wash (warm cream for Aam Papad, lime-sage for Fruit Cocktail)
while the painted motifs keep their own colours.

For print, save Magnific's full-size 16-bit PNG exports (4096 × 1032 px, about
350 dpi) into `src/` under the names above, then run:

    python3 scripts/edit_watercolour_art.py
    python3 scripts/generate_belts_watercolour.py
    python3 scripts/render_previews.py F-palace-garden
    python3 scripts/export_ai.py
