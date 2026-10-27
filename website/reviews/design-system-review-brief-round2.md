# Review brief, round 2: Playbook Design System

Re-review the design system after the round-1 fixes and one owner decision. Report **findings only**: do not edit files, commit, push or publish. Branch `codex/android-completion` in the website repo.

## Context

- **Round 1:** your findings on `61b97a5` were all accepted. Their fixes and evidence are in `website/reviews/design-system-review-disposition.md`, landed in `3868e64`.
- **Owner decision after round 1:** static diagrams should scroll sideways on phones instead of reflowing. Moving diagrams keep a stacked phone layout, because their cause and effect must stay on screen together.
- **Round 2 commit:** this brief and its changes, on top of `3868e64`.

To see the previews, run:

```bash
cd /Users/swaransinghaulakh/AndroidStudioProjects/android-staff-engineer-playbook-website && python3 website/tools/build_design_system_preview.py
```

Then open `website/.cache/design-system-preview/index.html`.

## What changed in round 2

1. **WideDiagram, a new component:** `components/WideDiagram/`.
   - Static drawings keep a readable `min-width` and scroll sideways inside their own box.
   - `overscroll-behavior-x: contain` stops sideways swipes from triggering browser navigation.
   - Edge fades and a one-line hint appear only while the box overflows.
   - The box is focusable and named only while it overflows.
   - Drawings are capped at 1.2× their drawn size on wide screens.
2. **Generated layouts for row flows:** `autoLayouts()` in `components/bundle.js`.
   - When a FlowDiagram lists `nodes` in order and `edges` as `{id, from, to, tone, lane, label}` between neighbouring nodes, the runtime generates both the `wide` row and the `narrow` column.
   - Both FlowDiagram examples now use this. FlowScene still authors its layouts explicitly.
   - Labels may contain a line break.
3. **Upscaling cap:** stacked layouts cap at 440px; wide engine layouts cap at 1.2× their viewBox width.
4. **Docs:** `motion.md` (the Phones section), `README.md`, and the FlowDiagram and WideDiagram READMEs.

## Questions

1. **Round-1 fixes.** Do they hold? In particular:
   - Does Pause cancel packets in flight?
   - Is the live motion state shared with `html.reduce-motion`?
   - Do the stacked layouts keep labels at 15px or more at 320px?
   - Are outlines at 3:1 or better?
   - Are the fonts self-hosted?
   - Does high contrast use borders instead of tints?
2. **WideDiagram accessibility.**
   - Is the scroll region usable by keyboard and screen reader?
   - Is it right to add `tabindex` only while the box overflows?
   - Is the hint redundant or noisy for screen readers? It is `aria-hidden`; the region's name says it scrolls.
   - Does `overscroll-behavior-x` behave as intended on iOS Safari and Android Chrome?
3. **Minimum-width rule.** Is "labels 15px or more, sub-labels 12px or more at `min-width`" sound and clearly written? Is anything in the preview below it?
4. **`autoLayouts()` correctness.**
   - Is the edge geometry right for both directions?
   - Does it reject non-neighbour edges clearly?
   - Are order markers numbered only for toned edges, and placed sensibly?
   - Do multi-line labels stack correctly?
5. **Live layout switch.** Round 1 could not verify switching layout while the window is resized across 520px; the test pane stopped painting frames. Can you verify it in a real browser?
6. Anything else that is wrong, inconsistent or over-built.

## Output format

Number each finding and give it a priority: P1 (wrong, inaccessible or broken), P2 (weak or inconsistent), P3 (polish). For each, give the file and line, the problem, the evidence, and a concrete fix. End with what you checked and found sound.
