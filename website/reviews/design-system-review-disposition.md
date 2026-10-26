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
