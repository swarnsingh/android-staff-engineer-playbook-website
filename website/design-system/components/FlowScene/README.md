# FlowScene

One system drawn once and stepped through: packets travel between nodes, and when they land they change what they reach (a thread turns busy, a queue grows, a caller unblocks).

## When to use

Use it for the lesson's main mechanism, when the reader needs to watch one system evolve over several steps: a Binder call, a Looper draining its queue, an OkHttp interceptor chain, WorkManager constraints, a Zygote fork. A lesson has at most one FlowScene. Use **FlowDiagram** for a short loop that only shows direction, and a static visual for structure.

## Anatomy

- **Regions:** dashed rounded outlines with a `labelSmall` name (APP PROCESS, KERNEL, SERVICE PROCESS). They mark boundaries the reader must notice.
- **Nodes:** illustrated, role-coloured `sheet` actors with a `handNode` label and a live status line, for example "blocked · 1.4 s". The state classes are:
  - `is-active` (accent outline);
  - `is-warn` (warn outline and tint);
  - `is-done` (accent tint).
- **Slots and queues inside nodes:** chips for workers (thread T1: busy, your call, idle) and counted document trays for queued items. These are the "consequence" layer.
- **Edges:** faint dotted paths at rest. A step lights its edges in `accent` (forward), `event` (back) or `warn` (stuck), with marching dashes and a matching arrowhead.
- **Packets:** a named envelope, row list, command, file or frame with a `handNote` label riding along the edge. A packet takes about 950ms per hop, and hops within a step run one after another. The node it reaches pulses once and updates.
- **Caption bar:** step counter, progress line, a one-to-two-sentence caption, and Previous / Play (Pause) / Next / Reset.
- **Compare toggle (optional):** two tracks over the same drawing. In the pilot these are the Synchronous call and the `oneway` call.
- **Text version:** "Read every step as text" lists every caption, so the scene is complete without the drawing.

## Behaviour

- **Next** animates the step's packets, then applies its state. **Previous** and **Reset** jump instantly.
- **Play** advances on its own: packets, then 2.6s to read, then the next step. It stops at the last step, when the scene scrolls out of view, or when the reader presses Pause. Stopping cancels any packet in flight and shows the step's final state; edges march only while a packet travels.
- **Layouts:** `wide` while it renders large enough to keep handwritten labels at 15px or more and other text at 12px or more (about 700px of drawing width for this scene), `narrow` (stacked, 320 units wide, larger text) otherwise. Changing layout keeps the current step.
- **Turn-taking:** pressing Play or Next gives the scene the turn, so any looping diagram in view goes still. It gives the turn back when it leaves the screen.
- **Reduced motion (OS or reader setting, read live):** steps still advance, but state changes instantly and no packets travel. Turning it on mid-flight finishes the step at once.
- **State is computed from the step list,** so jumping backwards always shows exactly the state at that step.

## What the page provides

The scene is data in the lesson's blend file: edges (SVG path data), nodes (position, label, optional chips or queue), and per track an `initial` state and `steps`. Each step lists `packets` (edge, label, tone) and `set` (node state and status text, chip states, queue length). Captions must be accurate to the platform docs. A scene with example timings or queue lengths says "an illustrative run" in its subtitle, and the captions say "in this run" instead of stating times as guarantees.

## Pilot

The preview is the Binder lesson's scene. The synchronous track has 9 steps: the call blocks the UI thread, queues behind busy service threads, runs, and the reply unblocks the caller. The `oneway` track has 6 steps: the caller returns after handing the transaction to the kernel, the service side still queues, and no reply comes back. The ordering claim follows AOSP: "One-way methods from the same thread to the same binder also execute serially".

## When the data is invalid

If a diagram's data cannot be drawn (for example, a generated row of six nodes), the runtime hides the empty drawing and its controls and shows a short notice with the diagram's text description. A failed diagram never joins turn-taking, so the next valid diagram still plays.

## Tokens

`sheet-sunken`, `grid-dot`, `sheet`, `line`, `line-strong`, `ink`, `ink-muted`, `accent`, `accent-soft`, `on-accent`, `event`, `warn`, `warn-soft`, `focus`, `radius-md`, `radius-pill`, `radius-sm`, `space-4`.

## Reader integration after round 4

The reader shares playback ownership across loops, scenes and legacy state steppers. Next exposes Pause while a packet is in flight. The reader pause hook stops all three, and reduced motion stops scene autoplay while leaving manual steps available. The site build emits caption lists before JavaScript runs. Packet labels stay within drawing bounds along edge lanes. The applied reader has its own nested-padding checks; a passing standalone component preview does not establish phone label sizes inside a lesson.

## Illustrated scene data

Set `illustrated: true` and give each node `art: {kind, role}`. The renderer supports device, server, worker, queue, database, clock, parcel, memory, document, cloud, flow, code, player and gate objects. Choose each explicitly for the mechanism. `initial.visuals` and `steps[].set.visuals` hold per-actor changes such as `visible`, `count`, `rows`, `value`, `copied`, `built` and `playing`; patches accumulate and reconstruct when the reader jumps backwards. Queue actors may opt into the authored `state.queue`. Packet `kind` chooses its object symbol.

Numbered navigation compares final states without animation; `aria-current="step"` identifies the selected state. It uses the same stop/settle logic as Previous and Reset. All motion ownership, visibility and reduced-motion rules still apply.

The object renderer is also available as `Playbook.Actor` to HTML state figures. A shared object vocabulary does not require converting every comparison or decision into a transport scene. `Playbook.Payload` supplies the same envelope/file/row symbols for explicitly authored HTML transfers.

## Approved clarity direction · 28 October 2026

Keep the mechanism's arrows and ownership boundaries explicit. Current captions and controls lead the drawing, so readers know what to follow before advancing. Transfer scenes preserve the authored wide layout in a labelled local scroll viewport when a smaller composition would lose relationships. Labels retain their reading size. Resting arrows remain visible; packet motion is additional evidence, not the only indication of direction.

The 119 other state figures use topic-authored relationship maps and named walkthrough steps; ViewModel uses a three-scenario nested ownership scene. A state comparison is not a transport animation. See `website/content/diagram-models/` and `website/sequence.css`.
