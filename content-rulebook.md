# Content and Reader Experience Rulebook

This is the shared authoring and review rulebook for upcoming Playbook topics and their eventual website presentation. It records the owner's requirements from the reading-experience design discussions. It governs new or revised work; it does not claim that every existing chapter already meets these requirements.

Read it alongside [CONTRIBUTING.md](CONTRIBUTING.md), the [canonical](templates/canonical.md), [application](templates/application.md), [decision](templates/decision.md), and [blueprint](templates/blueprint.md) templates, and the [guided curriculum](learning-paths.md). Existing ownership and folder rules remain in force. This rulebook adds requirements for teaching and presentation; it does not create a fifth kind of knowledge chapter or authorise a repository-wide migration.

## 1. The outcome we want

A reader should want to continue reading, understand why a concept exists, build an accurate mental model, follow the real mechanics, and eventually reason about production and staff-level decisions.

The material must remain a long-term engineering handbook with depth. Making the opening approachable does not mean reducing the chapter to an introduction or replacing explanations with attractive visuals. Staff-level depth comes from reasoning about consequences and evidence, not from dense terminology.

### Firm rules and flexible choices

| Firm requirement | Flexible choice |
| --- | --- |
| Explain the need before asking readers to absorb unfamiliar machinery. | The opening may be a bug, scenario, design requirement, surprising observation, or decision. |
| Use clear language at every depth. | The amount of analogy and prerequisite recap depends on the reader and topic. |
| Preserve technical accuracy, important internals, and failure semantics. | Detailed mechanics may live in an existing canonical owner, linked deep dive, or clearly labelled disclosure. |
| Maintain a coherent chain of reasoning. | A single running example is preferred when useful, not compulsory for every chapter. |
| Make content usable across devices and accessible without animation playback. | The diagram type, layout, animation, tables, code, and interactions depend on what teaches the topic. |
| Identify known coverage gaps honestly. | A focused chapter may explicitly delegate material to another canonical topic. |

Do not apply one twelve-section template, one example shape, or one beginning/middle/end layout mechanically to every subject.

## 2. Explain necessity before machinery

The default reasoning chain is:

**Situation → problem or constraint → why the simple approach is insufficient → proposed idea → how it works → how it addresses the problem → remaining limits and trade-offs.**

Introduce a technical term, component, or abstraction when the reader has a reason to need it. Do not open with a list of APIs or technologies and only later explain their purpose. When the next complication appears, explain what broke or changed before introducing the next mechanism.

A useful transition answers one of these questions:

- What can the reader now do or explain?
- What important case does this solution still fail to handle?
- Which new requirement changes the decision?
- Why is the next layer necessary?

Return to the opening problem and state the resulting behaviour, including its limits. Do not end with an unexplained checklist or a question whose essential answer is missing.

### Reference for the storytelling technique

