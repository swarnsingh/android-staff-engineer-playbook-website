# Principles reader rollout

## Source and learning path

The Principles index and all 11 chapters match the merged playbook at [source PR #81](https://github.com/swarnsingh/android-staff-engineer-playbook/pull/81), commit `45201470a80d644a12eac0d9ff787e34f09062a2`. Each of the 12 files was compared byte for byte against that commit. `source-snapshot.json` records the corresponding hashes and provenance.

The learning path follows the original guided order from Simplicity through Optimize for Change. Three groups organize the same sequence around responsibilities and contracts, locality and simplicity, and failure and change. All 106 original questions and answers use the existing Q&A experience.

Each chapter opens on a concrete design problem and adds one short note on applying the principle during review. The notes distinguish code locality from memory locality, format invariants from data existence, and rollback of UI behavior from recovery of stored records.

## Figures

The shared FigureMap component redraws all 12 original diagrams, including the three views of locality. Each map has labelled relationships, role styling and a caption. The original diagram source remains available in its own disclosure. These are static comparisons and relationship maps.

## Evidence

- Full build preserved 31,833 original units across 261 pages in source order. The 22 preservation tampering fixtures passed.
- Figure validation passed 232 original diagram models and 197 teaching models.
- Browser frame checks passed all 249 lessons at 1440 px and 375 px, covering 303 figures, 137 relationship maps and 4,609 labels at each width. No overflow or label problems were reported.
- Local CI passed 64 website tests, 31 docs tests, the docs gate, 74 Computer Science Java examples, and 15 browser-script syntax checks.
- A desktop preview check followed all three phase cards to their first lessons and verified that each hero summary differs from its opening story. All 12 figures and captions stayed within their frames in light, dark, sepia and high contrast. Original-diagram disclosures opened on the three sampled lesson pages. The browser reported no page exceptions.

The desktop captures show the [learning path](principles-learning-path-desktop.png), [composition comparison](composition-over-inheritance-figure-desktop.png), [package layout](locality-of-reference-figure-desktop.png) and [timeout fallback](design-for-failure-figure-desktop.png). Cropped figure captures omit the sticky viewport controls. Phone evidence here is automated. The consolidated manual phone review follows integration of the remaining topic trees.

## Full site audit

All six audit suites passed on the combined site. The browser checked 261 pages, 8,528 code readability cases and 1,587 original Q&A pairs, including all 106 Principles pairs. The Binder suite passed 560 checks, motion 13, refinement 69, UX 278, and Q&A tampering 31. The publication gate binds this evidence to the lesson inputs and rechecks original preservation when building at the GitHub Pages project path.
