# Review brief, round 4: design system applied to the site

Review the reader after the Playbook Design System was applied. Report **findings only**: no edits, commits, pushes or publishing. The work is on branch `codex/android-completion` in the website repo, in the latest commits after `6495d3a`.

## What changed

1. **Site application.**
   - `build.py` compiles `design-system/tokens.json` into `dist/tokens.css`. The old variable names are aliases, so existing styles take the new palette.
   - `theme.css` applies the reading sheet, callout tints, code font, rail breakpoints (curriculum rail from 1440px, outline rail from 1181px) and high contrast.
   - `flow.css` and `flow.js` are the diagram runtime.
2. **Binder lesson.** Its step-through is replaced by the FlowScene pilot.
3. **Mermaid figures.** `blend.js` sizes each figure to at least 0.75 of its drawn width, so text stays at 12px or more, and the figure scrolls sideways otherwise.
4. **Code cards.** An overflow cue appears when a line runs past the edge. The design-system CodeCard has a Wrap lines toggle; on the site, wrapping is the reader setting.
5. **Checkpoint.** The question sits in one wrapped span (review round 3b).
6. **Dark theme.** It is now a navy page with a slate sheet and two faint glows. Contrast was checked: text ≥7.29:1 and outlines ≥3.22:1 on every dark surface.
7. **Fonts.** Shantell Sans (self-hosted) is the reader's handwritten setting. Diagram labels stay in Patrick Hand because Shantell is about 25% wider.
8. **Every step-through (138).** Moving forward sends a packet from the previously active box to the newly active one. Back and Reset jump without motion. Pause, reduced motion and leaving the screen cancel the packet.

## Questions

1. **Full-lesson check.** Does the Binder lesson read well at 320, 390, 768 and 1280–1440px, in both tabs and all four themes, with the reader's font and size settings?
2. **Handoff packets.**
   - Is the "previously active → newly active" rule right for most step-throughs?
   - Find step-throughs where it suggests a flow that isn't real, so they can opt out.
   - Does a packet ever stay behind after Pause or reduced motion?
3. **Navy dark theme.** Are contrast and legibility fine? Do the glows interfere with reading?
4. **Breakpoints and Topics drawer.** Is anything clipped or does the page scroll sideways at 1181–1439px?
5. **Regressions.** Any regressions in Kotlin pages, which share the reader?

## Output format

Number each finding and give it a priority: P1, P2 or P3. Give the file and line, evidence, and a fix.
