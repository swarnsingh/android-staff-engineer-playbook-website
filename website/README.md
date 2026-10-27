# Reader Website: Build Guide and Handover

This folder builds the reader website for the playbook. Read [`../content-rulebook.md`](../content-rulebook.md) first, especially sections 16–20: the original chapters are read-only, every page must contain its original chapter in full, and the website adds a clearly labelled teaching layer on top. This guide explains how the build works and where the work stands, so another model or person can continue it.

## Current state

The current result is recorded in [the completion report](reviews/completion/REPORT.md), with a per-finding [ledger](reviews/completion/backlog.json), pinned Android validation project and browser evidence. It supersedes older handovers and their pending/privacy statements.

- **Website:** one public repository and one [GitHub Pages deployment](https://swarnsingh.github.io/android-staff-engineer-playbook-website/). All models work in this repository; publication follows [DEPLOYMENT.md](DEPLOYMENT.md) and rulebook section 19.
- **Scope:** 22 Kotlin chapters, 101 Android chapters and both learning paths: 125 pages.
- **Corrections:** approved exact replacements render through content/corrections-*.json with visible original-wording/source disclosures. The website Markdown remains a hash-checked source snapshot; corrected source text is merged by the owner through original-source PR #57 and mirrored from its 743-record canonical inventory.
- **Review history:** the original 295-row Kotlin triage and nine Android phase reports remain historical evidence. Current dispositions include verified fixes and justified no-change results; superseded Reject decisions are identified in the completion ledger.
- **Visuals:** 17 full scenes, 119 illustrated state sequences and static decision diagrams. Movement is used for a real temporal mechanism; a decision or comparison does not need an animated packet.
- **Validation:** real Android/Hilt/Room/Compose compilation and focused runtime regressions complement the 125-page browser sweep. The report distinguishes these checks from device, Apple-runtime and benchmark evidence.

### Progress by chapter

| Chapter | Blend file | Status |
| --- | --- | --- |
| `kotlin.md` (learning path) | — | Original only |
| language-core/variables | `variables.blend` | Blended |
| language-core/null-safety | `null-safety.blend` | Blended |
| language-core/functions | `functions.blend` | Blended |
| language-core/extensions | `extensions.blend` | Blended |
| language-core/data-classes | `data-classes.blend` | Blended |
| language-core/value-classes | `value-classes.blend` | Blended |
| language-core/sealed-classes | `sealed-classes.blend` | Blended |
| language-core/delegation | `delegation.blend` | Blended |
| type-system/generics | `generics.blend` | Blended |
| type-system/variance | `variance.blend` | Blended |
| compiler-features/inline-functions | `inline-functions.blend` | Blended |
| compiler-features/reified-types | `reified-types.blend` | Blended |
| coroutines-and-flow/coroutines | `coroutines.blend` + `content/coroutine-*.html` | Blended |
| coroutines-and-flow/channels-and-select | `channels-and-select.blend` | Blended |
| coroutines-and-flow/flow-operators-and-backpressure | `flow-operators-and-backpressure.blend` | Blended |
| coroutines-and-flow/callbackflow-and-bridging-callbacks | `callbackflow-and-bridging-callbacks.blend` | Blended |
| coroutines-and-flow/coroutines-debugging-and-profiling | `coroutines-debugging-and-profiling.blend` | Blended |
| coroutines-and-flow/test-dispatchers-virtual-time | `test-dispatchers-virtual-time.blend` | Blended |
| runtime-and-jvm/memory-model | `memory-model.blend` | Blended |
| runtime-and-jvm/jvm-interop | `jvm-interop.blend` | Blended |
| runtime-and-jvm/bytecode | `bytecode.blend` | Blended |
| version-updates/kotlin-2-4-update | `kotlin-2-4-update.blend` | Blended |
| `android.md` (learning path) | `android/android.blend` | Blended (phase map) |
| architecture/activity | `android/activity.blend` | Blended |
| architecture/fragment | `android/fragment.blend` | Blended |
| architecture/viewmodel | `android/viewmodel.blend` | Blended |
| architecture/savedstatehandle | `android/savedstatehandle.blend` | Blended |
| architecture/process-death-and-state-restoration | `android/process-death-and-state-restoration.blend` | Blended |
| architecture/navigation | `android/navigation.blend` | Blended |
| architecture/mvvm-vs-mvi | `android/mvvm-vs-mvi.blend` | Blended |
| architecture/state-management | `android/state-management.blend` | Blended |
| architecture/modularization-strategies | `android/modularization-strategies.blend` | Blended |
| data-and-di/repository-source-of-truth | `android/repository-source-of-truth.blend` | Blended |
| data-and-di/room | `android/room.blend` | Blended |
| data-and-di/datastore | `android/datastore.blend` | Blended |
| data-and-di/room-vs-datastore | `android/room-vs-datastore.blend` | Blended |
| data-and-di/storage-and-content-sharing | `android/storage-and-content-sharing.blend` | Blended |
| data-and-di/paging | `android/paging.blend` | Blended |
| data-and-di/dependency-injection | `android/dependency-injection.blend` | Blended |
| data-and-di/components | `android/components.blend` | Blended |
| data-and-di/scopes | `android/scopes.blend` | Blended |
| data-and-di/hilt-vs-koin-vs-manual-di | `android/hilt-vs-koin-vs-manual-di.blend` | Blended |
| compose/compose-runtime | `android/compose-runtime.blend` | Blended |
| compose/snapshot-system | `android/snapshot-system.blend` | Blended |
| compose/recomposition-and-state | `android/recomposition-and-state.blend` | Blended |
| compose/stability | `android/stability.blend` | Blended |
| compose/modifiers-and-layout | `android/modifiers-and-layout.blend` | Blended |
| compose/custom-layout-measurement | `android/custom-layout-measurement.blend` | Blended |
| compose/side-effects | `android/side-effects.blend` | Blended |
| compose/compose-navigation | `android/compose-navigation.blend` | Blended |
| compose/adaptive-compose-large-screens | `android/adaptive-compose-large-screens.blend` | Blended |
| compose/form-factors-matrix | `android/form-factors-matrix.blend` | Blended |
| compose/compose-accessibility | `android/compose-accessibility.blend` | Blended |
| compose/view-interop-and-migration | `android/view-interop-and-migration.blend` | Blended |
| compose/compose-performance-tooling | `android/compose-performance-tooling.blend` | Blended |
| architecture/structured-concurrency | `android/structured-concurrency.blend` | Blended |
| architecture/flow | `android/flow.blend` | Blended |
| concurrency/coroutines-under-the-hood | `android/coroutines-under-the-hood.blend` | Blended |
| concurrency/threads-and-looper | `android/threads-and-looper.blend` | Blended |
| concurrency/shared-flow-and-state-flow | `android/shared-flow-and-state-flow.blend` | Blended |
| concurrency/synchronization-and-mutex | `android/synchronization-and-mutex.blend` | Blended |
| concurrency/services | `android/services.blend` | Blended |
| concurrency/workmanager | `android/workmanager.blend` | Blended |
| concurrency/battery-optimizations | `android/battery-optimizations.blend` | Blended |
| networking-and-security/retrofit-and-okhttp | `android/retrofit-and-okhttp.blend` | Blended |
| networking-and-security/ktor-vs-retrofit | `android/ktor-vs-retrofit.blend` | Blended |
| networking-and-security/graphql | `android/graphql.blend` | Blended |
| networking-and-security/networkcallback-metered-vpn-captive-portal | `android/networkcallback-metered-vpn-captive-portal.blend` | Blended |
| networking-and-security/security-and-keystore | `android/security-and-keystore.blend` | Blended |
| networking-and-security/device-connectivity-and-location | `android/device-connectivity-and-location.blend` | Blended |
| data-and-di/health-connect | `android/health-connect.blend` | Blended |
| networking-and-security/webview-and-hybrid | `android/webview-and-hybrid.blend` | Blended |
| media/media3-player-architecture | `android/media3-player-architecture.blend` | Blended |
| media/camerax-capture-architecture | `android/camerax-capture-architecture.blend` | Blended |
| testing/testing-strategy | `android/testing-strategy.blend` | Blended |
| testing/unit-testing | `android/unit-testing.blend` | Blended |
| testing/ui-testing | `android/ui-testing.blend` | Blended |
| performance/startup | `android/startup.blend` | Blended |
| performance/jank | `android/jank.blend` | Blended |
| performance/rendering | `android/rendering.blend` | Blended |
| performance/anrs | `android/anrs.blend` | Blended |
| performance/memory-management-and-leaks | `android/memory-management-and-leaks.blend` | Blended |
| performance/native-memory-bitmaps | `android/native-memory-bitmaps.blend` | Blended |
| performance/app-size-and-r8 | `android/app-size-and-r8.blend` | Blended |
| performance/baseline-profiles | `android/baseline-profiles.blend` | Blended |
| performance/macrobenchmark-and-perfetto | `android/macrobenchmark-and-perfetto.blend` | Blended |
| performance/battery-power-profiling | `android/battery-power-profiling.blend` | Blended |
| performance/network-radio-wakeups | `android/network-radio-wakeups.blend` | Blended |
| performance/thermal-low-end-device-strategy | `android/thermal-low-end-device-strategy.blend` | Blended |
| observability/logging | `android/logging.blend` | Blended |
| observability/crash-monitoring | `android/crash-monitoring.blend` | Blended |
| observability/mobile-apm-and-rum | `android/mobile-apm-and-rum.blend` | Blended |
| build-tooling/gradle-and-build-systems | `android/gradle-and-build-systems.blend` | Blended |
| build-tooling/multi-module | `android/multi-module.blend` | Blended |
| build-tooling/convention-plugins | `android/convention-plugins.blend` | Blended |
| build-tooling/ksp | `android/ksp.blend` | Blended |
| os-internals/intent-resolution-and-manifest | `android/intent-resolution-and-manifest.blend` | Blended |
| os-internals/broadcast-receivers | `android/broadcast-receivers.blend` | Blended |
| os-internals/content-providers-and-contentresolver | `android/content-providers-and-contentresolver.blend` | Blended |
| os-internals/permissions-and-app-ops | `android/permissions-and-app-ops.blend` | Blended |
| os-internals/activitymanager-process-lifecycle | `android/activitymanager-process-lifecycle.blend` | Blended |
| os-internals/package-manager-installation-classloading | `android/package-manager-installation-classloading.blend` | Blended |
| os-internals/the-binder | `android/the-binder.blend` | Blended |
| os-internals/the-zygote | `android/the-zygote.blend` | Blended |
| os-internals/art-and-dalvik | `android/art-and-dalvik.blend` | Blended |
| kotlin-multiplatform/kmp-decision-matrix | `android/kmp-decision-matrix.blend` | Blended |
| kotlin-multiplatform/foundations/overview-and-k1-vs-k2 | `android/overview-and-k1-vs-k2.blend` | Blended |
| kotlin-multiplatform/shared-domain-boundaries | `android/shared-domain-boundaries.blend` | Blended |
| kotlin-multiplatform/foundations/architecture-and-module-boundaries | `android/architecture-and-module-boundaries.blend` | Blended |
| kotlin-multiplatform/tooling/build-system-and-source-sets | `android/build-system-and-source-sets.blend` | Blended |
| kotlin-multiplatform/ecosystem/libraries-ecosystem | `android/libraries-ecosystem.blend` | Blended |
| kotlin-multiplatform/ecosystem/networking-with-ktor | `android/networking-with-ktor.blend` | Blended |
| kotlin-multiplatform/ecosystem/persistence | `android/persistence.blend` | Blended |
| kotlin-multiplatform/ecosystem/dependency-injection | `android/dependency-injection.blend` | Blended |
| kotlin-multiplatform/ui-sharing/compose-multiplatform | `android/compose-multiplatform.blend` | Blended |
| kotlin-multiplatform/ui-sharing/resource-sharing | `android/resource-sharing.blend` | Blended |
| kotlin-multiplatform/production/concurrency-and-memory | `android/concurrency-and-memory.blend` | Blended |
| kotlin-multiplatform/tooling/swift-interop | `android/swift-interop.blend` | Blended |
| kotlin-multiplatform/tooling/ios-distribution | `android/ios-distribution.blend` | Blended |
| kotlin-multiplatform/binary-compatibility-api-evolution | `android/binary-compatibility-api-evolution.blend` | Blended |
| kotlin-multiplatform/production/testing-and-mocking | `android/testing-and-mocking.blend` | Blended |
| kotlin-multiplatform/kmp-observability-crash-symbolication | `android/kmp-observability-crash-symbolication.blend` | Blended |
| kotlin-multiplatform/production/ci-cd-for-kmp | `android/ci-cd-for-kmp.blend` | Blended |
| kotlin-multiplatform/production/adoption-and-migration | `android/adoption-and-migration.blend` | Blended |

Update this table whenever a chapter changes state.

## Build and preview

```bash
python3 -m venv .venv && .venv/bin/pip install -r website/requirements.txt
.venv/bin/python website/scripts/build.py
python3 -m http.server 4177 --bind 127.0.0.1 --directory website/dist
```

Run from the new website repository root. Port 4177 is an example: choose an available port and verify the server serves this checkout’s `website/dist`, rather than reusing a server from the original repository. The build writes `website/dist/` (ignored by git), renders each Mermaid diagram with `npx @mermaid-js/mermaid-cli` (cached in `website/.cache/`; pass `--skip-diagrams` to skip), and then runs the preservation check. It exits non-zero if any original content is missing. Set `SITE_BASE=/android-staff-engineer-playbook-website/` to build for a project path such as GitHub Pages.

## How a page is assembled

`scripts/build.py` parses each original chapter with markdown-it and renders it into `templates/reader.html`. Sections are grouped into six parts (`PARTS` in the script) by their headings; parts only move forward. Then it adds, in order: the chapter's blend fragments, the Codex coroutine fragments for the coroutines page (each wrapped in a labelled `.blend` container), and approved corrections. Approved corrections read as normal current text. Their reasons, current/original wording and official sources are retained in optional technical correction history under About this lesson.

`scripts/check_preservation.py` reads the original areas of each page (`.original-opening` and `section#section-…`), skipping labelled additions. It checks original units, order, repetitions, heading levels and the title, and rejects concealed HTML containers including `template`, `noscript`, `script` and `style`. Only actual Mermaid source may use a diagram disclosure. It runs 22 tampering fixtures before checking 15,564 original units across 125 pages. It also writes `dist/coverage/original-units.json` from the approved rendering input. The static gate does not evaluate a browser CSS cascade.

Invoke the read-only `scripts/browser_preservation.js` async function in a rendered Content page with two arguments: parsed `dist/coverage/diagram-sources.json` and parsed `dist/coverage/original-units.json`. The second argument may instead be that page's unit array for a disposable fixture. Both are required for a meaningful preservation result. The audit compares rendered original-area text with the unit manifest in order, excluding labelled additions and folded prose. A default/empty unit manifest is reported as unverified, not success. Whitespace is ignored; this is not a typography or exact-layout comparison.

The browser audit detects the tested hidden styles, transparent text, effective opacity at or below 0.01, zero-opacity filters, selected clipping/offscreen patterns, folded prose and missing rendered units. It is **not** a proof of readability or accessibility: arbitrary overlays/occlusion, every CSS clipping/transform combination, low contrast and screen-reader behaviour require separate review. In particular, a labelled overlay can cover original text without this audit detecting it.

Diagram counts and successful image loads are separate fields. Original SVGs load eagerly; the audit calls `decode()` where available, waiting at most five seconds because Chrome can leave `decode()` pending for an off-screen lazy image, and otherwise requires `complete` plus a non-zero natural width. Pending lazy images are reported as unverified rather than passed. This validates resource decoding/readiness, not whether an SVG's artwork faithfully represents its source or is readable in every theme.

`scripts/check_review_data.py` runs before each build. It checks all 295 triage rows against chapter/overall counts, canonical verdict labels, 23 amended IDs / 24 replacements, proposal Markdown/JSON wording, exact source matches, non-overlap and all 125 read-only source hashes (23 Kotlin, 102 Android).

## Writing a blend file

Create `content/blend/<chapter-file-stem>.blend` for Kotlin (for example `variables.blend`), or `content/blend/<tree>/<chapter-file-stem>.blend` for other trees (for example `android/activity.blend`). It is Markdown with raw HTML allowed, split by markers:

- `<!-- @opening -->` — a problem-first story that replaces the generic intro.
- `<!-- @before Heading :: kind -->` / `<!-- @after Heading :: kind -->` — a fragment placed before, or at the end of, the section with that visible H2 text.
- `<!-- @diagram <hash> -->` — a designed redraw shown instead of a Mermaid diagram; the original stays one tap away. Hashes are the first 16 hex characters of the SHA-256 of the diagram source.
- `<!-- @part Heading :: KEY -->` — override the part a section belongs to.

Kinds: `story`, `guide`, `visual`, `animation`, `check`, `deeper`, `staff`, `try`, `review`, `bridge`. Use `review` (labelled "Under review") only to flag an original passage whose correction awaits approval, placed before the section that contains it. The build fails if a marker targets a heading or diagram that does not exist. Keep raw HTML blocks free of blank lines, or Markdown will end the block early. Use `variables.blend` as the reference example.

### Visual components (`blend.css`)

`viz-flow` (steps with arrows), `viz-cols` (comparison columns), `viz-grid`, `viz-stack`, `viz-tree`, `viz-lanes` (timelines with `.mark` positioned by `--at` and `--len`), and `viz-pair` (source beside generated output). Cards are `.node`, with `data-state` set to `active`, `done`, `error`, `warn` or `ghost`. All of them reflow on narrow screens.

### Animations (`blend.js`)

A `<figure class="stepper">` contains a `.stage` with elements marked `data-el="id"` (shown, hidden or given a state per step) and `data-text="id"` (text replaced per step), followed by `<script type="application/json" class="steps">`. Each step has `label`, `caption`, and optional `add`, `remove`, `state` and `text`. Frames are always folded from step one. The build prints every step as a numbered list, so no meaning depends on motion or JavaScript.

## Current authoring and verification rules

Original chapter Markdown remains the recorded source snapshot. Approved exact corrections render once, through the canonical inventory, and teaching additions are labelled. Source PR #57 is merged; the website's corrected text aligns with that revision. The [completion report](reviews/completion/REPORT.md) and [UX review](reviews/ux-2026-10-28/REPORT.md) describe their separate content and presentation checks.

Learning paths use phase selection and a start action, without lesson tabs or bookmarks. Individual lessons expose populated Q&A and Resources; Playground appears for the runnable coroutine example. Curriculum navigation starts in the current track, with an explicit All topics option. Focus mode retains access to the topic drawer at every width. Keep original questions and answers available in the static chapter. In the interactive practice view, pair each question with its own answer directly below it; retain checklist-only sections as checklists. This convention applies to every topic tree, including future subjects.

Diagram controls use consistent Previous, Next and Reset labels. Temporal playback retains Play/Pause, reduced motion and shared motion ownership. The current explanation remains beside the controls; optional help and the full transcript share one disclosure. Fenced code has a continuous code surface, including inside nested lists; inline-code chip styling must not leak into examples.

The static gate checks all 125 pages and 15,564 original units. Browser verification checks actual views, rendered preservation, enlarged text, illustrations, scenes and code presentation. Dedicated motion, Binder, gallery and UX suites complement that sweep. Browser emulation does not certify physical devices, other engines or screen-reader behaviour. Run the documented audits after changing shared reader code and record the tested scope before publication.

Earlier phase counts, held corrections and pending conversion lists belong to the historical phase reports. They do not describe current work: all nine Android phases and all Kotlin chapters are rendered, and the retained correction backlog has documented dispositions.

## Regression checks for the final review fixes

Run the build, documentation checker and `python3 website/scripts/check_kotlin_examples.py`. The Kotlin runner uses installed Kotlin 2.4.21 and coroutines/core-test 1.11.0 artifacts. Its reflect runtime matches the compiler 2.4.21 POM (`1.6.10`), rather than an unrelated installed version. It requires JDK 17 and prints the actual Java version; set `KOTLIN_JAVA_HOME` to an installed JDK 17 if needed. `KOTLIN_COMPILER_CP` and `KOTLIN_TEST_CP` can override cache discovery. It neither runs Gradle nor downloads dependencies. Missing prerequisites fail explicitly.

The runner compiles the exact CH4 JSON proposal with the chapter's command types. Twelve cases cover expected I/O failure/recovery; cancellation before startup; an already-cancelled owner; queued work before prevented startup; one active plus 256 additional submissions at shutdown; unexpected-error reporting; service-local timeout and cancellation followed by recovery; an active UI caller displaying actor shutdown; caller-owned cancellation; a checkout that commits during shutdown keeping its result; and boxed value identity. A separate negative compilation confirms `Meters === Meters` is prohibited.

The channel is cancelled by the worker's completion handler even if startup never occurred. Active callers receive ordinary `CartStoppedException` on shutdown. Their own cancellation remains `CancellationException`. A cancellation from the service while the worker stays active becomes `CheckoutRequestCancelledException` for that request; it does not kill the actor. A checkout that finishes while shutdown begins still returns its result rather than `CartStoppedException`. If cancellation or failure happens before the receipt is delivered, the outcome is unknown; use idempotency or reconcile server state before retrying. Unexpected failures still stop the worker and retain the owner's reporting policy. Accepted commands belong to the actor's owner; cancellation of the waiting caller does not promise rollback. The sample is in-memory and makes no durability guarantee.

CH4 is included in the approved canonical correction inventory. Tests use a temporary directory and never approve new corrections or edit original chapters. The sample needs the coroutine/channel imports and `java.io.IOException`, as stated beside the proposal.

For browser regressions, create disposable fixtures with `python3 website/scripts/make_browser_fixtures.py /absolute/scratch/path`, serve that directory on a free port and invoke the audit using each `cases.json` entry's diagrams and units. There are 19 cases: a visible control, 17 required detections, and an overlay case recorded as an explicit limitation. Compare each result to its `expected` field. The audit itself never changes DOM, preferences, scrolling or disclosures.

## Browser audit preparation

After building, run `python3 website/tools/prepare_browser_audit.py website/.cache/browser-qa`, then serve that disposable directory on an available localhost port and open `/audit.html`. Press **Start audit** and read its JSON result. The prepared copy loads the read-only audit as a script, without console `eval`; the QA runner uses isolated iframes to check preservation first, then animation readiness and enlarged-text geometry. It does not edit source or the deployable `website/dist` output. Never deploy the instrumented QA directory. The existing API still accepts a subset of routes when a focused sweep is appropriate.
