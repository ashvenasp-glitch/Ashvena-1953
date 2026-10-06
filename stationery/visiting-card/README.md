# Ashvena 1953: Visiting Card

![Board](ashvena-visiting-card-board.png)

A simple, premium two-colour card: plain colour, the logo and type, with no illustration.

| Side | Look |
|---|---|
| **Front: Dispensary blue** (`#CBE9F1`) | Horizontal logo lockup, **Krishana Arora** in Cormorant Garamond, a short Brick rule, then labelled rows: two mobile numbers, email and address. On the right is a dotted Instagram QR code in Brick with the Instagram glyph in the centre. Its caption sits on the same line as the address. |
| **Back: Brick red** (`#941528`) | An oversized logo mark, tone on tone with a soft debossed edge, bleeds off the left and bottom. The wordmark is in Khadi Cream with the year in sage, on the right. |

**Premium finish (optional):** the back's `Emboss_Mark` layer can go to the printer as a **blind-deboss** or **spot-UV** plate. Then the mark is felt rather than printed, as on the Shifo reference. Use a heavy uncoated or cotton stock (350 gsm or more).

## Instagram QR
The QR code opens **@ashvena_1953**. It encodes the same link as the QR code Instagram generated for the account:
`https://www.instagram.com/ashvena_1953?utm_source=qr&stkn=ZHF3cnhwemdkc3Bu`

The code is rebuilt as vector artwork in Brick, in Instagram's own style (round dots, rounded corner rings with round centres, the Instagram glyph in the middle), so it prints sharp. It uses error correction level H and is 21.6 mm wide. It was checked with the ZXing decoder down to quarter-size previews and from the print PDF at 300 dpi. Do a final scan from a printed proof before the full run.

## Size
3.5 × 2 in (88.9 × 50.8 mm) trim, plus 3 mm bleed on every side, so the artboard is 94.9 × 56.8 mm. The `.ai` and PDF files have their TrimBox and BleedBox set.

## Files
- `ashvena-visiting-card.ai` holds **front and back in one file**, as two artboards: page 1 front, page 2 back. It is a PDF-compatible Illustrator file with 3 mm bleed and the trim marked. Everything stays vector and the fonts are embedded. If Illustrator asks which pages to open, choose **All**.
- `ashvena-visiting-card_print.pdf` has the same two pages, to send to a printer.
- `*.svg` are the editable masters. They have named layers (`Logo`, `Name_Block`, `Contact_Details`, `QR_Instagram`, `QR_Caption`, `Emboss_Mark`, `Wordmark`, and a hidden `Trim_Guide`) and live text.
- `*.png` are previews cropped to the trim. `ashvena-visiting-card-board.png` shows both sides.

### CorelDRAW (.cdr)
`ashvena-visiting-card_coreldraw-curves.pdf` is the CorelDRAW-ready file. It has the same two pages (front, back) with **all text converted to curves** and no fonts or images, only vector shapes in the exact brand colours, with 3 mm bleed and the trim marked. It opens in any CorelDRAW version with nothing missing.

The `.cdr` format itself is proprietary and only CorelDRAW can write it, so there is no `.cdr` in the repo. To get one, in CorelDRAW:
1. **File → Open** `ashvena-visiting-card_coreldraw-curves.pdf`.
2. **File → Save As → CorelDRAW (CDR)**.

A print shop that uses CorelDRAW can also take this PDF as it is.

**Fonts** (free, Google Fonts): Cormorant Garamond and Montserrat.

## Regenerate
Edit `CARD` or `INSTAGRAM` in `scripts/generate_visiting_card.py`, then run:
```
pip install playwright pypdf segno cairosvg   # and poppler-utils for pdftocairo
python3 scripts/generate_visiting_card.py
```
