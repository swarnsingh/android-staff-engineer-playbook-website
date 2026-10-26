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
- Two layouts in the diagram's data: `wide` and `narrow`. Below 520px of container width the runtime switches to `narrow`, a stacked column with forward edges on the left and return edges on the right, so labels stay readable on a 320px phone.

## Behaviour

- **Reduced motion (OS or reader setting, read live):** the diagram goes still at once. Packets are hidden, the arrowheads, labels and queue stay, and numbered markers show the order. Play remains available.
- **Off screen:** the diagram pauses itself.
- **Pause:** shows the same still version. This is needed for WCAG 2.2.2, because the motion runs longer than five seconds.

## Tokens

`sheet-sunken`, `grid-dot`, `sheet`, `line-strong`, `ink`, `ink-muted`, `accent`, `event`, `warn`, `warn-soft`, `focus`, `radius-md`, `radius-pill`, `space-4`.
