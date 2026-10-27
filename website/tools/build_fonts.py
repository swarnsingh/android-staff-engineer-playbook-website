#!/usr/bin/env python3
"""Rebuild the self-hosted reading fonts from pinned Google Fonts sources.

Downloads each variable TTF from the google/fonts repository at a pinned commit (Source Serif 4 from Adobe's
release), checks its SHA-256,
limits the axes to what the reader uses, subsets to Latin plus the punctuation the lessons use and writes
WOFF2 into website/design-system/fonts/. Prints the @font-face metric overrides for the matched fallbacks.

Needs fontTools and Brotli (not part of the site build):
    python -m pip install fonttools==4.60.1 brotli
    python website/tools/build_fonts.py

Source Sans 3 and Source Serif 4 carry Adobe's Reserved Font Name "Source". A subset is a Modified Version
under the SIL OFL (OFL-FAQ 2.6), so those two are renamed to "Playbook Sans" and "Playbook Serif" inside the
font and in CSS. Shantell Sans and Atkinson Hyperlegible Next have no Reserved Font Name and keep theirs.
"""
import hashlib, io, sys, urllib.request, zipfile
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

GOOGLE_FONTS_COMMIT = 'ddf386ba1b9fbc6b2c818f1ddcd9148f54ced94b'
RAW = f'https://raw.githubusercontent.com/google/fonts/{GOOGLE_FONTS_COMMIT}/ofl/'
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT/'.cache/font-sources'
OUT = ROOT/'design-system/fonts'

# Google Fonts' "latin" range, plus the arrows, maths signs and Polish ł that lesson prose uses.
UNICODES = ('U+0000-00FF,U+0131,U+0141-0142,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,'
            'U+2000-206F,U+20AC,U+2122,U+2190-2199,U+21D2,U+2212,U+2215,U+2248,U+2260,U+2264-2265,U+FEFF,U+FFFD')
FEATURES = ['kern', 'liga', 'calt', 'ccmp', 'locl', 'mark', 'mkmk', 'rlig', 'rvrn', 'frac', 'numr', 'dnom', 'tnum', 'lnum', 'case']

# Adobe's 4.005 release fixes an hmtx issue in the variable TTFs (source-serif#110); Google Fonts still ships 4.004.
SOURCE_SERIF = 'https://github.com/adobe-fonts/source-serif/releases/download/4.005R/source-serif-4.005_Desktop.zip'
SOURCE_SERIF_ZIP = '549fdb8f9a682bd06944298621404969f6de77c2e422ff3b8244a1dcd6a0c425'

# (source, SHA-256 of the source TTF, axis limits, output file, renamed family or None).
# Shantell Sans has no italic here: an 89KB file for a slanted handwriting face is not worth it; the browser slants it.
# A source is a google/fonts path at the pinned commit, or (release zip URL, member).
FONTS = [
    ('sourcesans3/SourceSans3[wght].ttf', '042fe2cc0b933e328410d7acbd0aa6a1873dca5aef81875f4bc214b08825c7b9',
     {'wght': (400, 700)}, 'PlaybookSans-Variable-latin.woff2', 'Playbook Sans'),
    ('sourcesans3/SourceSans3-Italic[wght].ttf', '39e3ab05ccd7cb94907c31005bb5bec1d5432f0b096a2b782976e217a540eb6c',
     {'wght': (400, 700)}, 'PlaybookSans-Italic-Variable-latin.woff2', 'Playbook Sans'),
    ((SOURCE_SERIF, 'source-serif-4.005_Desktop/VAR/SourceSerif4Variable-Roman.ttf'), '14d360ee1b76655da9276628b229e11671bc1f5d1083636144db6677d452cf55',
     {'wght': (400, 700), 'opsz': 18}, 'PlaybookSerif-Variable-latin.woff2', 'Playbook Serif'),
    ((SOURCE_SERIF, 'source-serif-4.005_Desktop/VAR/SourceSerif4Variable-Italic.ttf'), '6a059a64838978d54e8fab71ed86b0d82e948c0e12b2664d0c15166326dcff82',
     {'wght': (400, 700), 'opsz': 18}, 'PlaybookSerif-Italic-Variable-latin.woff2', 'Playbook Serif'),
    ('shantellsans/ShantellSans[BNCE,INFM,SPAC,wght].ttf', 'd98a7913853f78d71aa0b86daf66b5eddb5a3266c07bfd51ef70632b88c41084',
     {'wght': (400, 700), 'BNCE': 0, 'INFM': 0, 'SPAC': 0}, 'ShantellSans-Variable-latin.woff2', None),
    ('atkinsonhyperlegiblenext/AtkinsonHyperlegibleNext[wght].ttf', '5a455d1cfa099b601ab70751bb9673e8fe1854dc4500c80e1a220d0d75e31745',
     {'wght': (400, 700)}, 'AtkinsonHyperlegibleNext-Variable-latin.woff2', None),
    ('atkinsonhyperlegiblenext/AtkinsonHyperlegibleNext-Italic[wght].ttf', 'ce9cffed32742ad2d9238c561a93220385e5934cdc02b8eb4097a50efa957dc6',
     {'wght': (400, 700)}, 'AtkinsonHyperlegibleNext-Italic-Variable-latin.woff2', None),
]

