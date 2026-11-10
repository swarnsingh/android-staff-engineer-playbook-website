# FigureMap

The designed replacement for every original Mermaid diagram. It draws a static relationship map or a two-lane sequence in the shared visual language, so no rendered Mermaid picture appears on the website (rulebook §20, "Designed visuals only").

## Authoring

Add one model per original diagram to `website/content/diagram-models/figures/<tree>.json`. The `diagram` field is the first 16 hex characters of the SHA-256 of the diagram source after approved corrections. The build prints these hashes as `data-original-diagram` values, and also writes them to `dist/diagram-sources/`.

| Field | Meaning |
|---|---|
| `path`, `diagram`, `number`, `title`, `caption`, `sources` | Required. The caption states the figure's point. Sources are official https URLs. |
| `kind: "map"` | `nodes` (id, title, optional detail, role, x, y, optional w/key), optional `groups` (owner boundaries), and `edges` (from, to, label, optional route `straight`/`hv`/`vh`/`vhv`, `mid`, `at`, `style: "dashed"`). |
| `kind: "sequence"` | `participants` (id, title, detail, role) and `events`: a note `{over, text}`, a self step `{at, label}`, a message `{from, to, label}`, or a list of notes that share one row. |

Roles are `client`, `runtime`, `storage`, `queue` and `neutral`. Each role has a colour token and a border pattern: solid, heavy, double, dashed and dotted, respectively. Mark at most one card as `key` (filled) for the figure's central idea.

The build fails in these cases:
- a model names an unknown actor or role;
- an actor has two owners;
- a relationship has no label;
- a label would be clipped by its card;
- a model has no original diagram on the page.

The chapter's Mermaid source stays on the page as preserved text under "Original diagram from the chapter".

## Automatic layout

A model whose cards have no `x`/`y` or `col`/`row` is placed automatically. The model's `layout` field chooses one of three layouts:
- **`columns`** (the default): one column per top-level owner boundary, with nested boundaries drawn inside their parent, and rows in relationship order. Columns that would exceed `max_w` continue on a band below.
- **`layers`**: rows by relationship depth, for trees and fan-outs. Several same-label edges from one parent share a bus and one label, and edges to a wrapped row turn in the gap just above it.
- **`snake`**: wraps a long pipeline into rows that alternate direction.

Routing works the same way in every layout:
- Each clean route option is scored, and the one with the fewest line crossings and bends wins.
- Labels are wrapped and placed where they cover no card, boundary label or other label.
- A model that cannot be placed cleanly fails the build.

The 118 relationship maps and the Android figures use automatic layout.

Use nested boundaries rather than arrows when a diagram shows containment, such as source sets or directories; arrows are for relationships.

## Layout guidance

- **Run flows top to bottom.** A label pill can sit on any vertical line, because only the pill's height has to fit between two rows. On a horizontal line the whole pill has to fit between two cards. Vertical layouts also stay narrow enough for phones.
- **Use the grid.** Give `col` and `row` instead of pixels when cards align. The figure-level `grid` (default 260 × 120) and `card_w` (default 220) set the pitch.
- **Choose a route.**
  - `vhv` makes a tidy fan-out or fan-in.
  - `around` sends a feedback edge past a column.
  - `curve` separates a return edge from its forward twin.
- **Share a bus.** Edges that genuinely share a path can share a `bus` key, which gives them one number and one visible label. The text transcript still lists every relationship.
- **Separate label pills.** When two pills compete for one gap, move one along its segment with `t`, or choose a different segment with `at`.
- **Mark the point, keep words.** Mark only the figure's central idea as `key`. Multi-line details and labels take a list of strings; keep each line short rather than shrinking text.
- **Start and end.** State diagrams use `shape: "start"` and `shape: "end"` markers. Their edges still need labels such as "initial" or "done".

## Accessibility

Each SVG has a title and a description taken from the figure's caption. The "Read the figure as text" disclosure lists every relationship or sequence step in order, so the figure does not depend on seeing colour, arrows or position. Colour is always paired with a border pattern and a legend entry, and labels never fall below 13px.

## Rendering

`website/scripts/figure_maps.py` computes geometry only. Every colour, typeface and pattern comes from `tokens.json` through the `.fm-*` rules in `bundle.css`, so the figures follow the light, dark, sepia and high-contrast themes. Figures use the shared wide frame. On narrow screens they keep their 15px labels and scroll sideways through `WideDiagram`.


Compact maps retain the same actors, labels, edge directions and logical owners. The shared renderer removes desktop coordinates, reflows the semantic graph and applies the usual collision checks. It emits an alternative only when it fits the `figure-phone-width` and `figure-phone-max-height` budgets and is narrower than the normal drawing. The two drawings have unique SVG and marker IDs, and WideDiagram selects one from the actual region width using `figure-phone-breakpoint`; label sizes are never reduced. Automatic card bounds, label insets and wrap budgets also come from the figure tokens.

The renderer first reflows the owner columns within the phone width. When that does not fit, it tries the **phone ladder**, a one-column composition:

- Cards stack in relationship order. The members of each owner boundary stay together, so a boundary still encloses exactly its own cards.
- A relationship to the next card drops straight down with its numbered label on the line. If the line would cross a boundary label, it moves right or takes a dog-leg with the label on its own horizontal run.
- Every other relationship, including back edges and self-relationships, leaves its source on a row of its own under that card. The row carries the numbered label. The line then travels in a lane beside the column and enters its target from the side. Lanes are assigned shortest first, so nested relationships do not cross.
- Labels wrap between words, trying the `phone-label-wraps` budgets widest first. Cards wrap between words or after `/`, `.` or `-`, never inside a word. A model whose longest word does not fit the card column keeps its wide drawing.
- Besides the usual card and label collision checks, the ladder rejects any label that would hide part of another relationship's line.

Numbers, labels, endpoints, dashed and two-way arrows, and text are the same as in the wide drawing; only positions and line breaks change. Edges that share one bus and one number in the wide drawing become separate lines on the phone, and each keeps that same number and label. The `phone-*` entries in `figureGeometry` hold the ladder's dimensions.

Some figures still keep the normal labelled scroll area under section 20 of the rulebook, because a phone composition would lose relationships or shrink text:

- sequence diagrams, whose lanes carry meaning;
- state diagrams with start and end symbols;
- models with a code identifier longer than a phone card;
- graphs that need more lanes than the column can spare;
- boundary labels wider than a phone boundary.

Relationship maps beside a step-through use the same ladder at their 1.25× scale, so their budget is the phone width divided by `figure-map-scale`.

## Geometry tokens

The `figure` token family owns shared card widths, typography, frame limits and compact profiles. `figureGeometry` owns the remaining drawing defaults: arrow markers, terminal symbols, card padding, label pills, route clearances, group and row gaps, fit attempts and sequence lane spacing. `scripts/design_tokens.py` validates the registry; `figure_maps.py` consumes its numeric values without changing their integer or floating-point representation. FigureMap CSS values belong to `componentCss` and expand with the reader stylesheets.

Change these defaults in `tokens.json`, then run `dev.py figures`, the frame checks and the full audit. Author-defined model overrides remain part of the existing model contract. Algorithmic constants such as midpoint fractions, Bézier coefficients, collision sampling, route cost weights and sentinel bounds stay in the renderer; they express the solver rather than a visual dimension. The November extraction preserves all emitted SVGs, including alternate compact drawings.
