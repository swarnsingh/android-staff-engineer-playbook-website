# Designed figures across the whole website

The owner asked, 29 October 2026, to remove Mermaid from the Android and Kotlin topics as well and merge the result into `main`. This follows the Engineering Fundamentals rollout in [figure-maps-2026-10-29](../figure-maps-2026-10-29/REPORT.md) and rulebook §20, "Designed visuals only".

## Delivered scope

- **The 41 Android diagrams that were still Mermaid pictures** are now FigureMap models in `content/diagram-models/figures/android.json`.
  - Actors, owner boundaries, relationships and original labels come from each Mermaid source.
  - Roles, labels for relationships the original left unlabelled, captions and layout choices are authored.
  - Sources come from the chapter's own verified references.
  - The KMP source-set tree is drawn as nested containment boundaries instead of arrows.
- **The 118 relationship maps beside step-throughs** are drawn by FigureMap from their existing authored models. Mermaid no longer lays them out. They render at 1.25×, so every label displays at 15px or more.
- **The 54 original diagrams that already had authored HTML redraws** keep only their preserved Mermaid source text in "Original diagram from the chapter"; the rendered Mermaid picture is gone.
- **Build enforcement.** The build no longer renders Mermaid at all, and it fails if any page shows a rendered Mermaid picture. No page does: 79 designed figures and 120 relationship maps are all FigureMap SVG.
- **Automatic layout in FigureMap,** with three modes:
  - columns per owner boundary;
  - layered trees with shared bus labels;
  - snake pipelines.

  Routes are scored for fewest crossings: 15 of 155 automatically placed figures have any crossing, and none has more than two. The build rejects:
  - clipped or overlapping labels;
  - lines through cards;
  - boundaries that visually enclose cards they do not own.
- **Tests and audits.** The diagram-model tests and the browser audit's relationship-map checks now inspect FigureMap output. They keep the same guarantees: actor, owner and arrow counts; labels inside cards; text size; no markup injection; nested ownership.

## Verification

All six suites ran headlessly in Chrome on a full build:

| Suite | Result |
|---|---|
| `browser.json` | 139/139 pages: preservation in order, seven widths, enlarged text, scenes and relationship maps, code readability (4,932 checks) and 1,058 Q&A pairs. All 120 original-diagram redraws count as rendered. |
| `binder.json` | 560 checks, no problems |
| `motion.json` | 13/13 |
| `refinement.json` | 69/69 |
| `ux.json` | 278/278 |
| `qa-tampering.json` | 31/31 |
| `kotlin-validation.json` | Carried over unchanged; the gate re-verifies the fragment hashes. |

Additional checks:
- In a real browser with the bundled fonts, every card, pill, note and boundary label fits its shape in all 197 figures on the 136 chapter pages.
- A visual sample of Android figures and relationship maps was reviewed on desktop.
- Website unit tests: 15/15 pass.

## Remaining gaps against the rulebook

- **181 teaching-layer HTML diagrams** (766 cards) in Kotlin and Android lessons use neutral cards without role colours, legends or numbered captions. This includes the 50 HTML redraws of original diagrams. They still need conversion to FigureMap or role styling in the shared `viz` component.
- **Lesson length.** About 40 of 106 Kotlin and Android lessons may exceed the "added prose under about a quarter of the original" target. The estimate includes some visual text, so these lessons need a proper review before any trimming.
- **Phone layouts.** On phones, wide figures scroll sideways instead of switching to a dedicated narrow composition. The full manual mobile review remains deferred as §20 requires.
