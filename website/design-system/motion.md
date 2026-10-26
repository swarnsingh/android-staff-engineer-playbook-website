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

### Choose the representation before the component

Owner clarification, 27 October 2026: no topic is required to have an animation. A beautiful, readable static diagram can fully satisfy the lesson's visual needs.

| What the reader needs to understand | Preferred representation |
|---|---|
| Parts, boundaries, relationships or hierarchy | A labelled static diagram |
| Options, constraints, trade-offs or decision gates | A static comparison, matrix or decision tree |
| A small sequence whose states need close inspection | Numbered still panels or a manual step-through |
| Timing, movement, contention, cancellation or changing state that is easier to follow in motion | A controlled animation with captions and an equivalent still/text explanation |

These are choices within a topic, not labels for an entire chapter. A DI hierarchy can stay static while a separate lifetime sequence shows which owner survives recreation. Keep a module dependency graph still; use distinct before/after views if a contract edit changes which modules are affected. Looper queue dispatch and WorkManager waiting/retry sequences have meaningful temporal changes. Form-factor decision gates and the KMP adoption decision can be presented as a decision diagram or comparison without playback.

During refinement, identify what motion adds. If the explanation is equally clear as a still, consolidate its states into a static diagram or comparison, preserving the useful captions and caveats. Do not discard an explanation when removing its playback controls. Update the coverage manifest and checks when changing a figure's representation. Animation counts describe the implementation; they are not a quality target or a requirement to turn the existing state figures into full scenes.

## How it moves (FlowDiagram)

1. **Connectors** are drawn paths, with an arrowhead, coloured by direction: `accent` forward, `event` back.
2. **Packets** are small dots (`radius-pill`) that travel along the connector, fading in at the start and out at the end. Three packets per edge, 0.8s apart, so the flow reads as continuous.
3. **The dashes march** slowly in the direction of travel, so the direction is still readable between packets.
4. **Blocked work** turns `warn`: packets slow down and pile up in front of the node that cannot take them.
5. **Labels** on nodes use `handNode`; one `handNote` annotation per diagram says what the motion means.

## Stepped scenes (FlowScene)

A FlowScene does not loop. Edges march only while a packet is travelling. Each step plays its packets once, about 950ms per hop with an ease-in-out curve, then applies the step's state change with one 500ms pulse on each node it changed. Play waits 2.6s on each step so the caption can be read. Previous and Reset jump without motion.

## One motion state

`Playbook.motion` combines the OS preference (`prefers-reduced-motion`) with the reader's own setting (the reader puts `reduce-motion` on `<html>`). It is read live: a change takes effect immediately in CSS and in scripted packets, with no reload.

## Phones

Moving and static diagrams behave differently on phones:

- **Moving diagrams (FlowDiagram, FlowScene)** use the wide layout only when it fits: the runtime computes the scale the wide drawing would render at and keeps it only if handwritten labels stay at 15px or more and other text at 12px or more. Otherwise they switch to the stacked layout, whose text is drawn larger so it meets the same minimums on a 320px phone. Nodes form a column, forward edges run on the left lane and return edges on the right, so the cause and the effect stay on screen together and no packet travels out of view. A row flow (two to five nodes in order, edges only between neighbours) gets both layouts generated from its node order, with the row as wide as its node count needs; anything else is authored with a `wide` and a `narrow` layout.
- **Static diagrams (WideDiagram)** keep their drawing and scroll sideways inside their own box at a readable minimum width, with edge fades and a hint. Nothing moves, so scrolling loses nothing.

Neither kind is ever shrunk to fit a phone, or stretched past 1.2× its drawn size on a wide screen. Handwritten labels stay at 15px or more and other diagram text at 12px or more.

## When it stops

Motion must stop in all of these cases, and the diagram must still teach:

- **The OS asks for reduced motion** (`prefers-reduced-motion: reduce`), or the reader turns on the site's own motion toggle. The packets are hidden, the arrowheads and labels stay, and each connector shows its order number.
- **The diagram is off screen.** An `IntersectionObserver` pauses it, which also saves battery on long pages.
- **The reader presses Pause.** In a FlowScene, a packet already travelling is cancelled and the step jumps to its final state, and the marching dashes stop. In a FlowDiagram the loop stops and the still version shows. Every moving diagram has a visible Pause/Play button. Anything that moves for more than five seconds needs one (WCAG 2.2.2).

## Budget

At most one diagram moves at a time, and the runtime enforces it. Among visible looping diagrams, only the first plays on its own; the others show their still version with a Play button. Pressing Play on another diagram, or stepping a FlowScene, gives it the turn and stills the rest. Pausing a diagram keeps its turn, so pausing one never starts another. A diagram gives up its turn when it leaves the screen. No motion appears in the hero, the navigation or the body text.
