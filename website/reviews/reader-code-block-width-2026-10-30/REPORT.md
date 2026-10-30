# Code blocks stay in the text column

## Change

Owner rule, 30 October 2026: code blocks keep the existing text-column width on every topic and scroll sideways. They no longer widen like diagrams and step-throughs. The fix is in the shared design system, not per lesson:

- **`design-system/components/bundle.js` (ReadingSheet):** on screens 641 px and wider, ReadingSheet added `content-bleed` to any code card whose lines overflowed, which widened it into the 1000 px visual frame. It now considers only tables for that expansion. Code cards stay at the 760 px text column and scroll inside the card, with the existing edge fade and hint.
- **`design-system/components/bundle.css`:** the "Original diagram from the chapter" disclosure, which shows a diagram's Mermaid source as a code block, is removed from the wide visual-frame selector. It now stays in the text column too.
- **Docs:** the ReadingSheet and CodeCard READMEs and the `measure-wide` token note now state the rule.

Diagrams, step-throughs and tables are unchanged.

## Evidence

A headless scan covered every built page at 1440, 1024 and 375 CSS pixels. It looked at 1,708 code blocks: code cards plus original-diagram disclosures.

| Measure | Live site before (sample of 30 Kotlin and Mobile System Design pages, 1440 px) | This build (all pages) |
| --- | --- | --- |
| Code blocks wider than the text column | 140 of 451 | 0 of 1,708 at each width |
| Code cards that scroll sideways inside the card | 31 | 416 at 1440 and 1024 px; 1,602 at 375 px |
| Diagrams and step-throughs wider than the text column | 52 | 241 at 1440 and 1024 px (unchanged behaviour) |
| Tables with `content-bleed` | 0 | 0 |
| Pages that scroll sideways | 0 | 0 |

All four local checks pass:

| Check | Result |
| --- | --- |
| `dev.py build` | 175 pages; 22,108 original units preserved in order |
| `dev.py frames` | 169 pages, 112 figures, 128 maps and 2,357 labels; no problems |
| `dev.py ci` | website tests, docs tests, docs check and browser-script syntax |

## Browser audit

All six fresh browser audits passed on this build:

| Audit | Result |
| --- | --- |
| Browser preservation | 175/175 pages; code 6,280/6,280; Q&A pairs 1,194/1,194 |
| Binder | 560/560 |
| Motion | 13/13 |
| Refinement | 69/69 |
| UX | 278/278 |
| QA tampering | 31/31 |
