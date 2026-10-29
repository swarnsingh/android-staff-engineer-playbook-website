# Designed figures replace Mermaid in Engineering Fundamentals

Owner direction, 29 October 2026: no Mermaid pictures, no colourless diagrams and no ordinary animations on the website. All styling lives in the shared design system. The owner approved the Time & Clocks prototype and asked for a rollout across Engineering Fundamentals. The rule is recorded in `content-rulebook.md` §20, "Designed visuals only".

## Delivered scope

- **FigureMap, a new shared design-system component.** Models in `content/diagram-models/figures/engineering-fundamentals.json` are bound to a diagram by its source hash. `scripts/figure_maps.py` lays out the geometry; colours, type, border patterns and legends come from the existing actor tokens through the `.fm-*` rules in `components/bundle.css`.
- **What each figure has:**
  - role-coloured title-and-detail cards;
  - numbered, labelled arrowheads;
  - owner boundaries;
  - a legend for the roles it uses;
  - a numbered caption that states its point;
  - a "Read the figure as text" transcript;
  - official sources.
- **38 figures in total:** 27 original chapter diagrams and 11 teaching-layer diagrams.
  - The original diagrams keep their Mermaid source as preserved text under "Original diagram from the chapter".
  - No rendered Mermaid picture remains on any Fundamentals page.
- **Build-time checks.** The build rejects:
  - clipped card labels, and boundary labels wider than their boundary;
  - labels that overlap each other or a card;
  - lines that pass through a card;
  - actors with two owners;
  - unlabelled relationships;
  - figure models without a matching diagram.
- **FlowScene layout, which changes every step-through scene on the site.** Order is now: picture, progress bar, step caption, then one row with step dots, Previous/Play/Next and Reset. The sideways-scroll hint appears only when a scene overflows.
- **Gate inputs.** The publication fingerprints now include `scripts/figure_maps.py` and the figure models.
- **Preservation audit.** `scripts/browser_preservation.js` counts a FigureMap redraw as the rendering of the original diagram whose preserved source it names; the figure must contain drawn actors.

## Verification

All results in this folder come from a full build with diagrams rendered, run headlessly in Chrome against the instrumented QA copy:

| Suite | Result |
|---|---|
| `browser.json` | 139/139 pages pass: preservation in order, seven widths, enlarged text, scenes, code readability (4,932 checks, 47 in nested lists) and 1,058 Q&A pairs. All 27 original-diagram figures count as rendered. |
| `binder.json` | 560 theme × font × size × width × view checks, no problems |
| `motion.json` | 13/13 |
| `refinement.json` | 69/69 |
| `ux.json` | 278/278 |
| `qa-tampering.json` | 31/31 preservation negative fixtures detected |
| `kotlin-validation.json` | Carried over unchanged: no Kotlin fragment or fixture changed, and the gate re-verifies their hashes. |

Additional checks:
- In a real browser with the bundled fonts, every card, pill, note and boundary label fits its shape in all 38 figures.
- All 38 figures were reviewed visually on desktop. Representative figures were checked in dark theme and at 375px width, where figures keep 15px labels and scroll sideways inside their own frame.

## Boundaries

- Kotlin and Android still render Mermaid source diagrams and Mermaid-laid-out relationship maps. Under the new rule, migrating them is the next task.
- On phones, wide figures scroll sideways instead of switching to a dedicated narrow composition.
- The full manual mobile review remains deferred until the whole website is integrated, per §20.
