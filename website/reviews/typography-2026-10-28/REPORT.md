# Reading typography refinement

The owner asked for a refinement of the existing typography system and Reading settings, not a redesign: five prose fonts with a textbook body, while interface, headings, code, diagrams and data tables keep their faces. This is a presentation-layer change. Chapter Markdown, explanations, corrections, citation data, diagram semantics and animation, and navigation logic are unchanged.

## What changed

**Two typographic roles.** Inter remains the interface face: navigation, buttons, tabs, labels, H1 (700), H2 and H3 (650), tables, captions and diagram text. The reader's chosen font now applies only to prose: paragraphs, list items, blockquotes, callout text and Q&A. Previously the reading font also reached tables, captions, step transcripts and stepper controls; those now stay in Inter whatever the reader picks.

**Five reading fonts**, each a token swap on `html[data-reader-font]`:

| Option | Face | Notes |
|---|---|---|
| Modern Sans | Source Sans 3, served as "Playbook Sans" | New default for article prose, replacing Inter there |
| Book Serif | Source Serif 4, served as "Playbook Serif" | Was a single SemiBold file; now regular to bold with true italics |
| Classic Serif | Times New Roman | The device's own font; nothing bundled |
| Handwritten | Shantell Sans 1.011 | Now 400–700; the browser slants it for emphasis |
| Easy Read | Atkinson Hyperlegible Next 2.001 | New. Presented as an alternative some readers find easier, not a better default |

