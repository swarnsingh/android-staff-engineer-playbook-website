# Phone layouts for wide figures

## Scope

This milestone gives wide figures a phone composition in the shared FigureMap renderer, so they no longer scroll sideways at 375px. It starts from website main `f7b4b19` (PR #35). It changes shared code only: `figure_maps.py`, `diagram_models.py`, `tokens.json`, the FigureMap README, the phone frame check's summary and the page audit's relationship-map check. No lesson file, figure model, blend, correction or original chapter changed.

## Before and after at 375px

`phone-inventory.json` lists every element inside the reading column that scrolls sideways at a 375px viewport. Code blocks and tables scroll by design and are not counted.

| Scrolls sideways at 375px | Before | After |
|---|---|---|
| FigureMap figures (339 on pages) | 278 | 111 |
| Relationship maps beside step-throughs (137) | 137 | 136 |
| FlowScene step-throughs | 21 | 21 |

`dev.py frames-phone` now prints these local-scroll counts on every run, so the open-work numbers in `AGENTS.md` can be reproduced.

## The phone ladder

FigureMap already tried to reflow a map's owner columns into 260px. Only 61 models fit that way. When it does not fit, the renderer now tries a one-column composition:

- Cards stack in relationship order. Each owner boundary's members stay together, so every boundary still encloses exactly its own cards.
- A relationship to the next card drops straight down with its numbered label on the line. If that line would cross a boundary label, it moves right or takes a dog-leg. Failing both, it uses a lane.
- Every other relationship leaves its source on a row of its own, carrying its numbered label. Back edges and self-relationships are included. The line then runs in a lane beside the column and enters its target from the side. Lanes are assigned shortest first, so nested relationships never cross.
- Text keeps its design-system sizes. Labels wrap between words, trying wider budgets first. Card text never breaks inside a word, and a model whose longest word does not fit keeps its wide drawing.
- A boundary label wider than its phone boundary wraps between words onto a second header line.
- Edges that share one bus and one number in the wide drawing are separate lines on the phone. Each keeps that number and label.
- Besides the usual card and label collision checks, the ladder rejects any label that would hide part of another relationship's line.

Every dimension is a `phone-*` (or `boundary-label-line`) token in `figureGeometry`. The 260px budget is unchanged: it also fits a 360px Android phone, whose figure column is 278px.

Relationship maps beside a step-through use the same ladder at their 1.25× scale. That scale keeps every label, including 12px boundary labels and number badges, at 15px or more, as §20 requires. It leaves 208 drawing units, which fits only one map's cards and owners.

## Meaning is unchanged

`phone-parity.json` compares the renderer on this branch with main for all 343 figure models (268 original redraws, 75 teaching maps):

- All 343 wide drawings are byte-identical to main.
- All 61 phone drawings that existed before are byte-identical.
- 169 models gain a phone drawing, for 230 in all; every one is at most 260px wide.
- Every phone drawing carries exactly the numbered labels of its wide drawing. Its text is the same apart from line breaks, and apart from bus labels repeated on each separate line.

Rendered meaning is unchanged: the same cards, owners, labels, arrow directions, dashed and two-way styles, captions, legends and text transcripts. Only positions and line breaks differ. Eight regression tests in `scripts/test_phone_ladder.py` cover:

- numbered labels and text;
- endpoints;
- boundary membership;
- hidden lines;
- word splitting;
- wrapped boundary labels;
- shared bus numbers;
- the narrow-column fallback.

## What still scrolls, and why

Each remaining figure keeps a labelled, keyboard-accessible local scroll. §20 asks for that when a phone composition would lose relationships or shrink text.

- **111 FigureMap figures:**
  - 44 sequence diagrams, whose lanes carry meaning;
  - 33 graphs that need more lanes or nested owners than a phone column can spare;
  - 19 with more labelled relationships leaving or entering one card than fit beside each other;
  - 11 with a code identifier longer than a phone card, such as `ActivityTaskManagerService`;
  - 4 state diagrams with start and end symbols.
- **136 relationship maps,** for the 15px rule above.
- **21 FlowScene step-throughs,** which keep their authored cross-process lanes (`pickLayout` in `bundle.js`).

## Validation

- `dev.py build`: 35,912 original units preserved in order across 295 pages, and all 22 preservation tampering fixtures detected.
- `dev.py figures`: 268 original and 197 teaching models, no problems.
- `dev.py frames`: both sweeps pass across 279 chapter pages, at 1440px and at 375px.
- `dev.py ci`: 72 website tests (64 before, plus 8 new), 33 docs tests, the docs check, 74 Java snippets and 15 browser-script syntax checks.
- Six browser audits:
  - pages 295/295, with 8,908 code checks and 1,732 original Q&A pairs;
  - Binder theme, font and width matrix 560/560;
  - motion 13/13;
  - refinement 69/69;
  - UX 278/278;
  - deliberate tampering 31/31.

The first full audit failed one page, `android/compose/modifiers-and-layout`. Its relationship map is the one that gained a phone drawing, and the page audit counted actors and arrows across both drawings and measured the hidden one. `browser_audit_runner.js` now checks that each drawing has every actor, owner and arrow, that exactly one drawing is shown, and that the shown drawing's labels are at least 15px. The failed result is kept in `attempts/01-relationship-variant/`. The final audit ran against the corrected tool.

In a 375px browser viewport, representative phone drawings were inspected for reading order, lane crossings and boundary clearance. These covered a decision tree, an offline-first architecture with three owners, a release-branch graph with self-relationships and back edges, and a mutex comparison with a wrapped boundary label.

## Limits

These are automated checks plus spot checks in a 375px browser viewport. They are not a manual phone review: §20 defers the single consolidated manual review until the whole website is integrated. At a 320px viewport, the figure column is about 238px, so a 260px phone drawing still scrolls by about 22px there, as the existing compact drawings already did.
