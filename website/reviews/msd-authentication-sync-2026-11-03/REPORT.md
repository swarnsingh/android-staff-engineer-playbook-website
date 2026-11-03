# Mobile System Design: approved Authentication sync

This is the separate Authentication synchronization included explicitly in the owner's authorization, alongside the four topic trees. It updates only the approved `mobile-system-design/authentication.md` snapshot from source PR #80, at combined source commit `fb8354edb079e901edf18710ca9388a124712a5b`. The remaining Mobile System Design snapshots retain their recorded source versions. The canonical source checkout and other chats' worktrees are unchanged.

## Source and provenance

The raw chapter is copied as exact approved Git-object bytes. Its recorded SHA-256 and Authentication-specific reference commit are updated. A per-file provenance entry makes canonical lesson links point to this approved chapter without claiming that the whole MSD tree was synchronized. The shared source-link resolver checks that specific override before the existing per-tree provenance. The source's complete sections, code, requirements, tables and follow-up answers remain available in order.

The updated source adds explicit browser-result lifecycle handling, session-bound vault/refresher ownership, atomic replacement after invalidation, provider-dependent recovery limits and a server action-bound biometric step-up contract. No executable source example is rewritten for the website. The reader keeps the existing generated interview scaffolding; this batch adds no practice-mode decision, prediction prompt or answer-hiding interaction.

## Teaching changes

The old seven-card HTML token refresher walkthrough is replaced by the approved compact manual FlowScene pattern. Three logical actors represent the already-failed bodyless callers, their captured login's refresher/vault and the identity provider. The caption explicitly puts the resource API outside this compact scene, while the original architecture FigureMap retains it. Both comparison runs have a readable precondition before message travel, stable steps and a full text transcript.

The first run serializes refresh ownership, finishes a started bounded rotation and atomic commit before propagating caller cancellation, then lets the waiting caller re-read T2 without another token POST. The contrasting run uses independent refresh owners and reuses R1 after rotation. Its failure is explicitly conditioned on the illustrative provider's token-family revocation policy; it does not claim that every identity provider has the same rotation or reuse behavior. Both runs state that a mutex and NonCancellable cannot protect process death, a second process, a lost response or failed durable commit.

Both original Mermaid diagrams have updated designed FigureMaps bound to the approved source hashes. The obsolete HTML actor manifest and old relationship-map entry are removed only for this replaced walkthrough. The rest of the MSD figure and coverage inventories remain intact.

The interview recap now separates local biometric UI state from server authorization. A local timestamp cannot grant a protected server operation; the reader is directed to the canonical enrolled-key, challenge and step-up action-grant contract. A guide also scopes the preserved Major Concerns storage-key suggestion to local key use, so it does not override that server contract. Browser login assumptions, bodyless-read-only retry and captured-session invalidation remain explicit.

## Validation and limits

Official OAuth native-app and security references, Kotlin Mutex and NonCancellable contracts, and Android biometric cryptographic-authentication guidance were checked. The model illustrates those ownership boundaries; it does not execute a coroutine, rotate a real grant, open AppAuth or enroll a biometric key. Original compile evidence retains the scope of the approved source audit. Browser evidence covers headless Chromium at recorded reading and viewport settings, not physical-device, identity-provider or screen-reader certification. Final focused walkthrough, figure/frame, full-site audit and publication-gate results are recorded below after validation against the latest published main.

Validation uses website main `ceea5ae999b72fbec9c65d90534b70a94b7d4044`, after Security was deployed and verified on all eight index/chapter URLs. The raw Authentication bytes and recorded hash independently match source PR #80's approved Git object. The focused suite passes 164 assertions across both modes, all eight steps, and 48 viewport/state combinations at 375×812, 1024×768 and 1280×900. It also checks explicit packet travel, contrasting final outcomes, stable focus, same-step switching, reduced motion, 320px page overflow and complete static transcripts. Final phone screenshots were inspected and long captions shortened so owner labels remain visible with the actors and controls.

The build preserves 237 pages and 29,508 original units. Figure validation passes 205 models. The final frame check passes 227 chapter pages, 204 figures, 137 relationship maps and 3,657 labels. Local CI passes twenty website tests, thirty-one checker tests, all seventy-four exact Java examples, documentation checks and ten browser-script syntax checks. These checks add no claim that the Authentication integration was executed against a real provider.

All six fresh audit suites pass on the final inputs: browser 237/237 pages, code readability 7,872/7,872, original Q&A pairing 1,471/1,471, Binder 560/560, motion 13/13, refinement 69/69, UX 278/278 and tampering 31/31. Application console/runtime errors are absent in the focused run. The real project-path gate is refreshed against this evidence before committing.
