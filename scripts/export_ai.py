#!/usr/bin/env python3
"""Export the v4 watercolour belts as Illustrator .ai files.

A PDF-compatible .ai is a PDF that Illustrator opens directly (the same
container Illustrator writes when "Create PDF Compatible File" is ticked).
Type stays live as long as Fraunces, Bricolage Grotesque, Lobster and
Tiro Devanagari Hindi are installed; the painting is embedded.

Run after render_previews.py. Output:
packaging/F-palace-garden/ai/Ashvena-Belt-297x74.8-<Flavour>.ai
"""
import os

from pypdf import PdfReader, PdfWriter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packaging", "F-palace-garden")
BELTS = {"aam-papad": "Aam-Papad", "fruit-cocktail": "Fruit-Cocktail"}


def main():
    out_dir = os.path.join(ROOT, "ai")
    os.makedirs(out_dir, exist_ok=True)
    for key, name in BELTS.items():
        src = os.path.join(ROOT, f"ashvena-{key}-v4_belt.pdf")
        w = PdfWriter(clone_from=PdfReader(src))
        w.add_metadata({"/Title": f"Ashvena {name.replace('-', ' ')} belt 297.04 x 74.8 mm",
                        "/Author": "Ashvena 1953", "/Creator": "Ashvena belt generator"})
        dst = os.path.join(out_dir, f"Ashvena-Belt-297x74.8-{name}.ai")
        with open(dst, "wb") as fh:
            w.write(fh)
        print(os.path.relpath(dst, os.path.join(ROOT, "..", "..")))


if __name__ == "__main__":
    main()
