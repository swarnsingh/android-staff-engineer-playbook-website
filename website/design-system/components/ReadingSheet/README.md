# ReadingSheet

The page frame for a lesson: a tinted `canvas`, one `sheet` holding the hero, tabs and text, and running text capped at `measure-text`.

## When to use

Every lesson page, phase page and landing page. Never nest a sheet inside a sheet.

## Rules

- The sheet is at most `measure-wide` (880px) and is centred between the rails. Text inside it is at most `measure-text` (760px). Code cards, tables and diagrams may use the full sheet width. On the site, the sheet is a size container (`container-type: inline-size`) and diagram figures take `margin-inline: min(0px, (100% - 100cqw) / 2)`, so they widen to the sheet's inner width on desktop and stay put on phones.
- The sheet uses `box-sizing: border-box`, so `measure-wide` (880px) includes its padding.
- Breakpoints come from the space the sheet needs: both rails from 1440px (244 + 880 + 220 + gutters); the outline rail alone from 1181px; below 1181px the outline moves to the top of the sheet and the curriculum lives in the menu.
- At phone width the sheet's corner radius stays and its side padding drops to 20px; the canvas shows as a thin edge.
- The hero carries an eyebrow (`labelSmall` in `accent`), the title (`displayLarge`), a lead (`bodyLarge`) and a meta line (read time and position in the phase).
- High contrast: no shadow and a 1px `line` border instead.

## What the page provides

The breadcrumb, title, lead, read time (from the word count) and the lesson's position in its phase.

## Tokens

`canvas`, `sheet`, `shadow-sheet`, `radius-lg`, `measure-wide`, `measure-text`, `ink`, `ink-muted`, `accent`, `accent-soft`, `line`, `space-4` to `space-12`.
