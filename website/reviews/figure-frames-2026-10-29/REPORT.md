# Figures sit inside one frame and fit without sideways scrolling

**Owner report, 29 October 2026.** On every topic, a figure's legend, caption and text-version line spilled outside the labelled "See it" box. The figure broke out to the wide-visual width, but it had no frame of its own, so those parts hung over the box edges.

## Shared fixes (one change each, applied to every topic)

- **Framing.** `components/bundle.css` gives FigureMap figures the same ReadingSheet visual frame as step-through scenes. The frame is padded and rounded and uses the sunken surface. The surrounding "See it" label becomes the divider style used for scenes. The figure title, drawing, legend, caption and text version now sit inside one box, on desktop and on phones.
- **Inner margin.** `scripts/figure_maps.py` trims the drawing's own margin from 20px to 8px, because the frame now supplies the padding.
- **Sequences fit the frame.** Lane spacing shrinks to the frame width, and participant cards narrow with it. Long message, note and self-step labels wrap. On the last lane, labels move to the left of their loop.
- **Automatic layouts fit the frame.** Auto-layout retries progressively tighter spacing until a figure fits. Relationship maps are drawn at 1.25×, so they use a 700px layout budget.
- **Hand-placed figures.** Six manual Fundamentals models received small coordinate or label-wrap adjustments; these are data changes, not styling.
- **New command.** `tools/dev.py frames` checks every chapter page in Chrome at 1440px:
  - no element extends outside the nearest visible box that contains it (the rulebook's new common rule, §20 "Nothing outside its box");
  - no figure or map scrolls sideways;
  - every label fits its card, pill or note.

  It is a required publishing step in `AGENTS.md`.

## Verification

- `dev.py frames`: 136 pages, 79 figures, 118 relationship maps and 1,761 labels, with no problems.
- The same check against the previous live site reports 1,069 elements outside their boxes, including the "Where each clock gets its time" title, plus 122 sideways-scrolling figures and maps. This shows that the check catches the reported problem.
- `dev.py figures`: 79 models, with no problems.
- `dev.py build` passes, and preservation is intact (17,330 units).
- Website unit tests pass (15/15).
- The six browser audits pass on this build: 139/139 pages, 4,932 code checks, 1,058 Q&A pairs, binder 560/560, motion 13/13, refinement 69/69, UX 278/278 and tamper fixtures 31/31.

## Limits

- On phones, wide figures still scroll sideways inside their frame by design; this check runs at desktop width.
- The full manual mobile review remains deferred (§20).
