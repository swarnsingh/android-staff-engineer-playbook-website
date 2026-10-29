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

### Define the structure before conversion

Before starting a new section/phase, write its topic-by-topic structure in `website/reviews/android-phaseN-structure.md` (or the corresponding tree's review directory). Do this before drafting the teaching layer. Record the opening problem, chosen narrative route, original coverage to retain, important mechanism/internals, planned visuals or animations, production/staff decisions, prerequisites and sources. Explain differences between topics instead of mechanically reusing a template. The owner's instruction is to complete the remaining Android phases and publish a private preview for review; it does not approve pending technical corrections.

For Android, consult relevant sections of the owner's *Manifest Android Interview* by Jaewoong Eum where they address the topic. Record the edition and actual pages read; use it to identify missing teaching questions and internals, then verify changing technical claims against primary sources. Do not claim the whole book was reviewed or copy its prose, examples or figures into lessons.

### Content and Q&A have separate jobs

For **every topic tree**, including future subjects beyond Kotlin and Android, the Content tab carries the explanation, code and visual walkthroughs. Dedicated probing questions, answers, review checklists and added question checkpoints belong in the Q&A tab only in the interactive reader. Place each question immediately before its own answer, with a clear **Answer** heading on a new line. Do not send the reader to a separate answer key or require scrolling back to recover the question. New source material uses adjacent question/answer sections; the shared reader pairs legacy numbered lists without duplicating or abbreviating their text. Checklists remain checklists rather than acquiring invented answers. Preserve every original question and answer; move the existing blocks rather than duplicating them. A rhetorical question that develops the lesson is still part of Content. The complete static chapter remains a readable fallback when JavaScript is unavailable. Test both activated tabs and deep links, not just the default Content view.

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

Owner clarification, 2026-10-27: **animation is optional for every topic. A beautiful, clear static diagram is a complete result when it teaches the idea well.** Choose the representation for the mechanism, and use motion only when seeing a change over time makes that mechanism easier to understand. Neither an animation count nor a requirement to animate every chapter is a completion criterion.

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

Retain the requested choice of sans serif (the default), book serif, Times New Roman, handwriting-style and legibility-oriented reading fonts as optional preferences. The choice changes prose only; headings, interface, tables and diagrams keep their faces. Keep code independently monospaced. Explain platform font differences; consistent self-hosted fonts require appropriate assets and licensing. A choice should improve reader control, not promise a medical or learning benefit without evidence.

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

Owner authorization, 29 October 2026: for the Engineering Fundamentals rollout, verify material source errors against official documentation, specifications or original papers, apply the supported corrections on the website, and raise a matching pull request in the original private playbook repository. This scoped instruction supersedes the historical ban on source correction PRs below. Keep the website raw snapshot unchanged so exact correction replay remains auditable. The owner reviews and merges the source PR.

Owner layout direction, 29 October 2026: keep the existing 880px sheet, 760px reading column and prose measure. Only wide diagrams/animations or genuinely overflowing code and tables may extend symmetrically into the margins, by at most 120px per side and up to 1000px total, further limited by the viewport and navigation rails. Do not widen ordinary paragraphs or the whole page.

The original chapters (for example `kotlin/**/*.md`) are the owner's verified "gold" content. They are **never edited** as part of website work — not to fix errors, not to restructure, not through a separate pull request.

The website page for a chapter is a blend of two layers:

1. **The original chapter, rendered in full.** Every heading, paragraph, list item, table row, code block and diagram appears, in the original order. `website/scripts/check_preservation.py` runs on every build and fails it if any original unit is missing, out of order, repeated fewer times than in the Markdown, hidden or folded away, or if unlabelled text appears among the original blocks. Heading levels are checked, and diagram disclosure exemptions apply only to actual Mermaid source. It tests itself against those cases first. Browser CSS visibility is verified separately with the read-only audit in `website/scripts/browser_preservation.js`; the static build does not evaluate a browser CSS cascade. The original order changes only when the owner approves a specific move.
2. **An added teaching layer** in website-only files (`website/content/blend/<chapter>.blend`): a problem-first opening story, plain-language guides before dense passages, designed diagrams, step-through animations, checkpoints with answers, bridges between sections, and staff-level framing. Every added fragment is visibly labelled ("Start here", "In plain words", "See it", "Step through it", "Check yourself" and similar) so readers can always tell the original from the additions.

**Corrections** to original text are also website-only. They live in `website/content/corrections-*.json`, each with the exact original text, the replacement, a reason and sources. A correction is applied only after the owner approves it (`"status": "approved"`), and an applied correction reads as the current lesson text. Owner decision, 2026-10-28: remove repeated correction notices and inline correction highlighting from the main article. Retain each correction, its reason, official sources and original wording in the repository and optional technical correction history under About this lesson. This supersedes the earlier visible-marking rule. Wording or style rewrites are not corrections and are not applied.

**Diagrams.** Original Mermaid or text diagrams may be redrawn as designed, theme-aware visuals that reflow on phones. The original diagram stays available beside the redraw ("Original diagram from the chapter"), so it is never lost.

## 18. Quality bar for the blended pages

- **Different and impactful, not decoration.** Each addition must teach something the original text alone makes harder to see: the problem that makes the concept necessary, a mental picture, a sequence over time, a cause and effect, or a decision. Do not add material just to fill a format.
- **Keep visual labels readable when text grows.** Check intermediate as well as narrow/wide layouts with enlarged reading text. A proportional timeline may use numbered bars and a full-text legend; do not discard labels merely to pass an overflow check.
- **Choose the visual that teaches the mechanism.** Use beautiful, labelled static diagrams for structure, relationships, comparisons and decisions. Use a manual step-through or animation when changing state, timing, order or movement reveals something a still diagram makes harder to understand. A topic may need both. Every animation has suitable step/playback controls, a caption per step, respects reduced motion, and prints all its steps as text. Do not add motion or controls merely to increase coverage.
- **Stay concise.** Additions should sharpen the chapter, not double it. As a working target, keep added prose under roughly a quarter of the original chapter's words; visuals and animations do not count against it. Review each finished chapter for verbosity and whether it should be split.
- **Be exactly right.** Added explanations, code and captions follow sections 6 and 7: verify against primary sources, compile or run added code where possible, and never restate an original claim that is pending correction review.
- **Split wide trees into sub-sections.** A tree with many chapters (Android has 101) is grouped by the phases of its guided reading sequence, in the tree index's `### Phase …` lists. The navigation shows one group per phase, each page names its phase, and a large tree may be converted phase by phase as a pilot.
- **Flag, do not silently fix.** When blending reveals a possible error in an original chapter, add an "Under review" note before the section that contains it, list the finding with evidence in `website/reviews/<tree>-<scope>-findings.md`, and keep the teaching layer from restating the claim. The replacement wording is applied only after the owner approves it.
- **Follow the story parts.** Pages are grouped into parts — The problem and the idea, How it really works, In real apps, Staff-level judgement, Practise, Go deeper — shown as bands in the page and groups in the outline. Additions should make each transition between parts feel necessary.

How to build, preview and continue this work — including the blend file format, the animation format, the per-chapter progress table and the open decisions — is documented in [`website/README.md`](website/README.md). Any model or person picking up the website work should read this rulebook and that guide first.

<a id="19-separate-website-repository-and-private-previews"></a>

## 19. Separate website repository and publication

### Website UX publication, 2026-10-28

The owner approved completing the UX review with subagents and publishing the verified result. Website PR #1 is merged; `main` is the current publication branch and source-reference target. Apply this presentation work in the existing website repository and preserve the canonical corrected content. The later code-readability request includes fixing fenced examples inside lists throughout the site.

### Merged-source synchronization, 2026-10-27

The owner merged source PR #57 and instructed website synchronization and publication. Use merged source commit b8b56170e3b78f26ad73807b626acfb9530deb47 and its 743 correction records as the canonical content for this release. Keep the website snapshot immutable, render the canonical approved inventory once, and verify exact alignment before publication. The earlier “do not merge” instruction below is historical; do not infer permission to merge website PR #1 or future source changes.

### Completion authorization, 2026-10-27

The owner then instructed: “fix the remaining part as well” before the final Gemini review. This extends the earlier selected-issue approval to the retained Kotlin triage, all nine Android phase reports, candidates and handover follow-ups. Verify each issue against official documentation or the owning project's official implementation, apply only a supported correction, record justified no-change decisions, and validate framework-dependent examples with real dependencies where feasible. Keep an exact completion ledger and disclose validation limits. Update both existing PRs; publish the completed website through this repository's GitHub Pages workflow. Do not merge either PR or change the original repository's private visibility. This authorization does not approve unrelated new claims or every historical proposal verbatim.

### Verified source-correction approval, 2026-10-27

The owner subsequently instructed: “fix and publish them” and requested a PR in the original repository as well, with official documentation as the source of truth. Apply the specifically verified incoming-review corrections on the website, label their changes, and propose the same corrections in an isolated branch/PR in the original repository. Do not interpret this as approval of every older correction proposal or a merge instruction. Preserve unrelated local work and the original repository's private visibility. Incorrect explanations must be replaced in active lessons; Git history and correction disclosures retain the former wording for traceability. The detailed source-verification report identifies this approved scope.


### One website repository and one deployment path

Owner decision, 2026-10-26: [swarnsingh/android-staff-engineer-playbook-website](https://github.com/swarnsingh/android-staff-engineer-playbook-website) is the single source of truth for the website, regardless of which LLM or developer does the work.

- Make all website changes in this repository: lessons, design tokens, components, assets, reviews, audit tools and deployment configuration. Continue from its current branch and handover; do not create another website repository or an agent-owned copy as the working source.
- Publish through one deployment workflow defined in this repository. Build the deployed website from an identified commit in this repository and record that commit, the audit result and the deployed URL. Keep the workflow and commands usable by the next LLM or developer.
- Do not push website source to a second hosting repository, publish separate Codex/Claude artifacts, create a new agent-specific hosting project, or maintain competing preview URLs. A hosting runtime may serve the build, but it must use this repository's documented deployment path; it must not become another source of truth.
- Local build directories and localhost servers are temporary verification tools. They are not the published website. Existing external previews are historical snapshots until the repository's deployment path replaces them; do not present them as current after local changes.
- If the repository has no suitable deployment setup, prepare the configuration here and identify the concrete hosting or access decision that remains. Do not silently publish somewhere else or make a private preview public to work around that gap.

This decision supersedes earlier handovers suggesting publication as Claude artifacts or separate agent-hosted previews. It does not approve original-chapter corrections. The public publication decision below supersedes the earlier private-preview requirement.

Website development belongs in the separate [website repository](https://github.com/swarnsingh/android-staff-engineer-playbook-website). Since separation, website work makes no further changes to the [original playbook repository](https://github.com/swarnsingh/android-staff-engineer-playbook). Its earlier remote website branch (`codex/reader-website` at `390f8f8`) remains historical work; its `main` and canonical chapters are unchanged. Do not push, merge, delete branches or change visibility there as part of website work. A future source import requires an explicit reviewed revision; do not silently synchronise or rewrite the collected chapters.

The website repository retains the original chapter layout as a read-only source snapshot. `source-snapshot.json` records its origin, revision and Kotlin file hashes. All reading explanations are rendered in full; the labelled teaching layer lives under `website/content/blend/`. Proposed corrections remain separate, unapplied and unapproved until the owner approves exact replacements. A request to fix a website defect does not approve the entire corrections triage.

Preserve the existing website branches (`codex/reader-website` and `claude/reader-website-kotlin`) and their commit identities in the new repository. They provide the earlier drafts and review history. Keep the current website work on its own branch and describe which branch is the current preview. Never remove earlier work simply to make the new repository look cleaner.

Owner decision, 2026-10-27: publish the website repository and rendered website publicly through GitHub Pages, like the AirBridge blog. This explicitly supersedes the earlier private-source/private-preview decision. Keep the original playbook repository private. The single website URL is https://swarnsingh.github.io/android-staff-engineer-playbook-website/ and publication runs through `.github/workflows/website.yml` in this repository. A local server, downloadable build or Codex/Claude artifact is not the delivered website. Verify the actual deployment, live lesson links and `build-info.json` commit before reporting publication. Keep deployment credentials out of source and logs. Later changes require a newly verified deployment.

Preservation has two complementary checks: the static build verifies original units, order, repeat counts, heading levels and permitted diagram disclosures; the rendered browser audit checks source-unit presence in rendered text and the specific visibility/resource failures documented in `website/README.md`. It is not proof against arbitrary overlays, all CSS combinations, low contrast, or accessibility defects. Record both results and the tested browser/device scope. Compile coroutine teaching examples against their stated versions and test lifecycle boundaries, including cancellation before startup, active work, queued work and submissions after shutdown. A single successful happy-path run is not evidence for those contracts.

For actor-style examples, test service-local timeouts separately from cancellation of the worker or caller. Actor shutdown is an ordinary failure for a caller that remains active; do not accidentally cancel that caller by forwarding the actor’s cancellation exception. Before accepting a value-class identity explanation, compile the exact operand types: `===` is prohibited for two value-class operands even though reference identity can be observed after boxing as `Any`. Do not render a proposed correction as an unmarked teaching replacement while the original contradictory example remains unapproved; retain such fragments in review files until approval.

## 20. Website-wide learning experience

### Learning navigation and diagram interactions

Owner-approved UX refinement, 2026-10-27:

- Learning-path pages prioritise choosing a phase and starting a chapter. Lesson-specific tabs and save controls belong on lessons, and tabs appear only when they contain meaningful material.
- Curriculum navigation defaults to the current Android or Kotlin track. Make the complete catalog an explicit choice, label title/path search scope and mark external destinations.
- Distinguish curriculum navigation, the current-page outline and the next lesson. Retain the complete original chapter and no-JavaScript fallback; simplified controls must not discard questions, answers, sources or explanations.
- Keep the current diagram state, caption and controls together. Use consistent Previous, Next and Reset labels for equivalent actions; offer Play/Pause for temporal playback. Put reusable help and the full textual transcript in an optional disclosure while keeping the current-step explanation visible.
- Fenced code uses one continuous code surface in every context, including nested lists. Inline-code chip styling must never apply to a fenced example. Keep code headers concise; retain specific example assumptions near the explanation.
- Keep editorial provenance, technical correction history and original-source details in an About disclosure. Corrected explanations read normally, without repeated review notices or highlighted replacements. Published reader chrome must not show draft labels.
- Verify learning paths and representative lessons on desktop/tablet and run automated phone regressions, including keyboard operation, motion preferences, touch controls and enlarged text. Follow the mobile review timing below and record evidence and limits before publication.

### Mobile review timing across the whole website

Owner instruction, 2026-10-29; this takes precedence over earlier review-timing guidance:

- Perform **one consolidated full manual mobile visual and interaction review only after all topic trees and planned pages are implemented and integrated into the complete website build**. Completing Android and Kotlin, or any other subset, does not satisfy this condition.
- While individual topics or tracks are being built, use desktop/tablet reviews and automated mobile regression checks only. Fix failures found by those checks during the current work.
- Do not repeat full manual mobile reviews after each chapter, track or partial release. Keep the consolidated review deferred until the whole website is ready, and report that status accurately.
- This rule applies to every current and future topic, and to all models and contributors working on this website.

### Primary article reference: AirBridge

Owner preference, 2026-10-27: the [AirBridge technical architecture blog](https://swarnsingh.github.io/swaran-technical-blogs/blogs/airbridge-technical-architecture.html) is the primary reference for the overall technical article experience. Use its readable visual hierarchy and connected explanation to guide new articles and reader refinements.

- **Give the article a clear opening.** Use a strong title, a concrete engineering problem and a concise statement of the idea. An opening illustration is useful when it establishes the system or mental model; it is optional.
- **Create a calm reading rhythm.** Use generous spacing, clear heading levels, restrained colour and readable paragraphs. Let substantial figures have enough room for their labels and relationships to be understood together.
- **Integrate diagrams with the argument.** Introduce what a figure explains, place it beside the relevant mechanism and add a useful caption. A beautiful static architecture, relationship or state diagram can be the finished visual.
- **Explain the decisions.** Connect requirements and failure cases to boundaries, ownership, mechanisms, alternatives and trade-offs. Callouts should identify a specific invariant, decision or caveat. Metrics and status badges require evidence; do not invent them to fill a layout.
- **Use code and tables with a purpose.** A focused code example should explain a contract or mechanism. A comparison table should help the reader choose or understand a consequence. Explain unfamiliar terms where the audience needs them.
- **Keep claims bounded.** Distinguish verified behaviour, illustrative examples, open findings and unfinished work. Treat the blog as a presentation reference; verify each lesson's technical claims against its own sources.

Adapt these principles to each topic and to the playbook's agreed reading measures, themes, accessibility and navigation. Do not force the AirBridge section list, hero layout or project-specific content onto every Kotlin or Android lesson. ByteByteGo and Cloudmash remain supporting references for diagrams and interactive teaching. The following earlier direction remains relevant within that priority.

Owner direction, 2026-10-27: learn from the whole experience of [ByteByteGo](https://bytebytego.com/courses/system-design-interview/design-a-chat-system) and [Cloudmash Learn](https://cloudmash.dev/learn/hld/load-balancing-and-traffic-management/what-a-load-balancer-does/). Apply the principles across the website, rather than treating a linked lesson as the sole chapter to improve. Use original artwork, wording and implementation.

- **Give the reader a route.** Keep phase navigation, topic search, the current section, previous/next lessons and a clear route to practice available. Introduce the problem, build a mental model, explain the mechanism, expose a failure or trade-off, then ask the reader to reason about it. Preserve the original chapter as required by section 17.
- **Use one visual language.** Recognizable devices, servers, workers, queues, memory pages and data stores should carry the explanation. Derive colours, typography and surfaces from the shared tokens. Reuse actor colours consistently: blue for devices, purple for execution, teal for stored data, rose for queued work. Show status with words and shapes as well as colour. Attractive diagrams must still identify ownership, boundaries and direction correctly.
- **Show consequences.** A queue should visibly gain or lose an item; a saved value should remain when its collector leaves; a copied memory page should look different from its parent. Author these changes explicitly. An active box alone is not evidence of a transfer. Numeric badges require an authored quantity; schematic rows must not imply measured totals.
- **Let readers explore meaningful alternatives.** Use modes or controls when changing an input reveals a different outcome. Make the constraint, action and consequence visible together. Deterministic step-throughs and static structure diagrams remain useful; do not add a simulated control whose outcome the lesson does not explain.
- **Keep detail progressive.** Make the main diagram understandable at a glance, tie each step to a short caption, and provide the full explanation and sources nearby. Put optional instructions and complete transcripts behind clearly named disclosures. Never hide the original explanatory text to simplify the page.
- **Protect reading comfort.** Keep the established reading measure, theme/font/text-size controls, keyboard access, readable phone labels, reduced motion and one moving diagram at a time. Adapt the composition to the device rather than shrinking a desktop diagram into unreadable text.
- **Improve shared components, then inspect real lessons.** Put reusable behaviour in the design system. Review representative structure, time, ownership and failure diagrams on desktop/tablet and use automated phone checks during development. Follow the consolidated manual mobile review timing above. Audit the entire rendered tree after shared changes. Record implemented coverage and remaining gaps; do not claim that all state steppers are full animated scenes.

The reference review and implementation evidence belong in `website/reviews/website-experience-2026-10-27.md`. Future contributors should use this standard for every new or revised lesson.

The illustrated first pass across all existing step-throughs is recorded in the [122-item coverage report](website/reviews/illustrated-coverage-2026-10-27.md). The owner's subsequent clarification on 2026-10-27 sets the refinement order: assess what each topic needs, retain useful motion, and simplify unnecessary playback into a beautiful static diagram or comparison. The earlier quantity-first pass does not require every topic to become a full animated scene. Preserve the explanatory content when simplifying a visual, and update the coverage manifest and relevant checks with any representation change. Correctness, readable layouts, reduced motion and source preservation remain required.

### Approved diagram direction · 28 October 2026

The owner rejected box/highlight-only teaching and approved a problem-first ViewModel draft. Apply the following to every topic, including future trees:

- Explain the concrete problem before the diagram and what the reader should follow.
- Draw directional arrowheads with explicit relationship or action labels. Arrow numbering identifies relationships; numbered step captions identify changes over time. Never infer a transfer from box order or an active state.
- Put members inside their true owner or boundary. Distinguish logical scope from physical object lifetime; retention across recreated owners needs an explicit explanation.
- Keep object identities and visible consequences clear. Show creation, retention, removal, clearing and restoration with words. Colour and highlighting alone never explain a transition.
- Use consistent role colours alongside text, border patterns and stable labels. A diagram must remain understandable without colour.
- Keep a complex diagram at a readable size in a labelled local scroll viewport when a phone composition would lose relationships. Do not flatten connected owners into unrelated cards or shrink its text to fit.
- A static relationship map or comparison is complete when motion adds no teaching value. Keep playback for actual temporal mechanisms, without decorative object bouncing.
- Author each relationship map in `website/content/diagram-models/`, cite official sources and verify actor IDs, memberships and arrow endpoints in the build. Changes in current state remain available as labelled text and a full transcript.

### Shared layout ownership · 29 October 2026

All reading-width, visual-breakout, frame, padding and responsive layout rules belong to the shared website design system. Define dimensions and surfaces in `website/design-system/tokens.json` and implement their behavior once in the shared components. Every existing and future topic consumes those components. Do not add chapter-specific layout CSS or duplicate the same fix across lesson files. Show proposed visual changes for owner approval when requested before publishing them.

Owner approved the shared layout draft on29 October 2026: prose fills the existing760px reading column; wide visuals use padded, rounded frames and symmetric bounded extension. This replaces the earlier font-specific narrower prose measure. Implement once in design-system tokens and ReadingSheet shared components.

### Designed visuals only · 29 October 2026

Owner rule, 29 October 2026. It applies to every current and future topic and tree, and supersedes any earlier guidance that allowed default renderings:

- **No Mermaid on the website.** Do not publish a rendered Mermaid picture, including a default-themed original diagram or a Mermaid-laid-out relationship map. Redraw every original Mermaid diagram as a designed figure built with the shared design system. Keep the chapter's Mermaid source as preserved text in a labelled disclosure, so section 17's "never lost" requirement still holds. Migrate the existing Mermaid-laid-out relationship maps to the shared figure renderer.
- **No ordinary, colourless diagrams.** Every figure uses the shared role colours from `tokens.json`: blue for devices and clients, purple for execution, teal for stored data, rose for queued work, and neutral for external sources and structure. Each figure has:
  - title-and-detail cards;
  - numbered, labelled arrowheads;
  - explicit owner boundaries;
  - a legend for the roles it uses;
  - a numbered caption that states the figure's point.

  The approved diagram direction above still applies: colour is never the only cue, and words and border patterns carry the same meaning.
- **No ordinary animations.** Use motion only where change over time reveals the mechanism. Build it with the shared scene and stepper components, using illustrated actors and visible consequences. Show the picture first; the current caption and the controls follow it, together. A designed static figure remains a complete result when motion adds nothing (section 8). A generic box-highlight stepper is not an acceptable substitute for either.
- **Design system only.** Colours, card shapes, arrow and label styles, legends, captions and stepper layout live in `website/design-system/tokens.json` and the shared components, so one change applies to all website content. Lesson files supply content: models, labels, captions and sources. They never supply styling.
- **Every theme, readable labels.** Check each figure in the light, dark, sepia and high-contrast themes.
  - Text follows the design-system figure type scale: card titles 15px, secondary text and arrow labels 13px. Relationship maps beside a step-through display every label at 15px or more.
  - Labels are never clipped; the build rejects clipped or overlapping labels.
  - On narrow screens, use a labelled local scroll rather than shrinking text.
- **Nothing outside its box.** Owner rule, 29 October 2026. Text, figures, cards, legends and captions stay inside the visible box that contains them: lesson additions, callouts, figure frames, scenes, code cards, Q&A blocks and disclosures. Only content inside a labelled scroll area may extend past its box. Wide visuals carry their own shared frame when they extend beyond the reading column. Fix violations in the shared design system, never per lesson. Before publishing, `website/tools/dev.py frames` checks every page.
