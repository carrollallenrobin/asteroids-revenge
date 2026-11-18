#!/usr/bin/env python3
"""Build the subsetted Noto fallback fonts used behind kenvector_future(_thin).

Web exports have no system fonts to fall back on, so every glyph the
translations need must ship with the game. The full Noto CJK fonts are
~10-18 MB each, so each font is cut down to the characters actually used
in locale/translations.csv.

Re-run after changing translations.csv:

    python3 art-and-sound/fonts/subset_fonts.py <dir-with-source-fonts>

Source fonts (OFL) come from https://github.com/google/fonts/tree/main/ofl :
    NotoSans[wdth,wght].ttf, NotoSansSC[wght].ttf, NotoSansTC[wght].ttf,
    NotoSansJP[wght].ttf, NotoSansKR[wght].ttf, NotoSansThai[wdth,wght].ttf,
    NotoSansHebrew[wdth,wght].ttf, NotoSansArabic[wdth,wght].ttf

Requires fontTools (pip install fonttools).
"""
import csv
import string
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = Path(__file__).resolve().parent
CSV = HERE.parent.parent / "locale" / "translations.csv"
WEIGHT = 700  # kenvector is a heavy display face

# output name -> (source file, translation columns whose text it must cover)
FONTS = {
    "NotoSans-subset.ttf": ("NotoSans[wdth,wght].ttf", None),  # all non-CJK columns
    "NotoSansSC-subset.ttf": ("NotoSansSC[wght].ttf", ["zh"]),
    "NotoSansJP-subset.ttf": ("NotoSansJP[wght].ttf", ["ja"]),
    "NotoSansTC-subset.ttf": ("NotoSansTC[wght].ttf", ["lzh"]),
    "NotoSansKR-subset.ttf": ("NotoSansKR[wght].ttf", ["ko"]),
    "NotoSansThai-subset.ttf": ("NotoSansThai[wdth,wght].ttf", ["th"]),
    "NotoSansHebrew-subset.ttf": ("NotoSansHebrew[wdth,wght].ttf", ["he"]),
    "NotoSansArabic-subset.ttf": ("NotoSansArabic[wdth,wght].ttf", ["ar"]),
}
CJK = {"zh", "ja", "lzh", "ko"}
ALWAYS = string.printable + "–—…«»“”‘’·•×"


def column_text(rows, cols):
    header = rows[0]
    idx = [i for i, name in enumerate(header) if name in cols]
    return "".join(r[i] for r in rows[2:] for i in idx if i < len(r))


def main(src_dir: Path):
    rows = list(csv.reader(CSV.open(encoding="utf-8")))
    header = rows[0]
    non_cjk = [h for h in header[2:] if h not in CJK]

    for out_name, (src_name, cols) in FONTS.items():
        text = ALWAYS + column_text(rows, cols or non_cjk)
        font = TTFont(src_dir / src_name)
        if "fvar" in font:
            axes = {a.axisTag: a for a in font["fvar"].axes}
            limits = {"wght": WEIGHT}
            if "wdth" in axes:
                limits["wdth"] = 100
            font = instancer.instantiateVariableFont(font, limits)
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        sub = subset.Subsetter(opts)
        sub.populate(text=text)
        sub.subset(font)
        out = HERE / out_name
        font.save(out)
        print(f"{out_name}: {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
