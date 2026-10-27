# Bundled fonts

Every face the reader serves is self-hosted from this folder. Nothing loads from a font CDN. Each family is licensed under the SIL Open Font License 1.1; the licence text from each official repository is in [`licenses/`](licenses/). The build copies this file and the licences next to the fonts on the published site.

| Role | Served family | Source | Version | File | Bytes |
|---|---|---|---|---|---|
| Interface, headings, tables, captions | Inter | [rsms/inter](https://github.com/rsms/inter) (commit `66647c0`) | 4.001 | `Inter-Variable-latin.woff2` | 48,432 |
| Code | JetBrains Mono | [JetBrains/JetBrainsMono](https://github.com/JetBrains/JetBrainsMono) | 2.211 | `JetBrainsMono-Variable-latin.woff2` | 31,340 |
| Diagram labels | Patrick Hand | [google/fonts `ofl/patrickhand`](https://github.com/google/fonts/tree/aeb9574d3cb4ab2ac5de70a8c730b11662281803/ofl/patrickhand) | 1.003 | `PatrickHand-Regular.woff2` | 62,788 |
| Modern Sans prose (default) | Playbook Sans | Source Sans 3, [google/fonts `ofl/sourcesans3`](https://github.com/google/fonts/tree/ddf386ba1b9fbc6b2c818f1ddcd9148f54ced94b/ofl/sourcesans3) | 3.052 | `PlaybookSans-Variable-latin.woff2`, `PlaybookSans-Italic-Variable-latin.woff2` | 31,392 + 31,532 |
| Book Serif prose | Playbook Serif | Source Serif 4, [adobe-fonts/source-serif 4.005R](https://github.com/adobe-fonts/source-serif/releases/tag/4.005R) | 4.005 | `PlaybookSerif-Variable-latin.woff2`, `PlaybookSerif-Italic-Variable-latin.woff2` | 40,680 + 41,060 |
| Handwritten prose | Shantell Sans | [google/fonts `ofl/shantellsans`](https://github.com/google/fonts/tree/ddf386ba1b9fbc6b2c818f1ddcd9148f54ced94b/ofl/shantellsans) (upstream [arrowtype/shantell-sans](https://github.com/arrowtype/shantell-sans) 1.011) | 1.011 | `ShantellSans-Variable-latin.woff2` (no italic file; the browser slants it) | 86,412 |
| Easy Read prose | Atkinson Hyperlegible Next | [google/fonts `ofl/atkinsonhyperlegiblenext`](https://github.com/google/fonts/tree/ddf386ba1b9fbc6b2c818f1ddcd9148f54ced94b/ofl/atkinsonhyperlegiblenext) (upstream [googlefonts/atkinson-hyperlegible-next](https://github.com/googlefonts/atkinson-hyperlegible-next)) | 2.001 | `AtkinsonHyperlegibleNext-Variable-latin.woff2`, `AtkinsonHyperlegibleNext-Italic-Variable-latin.woff2` | 20,644 + 23,756 |
| Classic Serif prose | Times New Roman | The reader's device. No file is bundled. | | | 0 |

## Why two families are renamed

Adobe licenses Source Sans 3 and Source Serif 4 with the Reserved Font Name "Source". Subsetting a font for the web makes a Modified Version under the OFL, and a Modified Version may not use a Reserved Font Name ([OFL-FAQ 2.6–2.7](https://openfontlicense.org/ofl-faq/)). The subsets are therefore named **Playbook Sans** and **Playbook Serif** inside the font files and in CSS. Their copyright notices, licence text and designer credits are unchanged. Reader-facing labels describe the style ("Modern Sans", "Book Serif") rather than the original names. Shantell Sans, Atkinson Hyperlegible Next, Inter, JetBrains Mono and Patrick Hand have no Reserved Font Name.

## How the reading fonts are made

`python website/tools/build_fonts.py` rebuilds the seven reading-font files. It needs fontTools 4.60.1 and Brotli, which are not site-build dependencies. The tool:

1. downloads each variable TTF from `google/fonts` at commit `ddf386ba1b9fbc6b2c818f1ddcd9148f54ced94b`, or from Adobe's Source Serif 4.005R release, and checks the SHA-256 recorded in the tool;
2. limits weight to 400–700 (regular, semibold and bold in running text), pins Source Serif's optical size at 18 and pins Shantell Sans' bounce, informality and spacing axes at 0;
3. keeps Google Fonts' Latin range plus the arrows, maths signs and `ł` that lesson prose uses, with kerning, ligatures and figure features; drops hinting, as the existing Inter and JetBrains Mono files do;
4. renames the two Adobe families as explained above, then writes WOFF2.

Adobe's 4.005 release fixes an hmtx defect in the Source Serif variable TTFs (`adobe-fonts/source-serif#110`); `google/fonts` still carries 4.004, so Source Serif comes from the release. Inter and JetBrains Mono predate this typography pass and are unchanged. The Inter subset reports version 4.001 and was built from rsms/inter commit `66647c0` (May 2024), 13 commits before the v4.1 release tag. JetBrains Mono's latest release is 2.304; the bundled subset is 2.211.

`python website/tools/build_fonts.py --fallbacks` also prints the metric overrides for the local fallback faces in `tokens.json` (`size-adjust`, `ascent-override`, `descent-override`). Text set in Arial or Times New Roman while a web font loads then takes about the same width and line height, so lines barely move when the font swaps in.

## Loading

Every face uses `font-display: swap`. Each page preloads Inter, plus the reader's chosen prose font from a small head script that runs before first paint; Classic Serif needs no preload. Other reading fonts and the italics download only when a page uses them. Shantell Sans ships no italic: the browser slants it, which suits a handwriting face and saves 89KB. A reader on the default font downloads Inter and Playbook Sans, Playbook Sans Italic when the lesson has emphasis, and, as before, JetBrains Mono and Patrick Hand where it has code and diagrams.

SHA-256 of the served files:

```text
272ebc8193addb98174ddc40288a67294ca1d9f843b5cd5c5a0481b6b3a7529c  AtkinsonHyperlegibleNext-Italic-Variable-latin.woff2
b82cfa66cc94a30c7489d3be51908e3761e9362d4b533228f835cd568d181274  AtkinsonHyperlegibleNext-Variable-latin.woff2
c940764593d0fe5d596be327ca7558855e018039fb78509aa21921fd3644c3e4  Inter-Variable-latin.woff2
2c32b9b3ee358c119e210f6f5195f9bd34894d78a785ff2e95d60e718e400af4  JetBrainsMono-Variable-latin.woff2
9a110f3256ddfad81226edda134ae25d3adb1bcb18b39fcf82e3df3cc5ccbc5f  PatrickHand-Regular.woff2
1472e8bf2e9d503a3d0045293926a371824423a25a7522f3fa221260ec62ee92  PlaybookSans-Italic-Variable-latin.woff2
641058f4c05f5984b8c18decc7d99096881e32a2ea5c82d7c4963de82c8dd044  PlaybookSans-Variable-latin.woff2
637e288738d32c002dddea3d48eba2c0b580d9661ac0233e6a96ac01f3adf515  PlaybookSerif-Italic-Variable-latin.woff2
9915e3bde6a3ce7646b5fa49508d0b855230463c081dec7bf68b6e86d4f04497  PlaybookSerif-Variable-latin.woff2
10ecaa90f1600cee2e88a159be1ade1e9a4a914d5211c2c8e7318ef2a6a1c966  ShantellSans-Variable-latin.woff2
```
