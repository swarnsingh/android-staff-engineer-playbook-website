# Android section: handover

Written 2026-10-25, so another model or person can continue the work exactly where it stopped. Read `content-rulebook.md` §16–19 and `website/README.md` first.

## Goal (from the owner)

Turn the whole Android tree (`android.md` plus 101 chapters) into blended website lessons, one guided-reading **phase** at a time. After each phase:

1. Have an independent reviewer (a subagent or Codex) review it. Reviewers report findings only.
2. Fix what the review confirms.
3. Move on to the next phase.

Never push or merge without the owner's approval.

## Where things are

**Repository:** `/Users/swaransinghaulakh/AndroidStudioProjects/android-staff-engineer-playbook-website`. Current checkpoint branch: `codex/android-completion`, based on `claude/android-phase1` at `ce58ead`. The Claude branch is preserved. Nothing from the Android work is pushed or published; `main`, origin/main and the hosted Kotlin preview remain at `d9cae81`.

**Commits on the branch:**

| Commit | Content |
|---|---|
| `3f3e7a2` | Multi-tree build, phase sub-sections in the Topics menu, Android Phase 1 (9 chapters) |
| `ca7f75c` | Phase 2: data ownership and DI (10) |
| `9c97245` | Phase 3: Compose runtime and UI (13); preservation checker accepts an original's own H1s |
| `09ecd7b`, `f5f1093` | Phase 4: concurrency and background work (9) |
| `a828c58` | `phases()` ignores anchored links (this had moved Kotlin 2.4 into the middle of the Kotlin path) |
| `4a70592` | Phase 1 review fixes; Under review notes no longer state replacements |
| `3e8aba3` | Phase 2 review P2 fixes (Paging triggers, DataStore read, Koin and Dagger errors) |
| `c3e190d` | Codex checkpoint: Q&A tab, wider reader, Phase 5–9 structure plans and draft lessons |
| `32fd7fc` | Render Phases 5, 6, 7 and 9 with problem-first intros |
| `f2317a0` | Phase 8 lessons; checkpoint answers no longer carry their own "Answer" label |
| `437019c`, `963635a`, `d1c432a` | Review fixes for Phases 5–6, 7 and 9 |
| (next commit) | Phase 8 review fixes; checkpoint code wraps in the Q&A tab |

**Last verified build:** 125 pages (Kotlin and Android), 15,572 original units, 0 preservation problems. Browser audit on 2026-10-26 (after the Phase 8 fixes): all 125 pages ok, 138/138 steppers initialised, 93/93 diagram images loaded, 1,000 layout checks at 320/390/768/1280px with no overflow.

## Status by phase

| Phase | Chapters | Blends | Review | Review fixes |
|---|---|---|---|---|
| 1 Lifecycle, state, architecture | 9 | done | done (follow-up attempt hit usage limit) | applied |
| 2 Data and DI | 10 | done | done | applied |
| 3 Compose | 13 | done | done | applied |
| 4 Concurrency | 9 | done | done | applied (`android-review-todos/review-phase4-todo.md`) |
| 5 Network, security, device APIs, media | 10 | done | done | applied |
| 6 Testing | 3 | done | done | applied |
| 7 Performance and observability | 15 | done | done | applied |
| 8 Build tooling and OS internals | 13 | done | done (2 P1, 10 P2, 11 P3) | applied; see the findings file's "Independent review" section |
| 9 KMP (optional specialisation) | 19 | done | done | applied |

## Findings in the original chapters

There is one file per phase: `website/reviews/android-phaseN-findings.md`. Nothing is approved or applied. Each finding is flagged on its page with an **Under review** note.

The rule, following the Kotlin K1 precedent: the note **identifies the passage** and says "is under technical review. A correction is pending the owner's approval." It must **not** state the replacement, and the teaching layer must not present the disputed correction as fact. Teaching that depends on an unapproved correction is held in `reviews/pending-android-teaching.blend`. Put a note before **each** affected section, including the Answer Key, Failure Modes and Common Pitfalls when they repeat the claim.

## How to do one phase

1. **Outline.**
   - Command: `venv/bin/python website/tools/outline.py N`
   - It prints each chapter's H2 headings and Mermaid diagram hashes.
   - The venv is `/Users/swaransinghaulakh/AndroidStudioProjects/android-staff-engineer-playbook/venv`; pip has no network here.
2. **Read** each original chapter in full.
3. **Write** `website/content/blend/android/<chapter-stem>.blend`. The format is in `website/README.md`, and existing Android blends are examples. Per chapter:
   - A problem-first `@opening` story, plus one paragraph saying what the chapter does.
   - `@diagram <hash>` redraws of the original Mermaid diagrams. Keep the content faithful; don't silently fix the original.
   - One step-through animation (`<figure class="stepper">`) where behaviour unfolds over time.
   - One or two designed visuals (`viz-flow`, `viz-grid`, `viz-cols`, `viz-lanes`, `viz-stack`).
   - A three-question checkpoint (`check`).
   - `@before <H2> :: review` notes for original errors.

   Constraints:
   - Markers target **H2 headings only**, matched on cleaned text (no backticks).
   - Keep added prose under about 25% of the chapter's words.
   - Raw HTML blocks must have no blank lines.
4. **Verify** every added claim against developer.android.com, kotlinlang.org, the androidx or Dagger source, or release notes.
   - Compile only small pure-Kotlin language examples, with the classpath from `website/scripts/check_kotlin_examples.py`.
   - Don't try to compile Android framework code.
