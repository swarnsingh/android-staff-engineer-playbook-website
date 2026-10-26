# FlowDiagram

A hand-drawn diagram whose connectors carry moving packets, for sections where the direction, rate or order of data is the lesson.

## When to use

- Data or control moving between components: state to the UI, events back, a request and its reply.
- Something getting stuck: a queue in front of a busy thread, a full buffer, a blocked call.

Use a static diagram, not this one, for structure: module graphs, class hierarchies and layer lists. Moving packets on a dependency graph would suggest data flows that do not exist. The full rules are in **Motion and diagrams**.

## Anatomy

- **Nodes:** a `sheet` rectangle with a `line-strong` 2px outline, `radius-md` corners and a slight hand-drawn wobble. The label uses `handNode`; an optional sub-label uses `bodyMedium` at 12px in `ink-muted`. A node in trouble takes a `warn` outline and a `warn` sub-label.
- **Connectors:** curved paths with an arrowhead and slowly marching dashes. `accent` is forward, `event` is back, `warn` is stuck, and a dotted `line-strong` path is one that has nothing on it yet.
- **Packets:** round dots forward, diamonds back, about 13px across. Up to three per edge, evenly spaced, each taking 2.4s to cross; on a stuck edge 4.8s. Blocked work shows as queue dots inside the node that holds it.
- **Annotation:** one `handNote` line under the diagram saying what the motion means.
- **Bar:** a one-sentence caption in `ink-muted` and a Pause/Play button.

## What the page provides

- The node and edge geometry. Each lesson's diagram is authored for its own content, starting from the original chapter's Mermaid diagram where one exists.
- A text alternative (`aria-label` on the SVG). It must say what moves where, so a screen-reader user gets the same lesson.
- Layouts. For a row flow of two to five nodes, give `nodes` in order and `edges` as `{id, from, to, tone, label}` between neighbouring nodes: the runtime generates the `wide` row and the `narrow` column itself. Otherwise give `layouts.wide` and `layouts.narrow` explicitly. The runtime uses `wide` only while it renders large enough to keep handwritten labels at 15px or more and other text at 12px or more; otherwise it uses `narrow`. Labels may contain a line break (`\n`).

## Behaviour

- **Reduced motion (OS or reader setting, read live):** the diagram goes still at once. Packets are hidden, the arrowheads, labels and queue stay, and numbered markers show the order. Play remains available.
- **Off screen:** the diagram pauses itself and gives up its turn.
- **Several in view:** only the first plays on its own; the others wait as still diagrams with Play.
- **Pause:** shows the same still version. This is needed for WCAG 2.2.2, because the motion runs longer than five seconds.

## When the data is invalid

If a diagram's data cannot be drawn (for example, a generated row of six nodes), the runtime hides the empty drawing and its controls and shows a short notice with the diagram's text description. A failed diagram never joins turn-taking, so the next valid diagram still plays.

## Tokens

`sheet-sunken`, `grid-dot`, `sheet`, `line-strong`, `ink`, `ink-muted`, `accent`, `event`, `warn`, `warn-soft`, `focus`, `radius-md`, `radius-pill`, `space-4`.
