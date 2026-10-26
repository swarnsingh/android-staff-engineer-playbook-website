# Design system review: disposition

Codex reviewed `61b97a5`. All 11 findings were accepted and fixed. The fixes were checked in the local previews (`website/tools/build_design_system_preview.py`) at 320, 390, 768 and 1280px.

| # | Finding | Fix | How it was checked |
|---|---|---|---|
| P1 | Diagrams unreadable on phones | Both diagrams now run on one runtime (`components/bundle.js`) with authored `wide` and `narrow` layouts. Below 520px of container width the stacked layout is used, capped at 440px wide. | Node labels measured 16.1px at 320, 19.9px at 390 and 17.2px at 768 (desktop layout). No horizontal scroll at any width. |
| P1 | Pause leaves a packet travelling | `stop()` cancels the packet in flight (token), shows the step's final state, and removes the edge's marching class. Edges march only while a packet travels. Leaving the screen calls the same stop. | One packet was in flight when Pause was pressed. 60ms later: 0 packets, 0 moving edges, state at the step's final value. After 3.5s nothing had changed. |
| P1 | Reader motion setting not wired | `Playbook.motion` combines `prefers-reduced-motion` with `html.reduce-motion` (set by `app.js`) and is read live. CSS also stops under `html.reduce-motion`. | Turning on `reduce-motion` mid-flight: the packet was cancelled and the step finished at once. The next step ran with no packets. FlowDiagram went still and came back when the class was removed. |
| P1 | `line-strong` below 3:1 | Light `#6a8070`, dark `#6c8172`, sepia `#86714d`. | At worst 3.64 (light), 3.64 (dark), 3.45 (sepia) across canvas, sheet and sheet-sunken. |
| P2 | Binder captions overstate timing and ordering | The scene is labelled "an illustrative run". "Oldest" is removed, and so is the method-time claim. The run's times are labelled "in this run". The oneway caption now says the proxy "passes the transaction into the kernel and returns". | Captions were re-read against the AOSP AIDL language page. |
| P2 | Sheet width and breakpoints | `box-sizing: border-box`. Both rails show from 1440px and the outline alone from 1200px, derived from 244 + 880 + 220 plus gutters. | The sheet measured 880px at a 1280px viewport. |
| P2 | High contrast keeps tints | `bundle.css` swaps tints for 1px `line` borders on the sheet, callouts, checkpoints and diagram paper. It drops the dot grid, and warn and done nodes keep the sheet fill with a 3px outline. | Callout in contrast: transparent background, 1px solid border. |
| P2 | Fonts not self-hosted | Latin WOFF2 subsets of Inter, Source Serif 4, JetBrains Mono and Patrick Hand are in `fonts/` (164KB total, OFL) and listed in `tokens.json`. The previews no longer load Google Fonts. | 0 external requests; Inter, Source Serif 4 and JetBrains Mono load locally. |
| P2 | Colour-vision claim unsupported | The claim is revised: green and blue are about 1.08:1 apart in lightness. Direction now also differs by line pattern (dashes, dots, dash-dot) and packet shape (circle, diamond), plus arrowheads and labels. | Visually checked at 320px in dark. |
| P3 | Invented checkpoint quota | The quota is removed: "as many as the section needs, often one to three". | — |
| P3 | Copy button inert | It now copies to the clipboard, with a select-and-prompt fallback. | — |

**Not verified:** the live layout switch when a window is resized across 520px. It uses `ResizeObserver`, and the test browser pane stopped painting frames during that check, so neither `ResizeObserver` nor `requestAnimationFrame` fired. A fresh load picks the correct layout at every tested width. Physical devices and other browser engines were not tested.

## Round 2 (review of `6020b03`)

All five findings were accepted and fixed. Every check below was measured in the local previews.

| # | Finding | Fix | How it was checked |
|---|---|---|---|
| P1 | Moving diagrams too small just above the breakpoint | The fixed 520px switch is gone. `pickLayout()` computes the scale the wide drawing would render at and keeps it only if handwritten text stays at 15px or more and other text at 12px or more. A `TEXT` table matches `bundle.css`: wide smallest 17/13, stacked 19/15. The stacked layout draws its secondary text, edge and packet labels, chips, region names and order markers larger. Chip text is shortened to "T1 busy". | Smallest text, handwritten / other: 320px stacked 16.1 / 12.7; 570px stacked 26.1 / 20.6; 768px FlowDiagram wide 16.2 / 12.4 and FlowScene stacked; 1280px FlowScene wide 20.4 / 15.6. No label clipped outside the drawing, and chip text fits its chip. |
| P2 | Generated rows break at four or more nodes | Row width = 48 + n × 168 + (n − 1) × 84, so gaps are always 84 units. Rows take 2 to 5 nodes; anything else throws a clear error. `mountAll` now isolates failures, so one broken diagram does not stop the others. | 4 nodes: viewBox 972, gaps 84, connectors end inside the gaps. 5 nodes: viewBox 1224, the same. 6 nodes: rejected with the error message; the other diagrams on the page still mounted. |
| P2 | Two looping diagrams play together | A shared turn: the first visible eligible loop plays and the others wait still with Play. Play on another diagram, or Play/Next on a FlowScene, takes the turn. Pausing keeps the turn, and leaving the screen releases it. | At 570×800 both diagrams were in view and only the first played. Play on the second stilled the first. Pausing the second left both still. |
| P2 | Back-navigation protection overstated | The README now says `overscroll-behavior-x: contain` is containment where supported, and cites WebKit bug 240183 ("does not disable history navigation", open). It asks for a real-iPhone test before relying on it. | Bug report read; not tested on an iPhone. |
| P3 | Scroll-region name exposed when nothing scrolls | `role="region"`, the "…, scrolls sideways" name and `tabindex` are now added only while the box overflows, using the box's `data-label`. | 320px: region, label and tabindex present. 1280px: all three absent. |

**Still unverified:** Safari's swipe behaviour on a physical iPhone, and other browser engines.

## Round 3 (review of `39ce991`)

| # | Finding | Fix | How it was checked |
|---|---|---|---|
| P2 | A failed diagram still blocks later diagrams from auto-playing | FlowDiagram builds first and joins turn-taking only after a successful build, so a diagram whose data throws is never registered. Its listeners are also attached only after the build. On failure, `mountAll` adds `pb-error`: the empty drawing and its controls are hidden and buttons disabled, and a notice shows "This diagram could not be drawn." plus the diagram's text description. | Codex's case reproduced: a 6-node row placed first, a valid 3-node row second. The failed figure showed the notice with no drawing or controls. The valid figure rendered 3 nodes, 2 packets and Pause, so it auto-played. On the normal FlowDiagram preview, turn-taking was unchanged: the first played, the second waited, and Play on the second moved the turn. |
