# Ashvena 1953: Visiting Card

![Board](ashvena-visiting-card-board.png)

This design follows the references: the botanical palm and jharokha-window illustrations, the Shifo card (dotted QR with an Instagram glyph) and the Almanova cards (labelled contact rows, interlocking-circle pattern).

| Side | Look |
|---|---|
| **Front: Dispensary blue** (`#CBE9F1`) | Horizontal logo lockup, **Krishana Arora** in Cormorant Garamond, then labelled rows: two mobile numbers, email and address. On the right is a dotted Instagram QR code in Brick with the Instagram glyph in the centre, captioned with the handle. A line-art palm leans in from the right edge. |
| **Back: Brick red** (`#941528`) | The reversed logo inside a cusped jharokha arch (eave, double frame, scalloped sill), with line-art leaves in sage on both sides and a faint interlocking-circle lattice. |

## Choose the Instagram QR
There are two fronts. They are identical except for the QR code:

| Option | QR opens | Files |
|---|---|---|
| A | instagram.com/ashvena1953 | `*_front_ashvena1953.*`, `*_print_ashvena1953.pdf` |
| B | instagram.com/ashvena.sp | `*_front_ashvena.sp.*`, `*_print_ashvena.sp.pdf` |

Scan each code with a phone and keep the option that opens the right profile. Both codes were checked with the ZXing and OpenCV decoders. They use error correction level H, so the centre glyph does not affect scanning. The printed code is 19.6 mm wide.

## Size
3.5 × 2 in (88.9 × 50.8 mm) trim, plus 3 mm bleed on every side, so the artboard is 94.9 × 56.8 mm. The `.ai` and PDF files have their TrimBox and BleedBox set.

## Files
- `*.ai` are PDF-compatible Illustrator files, one artboard each, with bleed. Everything stays vector and the fonts are embedded.
- `ashvena-visiting-card_print_<handle>.pdf` is a 2-page print file (page 1 front, page 2 back).
- `*.svg` are the editable masters. They have named layers (`Logo`, `Name_Block`, `Contact_Details`, `QR_Instagram`, `Palm`, `Jharokha`, `Banana_Leaves`, `Lattice`, and a hidden `Trim_Guide`) and live text.
- `*.png` are previews cropped to the trim. `ashvena-visiting-card-board.png` shows all three.

**Fonts** (free, Google Fonts): Cormorant Garamond and Montserrat.

## Regenerate
Edit `CARD` or `HANDLES` in `scripts/generate_visiting_card.py`, then run:
```
pip install playwright pypdf segno
python3 scripts/generate_visiting_card.py
```
