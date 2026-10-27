# Review brief: Playbook Design System (final draft, 26 Oct 2026)

Review the proposed design system for the reader website. Report **findings only**: do not edit files, commit, push or publish.

## What to review

All files are in `website/design-system/`:

- `README.md`: principles, surfaces, colour roles mapped to Compose `ColorScheme`, the type scale mapped to Compose `Typography`, shapes, what changes from today's site, and the three default choices.
- `motion.md`: motion values, when a diagram may move, FlowDiagram and FlowScene behaviour, and when motion must stop.
- `tokens.json`: 22 colour tokens in 4 themes (light, dark, sepia, high contrast), 4 font families, 12 text styles, spacing, radius, shadow and layout tokens.
- `components/<Name>/README.md` and `preview.html` for ReadingSheet, Callout, CodeCard, Checkpoint, FlowDiagram, FlowScene and the Cover.

To see the previews locally, run:

```bash
python3 website/tools/build_design_system_preview.py
```

Then open `website/.cache/design-system-preview/index.html`. It shows every component in all four themes. The owner also has the published version, a private claude.ai artifact.

## Questions to answer

1. **Contrast.** Does every text and label pair named in a token's `usage` meet 4.5:1 in all four themes? Do diagram strokes, chip borders and focus rings meet 3:1? Pay particular attention to:
   - `ink-muted` on `canvas` and on `sheet-sunken`;
   - label text on `accent`, `event` and `warn` fills;
   - the `code-*` colours on `code-bg`.
2. **Colour meaning.** The rule is "green forward, blue back, orange stuck". Do those three stay distinguishable for common colour-vision deficiencies and in high contrast? Is any meaning carried by hue alone?
3. **Motion accessibility.**
   - Do FlowDiagram and FlowScene honour `prefers-reduced-motion`?
   - Do they pause off screen, and is there a visible pause control (WCAG 2.2.2)?
   - Can everything be operated by keyboard?
   - Is the "Read every step as text" list a complete text alternative?
4. **FlowScene engine** (`components/FlowScene/preview.html`, inline script).
   - Is the state computation from the step list correct for Previous, Reset and the mode switch?
   - Does cancellation (the `token` counter) leave stray packets or an inconsistent state when buttons are pressed mid-animation?
   - Does it leak `requestAnimationFrame` loops or timers?
5. **Technical accuracy of the Binder pilot.** Check every caption in both tracks against Android and AOSP documentation. Key claims:
   - a synchronous `transact()` blocks the caller until the reply;
   - transactions queue when no Binder thread in the target is free;
   - `oneway` methods cannot return a result and do not wait for the service;
   - "One-way methods from the same thread to the same binder also execute serially" (AOSP AIDL language page).

   Timings are labelled illustrative. Flag any caption that overstates a guarantee.
6. **Fit with the site.**
   - Can this be implemented on the existing static build (`website/scripts/build.py`, `app.js`, blend files) without adding React?
   - Does it conflict with `content-rulebook.md`, for example the Q&A tab rule, the 25% added-prose cap or the Under review note wording?
   - Does the reader-settings override (font, size, theme, motion) still work?
7. **Design quality.**
   - Does the typography hold up for 3,000 to 6,000-word lessons at 320, 390, 768 and 1280px?
   - Are the callout kinds distinct without icons?
   - Is anything generic, inconsistent or over-designed?

## Output format

Number each finding and give it a priority:

- **P1:** wrong, inaccessible or broken.
- **P2:** weak or inconsistent.
- **P3:** polish.

For each finding, give the file and line, the problem, the evidence (a contrast ratio, a doc quote with its URL, or a reproduction), and a concrete fix. End with a short list of what you checked and found sound.
