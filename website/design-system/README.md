# Playbook Design System

The look and behaviour of the Android Engineering Playbook reader: a calm, professional reading sheet for long technical lessons, with illustrated diagrams where data visibly moves. Think of it as the playbook's `MaterialTheme`: one `colorScheme`, one `typography`, one `shapes`, plus motion rules, applied the same way on every page.

**Status:** implemented across the reader; illustrated scene update, 27 Oct 2026. The build includes an interactive gallery at `design-system/index.html` in the private GitHub Actions artifact. Source, tokens, renderer and publication workflow all live in this repository. See [the website experience report](../reviews/website-experience-2026-10-27.md) for coverage and verification.

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

Code cards are the one dark object on the sheet (`code-bg`) in every theme. High contrast drops the tints and uses a 1px `line` border instead, because tinted grounds lower contrast there; `components/bundle.css` applies this to callouts, checkpoints and diagrams.

**Widths.** The sheet is `measure-wide` (880px) including its padding. Both rails show from 1440px; from 1181px only the chapter outline shows; below 1181px the outline moves to the top of the sheet and the curriculum lives in the menu.

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

Transfer tokens use long dashes for forward paths, dots plus a diamond cue for returns, and dash-dot for warnings. Illustrated scenes carry envelopes, row lists, files, commands or video-frame symbols. These cues remain distinct when themes change.

Actor colours have a separate role: `scene-client` (blue devices), `scene-runtime` (purple execution), `scene-storage` (teal stored data) and `scene-queue` (rose queued work). Actor colour stays stable while status changes. Authored visual state changes show queue counts, visible collectors, stored values, generated files and private memory pages. Counts are illustrative only when the lesson explicitly gives an example quantity.

## Typography (Compose mapping)

| Style | `Typography` slot | Face |
|---|---|---|
| `displayLarge`, `headlineMedium` | `displayLarge`, `headlineMedium` | Source Serif 4: lesson and phase titles only |
| `titleLarge`, `titleMedium` | `titleLarge`, `titleMedium` | Inter: H2 and H3 |
| `bodyLarge`, `bodyMedium` | `bodyLarge`, `bodyMedium` | Inter: running text, captions |
| `labelLarge`, `labelSmall` | `labelLarge`, `labelSmall` | Inter: controls, eyebrows |
| `codeBlock`, `codeInline` | (none) | JetBrains Mono, ligatures off |
| `handNode`, `handNote` | (none) | Patrick Hand: diagrams and one annotation per diagram |

Five families, self-hosted from `fonts/` (Latin subsets, SIL Open Font License): Inter variable 400–700 (48KB), Source Serif 4 SemiBold (21KB), JetBrains Mono variable 400–500 (31KB) and Patrick Hand (63KB), plus Shantell Sans variable 400–600 for the reader's handwritten setting. Shantell Sans was designed for on-screen reading, but it is about 25% wider than Patrick Hand, so diagram labels stay in Patrick Hand to fit their boxes. Nothing loads from a font CDN. Handwriting never carries an answer, a finding, an Under review note or code.

## Shapes and spacing

`radius-sm` (6) for inline code and chips, `radius-md` (10) for nodes, callouts and code cards, `radius-lg` (18) for the sheet, `radius-pill` for tabs and packet dots. Spacing runs on a 4px base; the diagram dot grid uses `space-4`. Gutters are never under `space-4`.

## Motion

See the **Motion and diagrams** section for the full rules. In short: interface feedback takes 150ms; state changes take 300ms with a standard ease; diagram packets take 2.4s per edge and loop; everything stops for reduced motion (from the OS or the reader's setting, read live), an off-screen diagram, or the diagram's own pause button.

## Components

| Component | Use |
|---|---|
| ReadingSheet | The page frame: canvas, sheet, capped text column, hero. |
| Callout | Start here, Staff note, Remember, Under review. |
| CodeCard | Kotlin examples, dark in every theme. |
| Checkpoint | Q&A tab questions with an Answer heading. |
| FlowDiagram | A short looping diagram that shows direction and blockage. |
| FlowScene | One system stepped through, where packets land and change state. 17 authored lessons, including Binder, Room, Looper, Flow, build tooling and Media3. |
| Illustrated state stepper | The 122 existing HTML sequences with explicit object choices, authored visual contents and numbered navigation. |
| WideDiagram | A static diagram that keeps a readable size and scrolls sideways on phones. |

FlowDiagram, FlowScene and WideDiagram share one runtime, `components/bundle.js` (`window.Playbook`, no dependencies), and one stylesheet, `components/bundle.css`.

## Applied to the reader

- The text column is capped at `measure-text` and centred on a sheet, instead of spanning the space between the rails.
- Body text defaults to Inter instead of the handwritten face; handwriting moves into diagrams.
- Callouts lose their left accent bar and become tints with a capital label.
- Flow diagrams animate packets along their connectors instead of showing static arrows, and each lesson's main mechanism becomes one stepped FlowScene instead of separate small visuals.

## Established defaults

1. **Accent hue: green (default).** It keeps the playbook's identity. A blue or teal accent would need the `event` colour to change too, so the two directions stay distinct.
2. **Title face: serif (default).** A serif title (Source Serif 4) keeps the current site's editorial feel; Inter at `displayLarge` would make it plainer and more product-like.
3. **Default theme: light.** The reader can switch. Dark is a deep navy page (`canvas` #0a0f1e) with a slate sheet and two faint glows behind it (in the style of the AlgoInsight reference); every text and outline pair passes 4.5:1 and 3:1 on all three dark surfaces. The AlgoInsight reference is dark-first.

## Website-wide learning standard

Rulebook section 20 applies the reference review across the website: consistent navigation and reading comfort, problem-first lessons, progressive detail, meaningful alternatives, and one shared visual language. Reusable behaviour lives in the components rather than individual preview copies. The 17 illustrated scenes use numbered step navigation, adaptive layouts, optional visual-key instructions and complete captions. All 122 additional state steppers now have explicitly chosen SVG actors, visible status changes, numbered navigation and a progress bar. These cover 545 objects across 107 lesson files. They retain their authored structure and are described as illustrated state sequences, separately from the 17 full scenes. See the [coverage report](../reviews/illustrated-coverage-2026-10-27.md).

The gallery is generated from the actual lesson sections in the same build, so changing a lesson or shared renderer changes its gallery sample too. Previous component preview HTML files are historical standalone samples; use the generated gallery to review the current design.

## Illustrated state sequence contract

The existing `.stepper` data format supports `visuals: {actorId: patch}` in each step. Patches accumulate from the beginning, so backwards jumps restore earlier queue contents and object visibility. The markup explicitly selects `data-art` and `data-art-role` per node. `window.Playbook.Actor` renders the same vector objects used by FlowScene. Only reviewed `handoff: {from, to, kind, label}` entries create moving payloads; active-state changes never infer one. The build verifies every object against `website/content/illustrated-stepper-coverage.json`.
