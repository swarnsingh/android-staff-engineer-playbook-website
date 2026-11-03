# Delivery Semantics: review polish

This revision addresses the three non-blocking notes in [review 5747231362](https://github.com/swarnsingh/android-staff-engineer-playbook-website/pull/18#pullrequestreview-5747231362). It updates PR #18 on `distributed-systems-site`. It converts no additional chapter and leaves approval, merge and publication with the owner.

## Visible changes

In “Without deduplication,” step 2 now says that this run keeps no replay record. It no longer describes binding the payload to an operation ID, which suggested the retained record omitted by this comparison. The deduplicated run retains its existing caption.

Help text names the step dropdown when that control is selected. Scenes using numbered buttons retain their existing instruction.

Both lost-reply steps now declare a lost packet. The shared renderer replaces that route’s endpoint arrowhead with a persistent warning-coloured ×. It remains after packet travel finishes, on direct step selection, with reduced motion, in both modes and after responsive redraw. Selecting another step clears it. The cross sits in the transport gap, before the sender; the caption and sender’s “outcome unknown” state retain the explanation. The faint resting route remains available as context, while the cross marks where this reply stopped. Marker geometry, stroke and colour belong to the shared design-system tokens/components; the lesson supplies only the loss flag. The gallery consumes the same example.

The SVG marker behaviour was checked against the [SVG 2 marker specification](https://www.w3.org/TR/SVG2/painting.html#MarkerElement). This revision changes the illustrative presentation, not the delivery contract or executable consumer.

## Focused browser evidence

All 70 focused checks pass. They include packet travel, the lost-route endpoint, a visible cross after the packet disappears, direct step selection, reduced motion, comparison of effects, marker cleanup, retained keyboard focus, responsive redraw, both static transcripts and all ten original Q&A pairs.

The measurements cover every actor, the full caption and the controls at every step in both modes: 42 state/viewport records across 375×812, 1024×768 and 1280×900. They all fit below the sticky reader header after one initial scroll, with no manual scrolling between steps. The 320px overflow check also passes. Screenshots capture both settled loss states and final outcomes at all three measured sizes. The phone and desktop loss screenshots were visually inspected.

No application console or runtime error was observed. The bare local HTTP server returns one unrelated 404 for `/favicon.ico`; this is explicitly recorded in `auxiliaryErrors`, separate from application errors. An initial focused run failed the broad console assertion on that missing icon; the final assertion preserves reporting of the icon request while continuing to fail on application errors.

These are headless Chromium viewport checks at the default reading size, not physical-device or screen-reader certification. Larger text and shorter windows still use ordinary scrolling. The walkthrough models loss and local effects; it does not execute a network, database or payment system.

## Preservation and scope

Both source snapshots remain byte-identical to approved source `fb8354edb079e901edf18710ca9388a124712a5b`. Navigation, five original FigureMaps, original Q&A text and the four structure plans are unchanged in this revision. Earlier [source-scope findings](../distributed-systems-pilot-2026-11-02/findings.md) and [consumer validation](../distributed-systems-pilot-2026-11-02/consumer-validation.json) retain their stated limits. No new consumer integration claim is made.

The source checkout and its untracked `.claude/launch.json` were not edited. The temporary server used for these checks is stopped after testing; no lasting preview service is promised. The separate Authentication synchronization remains outside this milestone.

## Shared-site verification

Build preservation passes 209 pages and 26,479 original units. Figure checks pass all 172 models. Frames pass 201 chapter pages, 171 figures, 138 relationship maps and 3,351 labels. Local CI passes 20 website tests, 31 checker tests, all 74 exact Java examples, documentation checks and browser-script syntax.

All six fresh browser audit suites pass: browser 209/209 pages, code readability 7,416/7,416 checks, original Q&A pairing 1,309/1,309, Binder 560/560, motion 13/13, refinement 69/69, UX 278/278 and tampering 31/31. The publication gate is refreshed against this final evidence and the unchanged website main `a8a563e91327f7e04c23f93ee2ff1bc6ebdba216` before committing. No merge, deployment or publication is performed.