The owner identified [Cloud X Berry's backend ecosystem explainer](https://www.youtube.com/watch?v=mZ27vUoOEB0) as a useful example. Its transcript was fetched programmatically and read during planning. It follows one user action, introduces new needs along the journey, and connects the resulting components into a system. For example, repeated reads motivate caching, post-order work motivates asynchronous processing, and deployment/environment problems motivate further infrastructure.

Use that need-driven sequencing, not the video's wording, artwork, exact script, or every technical generalisation. It is a presentation reference, not the authority for platform behaviour. The broader [channel](https://www.youtube.com/@TheCloudXBerry) also supplies visual inspiration.

## 3. Choose the narrative for the topic

These are authoring routes, not new repository file kinds. Select the route that fits the existing canonical/application/decision/blueprint owner. State a short rationale during review when choosing an unusual structure; do not add boilerplate justification to every reader-facing page.

| Topic family | Suitable route | What must not be forced |
| --- | --- | --- |
| Language, concurrency, compiler, runtime | Concrete need → observable behaviour → small example → mechanism and internals → edge cases → engineering decisions | A technology-name catalogue or unexplained compiler listing at the start |
| Android platform mechanism | User/app scenario → platform boundary → lifecycle or request path → OS/runtime mechanics → failure/performance/security consequences | Re-explaining all Kotlin or distributed-systems fundamentals owned elsewhere |
| System design application | Problem and requirements → constraints and quality goals → simplest useful design → follow a request/data lifecycle → failures and scale → alternatives and decisions | A language-lesson structure, an early vendor shopping list, or the same architecture for every problem |
| End-to-end blueprint | Product promises → requirements and assumptions → boundaries and ownership → core flows → consistency/recovery/security → operation and evolution | Code for every component or scale numbers without a workload |
| Comparison or decision | Decision context → criteria → alternatives under those criteria → default and exceptions → consequences and revisit triggers | A contrived storyline, a universal winner, or feature-count tables with no decision consequence |
| Algorithm, data structure, fundamental concept | Concrete problem → straightforward approach → limitation → improved model → trace → correctness and complexity → limits | Animation or code where a short proof or table communicates better |
| Testing, performance, release, observability | Risk or symptom → evidence → hypothesis/strategy → experiment or intervention → result and limits → ongoing contract | Unsupported benchmark claims or a checklist detached from a failure it prevents |
| Leadership or career | Situation and stakeholders → competing needs → options and judgement → consequences → reflection and reusable heuristics | Artificial compiler internals, code examples, or a technical architecture diagram |

### System design has its own structure

Do not force system design to follow the coroutine lesson. A design discussion can begin with requirements, traffic/workload assumptions, user journeys, offline behaviour, or correctness invariants. Use the appropriate route from [mobile system design](mobile-system-design.md) and [reference architectures](reference-architectures.md).

A system design chapter should explain why each boundary, datastore, queue, cache, protocol, or background worker is needed. Follow a meaningful flow through the system and identify who owns each fact. Evaluate relevant failures, consistency, latency, battery/network/storage budgets, security, observability, rollout, and organisational consequences. Select the concerns the scenario actually needs; do not require every chapter to cover every category at equal length.

## 4. Progressive depth without losing readers

For a substantial mechanism topic, the reader's journey usually moves through three layers:

1. **Accessible entry:** a concrete problem, essential vocabulary, prerequisites, a plain-language mental model, and a small example.
2. **Deep understanding:** actual execution, internals, edge cases, misconceptions, failure behaviour, and progressively richer examples.
3. **Staff-level judgement:** ownership, contracts, alternatives, evidence, operational consequences, and decisions that affect a wider system or team.

This is a depth requirement, not a fixed page template. A decision file or system blueprint may interleave these layers differently. Keep language plain as complexity increases. Do not hide essential explanations behind a beginner/advanced switch or divide one argument into disconnected summaries.

Explain jargon near first use. Give analogies a clear boundary and connect them to the actual mechanism. A tooltip alone is insufficient for a definition a touch or assistive-technology user needs. Link prerequisites without turning each chapter into a reimplementation of the whole curriculum.

Use headings that name recognisable concepts. Warm, conversational lead-in sentences can accompany them. The outline and section headings should use consistent vocabulary.

## 5. Coverage and internals: no silent material omissions

Before drafting or adapting a topic, create a coverage inventory in the working/review notes. Compare the current chapter, its template, primary sources, and relevant user-provided materials. Do not silently shorten away substance to make the website look tidy.

For each material area, record one of:

- Explained in the main narrative.
- Explained in a labelled deeper section or disclosure on this page.
- Owned by another existing canonical chapter, with a meaningful link and a clear prerequisite/continuation relationship.
- A known gap requiring authoring or verification, explicitly recorded rather than presented as covered.
- Out of scope for a justified reason, with its boundary explained.

A link is not proof that a subject is complete. Verify that it exists, addresses the promised question, and is reasonably current. Do not create parallel owners or new folders just to make a coverage map look complete.

### What internals means

Explain the internals necessary to answer the topic's important “how” and “why” questions. This can include compiler transformation, data structures, scheduling, state transitions, protocol messages, storage, kernel/process boundaries, or resource ownership. The exact list is topic-dependent.

For coroutines, relevant areas include continuation passing, saved locals/resume state, labels and suspension markers, dispatcher/context behaviour, Job relationships, cooperative cancellation, exception propagation, supervision, callback bridging, and testing/debugging. Some related areas, such as Flow and channels, have their own canonical chapters. A beginner-friendly entry must lead to this depth or clearly route readers to it; it must not pretend the introductory model is the whole explanation.

Generated Java/bytecode views must identify whether they are actual tool output or explanatory pseudocode. Actual output needs compiler/backend/tool context sufficient to interpret it. Simplified output must say what was omitted. Do not teach that every suspend function produces an identical state machine, that every call actually suspends, or that an implementation detail is a stable API contract.

Useful primary references: [Kotlin's coroutine specification](https://kotlinlang.org/spec/asynchronous-programming-with-coroutines.html), [Continuation API](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.coroutines/-continuation/), and [JVM continuation lowering source](https://github.com/JetBrains/kotlin/blob/master/compiler/ir/backend.jvm/lower/src/org/jetbrains/kotlin/backend/jvm/lower/AddContinuationLowering.kt). [Dove Letter's compiler walkthrough](https://doveletter.dev/articles/coroutines-compiler-machinery) is a companion explanation to cross-check, not a substitute for primary contracts. Source branches move; pin versions/revisions when the actual implementation detail matters to a claim.

## 6. Research and source discipline

Use this evidence order:

1. Current primary documentation, specifications, official API contracts, and implementation source appropriate to the claim.
2. Reproducible experiments, tests, generated output, or traces with their context and limits.
3. Relevant user-provided books and notes, checked against current contracts for changing behaviour.
4. Strong technical articles and educational references for explanation, alternative mental models, and leads to verify.

Official documentation can simplify too; use the specification or source when the public explanation does not settle an important detail. A popular website or video does not override an API contract. When sources disagree, make the context/version distinction explicit or record the unresolved gap.

Cite sources close to substantive claims and provide further reading. Preserve provenance when adapting content. Write original explanations and examples; do not reproduce book chapters or third-party scripts in the website or reviewer package. Do not invent personal experience, benchmarks, exact timings, compatibility claims, source access, or review results.

### Available local reading materials

The owner identified a local `Documents/Books` collection. Files found during planning include `Kotlin.pdf`, `Android.pdf`, `Java Multithreading for Senior Engineering Interviews.pdf`, `Manifest_Android_Interview_The_ultimate_guide_Jaewoong_Eum.pdf`, algorithm notes/books, and a coding interview book. Presence is not a statement that every file or page has been reviewed. Read the relevant sections before citing them; record actual titles/authors/editions/pages when available. Local source PDFs are not website assets and must not be bundled with the review draft.

The initial pages of `Kotlin.pdf` were inspected during planning and contain coroutine material, including links to Android documentation. Treat those notes as source material to verify and synthesise, not an authority that bypasses current documentation.

Core official starting points: [Kotlin coroutines guide](https://kotlinlang.org/docs/coroutines-guide.html), [Android coroutine best practices](https://developer.android.com/kotlin/coroutines/coroutines-best-practices), and [Android lifecycle-aware coroutines](https://developer.android.com/topic/libraries/architecture/coroutines).

## 7. Code and experiments

Every block must make its role clear: runnable example, application-shaped fragment, pseudocode, generated output, command, or diagnostic output. Provide dependencies or prerequisites sufficient for its stated purpose. A fragment may depend on app APIs, but it must name those assumptions and must not claim to run independently.

- Start with the smallest example that proves the current idea, then evolve it. Explain what changed and why.
- Connect the code to visible behaviour, expected output, or a property readers can check.
- Give experiments precise edits and observable consequences. Do not ask readers to compare two programs that only print identical results when the learning objective is ordering or timing.
- Separate measured output from predictions and illustrative traces. State overhead/environment limits for timings.
- Explain harness code. For example, a console `runBlocking` bridge is not an Android UI entry point.
- Preserve cancellation, ownership, exception, resource, and main-safety contracts in examples. Avoid a technically misleading shortcut merely because it is shorter.
- Keep code monospaced and selectable. Scale it with reading preferences; provide readable scrolling/wrapping and keyboard access.
- Highlight the meaningful change or suspension/state transition when that teaches more than syntax colours alone.
- Copy controls should provide temporary feedback and recover gracefully when the clipboard is unavailable.

A Kotlin Playground integration is suitable for supported, verified JVM/language examples. It uses an external compiler service, not a JVM hosted by GitHub Pages. Explain when code leaves the browser, load it on demand, and provide a fallback. Android SDK, emulator, ADB, arbitrary shell execution, and full Gradle projects need an appropriate external/local environment; do not simulate execution while presenting it as real. See the [official Kotlin Playground component](https://github.com/JetBrains/kotlin-playground).

## 8. Animations and diagrams

Explanatory animation is part of the intended reading experience wherever temporal or causal behaviour benefits from it. For a topic where it adds no teaching value, use a suitable static representation instead and record that judgement during review. Do not invent decorative motion simply to satisfy a format requirement.

Choose motion that reveals a mechanism: suspension/resumption, changing state, request flow, cancellation, backpressure, retries, contention, failure propagation, or recovery. The visual must agree with the prose and code.

For substantial interactive models:

- Offer explicit steps, previous/next, replay, and play/pause when automatic playback is useful.
- Use consistent names between prose, code, animation, and tables. Distinguish related concepts rather than merging them for visual convenience.
- Tie highlights to actual concepts or code lines. Show different completions or failure states distinctly.
- Label conceptual scenarios, illustrative timestamps, and real traces honestly. Do not use arbitrary animation delays as performance evidence.
- Keep keyboard focus stable as state changes. Disabled actions need a deliberate focus strategy.
- Provide readable captions, keyboard/touch controls, and an equivalent static/text explanation of the sequence.
- Respect the OS reduced-motion preference and communicate the effective setting in the UI. Reduced motion must retain the lesson's meaning.
- Reflow diagrams on narrow screens rather than shrinking a large desktop canvas until labels are unreadable. Preserve the reader's state across resize/rotation where feasible.
- Avoid continuous decorative pulsing and autoplay that interrupts reading. Pause offscreen playback and avoid loading heavy assets before they are needed.

Keep Mermaid and local assets consistent with [the repository's visual/attribution rules](CONTRIBUTING.md#diagrams-images-and-attribution). Website-specific interactive renderers may supplement that canonical content in a future approved implementation; they must not make the Markdown incomprehensible on GitHub. See [Web Animations API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API) and [reduced-motion guidance](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion).

## 9. Reader controls, navigation, and accessibility

### Reading choices

Retain the requested choice of sans serif, book serif, Times New Roman, and handwriting-style reading fonts as optional preferences, with a sensible default. Keep code independently monospaced. Explain platform font differences; consistent self-hosted fonts require appropriate assets and licensing. A choice should improve reader control, not promise a medical or learning benefit without evidence.

Offer light, dark, sepia, and high-contrast themes, text resizing, motion controls, and focus mode. Reading size must support more than paragraphs: code, captions, diagram labels, Q&A, and tables also need to remain legible. Prefer relative units and respect browser zoom/default-font settings. Settings should preview their effect and remain discoverable at every width. Browser-local persistence does not imply accounts or cross-device sync.

### Navigation and tabs

Use a collapsible major-topic curriculum and an in-lesson outline. Follow the existing guided reading order rather than alphabetical filenames for the eventual learning sequence. Make search scope clear; prototype title search is not full-text search. Announce search results appropriately. Mark external destinations and new tabs accessibly.

Keep Content, Q&A, Playground, and Resources as the current design direction, subject to review. Essential explanations, checkpoint answers, source context, and experiment entry points must remain available in the continuous lesson. Supplemental tabs must not be required detours. Avoid duplicated hand-maintained answers; the future implementation should derive multiple views from one source.

Preserve reading position, provide meaningful anchors/deep links, keep the outline available on tablet/split-screen and in focus mode, and avoid multiple contradictory progress systems. A modal curriculum must manage focus, prevent interaction with its background, close predictably, and return focus to its opener.

### Accessibility targets

- Use semantic headings, landmarks, lists, tables, labels, and appropriate native controls. Provide visible focus and keyboard operation.
- Do not rely on colour, motion, hover-only tooltips, or icon shape alone for essential meaning.
- Aim for WCAG 2.2 AA. Ordinary text needs at least 4.5:1 contrast; qualifying large text has a 3:1 threshold. Verify rendered text/background combinations in every theme, not just token names. See [contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
- Target comfortable touch controls, ordinarily around 44 CSS pixels where practical. This is a product usability target; WCAG 2.2 AA's minimum target criterion is 24 by 24 CSS pixels with specified exceptions. Do not confuse the two. See [target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).
- Preserve information and operation at narrow widths and enlarged text. Keep genuinely two-dimensional code/tables/diagrams within accessible bounded regions rather than creating horizontal scrolling of the whole article. See [reflow guidance](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html).

## 10. Device and browser expectations

The experience must adapt to available browser/window space, not assumptions about a named device. Cover phones, tablets, foldables, desktop, portrait/landscape, and split-screen/multi-window use, including appropriate safe areas and available input methods.

Representative viewport checks should include narrow phones around 320/390 CSS pixels, intermediate widths around 540/768/1024, and larger desktop widths. Check content and controls with enlarged reading text, browser zoom, keyboard, and reduced motion. Exact breakpoints are design choices, not a universal device catalogue.

Before a production compatibility claim, test relevant browser engines and actual devices: Safari/WebKit on iOS/iPadOS, Chrome on Android, Firefox, and relevant desktop Chrome/Edge/Safari/Firefox configurations across Windows/macOS/Linux. Verify touch, rotation, OS text scaling, and real foldable/split-screen behaviour where supported. A browser-width simulation is not a physical-device or hinge test. Report what was actually tested and what remains unknown.

## 11. Durable content and future stack changes

The owner requires maintainability, robustness, scalability, and practical future technology changes. Keep canonical content and stable lesson identities independent of the site framework. Keep learning/simulation behaviour separate from rendering and playback timing where that boundary is useful. Prefer small explicit interfaces and shared design tokens over framework imports spread through the knowledge base.

A future stack migration will still need layout/integration work and verification. Do not promise effortless switching or create an elaborate universal content/animation engine in advance. Keep abstractions proportionate to demonstrated needs.

Existing raw Markdown, ownership, relative-link, folder, visual, and source rules remain the starting point. Website-specific source locations, metadata formats, renderer exceptions, or MDX adoption require an explicit implementation decision; do not silently rewrite all chapters or duplicate the knowledge base.

Astro, TypeScript, static search/Pagefind, and small browser components were earlier proposals, not an approved stack. [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) can host static HTML/CSS/JavaScript; a custom domain is optional, and publication needs configuration/workflow beyond merely pushing source. [Astro's Pages guide](https://docs.astro.build/en/guides/deploy/github/) is one possible deployment route, not a requirement. Browser animations do not need an application backend; external compilation, accounts, shared discussion, or synced progress introduce separate service needs if later requested.

## 12. Future video explanation

A separate Video explanation tab may later present a narrated, more extensively animated version of a topic. It is future scope. Do not add a non-working placeholder or make the written lesson dependent on video.

If approved later, keep the script aligned with the canonical explanation, provide captions/transcripts, retain readable labels and user controls, and plan how technical corrections update both forms. Reuse storyboards and validated models where useful rather than maintaining conflicting explanations. More animation and voice-over do not excuse skipping the problem, need, mechanism, or limits.

## 13. Review workflow and definition of ready

Work on representative local drafts before a broad migration. The current pilot is coroutines; later pilots should include an Android platform topic and a system design topic with their own suitable structures. Reviewing a draft is not approval to publish, migrate, or replace all source material.

A review package should contain the actual draft, useful current screenshots, the author's content intent, known limits, and precise questions. A localhost address is not accessible to an unrelated LLM session. Do not include local books, secrets, or a full third-party transcript in that package.

Require reviewers to distinguish source inspection, screenshots, actual interaction, and unverified assumptions. Prioritise specific reader problems and concrete changes over generic praise or architecture churn. Keep the requested review scope explicit. Cross-LLM agreement is useful input, not evidence that a technical claim is correct.

Before treating a revised topic as ready, check:

- The opening explains the need and the chosen structure suits this topic.
- Each major transition has a reason; the chapter closes the problem it opens.
- The depth/coverage inventory accounts for important internals and known gaps.
- Code and experiments demonstrate their claims and identify their execution context.
- Animation, diagrams, prose, and static alternatives tell the same technical story.
- Reasoning answers and source trails are available without forced tab switching.
- Reading preferences, code/labels, navigation, keyboard/focus, and small/large layouts were checked with appropriate evidence.
- Sources, assumptions, predictions, actual measurements, and limitations are distinguishable.
- Canonical ownership, links, templates, and existing repository checks remain valid.

Check the work that changed; do not invent tests or repeatedly run unrelated suites. A draft can be ready for another design review while still having clearly recorded production gaps.

## 14. Presentation references and their limits

| Reference | What to learn from it | What not to assume |
| --- | --- | --- |
| [AlgoInsight mobile system design course](https://algoinsight.io/courses/mobile-system-design) | Grouped learning sequence and course navigation | Its commercial course model, gating, or every UI choice fits this free handbook |
| [AirBridge architecture article](https://swarnsingh.github.io/swaran-technical-blogs/blogs/airbridge-technical-architecture.html) | Problem-led technical narrative, ownership, explicit trade-offs, source trail | Its diagrams or layout automatically solve narrow-screen readability |
| [Cloud X Berry backend explainer](https://www.youtube.com/watch?v=mZ27vUoOEB0) | Need-driven sequencing, one journey, explanatory reveals | Its exact toolchain is known, all generalisations are universal, or its assets should be copied |
| [Dove Letter coroutine compiler article](https://doveletter.dev/articles/coroutines-compiler-machinery) | A route into deep compiler mechanics | An article replaces official contracts or applies unchanged to every backend/version |

## 15. Living decisions, not a rigid script

Revisit presentation choices when evidence or reader feedback shows a better approach. Preserve explicit owner requirements unless they are revised in the conversation. A proposal from a reviewer is not automatically an approved requirement.

When deviating from a recommended structure, preserve the actual learning outcome and record the reason in review notes. Do not add approval gates for routine authoring decisions, and do not interpret the flexibility in this rulebook as permission to omit meaningful depth, accuracy, or accessibility.

## 16. Completeness: readers should not need to go elsewhere

The owner's goal is that a reader can understand a topic from this handbook alone, without needing official documentation, videos or blogs to fill gaps. Those sources remain the evidence trail and further reading, not required detours. If a chapter needs a concept to make sense, explain it on the page (briefly, in plain language) or link to the playbook chapter that owns it. A chapter may be split into several parts or pages when that keeps it readable, as long as nothing is dropped.

## 17. The website layer: original content is read-only

The original chapters (for example `kotlin/**/*.md`) are the owner's verified "gold" content. They are **never edited** as part of website work — not to fix errors, not to restructure, not through a separate pull request.

The website page for a chapter is a blend of two layers:

1. **The original chapter, rendered in full.** Every heading, paragraph, list item, table row, code block and diagram appears, in the original order. `website/scripts/check_preservation.py` runs on every build and fails it if any original unit is missing, out of order, repeated fewer times than in the Markdown, hidden or folded away, or if unlabelled text appears among the original blocks. Heading levels are checked, and diagram disclosure exemptions apply only to actual Mermaid source. It tests itself against those cases first. Browser CSS visibility is verified separately with the read-only audit in `website/scripts/browser_preservation.js`; the static build does not evaluate a browser CSS cascade. The original order changes only when the owner approves a specific move.
2. **An added teaching layer** in website-only files (`website/content/blend/<chapter>.blend`): a problem-first opening story, plain-language guides before dense passages, designed diagrams, step-through animations, checkpoints with answers, bridges between sections, and staff-level framing. Every added fragment is visibly labelled ("Start here", "In plain words", "See it", "Step through it", "Check yourself" and similar) so readers can always tell the original from the additions.

**Corrections** to original text are also website-only. They live in `website/content/corrections-*.json`, each with the exact original text, the replacement, a reason and sources. A correction is applied only after the owner approves it (`"status": "approved"`), and an applied correction must be visibly marked on the page: the build highlights the corrected words where it safely can and adds a "Corrected on this website" note to the section with the reason, the original wording and the sources. Wording or style rewrites are not corrections and are not applied.

**Diagrams.** Original Mermaid or text diagrams may be redrawn as designed, theme-aware visuals that reflow on phones. The original diagram stays available beside the redraw ("Original diagram from the chapter"), so it is never lost.

## 18. Quality bar for the blended pages

- **Different and impactful, not decoration.** Each addition must teach something the original text alone makes harder to see: the problem that makes the concept necessary, a mental picture, a sequence over time, a cause and effect, or a decision. Do not add material just to fill a format.
- **Use visuals and animation generously where they teach.** Aim for a designed visual in each part of the story where structure, timing or ownership matters, and a step-through animation wherever behaviour unfolds over time (initialisation, capture, suspension, cancellation, backpressure, visibility between threads, compilation steps). Every animation has Previous/Next/Play controls, a caption per step, respects reduced motion, and prints all its steps as text.
- **Stay concise.** Additions should sharpen the chapter, not double it. As a working target, keep added prose under roughly a quarter of the original chapter's words; visuals and animations do not count against it. Review each finished chapter for verbosity and whether it should be split.
- **Be exactly right.** Added explanations, code and captions follow sections 6 and 7: verify against primary sources, compile or run added code where possible, and never restate an original claim that is pending correction review.
- **Split wide trees into sub-sections.** A tree with many chapters (Android has 101) is grouped by the phases of its guided reading sequence, in the tree index's `### Phase …` lists. The navigation shows one group per phase, each page names its phase, and a large tree may be converted phase by phase as a pilot.
- **Flag, do not silently fix.** When blending reveals a possible error in an original chapter, add an "Under review" note before the section that contains it, list the finding with evidence in `website/reviews/<tree>-<scope>-findings.md`, and keep the teaching layer from restating the claim. The replacement wording is applied only after the owner approves it.
- **Follow the story parts.** Pages are grouped into parts — The problem and the idea, How it really works, In real apps, Staff-level judgement, Practise, Go deeper — shown as bands in the page and groups in the outline. Additions should make each transition between parts feel necessary.

How to build, preview and continue this work — including the blend file format, the animation format, the per-chapter progress table and the open decisions — is documented in [`website/README.md`](website/README.md). Any model or person picking up the website work should read this rulebook and that guide first.

## 19. Separate website repository and private previews

Website development belongs in the separate private [website repository](https://github.com/swarnsingh/android-staff-engineer-playbook-website). Since separation, website work makes no further changes to the [original playbook repository](https://github.com/swarnsingh/android-staff-engineer-playbook). Its earlier remote website branch (`codex/reader-website` at `390f8f8`) remains historical work; its `main` and canonical chapters are unchanged. Do not push, merge, delete branches or change visibility there as part of website work. A future source import requires an explicit reviewed revision; do not silently synchronise or rewrite the collected chapters.

The website repository retains the original chapter layout as a read-only source snapshot. `source-snapshot.json` records its origin, revision and Kotlin file hashes. All reading explanations are rendered in full; the labelled teaching layer lives under `website/content/blend/`. Proposed corrections remain separate, unapplied and unapproved until the owner approves exact replacements. A request to fix a website defect does not approve the entire corrections triage.

Preserve the existing website branches (`codex/reader-website` and `claude/reader-website-kotlin`) and their commit identities in the new repository. They provide the earlier drafts and review history. Keep the current website work on its own branch and describe which branch is the current preview. Never remove earlier work simply to make the new repository look cleaner.

Remote previews must use owner-private hosting. A private GitHub repository alone does not establish private website access. Check the hosting service's returned access/deployment state; never make the preview public as a fallback. Keep deployment credentials out of source, logs and reviewer packages. A hosted preview is a snapshot of the verified build, and later local edits require a new verified deployment before claiming the hosted site includes them.

Preservation has two complementary checks: the static build verifies original units, order, repeat counts, heading levels and permitted diagram disclosures; the rendered browser audit checks source-unit presence in rendered text and the specific visibility/resource failures documented in `website/README.md`. It is not proof against arbitrary overlays, all CSS combinations, low contrast, or accessibility defects. Record both results and the tested browser/device scope. Compile coroutine teaching examples against their stated versions and test lifecycle boundaries, including cancellation before startup, active work, queued work and submissions after shutdown. A single successful happy-path run is not evidence for those contracts.

For actor-style examples, test service-local timeouts separately from cancellation of the worker or caller. Actor shutdown is an ordinary failure for a caller that remains active; do not accidentally cancel that caller by forwarding the actor’s cancellation exception. Before accepting a value-class identity explanation, compile the exact operand types: `===` is prohibited for two value-class operands even though reference identity can be observed after boxing as `Any`. Do not render a proposed correction as an unmarked teaching replacement while the original contradictory example remains unapproved; retain such fragments in review files until approval.
