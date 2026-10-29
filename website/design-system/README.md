# Playbook Design System

The look and behaviour of the Android Engineering Playbook reader: a calm, professional reading sheet for long technical lessons, with illustrated diagrams where data visibly moves. Think of it as the playbook's `MaterialTheme`: one `colorScheme`, one `typography`, one `shapes`, plus motion rules, applied the same way on every page.

**Status:** implemented across the reader; illustrated scene update, 27 Oct 2026. The build includes an interactive gallery at `design-system/index.html` on [GitHub Pages](https://swarnsingh.github.io/android-staff-engineer-playbook-website/design-system/). Source, tokens, renderer and publication workflow all live in this repository. See [the website experience report](../reviews/website-experience-2026-10-27.md) for coverage and verification.

## Principles

1. **Read first, decorate second.** Lessons run 3,000 to 6,000 words. Running text uses a calm text face at a comfortable size and a measure of about 70 characters; personality lives in diagrams and a few annotations.
2. **Show the mechanism moving, with consequences.** When a section is about direction, rate or order, the diagram animates it, and a packet that arrives changes what it reaches: a thread turns busy, a queue grows, a caller unblocks. A lesson's main mechanism is one system stepped through (FlowScene); short direction loops use FlowDiagram; structure stays static.
3. **One frame, not boxes in boxes.** The page is a canvas; the lesson sits on one sheet; blocks inside the sheet are tints, never cards with their own shadow.
4. **Every theme is designed.** Light, dark, sepia and high contrast each get their own values. Text meets 4.5:1 on its ground in all four.
5. **The reader is in control.** Reading font, size, theme and motion settings override these defaults.

## Surfaces (elevation)

| Level | Token | Use |
|---|---|---|
| 0 | `canvas` | The page around the sheet. A faint tinted ground, so the sheet reads as the lesson. |
| 1 | `sheet` + `shadow-sheet` + `radius-lg` | The reading sheet: hero, tabs and lesson text. Width `measure-wide`; text inside it is capped at `measure-text`. |
| 2 | `sheet-sunken` or a `*-soft` tint + `radius-md` | Callouts, checkpoints, diagram paper. Subtle border or role accent where useful; no independent shadow. |

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
| `displayLarge`, `headlineMedium` | `displayLarge`, `headlineMedium` | Inter 700 / 650: lesson and phase titles |
| `titleLarge`, `titleMedium` | `titleLarge`, `titleMedium` | Inter 650: H2 and H3 |
| `bodyLarge` | `bodyLarge` | The reader's prose font (`--font-prose`): 18px, line height 1.7, weight 400, paragraphs 1.1em apart |
| `bodyMedium` | `bodyMedium` | Inter: captions, table cells, labels |
| `labelLarge`, `labelSmall` | `labelLarge`, `labelSmall` | Inter: controls, eyebrows |
| `codeBlock`, `codeInline` | (none) | JetBrains Mono at 0.86em / 0.85em, line height 1.6, ligatures off |
| `handNode`, `handNote` | (none) | Patrick Hand: diagrams and one annotation per diagram |

**Two roles, kept apart.** Inter is the interface face: navigation, buttons, tabs, labels, headings, tables, captions and diagram text. The reader's chosen font sets prose only: paragraphs, list items, blockquotes, callout text and Q&A. Headings, code, data tables and diagrams never follow the reading font, so switching it changes how the lesson reads, not how the page is organised.

**Five reading fonts** (`type.prose` in `tokens.json`), each a token swap on `html[data-reader-font]`:

| Option | Face | Measure |
|---|---|---|
| Modern Sans (default) | Playbook Sans, the Source Sans 3 subset | 33em |
| Book Serif | Playbook Serif, the Source Serif 4 subset | 34em |
| Classic Serif | Times New Roman from the device (nothing bundled) | 34em |
| Handwritten | Shantell Sans | 34.5em |
| Easy Read | Atkinson Hyperlegible Next, developed to increase legibility for readers with low vision through distinctive letterforms. It is offered as an alternative some readers find easier, not as a better default for everyone. | 31em |

Owner approval,29 October 2026: prose now fills the established760px reading column for every font. Font-specific measures remain for gallery specimens only. ReadingSheet owns bounded wide visual frames and overflow expansion through shared tokens and the component bundle. `font-size-adjust` gives every prose font the same x-height, so "18px" looks the same size whichever font is chosen; Times New Roman, which is small on its body, is the only one visibly scaled. Saved choices from the earlier four-font setting map to their successors (`sans`, `serif`, `times`, `hand`); a reader who never chose a font follows the default and nothing is saved for them.

Self-hosted from `fonts/` as Latin WOFF2 subsets under the SIL Open Font License, with each licence beside the files. Adobe reserves the name "Source", so the two Adobe subsets are renamed Playbook Sans and Playbook Serif; see [fonts/README.md](fonts/README.md) for sources, versions, hashes and the build tool. Each face has a metric-matched local fallback, so text barely moves when the web font arrives. Only Inter and the active prose font are preloaded; other fonts and italics load when used. Nothing loads from a font CDN. Shantell Sans is about 25% wider than Patrick Hand, so animated diagram labels stay in Patrick Hand to fit their boxes; static structure diagrams use Inter. The design itself never sets an answer, a finding, an Under review note or code in handwriting; a reader who picks Handwritten chooses it for all their prose.

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
| FlowScene | One system stepped through, where packets land and change state. 17 authored lessons, including Binder, Room, Looper, Flow, build tooling and Media3. The picture comes first; the step caption and one row of controls follow it. |
| FigureMap | The designed redraw of a Mermaid diagram: role-coloured cards, numbered labelled arrows, owner boundaries, a legend, a numbered caption and a text version. Built from models in `content/diagram-models/figures/`; see [components/FigureMap](components/FigureMap/README.md). |
| Illustrated state stepper | 119 HTML sequences with explicit object choices, authored visual contents and numbered navigation. |
| WideDiagram | A static diagram that keeps a readable size and scrolls sideways on phones. |

FlowDiagram, FlowScene and WideDiagram share one runtime, `components/bundle.js` (`window.Playbook`, no dependencies), and one stylesheet, `components/bundle.css`.

## Applied to the reader

- The text column is capped at `measure-text` and centred on a sheet, instead of spanning the space between the rails.
- Body text defaults to Modern Sans (Source Sans 3) at a textbook measure; Inter stays for headings and the interface, and handwriting lives in diagrams unless the reader chooses it.
- Callouts use a restrained role accent, clear label and tinted ground.
- Flow diagrams animate packets along their connectors instead of showing static arrows, and each lesson's main mechanism becomes one stepped FlowScene instead of separate small visuals.

## Established defaults

1. **Accent hue: green (default).** It keeps the playbook's identity. A blue or teal accent would need the `event` colour to change too, so the two directions stay distinct.
2. **Title face: Inter.** Headings use the shared sans family for the AirBridge article hierarchy and do not follow the reading font. Book Serif (Source Serif 4) remains available for prose.
3. **Default theme: light.** The reader can switch. Dark is a deep navy page (`canvas` #0a0f1e) with a slate sheet and two faint glows behind it (in the style of the AlgoInsight reference); every text and outline pair passes 4.5:1 and 3:1 on all three dark surfaces. The AlgoInsight reference is dark-first.

## Website-wide learning standard

The owner's [AirBridge architecture blog](https://swarnsingh.github.io/swaran-technical-blogs/blogs/airbridge-technical-architecture.html) is the primary article-experience reference: clear headline hierarchy, generous spacing, substantial readable figures and prose that connects problems to mechanisms and decisions. Apply its visual clarity within the playbook's reading measures, themes and accessibility controls. Topic-specific structure remains flexible; ByteByteGo and Cloudmash support diagram and interaction choices. See [rulebook section 20](../../content-rulebook.md#20-website-wide-learning-experience).

Choose static diagrams, manual steps or animation according to what teaches the mechanism. The owner clarified on 27 October 2026 that beautiful static diagrams are sufficient where motion adds no explanation. There is no requirement to animate every topic or turn all existing state figures into full scenes. Use the [representation guide](motion.md#choose-the-representation-before-the-component) when refining a lesson.

Rulebook section 20 applies the reference review across the website: consistent navigation and reading comfort, problem-first lessons, progressive detail, meaningful alternatives, and one shared visual language. Reusable behaviour lives in the components rather than individual preview copies. The 17 illustrated scenes use numbered step navigation, adaptive layouts, optional visual-key instructions and complete captions. The quantity-first pass illustrated 122 state steppers with 545 objects across 107 lesson files. The refinement converts three decision examples to static diagrams with all explanations visible, leaving 119 state steppers with 532 actors. They have explicitly chosen SVG actors, visible status changes, numbered navigation and a progress bar. They retain their authored structure and are described as illustrated state sequences, separately from the 17 full scenes. See the [coverage report](../reviews/illustrated-coverage-2026-10-27.md).

The gallery is generated from the actual lesson sections in the same build, so changing a lesson or shared renderer changes its gallery sample too. Previous component preview HTML files are historical standalone samples; use the generated gallery to review the current design.

## Illustrated state sequence contract

The existing `.stepper` data format supports `visuals: {actorId: patch}` in each step. Patches accumulate from the beginning, so backwards jumps restore earlier queue contents and object visibility. The markup explicitly selects `data-art` and `data-art-role` per node. `window.Playbook.Actor` renders the same vector objects used by FlowScene. Only reviewed `handoff: {from, to, kind, label}` entries create moving payloads; active-state changes never infer one. The build verifies every object against `website/content/illustrated-stepper-coverage.json`.

## Learning paths and lesson interactions

Learning paths present phase counts, chapter choices and a start action. Lesson pages retain reading controls and only populated supplemental views. The current track is the default curriculum scope; All topics opens the full catalog. Focus mode retains the topic drawer on desktop as well as smaller widths.

Current-step captions and controls form one interaction area. Equivalent actions use Previous, Next and Reset; temporal playback uses Play/Pause. Reusable instructions and the full textual transcript share one optional disclosure. Each dedicated question is followed immediately by a clearly labelled answer. Verified corrections read normally; their detailed history is available under About this lesson. Inline-code chips belong to prose; fenced examples use one uninterrupted code surface, even inside a list. See the [UX review and browser evidence](../reviews/ux-2026-10-28/REPORT.md) for the verification scope.