Adobe reserves the name "Source" in both Source fonts, and a web subset is a Modified Version under the OFL ([OFL-FAQ 2.6–2.7](https://openfontlicense.org/ofl-faq/)), so the two subsets are renamed inside the font files and in CSS. Their copyright notices and licence text are unchanged. The old `SourceSerif4-SemiBold-latin.woff2` subset still carried the reserved name and is removed. Every bundled family's OFL text now ships beside the fonts; before this pass only Patrick Hand's did. Sources, versions, hashes and the rebuild tool are recorded in [design-system/fonts/README.md](../../design-system/fonts/README.md).

**Body text.** Prose is 18px, line height 1.7, weight 400, with 1.1em between paragraphs. `font-size-adjust` gives each prose font the same x-height, so 18px looks the same size in every option; only Times New Roman, small on its body, is visibly scaled. Each font has its own measure, calibrated by rendering lesson paragraphs, so every option sets a median of about 70 characters a line. At the previous 760px column, Source Sans 3 set about 93. Prose and prose-only callouts take that measure, while code cards, tables and diagrams keep the full 760px column they had before. The column keeps its left edge, aligned with the hero, tabs and breadcrumbs.

**Code** uses JetBrains Mono everywhere: 0.86em with line height 1.6 in code cards, the playground, diagram code pairs and Mermaid source; 0.85em inline. Previously code cards used line height 1.85, phones dropped to 0.82em, and diagram node code used the system monospace stack. Patrick Hand still labels diagrams. Data tables keep Inter.

**Reading settings.** The panel keeps its select and live preview. Options are generated from `tokens.json`, and a description under the select says what each font is for. Choosing a font applies immediately. The page does not reload, the active tab, diagram step and text size stay as they were, and the line under the header stays in place while text reflows (anchored on the nearest visible block by layout position; the browser's own scroll anchoring is suspended for that frame so the correction is not applied twice). Saved choices from the four-font version map to their successors (`sans`, `serif`, `times`, `hand`). A reader who never chose a font follows the default and nothing is written for them, so a later default change still reaches them.

**Loading.** All faces use `font-display: swap` and metric-matched local fallbacks (`size-adjust` and ascent/descent overrides measured against Arial or Times New Roman). Each page preloads Inter, and a small head script preloads only the reader's chosen prose font and applies it before first paint. Other reading fonts and italics load when used. Nothing loads from a font CDN.

## Performance

Font bytes downloaded on a first visit to each of the five test lessons, cache disabled (all five lessons use the same files):

| Setting | Before | After | Preloaded |
|---|---|---|---|
| Default | 142,560 (Inter, JetBrains Mono, Patrick Hand) | 205,484 (+ Playbook Sans and its italic) | Inter, Playbook Sans |
| Book Serif | 164,048 (SemiBold only) | 224,300 | Inter, Playbook Serif |
| Classic Serif | 142,560 | 142,560 | Inter |
| Handwritten | 284,716 (also fetched a duplicate Patrick Hand) | 228,972 | Inter, Shantell Sans |
| Easy Read | (new) | 186,960 | Inter, Atkinson Hyperlegible Next |

Fonts are cached across lessons, so this cost is paid once per site visit. Before this pass nothing was preloaded. Measurements are in [font-bytes.json](font-bytes.json).

## Verification

All checks ran on the final build in headless Chrome 151 (puppeteer 25.4.0), against a local root-path build.

- **Typography matrix** ([typography-matrix.json](typography-matrix.json)): five lessons named in the brief (Process Death and State Restoration, ViewModel, Compose Recomposition and State, Coroutines, Sealed Classes and Interfaces) plus both learning paths; five fonts; four themes at desktop and Light and High contrast at tablet, 390px and 320px. For each it checks the font is applied and loaded, prose uses it and nothing else does, headings stay Inter 600–700, code stays JetBrains Mono at 0.85–0.9em with line height 1.55–1.65, tables and diagram labels are unchanged, prose is 18px/1.7, prose contrast is at least 4.5:1 and the page does not overflow. 3,640 checks, all passed.
- **Interaction** ([typography-interaction.json](typography-interaction.json)): legacy ID mapping with size, theme and wrap preserved; default never persisted; unknown IDs fall back without overwriting; only the active font preloaded and no unchosen font fetched; on all seven pages at 1440px and 390px, switching through every font keeps the reading line (paragraph top within 3px, mid-paragraph within 0.08 of its height), the Q&A tab, a stepped diagram's position and a 20px text size; keyboard access to the font control in every theme with a 2px focus ring at 3:1 or more, type-ahead selection applied live to page and preview, Escape returning focus; reduced motion; 200% zoom, and a 200% default font size or the 22px reading size at 320px. 103 checks, all passed.
- **Repository browser audits**, from `prepare_browser_audit.py`: the full sweep passed all 125 pages, 1,736 layouts, 928 original question/answer pairs and 4,732 code presentation and contrast checks; Binder 560 of 560 combinations; motion 13 of 13; gallery/reader refinement 69 of 69; UX 278 of 278; Q&A preservation fixtures 31 of 31.
- **Static checks:** the build verifies 125 pages and 15,564 original units with no preservation problems; browser-script syntax checks, the 3 renderer tests, the 31 documentation-checker tests and the documentation gate pass.
- **Screenshots** in [images/](images/): before/after at desktop, tablet, 390px and 320px, the Reading settings panel, every font in every theme, and the gallery specimen.

## Fixes to the checks themselves

- The Binder matrix now iterates every font the panel offers (560 combinations, up from 448) and switches fonts through `data-reader-font`. The full sweep's worst case selects Handwritten the same way. Both previously set the retired `--reader-font` property.
- The Binder Q&A check still looked for answer-key list items, which the previous publication moved beside their questions. On an untouched copy of `main` it failed 224 of 448 combinations; it now checks each answer pair's heading and original answer-key item, keeping the 13-label count, and passes 448 of 448 on `main` ([binder-main-baseline.json](binder-main-baseline.json)). The evidence recorded for that publication shows a pass, so it was produced before that change.
- `check_completion.py` reads the current review folder from `validation.json` instead of a fixed path, and derives the Binder count from the number of reading fonts.

## Remaining limitations

- Checked in Chromium only (headless Chrome 151). Safari and Firefox were not run. `font-size-adjust` needs Chrome 127 or Safari 16.4 and later (MDN compatibility data); older browsers show each font at its natural size. Physical devices and screen readers were not tested.
- At 320px with a 200% browser default font size, the top-bar buttons overflow by 188px. This is identical on `main` and outside this change; lesson content itself fits.
- Classic Serif depends on the device. Android has no Times New Roman, so it falls back to Liberation Serif, Noto Serif or the system serif.
- Fallback metrics are tuned to Arial and Times New Roman. On systems without them (for example Android, which uses Roboto) the swap moves text slightly more.
- Inter (built from rsms/inter `66647c0`, 13 commits before v4.1) and JetBrains Mono (2.211; latest 2.304) predate this pass and were not updated.
- Code nested inside list items keeps its list indentation, as before.
