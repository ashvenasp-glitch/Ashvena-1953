#!/usr/bin/env python3
"""Extract the Ashvena logo vectors from brand/ashvena-logo_final.ai.

Reads artboard 1 (primary lockup) of the Illustrator file (PDF-compatible)
via poppler's pdftocairo and writes:
  brand/ashvena-logo-parts.json   mark / wordmark / year path data + bounding boxes
  brand/ashvena-logo-mark.svg     the brush "अ" mark on its own (Brick)
  brand/ashvena-logo-lockup.svg   mark + Ashvena + 1953, transparent background

Requires: poppler-utils (pdftocairo).
"""
import json
import os
import re
import subprocess

BRAND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "brand")
SRC = os.path.join(BRAND, "ashvena-logo_final.ai")

# Palette as named on the logo's colour-usage artboard
PALETTE = {"brick": "#941528", "deep_lac": "#35070f", "dispensary": "#cbe9f1",
           "khadi_cream": "#fce4cd", "sage_mist": "#bfd9d6"}


def bbox(d):
    nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", d)]
    xs, ys = nums[0::2], nums[1::2]
    return [min(xs), min(ys), max(xs), max(ys)]


def main():
    svg = subprocess.run(["pdftocairo", "-svg", "-f", "1", "-l", "1", SRC, "-"],
                         capture_output=True, text=True, check=True).stdout
    paths = re.findall(r'<path [^>]*fill="(rgb\([^)]*\))"[^>]*d="([^"]+)"', svg)
    assert len(paths) == 3, f"expected mark, wordmark, year; got {len(paths)} paths"
    parts = {}
    for name, (_, d) in zip(["mark", "wordmark", "year"], paths):
        d = re.sub(r"\s+", " ", d).strip()
        parts[name] = {"d": d, "bbox": [round(v, 2) for v in bbox(d)]}
    parts["palette"] = PALETTE
    json.dump(parts, open(os.path.join(BRAND, "ashvena-logo-parts.json"), "w"), indent=1)

    def doc(names, cols):
        bb = [min(parts[n]["bbox"][0] for n in names), min(parts[n]["bbox"][1] for n in names),
              max(parts[n]["bbox"][2] for n in names), max(parts[n]["bbox"][3] for n in names)]
        pad = 10
        vb = f"{bb[0] - pad:.1f} {bb[1] - pad:.1f} {bb[2] - bb[0] + 2 * pad:.1f} {bb[3] - bb[1] + 2 * pad:.1f}"
        body = "".join(f'<path id="{n}" fill="{c}" d="{parts[n]["d"]}"/>' for n, c in zip(names, cols))
        return f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">{body}</svg>\n'

    open(os.path.join(BRAND, "ashvena-logo-mark.svg"), "w").write(doc(["mark"], [PALETTE["brick"]]))
    open(os.path.join(BRAND, "ashvena-logo-lockup.svg"), "w").write(
        doc(["mark", "wordmark", "year"], [PALETTE["brick"], PALETTE["deep_lac"], PALETTE["brick"]]))
    for n in ["mark", "wordmark", "year"]:
        print(n, parts[n]["bbox"])


if __name__ == "__main__":
    main()
