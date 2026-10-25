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

**Last verified build:** 65 pages, 8,555 original units, 0 preservation problems. The integrated browser audit now passes all 65 pages: 41 original diagram images load, 74 steppers initialise, and 260 geometry checks pass at 320/390/768/1280px with 22px handwritten text. See `android-completion-validation.json`.

## Status by phase

| Phase | Chapters | Blends | Review | Review fixes |
|---|---|---|---|---|
| 1 Lifecycle, state, architecture | 9 | done | original review done; follow-up attempt hit usage limit | Listed teaching fixes, note coverage and new findings applied locally; see disposition |
| 2 Data and DI | 10 | done | independent follow-up done | Listed fixes applied, including the two follow-up P3 wording fixes |
| 3 Compose | 13 | done | independent follow-up done | P1/P2/P3 teaching fixes applied; follow-up ST1 note and Topics-order findings addressed |
| 4 Concurrency | 9 | done | done | **none applied yet**; 2 P1s (`review-phase4-todo.md`) |
| 5 Network, security, device APIs, media | 10 | todo | — | — |
| 6 Testing | 3 | todo | — | — |
| 7 Performance and observability | 15 | todo | — | — |
| 8 Build tooling and OS internals | 13 | todo | — | — |
| 9 KMP (optional specialisation) | 19 | todo | — | — |

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
- Apply the Phase 4 review items (`review-phase4-todo.md`).
- Uncommitted Phase 3 review edits exist in the working tree (13 blends plus `reviews/pending-android-phase3-teaching.blend`, made after ce58ead, author unconfirmed). Review them before committing.
- [x] Update the README counts for the current 65-page checkpoint; refresh them again as future phases are added.
- [x] Add original inner-H1 and missing/duplicated/hidden hero-H1 self-tests.
- [ ] Convert and independently review Phases 5–9 (60 remaining chapters).
- Report rendered scope, pending original findings, verification limits and publication state; the full Android section is not complete yet.

## Codex takeover checkpoint

The existing Phase 1–4 review lists have dispositions in `android-review-todos/`. Technical corrections in the original sources remain unapproved. Conflicting teaching fragments are retained outside active content in the phase-specific pending files. The generic footer now links to the current tree and no longer implies corrections are already applied. Both reading order and emitted Topics catalog use canonical unanchored phase lists, with contiguity checks. Hero-title and original inner-H1 regressions are covered. Long timeline labels remain readable through full-text numbered legends.

Verified checkpoint: 65 pages, 8,555 original units, 22 static adversarial fixtures, 41 loaded diagram images, 74 steppers, and 260 layout checks at four widths with 22px handwritten text. Build, documentation and source-hash checks pass; `android-completion-validation.json` contains actual browser results. Physical devices and other browser engines were not tested.

**Current blocker:** independent review agents reached the account usage limit. Do not mark phases 5–9 complete or bypass their review gate. Resume with Phase 5’s ten chapters after review capacity is available, follow the recipe, and update this status after each phase. No automatic future run has been scheduled. This checkpoint remains local and must not be pushed/merged/published without the owner's approval.