5. **Register** the chapters in `website/scripts/build.py`:
   - Add one-sentence, problem-first intros to `INTRO`, keyed by chapter path.
   - Add the phase number to `TREES['android']['phases']`.
6. **Build** with `venv/bin/python website/scripts/build.py`. It must show 0 preservation problems.
7. **Audit in a browser.**
   - Build first, then run `python3 website/tools/prepare_browser_audit.py website/.cache/browser-qa`.
   - Serve that disposable directory on an available localhost port, open `/audit.html`, and press **Start audit**.
   - The page displays a JSON report. Require `done: true`, no overall error and `ok: true` on every page.
   - The harness checks original rendered units/images first, then initialised steppers and added-card geometry at 320/390/768/1280px with enlarged handwritten text.
   - This copy is instrumented for QA only; never deploy it. No console eval is needed.
8. **Write** `website/reviews/android-phaseN-findings.md`, then run `venv/bin/python website/tools/update_readme.py` to refresh the README progress table.
9. **Commit.** No AI attribution in messages.
10. **Review.** Start an independent reviewer with a self-contained brief. Previous briefs asked for:
    - findings only;
    - a build only in a `/tmp` copy made with `git archive`;
    - checks for technical accuracy, restated original errors, findings correctness, internal consistency, note placement and concision.

## Before declaring the Android section complete

- [x] Apply the existing Phase 1–4 teaching/review fixes, including Phase 3 P1s. Further follow-up review attempts hit the account usage limit; do not claim those interrupted passes completed.
- [x] Apply the Phase 4 review items (`android-review-todos/review-phase4-todo.md`).
- Uncommitted Phase 3 review edits exist in the working tree (13 blends plus `reviews/pending-android-phase3-teaching.blend`, made after ce58ead, author unconfirmed). Review them before committing.
- [x] Update the README counts for the current 65-page checkpoint; refresh them again as future phases are added.
- [x] Add original inner-H1 and missing/duplicated/hidden hero-H1 self-tests.
- [x] Convert and independently review Phases 5–9 (60 chapters).
- Report rendered scope, pending original findings, verification limits and publication state; the full Android section is not complete yet.

## Codex takeover checkpoint

The existing Phase 1–4 review lists have dispositions in `android-review-todos/`. Technical corrections in the original sources remain unapproved. Conflicting teaching fragments are retained outside active content in the phase-specific pending files. The generic footer now links to the current tree and no longer implies corrections are already applied. Both reading order and emitted Topics catalog use canonical unanchored phase lists, with contiguity checks. Hero-title and original inner-H1 regressions are covered. Long timeline labels remain readable through full-text numbered legends.

Verified checkpoint: 65 pages, 8,555 original units, 22 static adversarial fixtures, 41 loaded diagram images, 74 steppers, and 260 layout checks at four widths with 22px handwritten text. Build, documentation and source-hash checks pass; `android-completion-validation.json` contains actual browser results. Physical devices and other browser engines were not tested.

## Current state (2026-10-26)

All 101 Android chapters across the 9 phases render as blended lessons, and each phase has had an independent review with its fixes applied. Original-chapter corrections remain **unapproved**; every one is flagged on its page with an Under review note and listed in `android-phaseN-findings.md`.

**Follow-ups, not blocking:**
- Seven Phase 9 KMP blends still share a templated shape and need lesson-specific visuals.
- The Phase 7 staff notes are generic, and some Phase 7 findings cite weaker evidence than other phases.
- Candidate findings without notes: Phase 8 KS4 and KS5, Phase 9 KO2 and KC8.
- Physical devices and other browser engines were not tested.

Nothing is pushed or merged. A private preview was published for the owner as a claude.ai artifact with relative links (`website/tools/make_artifact_preview.py dist <out>`); it is not a deployment.

## Design system (applied 2026-10-26)

The owner approved the Playbook Design System after three Codex review rounds; see `reviews/design-system-review-disposition.md`. It lives in `website/design-system/`, which is the single source:
- **Tokens:** `build.py` compiles `tokens.json` into `dist/tokens.css`. The old variable names (`--bg`, `--text`, `--accent`…) are aliases of the design-system roles in all four themes.
- **Diagram runtime and fonts:** `components/bundle.js` and `bundle.css` ship as `dist/flow.js` and `dist/flow.css`, and `fonts/*.woff2` are copied to `dist/fonts/`.
- **Site layer:** `website/theme.css` applies the reading sheet (880px sheet, 760px text column, canvas), the callout tints, JetBrains Mono, the rail breakpoints (curriculum rail from 1440px, outline from 1181px; `app.js` opens the curriculum drawer below 1440px) and high contrast.
- **Static Mermaid figures:** `blend.js` sizes each figure to at least 0.75 of its drawn width, so its text stays at 12px or more, and the figure scrolls sideways when narrower. Diagram figures may use the sheet's full inner width.
- **Moving diagrams:** a lesson adds `<section class="pb-figure" data-pb-flow="scene|diagram">` with its JSON (see the FlowScene and FlowDiagram READMEs). `blend.js` mounts them.

**Rolled out so far:** the Binder lesson's stepper is replaced by the FlowScene pilot (synchronous and `oneway` tracks). The ANR consequence moved into the waiting step and the contract fix stayed in the last step. Other lessons still use their steppers; converting the 15–20 lessons where movement is the lesson is a follow-up.