def download(url, path, expected=None):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(urllib.request.urlopen(url, timeout=120).read())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected and digest != expected: raise ValueError(f'{path.name}: SHA-256 {digest} does not match {expected}')
    return path

def fetch(source):
    if isinstance(source, tuple):
        url, member = source
        archive = download(url, CACHE/'releases'/url.rsplit('/', 1)[1], SOURCE_SERIF_ZIP)
        path = CACHE/'releases'/Path(member).name
        if not path.exists(): path.write_bytes(zipfile.ZipFile(archive).read(member))
        return path
    return download(RAW+urllib.request.quote(source), CACHE/GOOGLE_FONTS_COMMIT/source)

def rename(font, family):
    """Replace every name record that carries the Reserved Font Name; keep copyright, licence and designer."""
    names = font['name']
    old_family = names.getDebugName(16) or names.getDebugName(1)
    old_ps = (names.getDebugName(25) or names.getDebugName(6).split('-')[0])
    new_ps = family.replace(' ', '')
    for record in names.names:
        if record.nameID in (0, 7, 8, 9, 11, 12, 13, 14): continue
        text = record.toUnicode()
        updated = text.replace(old_family, family).replace(old_ps, new_ps).replace('SourceSans3', new_ps).replace('SourceSerif4', new_ps)
        if updated != text: record.string = updated
    left = [r.toUnicode() for r in names.names if r.nameID not in (0, 7, 8, 9, 11, 12, 13, 14) and 'Source' in r.toUnicode()]
    if left: raise ValueError(f'Reserved Font Name still present in {family}: {left}')

def build(origin, expected, limits, output, family):
    source = fetch(origin)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if expected and digest != expected: raise ValueError(f'{name}: SHA-256 {digest} does not match {expected}')
    try: font = instancer.instantiateVariableFont(TTFont(source), limits, updateFontNames=True)
    except ValueError: font = instancer.instantiateVariableFont(TTFont(source), limits)  # STAT has no value for a pinned axis
    if family: rename(font, family)
    # Round-trip so the subsetter reads fully compiled tables rather than the instancer's lazy ones.
    staged = io.BytesIO(); font.save(staged); staged.seek(0); font = TTFont(staged)
    options = subset.Options()
    options.flavor = 'woff2'
    options.layout_features = FEATURES
    options.hinting = False
    options.name_IDs = ['*']
    options.name_languages = ['*']
    options.notdef_outline = True
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=subset.parse_unicodes(UNICODES))
    subsetter.subset(font)
    buffer = io.BytesIO(); font.flavor = 'woff2'; font.save(buffer)
    (OUT/output).write_bytes(buffer.getvalue())
    print(f'{output}: {len(buffer.getvalue())} bytes from {source.name} (sha256 {digest}) '
          f'{TTFont(source)["name"].getDebugName(5)}')

def metrics(path, sample='abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    """Average advance of a frequency-weighted sample in em units, plus vertical metrics."""
    font = TTFont(path); cmap = font.getBestCmap(); hmtx = font['hmtx']; upm = font['head'].unitsPerEm
    weights = {' ': 18, 'e': 10, 't': 7, 'a': 6, 'o': 6, 'i': 6, 'n': 6, 's': 5, 'r': 5, 'h': 5, 'l': 3, 'd': 3, 'c': 2, 'u': 2, 'm': 2}
    total = sum(weights.get(ch, 1) for ch in sample)
    width = sum(hmtx[cmap[ord(ch)]][0]*weights.get(ch, 1) for ch in sample)/total/upm
    hhea = font['hhea']
    return width, hhea.ascent/upm, -hhea.descent/upm, hhea.lineGap/upm

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    for entry in FONTS: build(*entry)
    if '--fallbacks' in sys.argv:
        system = {'Arial': '/System/Library/Fonts/Supplemental/Arial.ttf', 'Times New Roman': '/System/Library/Fonts/Supplemental/Times New Roman.ttf'}
        for target, fallback in [('Inter-Variable-latin.woff2', 'Arial'), ('PlaybookSans-Variable-latin.woff2', 'Arial'),
                                 ('PlaybookSerif-Variable-latin.woff2', 'Times New Roman'), ('ShantellSans-Variable-latin.woff2', 'Arial'),
                                 ('AtkinsonHyperlegibleNext-Variable-latin.woff2', 'Arial')]:
            w, asc, desc, gap = metrics(OUT/target); fw = metrics(system[fallback])[0]; scale = w/fw
            print(f'{target} on {fallback}: size-adjust:{scale*100:.2f}%;ascent-override:{asc/scale*100:.2f}%;'
                  f'descent-override:{desc/scale*100:.2f}%;line-gap-override:{gap/scale*100:.2f}%')
