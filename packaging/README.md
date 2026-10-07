# Ashvena: Cashew Packaging Designs

Three carton design directions for **Peri Peri Cashews** and **Kadi Patta Cashews**, based on the Spice Royale / botanical spice-box references.

![Board](ashvena-cashew-packaging-board.png)

| Direction | Look |
|---|---|
| **A · Heritage Ivory** | Cream carton, botanical illustration, gold-ringed round window showing seasoned cashews, coloured side panel. Includes full **back panels** (about, ingredients, nutrition, storage, serving ideas, barcode/QR, FSSAI). |
| **B · Noir Royale** | Black and gold premium carton, oval beaded gold frame, gold-outlined botanicals, engraved vine on the side. |
| **D · Peacock Flash** | Wrap-around jar/tin label (220 × 180 mm: 155 mm front + 65 mm info panel), modelled on the striped "tattoo mascot" label reference. Tattoo-style peacock perched on a chilli / curry-leaf branch, vertical ASHVENA on both sides, stripe bands, and a rotated info panel (about, ingredients, allergens, storage, manufacturer, barcode). Fonts: DM Serif Display + Inter. |
| **E · Royal Collection** | Festive gift-box lid (250 × 250 mm) in *Midnight* and *Ivory* colourways. Ornamental vector elements (jaali lattice, lotus-petal border, mandala corner rosettes, a cusped Mughal jharokha arch with pillars and bead garland) around twin peacocks (Peri Peri chilli branch, Kadi Patta curry-leaf branch) and a brass urn of cashews. |
| **F · Thank-You Card** | 150 × 100 mm order insert, modelled on the "Say hello to your new favorite" reference and set in the official logo colours and style (`brand/ashvena-logo_final.ai`). **Front:** Brick red with the brush-stroke "अ" mark blown up and inked tone-on-tone into the background, the horizontal logo lockup (mark in Dispensary blue, wordmark in Khadi Cream), and a Bodoni serif / italic headline. **Back:** Dispensary blue with a thank-you note, a 15% off line and a scannable Instagram QR code. Fonts: Bodoni Moda, Montserrat. See `F-thank-you-card/ashvena-thank-you-card_mockup.png`. |
| **C · Spice Coast** | Bright illustrated scene: a bowl heaped with cashews, flowing botanicals, a wooden scoop, and a colour-block side panel. |

## Logo
`brand/ashvena-logo_final.ai` is the master logo. `scripts/extract_logo.py` pulls its vectors into `brand/ashvena-logo-parts.json` (used by F), plus standalone `ashvena-logo-mark.svg` and `ashvena-logo-lockup.svg`. Palette: Brick `#941528`, Deep Lac `#35070f`, Dispensary `#cbe9f1`, Khadi Cream `#fce4cd`.

## Files (per direction folder)
- `*_front-side.svg` is the **editable master for Adobe Illustrator** (File → Open). The artboard is 165 × 170 mm: a 45 mm side panel plus a 120 mm front panel. Named groups (`Front_Panel`, `Illustration`, `Product_Name`, `Footer`, `Side_Panel`, …) appear as layers. Text is live.
- `*_back.svg` (Direction A only) is the back panel, 120 × 170 mm.
- `*.pdf` is a vector PDF at the same size, and `*.png` is a preview.

**Fonts** (free, Google Fonts): Cinzel, Cormorant Garamond, Montserrat, plus DM Serif Display and Inter for D, and Bodoni Moda for F. Install them before opening in Illustrator.

## Before print, replace these placeholders
- Nutrition values (indicative only), ingredient percentages, and claims ("Made in India"). Get them from your lab report and your recipe.
- FSSAI licence no., address, MRP, barcode (EAN), QR code, batch and dates.
- Thank-you card (F): the QR and handle point to `instagram.com/ashvena.1953`, which is a placeholder. Regenerate with `python3 scripts/generate_thank_you_card.py --insta <your_handle>`. Confirm the 15% offer (or remove it) and add 3 mm bleed.
- Add bleed (3 mm), glue flap, top and bottom tuck flaps for your printer's actual dieline.

## Regenerate
```
pip install playwright segno
python3 scripts/generate_packaging.py   # SVGs (A-C)
python3 scripts/generate_wrap_labels.py # SVGs (D)
python3 scripts/generate_gift_box.py    # SVGs (E)
python3 scripts/extract_logo.py         # logo vectors (needs poppler)
python3 scripts/generate_thank_you_card.py  # SVGs (F)
python3 scripts/render_previews.py      # PNG + PDF (optionally: F-thank-you-card)
python3 scripts/render_card_mockup.py   # F flat-lay mockup
python3 scripts/render_mockups.py       # 3D board
```
