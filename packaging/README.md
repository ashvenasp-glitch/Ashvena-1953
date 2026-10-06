# Ashvena: Cashew Packaging Designs

Three carton design directions for **Peri Peri Cashews** and **Kadi Patta Cashews**, based on the Spice Royale / botanical spice-box references.

![Board](ashvena-cashew-packaging-board.png)

| Direction | Look |
|---|---|
| **A · Heritage Ivory** | Cream carton, botanical illustration, gold-ringed round window showing seasoned cashews, coloured side panel. Includes full **back panels** (about, ingredients, nutrition, storage, serving ideas, barcode/QR, FSSAI). |
| **B · Noir Royale** | Black and gold premium carton, oval beaded gold frame, gold-outlined botanicals, engraved vine on the side. |
| **D · Peacock Flash** | Wrap-around jar/tin label (220 × 180 mm: 155 mm front + 65 mm info panel), modelled on the striped "tattoo mascot" label reference. Tattoo-style peacock perched on a chilli / curry-leaf branch, vertical ASHVENA on both sides, stripe bands, and a rotated info panel (about, ingredients, allergens, storage, manufacturer, barcode). Fonts: DM Serif Display + Inter. |
| **E · Royal Collection** | Festive gift-box lid (250 × 250 mm) in *Midnight* and *Ivory* colourways. Ornamental vector elements (jaali lattice, lotus-petal border, mandala corner rosettes, a cusped Mughal jharokha arch with pillars and bead garland) around twin peacocks (Peri Peri chilli branch, Kadi Patta curry-leaf branch) and a brass urn of cashews. |
| **C · Spice Coast** | Bright illustrated scene: a bowl heaped with cashews, flowing botanicals, a wooden scoop, and a colour-block side panel. |
| **F · Modern Botanical** | Wrap labels **171 × 70 mm** for Peri Peri and Kadi Patta, in three panels: 40 mm left side, 91 mm front, 40 mm right side. **Left side:** story, "what's inside" ingredient icons, ingredients, allergens and storage. **Front:** an arch illustration, the Ashvena logo, the name, flavour notes, the veg mark, the heat level and the net weight. **Right side:** nutrition table, net wt. / MRP, dates, manufacturer, FSSAI and barcode. Illustrations are vector art drawn in code: a cusped Mughal arch with a jaali screen and a potted plant (bird's eye chilli for Peri Peri, curry leaf with a chhajja eave for Kadi Patta), plus ingredient icons. Colours are only the supplied pair per flavour, used solid or tinted: Maple Spice `#692721` + Burnt Orange `#8B4729`, and Pakistan Green `#283618` + Dark Moss Green `#606C38`. The only exception is the statutory veg mark, which keeps its regulation green. Fonts are the candies and dry-fruits set: **Lobster** (name), **Fraunces 9pt** (headings) and **Bricolage Grotesque 14pt** (body), stored in `scripts/fonts/`. There is **one Illustrator file**, `ashvena-cashews_modern-labels.ai`, which is PDF-compatible and holds both labels with 3 mm bleed, crop marks and panel ticks. There is also a print PDF per label and PNG previews. Built by `scripts/generate_modern_labels.py`. |

## Files (per direction folder)
- `*_front-side.svg` is the **editable master for Adobe Illustrator** (File → Open). The artboard is 165 × 170 mm: a 45 mm side panel plus a 120 mm front panel. Named groups (`Front_Panel`, `Illustration`, `Product_Name`, `Footer`, `Side_Panel`, …) appear as layers. Text is live.
- `*_back.svg` (Direction A only) is the back panel, 120 × 170 mm.
- `*.pdf` is a vector PDF at the same size, and `*.png` is a preview.

**Fonts** (free, Google Fonts): Cinzel, Cormorant Garamond, Montserrat, plus DM Serif Display and Inter for D. Install them before opening in Illustrator.

## Before print, replace these placeholders
- Nutrition values (indicative only), ingredient percentages, and claims ("Made in India"). Get them from your lab report and your recipe.
- FSSAI licence no., address, MRP, barcode (EAN), QR code, batch and dates.
- Add bleed (3 mm), glue flap, top and bottom tuck flaps for your printer's actual dieline.

## Regenerate
```
pip install playwright
python3 scripts/generate_packaging.py   # SVGs (A-C)
python3 scripts/generate_wrap_labels.py # SVGs (D)
python3 scripts/generate_gift_box.py    # SVGs (E)
python3 scripts/generate_modern_labels.py # .ai + PDF + PNG (F), needs reportlab, svglib, pdftoppm
python3 scripts/render_previews.py      # PNG + PDF
python3 scripts/render_mockups.py       # 3D board
```
