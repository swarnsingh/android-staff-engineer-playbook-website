# FlowScene

One system drawn once and stepped through: packets travel between nodes, and when they land they change what they reach (a thread turns busy, a queue grows, a caller unblocks).

## When to use

Use it for the lesson's main mechanism, when the reader needs to watch one system evolve over several steps: a Binder call, a Looper draining its queue, an OkHttp interceptor chain, WorkManager constraints, a Zygote fork. A lesson has at most one FlowScene. Use **FlowDiagram** for a short loop that only shows direction, and a static visual for structure.

## Anatomy

- **Regions:** dashed rounded outlines with a `labelSmall` name (APP PROCESS, KERNEL, SERVICE PROCESS). They mark boundaries the reader must notice.
- **Nodes:** hand-drawn `sheet` boxes with a `handNode` label and a live status line, for example "blocked · 1.4 s". The state classes are:
  - `is-active` (accent outline);
  - `is-warn` (warn outline and tint);
  - `is-done` (accent tint).
- **Slots and queues inside nodes:** chips for workers (thread T1: busy, your call, idle) and dots for queued items. These are the "consequence" layer.
- **Edges:** faint dotted paths at rest. A step lights its edges in `accent` (forward), `event` (back) or `warn` (stuck), with marching dashes and a matching arrowhead.
- **Packets:** a dot with a `handNote` label riding along the edge. A packet takes about 950ms per hop, and hops within a step run one after another. The node it reaches pulses once and updates.
- **Caption bar:** step counter, progress line, a one-to-two-sentence caption, and Previous / Play (Pause) / Next / Reset.
- **Compare toggle (optional):** two tracks over the same drawing. In the pilot these are the Synchronous call and the `oneway` call.
- **Text version:** "Read every step as text" lists every caption, so the scene is complete without the drawing.

## Behaviour

- **Next** animates the step's packets, then applies its state. **Previous** and **Reset** jump instantly.
- **Play** advances on its own: packets, then 2.6s to read, then the next step. It stops at the last step, when the scene scrolls out of view, or when the reader presses Pause.
- **Reduced motion:** steps still advance, but state changes instantly and no packets travel.
- **State is computed from the step list,** so jumping backwards always shows exactly the state at that step.

## What the page provides

The scene is data in the lesson's blend file: edges (SVG path data), nodes (position, label, optional chips or queue), and per track an `initial` state and `steps`. Each step lists `packets` (edge, label, tone) and `set` (node state and status text, chip states, queue length). Captions must be accurate to the platform docs; illustrative timings are labelled as such.

## Pilot

The preview is the Binder lesson's scene. The synchronous track has 9 steps: the call blocks the UI thread, queues behind busy service threads, runs, and the reply unblocks the caller. The `oneway` track has 6 steps: the caller returns at once, the service side still queues, and no reply comes back. The ordering claim follows AOSP: "One-way methods from the same thread to the same binder also execute serially".

## Tokens

`sheet-sunken`, `grid-dot`, `sheet`, `line`, `line-strong`, `ink`, `ink-muted`, `accent`, `accent-soft`, `on-accent`, `event`, `warn`, `warn-soft`, `focus`, `radius-md`, `radius-pill`, `radius-sm`, `space-4`.
