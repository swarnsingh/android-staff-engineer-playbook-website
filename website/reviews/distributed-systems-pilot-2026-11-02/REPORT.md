# Delivery Semantics website format pilot

This milestone prepares four guided structure plans and one reader prototype for owner format review. Work started on 2 November 2026 and continued into 3 November in the owner's timezone; the review directory retains its start date. The branch is `distributed-systems-site`, created from website main `a8a563e91327f7e04c23f93ee2ff1bc6ebdba216` in a separate topic worktree. No other chat's checkout was switched or modified. This report does not approve a merge, deployment or conversion of the remaining chapters.

## Structure and preservation

The plans were committed before teaching-layer authoring, in commit `b021de5`. They cover all 38 chapters in the exact guided order from the approved source indexes: [Distributed Systems](../structure-2026-11-02/distributed-systems.md), [Backend for Mobile](../structure-2026-11-02/backend-for-mobile.md), [Security](../structure-2026-11-02/security.md), and [Release Engineering](../structure-2026-11-02/release-engineering.md). Each chapter records its opening problem, narrative route, retained coverage and internals, visual candidates, staff decisions, prerequisites and official authorities. The inventory records hashes, headings and diagram counts without synchronizing those trees wholesale.

Only the Distributed Systems index and Delivery Semantics chapter are registered for this pilot. Both raw snapshots exactly match Git-object bytes at source main `fb8354edb079e901edf18710ca9388a124712a5b`; hashes and provenance are recorded in `source-snapshot.json`. The original source checkout remains on its older contributor branch with its pre-existing untracked `.claude/` directory. It was fetched and read through Git objects, never switched, reset or edited. Unconverted Distributed Systems chapters link to the canonical source at that approved revision, including from Topics navigation. The website's other snapshots remain unchanged.

The [teaching layer](../../content/blend/distributed-systems/delivery-semantics.blend) follows M42 through local commit, lost acknowledgement, retry, replay and confirmation. Added prose is about 470 words versus 4,066 original words, excluding visual captions. The ordinary conceptual chapter layout is retained. No interview walkthrough, added prediction question, decision-card practice interaction or original-answer disclosure is introduced. All ten original question/answer pairs remain adjacent and open in the existing interactive Q&A view; the complete static chapter retains its original answer key.

## Visual and shared-reader decisions

Every original Mermaid diagram has a designed FigureMap. The five figures cover send-once loss, acknowledgement uncertainty, atomic local capture, Kafka transaction scope and the paths where retry/deduplication enter. Arrows have labels, ownership is explicit, captions state the intended inference, and original Mermaid source remains available as text. Figure 5 combines the three policy alternatives on labelled paths to avoid a sprawling comparison of ten separate actors.

One illustrated FlowScene provides seven manual states. Its local database effect and replay record are inside the transaction boundary; an external provider is outside the stated guarantee. The shared component now supports manual playback and a named request/store layout. All geometry is in `sceneLayouts.request-store` in design-system tokens. Topic content supplies actor roles, labels, state patches and the preset name, with no styles or coordinates. The component contract and gallery document the option. Phone layouts stack the same actors and retain the selected state on resize; static text carries every step without JavaScript.

Desktop and phone screenshots were inspected, alongside all five figures. The focused regression checks keyboard focus at the final step, repeated boundary activation, reset, reduced motion, phone resize, absence of page overflow, source destinations, open Q&A answers and the no-JavaScript transcript. [Desktop scene](desktop-scene.png), [phone scene](phone-scene.png) and [phone controls](phone-controls.png) show representative states. Screenshots are appearance evidence; automated checks supply the interaction evidence.

## Validation and limits

Local build passes: 209 pages and 26,479 original units preserved in order, with zero preservation problems. Figure validation passes all 172 models. The final frame check passes 201 chapter pages, 171 figures, 138 relationship maps and 3,351 labels. CI passes 20 website tests, 31 docs checker tests, the docs gate, all 74 exact Computer Science Java compilations and browser-script syntax. A narrow word-floor exemption was needed for the existing 391-word Computer Science review report; its text was left unchanged.

Fresh evidence from all six browser audits passes: browser 209/209 pages, code readability 7,416/7,416, original Q&A pairing 1,309/1,309, Binder matrix 560/560, motion 13/13, refinement 69/69, UX 278/278 and tampering fixtures 31/31. These artifacts were generated from the final reader inputs; a preliminary run was discarded after appearance fixes.

The real project-path build also passes the publication gate after fresh evidence and fingerprint refresh. The generated project-path preview was opened in the in-app browser; the branch remains unmerged and no deployment was triggered.

The exact consumer class compiles with Kotlin 2.4.21, coroutines 1.11.0 and JDK 17.0.19, and passes six assertions with fake transaction contracts, including eight concurrent duplicate deliveries. [Compiler evidence](consumer-validation.json) records the exact chapter and fragment hashes. It does not establish real database atomicity, rollback, authentication, payload binding, retention, crash recovery or external effects. It does not claim that every chapter sample was compiled. The earlier source audit's 703 DS assertions remain separate supplied evidence.

The [findings](findings.md) account for complete touched sections, every caption and the full existing answer key, including broad source summaries that require scope. No original correction has been silently applied. The focused browser check passes nine checks in Chromium; physical devices, other engines, screen readers, real IdP/Play/FCM/WorkManager and payment integrations were not tested.

## Owner review and follow-up

The owner should review whether this problem-first conceptual route, the static figures and the one manual trace establish a suitable format for later Distributed Systems conversion. Practice mode remains an owner decision. Broader conversion and publication require that approval.

The published MSD Authentication lesson still needs a separate website sync to source #80 after the prerequisite canonical Security #78 synchronization and dependency review. Neither is included or claimed live here. Backend, Security and Release work stops at structure planning in this milestone.
