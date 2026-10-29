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
