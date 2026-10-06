# Ashvena: Cashew Packaging Designs

Three carton design directions for **Peri Peri Cashews** and **Kadi Patta Cashews**, based on the Spice Royale / botanical spice-box references.

![Board](ashvena-cashew-packaging-board.png)

| Direction | Look |
|---|---|
| **A · Heritage Ivory** | Cream carton, botanical illustration, gold-ringed round window showing seasoned cashews, coloured side panel. Includes full **back panels** (about, ingredients, nutrition, storage, serving ideas, barcode/QR, FSSAI). |
| **B · Noir Royale** | Black and gold premium carton, oval beaded gold frame, gold-outlined botanicals, engraved vine on the side. |
| **D · Peacock Flash** | Wrap-around jar/tin label (220 × 180 mm: 155 mm front + 65 mm info panel), modelled on the striped "tattoo mascot" label reference. Tattoo-style peacock perched on a chilli / curry-leaf branch, vertical ASHVENA on both sides, stripe bands, and a rotated info panel (about, ingredients, allergens, storage, manufacturer, barcode). Fonts: DM Serif Display + Inter. |
| **E · Royal Collection** | Festive gift-box lid (250 × 250 mm) in *Midnight* and *Ivory* colourways. Ornamental vector elements (jaali lattice, lotus-petal border, mandala corner rosettes, a cusped Mughal jharokha arch with pillars and bead garland) around twin peacocks (Peri Peri chilli branch, Kadi Patta curry-leaf branch) and a brass urn of cashews. |
| **F · Jharokha Garden** | **Chai Masala** and **Chaat Masala** wrap-around jar labels (171 × 70 mm: 44 mm info panel, 83 mm front, 44 mm info panel). A modern, premium take on the botanical-miniature references: a cusped Mughal arch over a quatrefoil jaali balcony, framing a potted tea bush (Chai) or pomegranate tree (Chaat), with banana leaves or palm fronds behind it. The colours come from the Tea Leaves / Biscuits / Orange Peels / Roses / Green Tea palette, with sage, marigold and wine. Both labels sit on **one file**: `ashvena-masala-labels.svg` (editable layers, live text) and `ashvena-masala-labels.ai` (the same sheet with crop marks). `_print.pdf` has one 171 × 70 mm page per label. Fonts: Cormorant Garamond, Cinzel, Montserrat. |
| **C · Spice Coast** | Bright illustrated scene: a bowl heaped with cashews, flowing botanicals, a wooden scoop, and a colour-block side panel. |

## Files (per direction folder)
- `*_front-side.svg` is the **editable master for Adobe Illustrator** (File → Open). The artboard is 165 × 170 mm: a 45 mm side panel plus a 120 mm front panel. Named groups (`Front_Panel`, `Illustration`, `Product_Name`, `Footer`, `Side_Panel`, …) appear as layers. Text is live.
- `*_back.svg` (Direction A only) is the back panel, 120 × 170 mm.
- `*.pdf` is a vector PDF at the same size, and `*.png` is a preview.

**Fonts** (free, Google Fonts): Cinzel, Cormorant Garamond, Montserrat, plus DM Serif Display and Inter for D. Install them before opening in Illustrator.

## Before print, replace these placeholders
- Nutrition values (indicative only), ingredient percentages, and claims ("Made in India"). Get them from your lab report and your recipe.
- FSSAI licence no., address, MRP, barcode (EAN), QR code, batch and dates.
- Masala labels (F): net weight (100 g is a placeholder), ingredient order and percentages, allergen statement and shelf life.
- Add bleed (3 mm), glue flap, top and bottom tuck flaps for your printer's actual dieline.

## Regenerate
```
pip install playwright
python3 scripts/generate_packaging.py   # SVGs (A-C)
python3 scripts/generate_wrap_labels.py # SVGs (D)
python3 scripts/generate_gift_box.py    # SVGs (E)
python3 scripts/generate_masala_labels.py  # F: SVG + AI + print PDF + PNG
python3 scripts/render_previews.py      # PNG + PDF
python3 scripts/render_mockups.py       # 3D board
```
