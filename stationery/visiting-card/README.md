# Ashvena 1953: Visiting Card

![Board](ashvena-visiting-card-board.png)

| Side | Look |
|---|---|
| **Front: Dispensary blue** (`#CBE9F1`) | Stacked logo lockup in Brick and Deep Lac on the left, a thin Brick divider, then name, designation and contact lines with small Brick icons. A large, faint copy of the mark bleeds off the right edge. |
| **Back: Brick red** (`#941528`) | The logo reversed, centred: the mark in sage (`#BFD9D6`, the brand's reversed-on-brick colour), the wordmark in Khadi Cream, and a fine double frame. |

The logo is the vector artwork from `logo_final.ai`, saved in `brand/ashvena-logo.svg`.

## Size
3.5 × 2 in (88.9 × 50.8 mm) trim, plus 3 mm bleed on every side, so the artboard is 94.9 × 56.8 mm. The PDFs and `.ai` files have their TrimBox and BleedBox set.

## Files
- `ashvena-visiting-card_front.ai`, `ashvena-visiting-card_back.ai` are PDF-compatible Illustrator files, one artboard each, with bleed. The logo stays vector. Fonts are embedded.
- `ashvena-visiting-card_print.pdf` is a 2-page print file (page 1 front, page 2 back).
- `*.svg` are the editable masters. They have named layers (`Logo`, `Name_Block`, `Contact_Details`, `Watermark`, `Frame`, and a hidden `Trim_Guide`) and live text.
- `*.png` are previews cropped to the trim. `ashvena-visiting-card-board.png` is the mockup.

**Fonts** (free, Google Fonts): Cormorant Garamond (name) and Montserrat (designation and contacts).

## Before print
Replace the placeholder name, designation, phone, email, website and address. You can do this in Illustrator, or edit `CARD` in `scripts/generate_visiting_card.py` and regenerate:
```
pip install playwright pypdf
python3 scripts/generate_visiting_card.py
```
