# Motion and diagrams

Motion in the playbook explains something. It shows which way data travels, how fast it arrives, or where it gets stuck. It is never ambient decoration.

## Motion values

| Name | Value | Use |
|---|---|---|
| Quick | 150ms, `cubic-bezier(.2, 0, 0, 1)` | Hover, press, focus, tab underline |
| Standard | 300ms, `cubic-bezier(.2, 0, 0, 1)` | A stepper step changing state, a node lighting up |
| Packet travel | 2.4s per edge, eased in and out | One packet crossing one connector |
| Packet spacing | 0.8s | Three packets in flight per edge |
| Slow lane | 4.8s per edge | A connector feeding a busy or blocked node |

The design-system format has no motion token family, so these values live here and in the components' CSS.

## When a diagram moves

Animate a connector only when **direction, rate or order is the point of the section**:

- state flowing from a repository to the UI, and events flowing back;
- a request crossing a process boundary and its reply returning;
- work queuing in front of a busy thread, a full buffer, a blocked call.

Keep it static when the diagram shows structure: a module graph, a class hierarchy, a layer list. Moving dots on a dependency graph suggest data flows that do not exist.

## How it moves (FlowDiagram)

1. **Connectors** are drawn paths, with an arrowhead, coloured by direction: `accent` forward, `event` back.
2. **Packets** are small dots (`radius-pill`) that travel along the connector, fading in at the start and out at the end. Three packets per edge, 0.8s apart, so the flow reads as continuous.
3. **The dashes march** slowly in the direction of travel, so the direction is still readable between packets.
4. **Blocked work** turns `warn`: packets slow down and pile up in front of the node that cannot take them.
5. **Labels** on nodes use `handNode`; one `handNote` annotation per diagram says what the motion means.

## Stepped scenes (FlowScene)

A FlowScene does not loop. Each step plays its packets once, about 950ms per hop with an ease-in-out curve, then applies the step's state change with one 500ms pulse on each node it changed. Play waits 2.6s on each step so the caption can be read. Previous and Reset jump without motion.

## When it stops

Motion must stop in all of these cases, and the diagram must still teach:

- **The OS asks for reduced motion** (`prefers-reduced-motion: reduce`), or the reader turns on the site's own motion toggle. The packets are hidden, the arrowheads and labels stay, and each connector shows its order number.
- **The diagram is off screen.** An `IntersectionObserver` pauses it, which also saves battery on long pages.
- **The reader presses Pause.** Every moving diagram has a visible Pause/Play button. Anything that moves for more than five seconds needs one (WCAG 2.2.2).

## Budget

At most one moving diagram should be in view at a time. A lesson may use several, but each one pauses when it leaves the screen. No motion appears in the hero, the navigation or the body text.
