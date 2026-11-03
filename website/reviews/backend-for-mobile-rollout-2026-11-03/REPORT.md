# Backend for Mobile: reader rollout

This batch implements and publishes the eight Backend for Mobile chapters under the owner's authorization to complete the four planned trees. It follows the approved Delivery Semantics format and the retained guided structure plan. It starts from website main `c299d45aa0282d51f10298dc7da25c6142179133`, after the complete Distributed Systems reader was deployed and its twelve live chapter URLs and twenty preserved original diagrams were verified.

## Source and reading path

The guided index and all eight chapters are exact Git-object bytes from approved combined source `fb8354edb079e901edf18710ca9388a124712a5b`, including source PR #77. All nine raw SHA-256 values and per-tree provenance are recorded in `source-snapshot.json`, and all nine were independently compared to the source Git objects before publication. The source checkout and the other chats' website worktrees were not edited.

The reader follows the index order: BFF, API design, formats, transport, GraphQL/REST, broad live-data choices, SSE/WebSocket, and rate limiting. Three contiguous phases group API foundations, query contracts, and live updates/admission. Canonical source links now use the tree's approved provenance rather than a stale website snapshot. All 72 original question/answer pairs and all original code, tables, sections and diagram source text are preserved.

Each chapter gets a problem-first opening and concise labelled additions. The text separates API shape, encoding and transport; syntax from semantic compatibility; partial execution data from transport failure; and a live connection from a continuity contract. No prediction prompts, practice mode, decision-card interactions or answer hiding are introduced.

## Figures and comparisons

All three original Mermaid diagrams have designed FigureMaps. Five additional static teaching figures show BFF response ownership, old/new client compatibility, HTTP versus normalized-cache units, cursor/outbox ownership and the three rate-limiting responsibilities. Role colours, card layout, edge routing and readable text transcripts come from the existing shared FigureMap component.

Three manual FlowScenes compare bounded optional work with waiting for every section, a cursor reset that retains pending edits with one that wipes them, and current-query result ownership with arrival-order replacement. These are explicitly illustrative policies. They do not claim to execute Ktor, a real stream server, a database or an HTTP admission system. The BFF guide states that the preserved failure-classification helper does not itself install a timeout and that parent cancellation must still propagate. The SSE guide distinguishes browser Last-Event-ID processing from Android persistence/reconnect responsibilities. Its answer note identifies in-stream auth refresh as a negotiated application protocol, not a standard WebSocket frame.

The new scenes reuse the existing compact request/store and three-peer layouts. Screenshot review found overlong route labels and a wrapped actor title colliding with its status; the labels were shortened before final evidence. The focused checker now rejects clipped drawing text and title/status overlap, in addition to label collisions, overflow and separated controls. Final phone screenshots were visually inspected after those fixes.

## Validation scope

All 320 focused checks pass over three walkthrough pages and ninety state/viewport combinations: both runs, every step, 375×812, 1024×768 and 1280×900. They measure all actors, full captions and controls below the sticky reader header after one initial scroll; focus remains stable with no manual scrolling between steps. They exercise declared packet travel, the intended contrasting final outcomes, same-step mode comparison, reduced motion, the 320px overflow boundary and complete no-JavaScript transcripts.

Build preservation passes 229 pages and 28,955 original units. Figure validation passes 197 models. Frames pass 220 chapter pages, 196 figures, 138 relationship maps and 3,583 labels. Local CI passes twenty website tests, thirty-one checker tests, all seventy-four exact Java examples, documentation checks and browser syntax checks.

The unchanged executable chapter examples retain the owner's earlier source-audit compile/runtime scope; no new code or real-service integration claim is added here. The browser checks use headless Chromium and the recorded reading settings, not physical devices or screen-reader certification. Larger text and shorter windows retain ordinary scrolling.

All six fresh audit suites pass on the final inputs: browser 229/229 pages, code readability 7,736/7,736, original Q&A pairing 1,463/1,463, Binder 560/560, motion 13/13, refinement 69/69, UX 278/278 and tampering 31/31. The Backend tree contributes exactly seventy-two Q&A pairs. The real project-path publication gate is refreshed against this evidence before committing. Primary contracts were rechecked against Azure BFF guidance, AIP-180, Protobuf and FlatBuffers evolution rules, RFCs 9000/9113/9114/9110/9111/6585/6455, the GraphQL specification, Apollo cache documentation, the HTML SSE processing model and Firebase message lifetime documentation; each lesson links the sources relevant to its additions.
