# Playbook Design System

The look and behaviour of the Android Engineering Playbook reader: a calm, professional reading sheet for long technical lessons, with hand-drawn diagrams where data visibly moves. Think of it as the playbook's `MaterialTheme`: one `colorScheme`, one `typography`, one `shapes`, plus motion rules, applied the same way on every page.

**Status:** final draft for review (26 Oct 2026). Nothing here is applied to the site yet. The three choices at the end are set to the defaults below unless the review changes them.

## Principles

1. **Read first, decorate second.** Lessons run 3,000 to 6,000 words. Running text uses a plain sans face at a comfortable size and measure; personality lives in diagrams and a few annotations.
2. **Show the mechanism moving, with consequences.** When a section is about direction, rate or order, the diagram animates it, and a packet that arrives changes what it reaches: a thread turns busy, a queue grows, a caller unblocks. A lesson's main mechanism is one system stepped through (FlowScene); short direction loops use FlowDiagram; structure stays static.
3. **One frame, not boxes in boxes.** The page is a canvas; the lesson sits on one sheet; blocks inside the sheet are tints, never cards with their own shadow.
4. **Every theme is designed.** Light, dark, sepia and high contrast each get their own values. Text meets 4.5:1 on its ground in all four.
5. **The reader is in control.** Font, size, theme and motion settings override these defaults.

## Surfaces (elevation)

| Level | Token | Use |
|---|---|---|
| 0 | `canvas` | The page around the sheet. A faint tinted ground, so the sheet reads as the lesson. |
| 1 | `sheet` + `shadow-sheet` + `radius-lg` | The reading sheet: hero, tabs and lesson text. Width `measure-wide`; text inside it is capped at `measure-text`. |
| 2 | `sheet-sunken` or a `*-soft` tint + `radius-md` | Callouts, checkpoints, diagram paper. No border, no shadow. |

Code cards are the one dark object on the sheet (`code-bg`) in every theme. High contrast drops the tints and uses a 1px `line` border instead, because tinted grounds lower contrast there.

## Colour roles (Compose mapping)

| Token | `ColorScheme` role | Rule |
|---|---|---|
| `canvas` | `background` | Page only. |
| `sheet` | `surface` | Lesson text sits here. |
| `sheet-sunken` | `surfaceContainer` | Blocks inside the sheet. |
| `ink` | `onSurface` | All running text and headings. |
| `ink-muted` | `onSurfaceVariant` | Captions and meta only, never paragraphs. |
| `line`, `line-strong` | `outlineVariant`, `outline` | Hairlines; node and control borders. |
| `accent`, `on-accent`, `accent-soft` | `primary`, `onPrimary`, `primaryContainer` | Links, active tab, buttons; state moving forward in diagrams. |
| `event`, `event-soft` | `secondary`, `secondaryContainer` | The other direction in a diagram: events, requests, replies. |
| `warn`, `warn-soft` | `error`, `errorContainer` | Blocked and failing states; Under review notes. |

Diagram rule: **green moves forward, blue comes back, orange is stuck.** The two directions differ in lightness as well as hue, so they stay distinct for colour-blind readers and in high contrast.

## Typography (Compose mapping)

| Style | `Typography` slot | Face |
|---|---|---|
| `displayLarge`, `headlineMedium` | `displayLarge`, `headlineMedium` | Source Serif 4: lesson and phase titles only |
| `titleLarge`, `titleMedium` | `titleLarge`, `titleMedium` | Inter: H2 and H3 |
| `bodyLarge`, `bodyMedium` | `bodyLarge`, `bodyMedium` | Inter: running text, captions |
| `labelLarge`, `labelSmall` | `labelLarge`, `labelSmall` | Inter: controls, eyebrows |
| `codeBlock`, `codeInline` | (none) | JetBrains Mono, ligatures off |
| `handNode`, `handNote` | (none) | Patrick Hand: diagrams and one annotation per diagram |

Four families, self-hosted on the site, only the weights listed. Handwriting never carries an answer, a finding, an Under review note or code.

## Shapes and spacing

`radius-sm` (6) for inline code and chips, `radius-md` (10) for nodes, callouts and code cards, `radius-lg` (18) for the sheet, `radius-pill` for tabs and packet dots. Spacing runs on a 4px base; the diagram dot grid uses `space-4`. Gutters are never under `space-4`.

## Motion

See the **Motion and diagrams** section for the full rules. In short: interface feedback takes 150ms; state changes take 300ms with a standard ease; diagram packets take 2.4s per edge and loop; everything stops for reduced motion, the reader's motion toggle, an off-screen diagram, or the diagram's own pause button.

## Components

| Component | Use |
|---|---|
| ReadingSheet | The page frame: canvas, sheet, capped text column, hero. |
| Callout | Start here, Staff note, Remember, Under review. |
| CodeCard | Kotlin examples, dark in every theme. |
| Checkpoint | Q&A tab questions with an Answer heading. |
| FlowDiagram | A short looping diagram that shows direction and blockage. |
| FlowScene | One system stepped through, where packets land and change state. Pilot: the Binder lesson. |

## What changes from today's site

- The text column is capped at `measure-text` and centred on a sheet, instead of spanning the space between the rails.
- Body text defaults to Inter instead of the handwritten face; handwriting moves into diagrams.
- Callouts lose their left accent bar and become tints with a capital label.
- Flow diagrams animate packets along their connectors instead of showing static arrows, and each lesson's main mechanism becomes one stepped FlowScene instead of separate small visuals.

## Choices (defaults set, open to review)

1. **Accent hue: green (default).** It keeps the playbook's identity. A blue or teal accent would need the `event` colour to change too, so the two directions stay distinct.
2. **Title face: serif (default).** A serif title (Source Serif 4) keeps the current site's editorial feel; Inter at `displayLarge` would make it plainer and more product-like.
3. **Default theme: light.** The reader can switch. The AlgoInsight reference is dark-first.
