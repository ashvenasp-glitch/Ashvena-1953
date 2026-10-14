#!/usr/bin/env python3
"""Turn a PDF-compatible Illustrator (.ai) logo into files CorelDRAW opens natively.

No open-source tool writes CorelDRAW's .cdr format, so this writes the formats
CorelDRAW imports as editable vectors instead. Open one in CorelDRAW and use
File > Save As > CDR to get the .cdr file.

  <name>.pdf          clean PDF 1.4, one page per artboard, DeviceCMYK
  <name>_<size>.eps   one EPS per artboard, CMYK (setcmykcolor)
  <name>_<size>.svg   one SVG per artboard, sRGB (converted with the file's ICC profile)
  <name>_<size>.png   preview

Paths and CMYK values are copied from the .ai unchanged.

Usage: python3 scripts/convert_logo_for_corel.py IN.ai OUT_DIR NAME
Requires: pip install pikepdf pillow, and poppler-utils (pdftocairo) for the previews.
"""
import io
import os
import subprocess
import sys

import pikepdf
from PIL import Image, ImageCms

SUPPORTED = {"q", "Q", "cm", "m", "l", "c", "v", "y", "h", "re", "f", "F", "f*", "W", "W*", "n",
             "cs", "scn", "sc", "k", "gs", "BDC", "BMC", "EMC"}


def num(x):
    s = f"{float(x):.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def mul(a, b):
    """Multiply PDF matrices [a b c d e f]: a then b."""
    return [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3],
            a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
            a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]]


def page_ops(page):
    """Content operators with colour set as CMYK ('k') and marked-content/gs dropped."""
    cs = page.Resources.get("/ColorSpace", {})
    for gs in page.Resources.get("/ExtGState", {}).values():
        if float(gs.get("/ca", 1)) != 1 or float(gs.get("/CA", 1)) != 1 or gs.get("/BM", "/Normal") != "/Normal" \
                or gs.get("/SMask", "/None") != "/None" or gs.get("/OP", False) or gs.get("/op", False):
            sys.exit("transparency / overprint graphics state is not supported")
    fill_n = None
    out = []
    for operands, op in pikepdf.parse_content_stream(page):
        op = str(op)
        if op not in SUPPORTED:
            sys.exit(f"unsupported PDF operator {op!r}")
        if op in ("BDC", "BMC", "EMC", "gs"):
            continue
        if op == "cs":
            space = cs[operands[0]] if str(operands[0]) in cs else operands[0]
            if isinstance(space, pikepdf.Array) and space[0] == "/ICCBased":
                fill_n = int(space[1].N)
            elif space == "/DeviceCMYK":
                fill_n = 4
            else:
                sys.exit(f"unsupported colour space {space!r}")
            continue
        if op in ("scn", "sc"):
            if fill_n != 4 or len(operands) != 4:
                sys.exit("only CMYK fills are supported")
            op = "k"
        out.append(([float(o) for o in operands], op))
    return out


def write_pdf(pages, path, title):
    pdf = pikepdf.new()
    for (w, h), ops in pages:
        pg = pdf.add_blank_page(page_size=(w, h))
        body = "\n".join(" ".join([num(o) for o in operands] + [op]) for operands, op in ops)
        pg.obj.Contents = pdf.make_stream(body.encode())
    pdf.docinfo["/Title"] = title
    pdf.save(path, force_version="1.4")


def write_eps(size, ops, path, title):
    w, h = size
    ps = {"q": "gsave", "Q": "grestore", "m": "moveto", "l": "lineto", "c": "curveto", "h": "closepath",
          "f": "fill", "F": "fill", "f*": "eofill", "W": "clip", "W*": "eoclip", "n": "newpath",
          "k": "setcmykcolor"}
    lines = [
        "%!PS-Adobe-3.0 EPSF-3.0",
        f"%%Title: ({title})",
        "%%Creator: scripts/convert_logo_for_corel.py",
        f"%%BoundingBox: 0 0 {round(w)} {round(h)}",
        f"%%HiResBoundingBox: 0 0 {num(w)} {num(h)}",
        "%%DocumentProcessColors: Cyan Magenta Yellow Black",
        "%%LanguageLevel: 2",
        "%%Pages: 1",
        "%%EndComments",
        "%%Page: 1 1",
    ]
    for o, op in ops:
        a = " ".join(num(x) for x in o)
        if op == "cm":
            lines.append(f"[{a}] concat")
        elif op == "re":
            x, y, rw, rh = (num(v) for v in o)
            lines.append(f"{x} {y} moveto {rw} 0 rlineto 0 {rh} rlineto {num(-o[2])} 0 rlineto closepath")
        elif op in ("v", "y"):
            sys.exit("v/y curves are not supported in EPS output")
        else:
            lines.append(f"{a} {ps[op]}".strip())
    lines += ["showpage", "%%Trailer", "%%EOF", ""]
    with open(path, "w") as fh:
        fh.write("\n".join(lines))


