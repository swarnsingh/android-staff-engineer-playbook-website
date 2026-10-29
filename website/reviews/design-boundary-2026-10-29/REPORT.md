# Content is the only per-topic layer

Owner rule, 29 October 2026 (rulebook §20): everything except topic content is controlled by the design system, so a single change restyles every topic.

## Changes

- **Lesson files carry no styling.** The 318 inline styles are gone:
  - grid column counts became `data-cols`, read by the shared grid components;
  - timeline positions became `data-at`/`data-len`, which the build turns into the timeline component's variables;
  - eight raw margin, padding or width styles became shared node variants (`is-lead`, `is-spaced`, `is-gap-after`).
- **The ViewModel ownership component's CSS** moved from its lesson file into the shared component bundle.
- **Colours come from `tokens.json`.**
  - The legacy hex palette in `styles.css` was removed; it was already overridden by the generated tokens.
  - Code-syntax, dialog, backdrop, print, theme-preview, glow and shadow colours are now tokens.
- **Type sizes come from tokens.**
  - Raw px font sizes in all shared stylesheets use a UI type scale (`ui-*`).
  - FigureMap text uses `figure-*` tokens.
- **FigureMap geometry is read from `tokens.json`** by the renderer. This covers card width, line pitch, margin, frame width, map scale and map budget.
- **The build enforces the boundary.** `build.py` rejects inline styles or `<style>` blocks in lesson content, hard-coded colours in shared stylesheets, and raw px font sizes.

## Verification

- `dev.py build` passes, including the new boundary check, with preservation intact (17,330 units).
- `dev.py figures`: 79 models, no problems.
- `dev.py frames`: 136 pages, 79 figures, 118 maps and 1,761 labels; nothing outside its box, nothing scrolls sideways.
- The six browser audits ran on this build. Their results are in this folder, and the gate requires them to pass.

## Limits

- Syntax-highlight colours now use the existing code tokens, so some shades shift slightly.
- Shared stylesheets outside `design-system/` still exist as files, but they read only tokens; relocating them is cosmetic.
