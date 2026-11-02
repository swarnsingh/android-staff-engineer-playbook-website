# Delivery Semantics: review revision

This revision addresses the three teaching and layout issues in [review 5741570197](https://github.com/swarnsingh/android-staff-engineer-playbook-website/pull/18#pullrequestreview-5741570197), plus the two minor reading/source-label notes. It updates the existing `distributed-systems-site` branch and PR #18. Approval of the format, merge and publication remain with the owner. No additional chapter is converted.

## Follow the message and the lost reply

Next now animates explicitly declared packets in the shared FlowScene. The manual option prevents automatic playback while preserving packet travel on an explicit Next. The first version suppressed both; that was the reason adding packet declarations alone would not have shown movement. Previous, Reset and named-step selection still reconstruct a final state immediately. Reduced motion keeps the selected transfer highlighted and shows its final state without travelling packets.

Both runs follow M42 through send, local commit, a lost R42 acknowledgement, retry and confirmation. The warning packet uses the existing `stuck` tone. Its shared `lostReply` route ends in the transport gap before the sender, so the visual does not show an acknowledgement arriving while calling it lost. Captions retain the distinction between the sender's unknown outcome and the receiver's committed effect. The simulated timings describe presentation only, not transport performance.

The second run, “Without deduplication,” uses the same message timing but omits the replay record. Its non-idempotent handler creates a second local order on retry. It ends at `deliveries: 2, effects: 2`, with receipt R43; confirmation does not undo the first order. The deduplicated run ends at two deliveries and one effect, replaying R42. Mode switching retains the selected step so the reader can compare these outcomes directly. The browser audit explicitly resets each mode before walking its states, while other scenes keep their existing start-at-step-one mode behaviour.

## Follow the state and controls on a phone

The shared request/store preset now uses compact illustrated rows on phones, with the same actor names, role tokens and full-size artwork. The old 900-unit stacked drawing is replaced by a 392-unit drawing. The shared component reads its compact status-line offset from design tokens. All geometry stays in `tokens.json`; the chapter still supplies no styling or coordinates.

A labelled native step selector replaces seven numbered buttons for this component choice. Previous, Next and Reset remain separate touch and keyboard controls. If a new caption pushes the controls beyond the viewport, explicit step navigation makes the smallest immediate scroll needed to retain all actors and controls, when that working area fits. It retains focus and does not scroll during ordinary reading, initialization or offscreen pausing. It does not shrink labels to fit short windows or enlarged reading text.

The focused regression performs one initial scroll to the controls, then advances by keyboard without manual scrolling between steps. At both 375×812 and 1024×768 it measures every actor, the full caption and all controls against the visible viewport below the sticky reader header, for all seven steps in both modes. It also checks actual packet movement, the lost path endpoint, comparison state, native selection, focus, reduced motion, resize, 320px overflow, Q&A and the no-JavaScript fallback. All 43 focused checks pass. Screenshots beside this report show both outcomes at each requested size; `lost-reply.png` captures the warning transfer. They supplement the measured interaction evidence rather than replacing it.

## Minor notes and preservation

The answer-scoping note now begins “As you read the answers…” so its forward reference is explicit. All ten original answers remain open and paired by the existing reader. No original Q&A text is rewritten and no practice prompt is added. All 63 source-link labels across the four structure plans now name their document or specification instead of only a hostname. Two unhelpful destinations were also replaced: the inaccessible Princeton CAP reference now points to Gilbert and Lynch's *Perspectives on the CAP Theorem* on MIT's author archive, and the Microsoft session-guarantee URL, which redirected to a research homepage, now points to Cornell's archived original paper. These are planning references, not a claim of in-depth review of all four trees.

Both approved raw snapshots remain byte-identical to source `fb8354edb079e901edf18710ca9388a124712a5b`. The five original FigureMaps and ordinary navigation are unchanged. Existing [source-scope findings](../distributed-systems-pilot-2026-11-02/findings.md) and [consumer compile evidence](../distributed-systems-pilot-2026-11-02/consumer-validation.json) retain their stated limits; the Kotlin class was not changed or newly claimed as a real database integration.

## Verification scope

Build preservation passes 209 pages and 26,479 original units. Figure checks pass 172 models. Frames pass 201 chapter pages, 171 figures, 138 relationship maps and 3,351 labels. CI passes 20 website tests, 31 checker tests, all 74 exact Java examples, documentation checks and browser script syntax. The shared FlowScene gallery uses the same revised lesson data, controls and layouts, with its contract updated in the design system.

All six fresh browser suites pass: browser 209/209 pages, code readability 7,416/7,416, original Q&A pairing 1,309/1,309, Binder matrix 560/560, motion 13/13, refinement 69/69, UX 278/278 and tampering fixtures 31/31. The focused measurements record a 356.7px phone drawing at 375×812. The real project-path publication gate is refreshed against these final inputs and evidence before committing.

This is headless Chromium viewport testing and screenshot review. It does not certify physical phones, other browser engines, screen readers, real network loss, database atomicity or external service effects. Larger text and shorter windows retain ordinary scrolling rather than a promise that the entire working area always fits on one screen. The separate MSD Authentication #80 / canonical Security #78 website synchronization remains outside this milestone.

Primary implementation contracts checked: [Window.scrollBy](https://developer.mozilla.org/en-US/docs/Web/API/Window/scrollBy), [Element.animate](https://developer.mozilla.org/en-US/docs/Web/API/Element/animate) and the existing shared FlowScene motion/ownership behaviour. Delivery reasoning remains based on [RabbitMQ acknowledgement boundaries](https://www.rabbitmq.com/docs/confirms) and the pilot's existing primary source trail. This revision adds an illustrative failure comparison; it does not claim to execute the order system or a payment integration.