def cmyk_to_srgb(cmyk, icc):
    src = ImageCms.ImageCmsProfile(io.BytesIO(icc)) if icc else ImageCms.createProfile("sRGB")
    xf = ImageCms.buildTransform(src, ImageCms.createProfile("sRGB"), "CMYK", "RGB",
                                 renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC)
    px = Image.new("CMYK", (1, 1), tuple(round(v * 255) for v in cmyk))
    return "#%02x%02x%02x" % ImageCms.applyTransform(px, xf).getpixel((0, 0))


def write_svg(size, ops, path, title, icc):
    w, h = size
    ctm, stack, d, fill, shapes = [1, 0, 0, 1, 0, 0], [], [], None, []

    def pt(x, y):
        X = ctm[0] * x + ctm[2] * y + ctm[4]
        Y = ctm[1] * x + ctm[3] * y + ctm[5]
        return f"{num(X)} {num(h - Y)}"

    for o, op in ops:
        if op == "q":
            stack.append(ctm)
        elif op == "Q":
            ctm = stack.pop()
        elif op == "cm":
            ctm = mul(o, ctm)
        elif op == "k":
            fill = o
        elif op == "m":
            d.append("M" + pt(*o))
        elif op == "l":
            d.append("L" + pt(*o))
        elif op == "c":
            d.append("C" + " ".join(pt(*o[i:i + 2]) for i in (0, 2, 4)))
        elif op == "h":
            d.append("Z")
        elif op == "re":
            x, y, rw, rh = o
            d.append(f"M{pt(x, y)}L{pt(x + rw, y)}L{pt(x + rw, y + rh)}L{pt(x, y + rh)}Z")
        elif op in ("f", "F", "f*"):
            cmyk = " ".join(f"{round(v * 100, 1):g}" for v in fill)
            rule = ' fill-rule="evenodd"' if op == "f*" else ""
            shapes.append(f'  <!-- CMYK {cmyk} -->\n'
                          f'  <path fill="{cmyk_to_srgb(fill, icc)}"{rule} d="{"".join(d)}"/>')
            d = []
        elif op in ("W", "W*", "n"):
            d = [] if op == "n" else d  # artboard clip; the SVG viewBox clips the same area
        else:
            sys.exit(f"{op!r} not supported in SVG output")
    with open(path, "w") as fh:
        fh.write(f'<?xml version="1.0" encoding="UTF-8"?>\n'
                 f'<svg xmlns="http://www.w3.org/2000/svg" width="{num(w / 72)}in" height="{num(h / 72)}in" '
                 f'viewBox="0 0 {num(w)} {num(h)}">\n  <title>{title}</title>\n' + "\n".join(shapes) + "\n</svg>\n")


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    src, out_dir, name = sys.argv[1:]
    os.makedirs(out_dir, exist_ok=True)
    ai = pikepdf.open(src)
    pages, icc = [], None
    for page in ai.pages:
        box = [float(v) for v in page.MediaBox]
        if box[:2] != [0, 0]:
            sys.exit("artboards with a non-zero origin are not supported")
        pages.append(((box[2], box[3]), page_ops(page)))
        for space in page.Resources.get("/ColorSpace", {}).values():
            if isinstance(space, pikepdf.Array) and space[0] == "/ICCBased" and int(space[1].N) == 4:
                icc = space[1].read_bytes()
    base = os.path.join(out_dir, name)
    write_pdf(pages, base + ".pdf", name)
    for i, (size, ops) in enumerate(pages):
        tag = f"{num(size[0] / 72)}in" if size[0] == size[1] else f"{num(size[0] / 72)}x{num(size[1] / 72)}in"
        write_eps(size, ops, f"{base}_{tag}.eps", f"{name} {tag}")
        write_svg(size, ops, f"{base}_{tag}.svg", f"{name} {tag}", icc)
        subprocess.run(["pdftocairo", "-png", "-singlefile", "-r", "150", "-f", str(i + 1), "-l", str(i + 1),
                        base + ".pdf", f"{base}_{tag}"], check=True)
        print("wrote", f"{name}_{tag}.eps/.svg/.png")
    print("wrote", f"{name}.pdf ({len(pages)} pages)")


if __name__ == "__main__":
    main()
