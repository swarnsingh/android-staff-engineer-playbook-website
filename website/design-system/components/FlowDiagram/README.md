# FlowDiagram

A hand-drawn diagram whose connectors carry moving packets, for sections where the direction, rate or order of data is the lesson.

## When to use

- Data or control moving between components: state to the UI, events back, a request and its reply.
- Something getting stuck: a queue in front of a busy thread, a full buffer, a blocked call.

Use a static diagram, not this one, for structure: module graphs, class hierarchies and layer lists. Moving packets on a dependency graph would suggest data flows that do not exist. The full rules are in **Motion and diagrams**.

## Anatomy

- **Nodes:** a `sheet` rectangle with a `line-strong` 2px outline, `radius-md` corners and a slight hand-drawn wobble. The label uses `handNode`; an optional sub-label uses `bodyMedium` at 12px in `ink-muted`. A node in trouble takes a `warn` outline and a `warn` sub-label.
- **Connectors:** curved paths with an arrowhead and slowly marching dashes. `accent` is forward, `event` is back, `warn` is stuck, and a dotted `line-strong` path is one that has nothing on it yet.
- **Packets:** dots 9–11px across. There are three per edge, 0.8s apart, and each takes 2.4s to cross. On a stuck edge they take 4.8s and pile up as a static queue in front of the node.
- **Annotation:** one `handNote` line under the diagram saying what the motion means.
- **Bar:** a one-sentence caption in `ink-muted` and a Pause/Play button.

## What the page provides

- The node and edge geometry. Each lesson's diagram is authored for its own content, starting from the original chapter's Mermaid diagram where one exists.
- A text alternative (`<title>` in the SVG). It must say what moves where, so a screen-reader user gets the same lesson.
- A vertical variant below 560px. Nodes stack top to bottom and the connectors turn downward, so handwriting never drops below 14px.

## Behaviour

- **Reduced motion or the site's motion toggle:** the diagram starts still. Packets are hidden, the arrowheads, labels and queue stay, and numbered markers show the order. Play remains available.
- **Off screen:** the diagram pauses itself.
- **Pause:** shows the same still version. This is needed for WCAG 2.2.2, because the motion runs longer than five seconds.

## Tokens

`sheet-sunken`, `grid-dot`, `sheet`, `line-strong`, `ink`, `ink-muted`, `accent`, `event`, `warn`, `warn-soft`, `focus`, `radius-md`, `radius-pill`, `space-4`.
