# Android section: handover

Written 2026-10-25, so another model or person can continue the work exactly where it stopped. Read `content-rulebook.md` §16–19 and `website/README.md` first.

## Goal (from the owner)

Turn the whole Android tree (`android.md` plus 101 chapters) into blended website lessons, one guided-reading **phase** at a time. After each phase:

1. Have an independent reviewer (a subagent or Codex) review it. Reviewers report findings only.
2. Fix what the review confirms.
3. Move on to the next phase.

Never push or merge without the owner's approval.

## Where things are

**Repository:** `/Users/swaransinghaulakh/AndroidStudioProjects/android-staff-engineer-playbook-website`, branch `claude/android-phase1`. Nothing is pushed. `main` and origin are at `d9cae81`.

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

**Last verified build:** 65 pages, 8,555 original units, 0 preservation problems. The browser audit passed for every Phase 1–4 page: diagrams load, steppers initialise, no overflow or clipped cards at 320 px.

## Status by phase

| Phase | Chapters | Blends | Review | Review fixes |
|---|---|---|---|---|
| 1 Lifecycle, state, architecture | 9 | done | done | P1/P2 applied; P3 and new findings open (`android-review-todos/review-phase1-todo.md`) |
| 2 Data and DI | 10 | done | done | P2 applied; rest open (`review-phase2-todo.md`) |
| 3 Compose | 13 | done | done | **none applied yet**; 2 P1s (`review-phase3-todo.md`) |
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
   - Serve `website/dist` together with a folder containing `browser_preservation.js` (as `fx/audit.js`) and `website/tools/browser_audit_runner.js` (as `fx/run.js`), on one localhost origin.
   - On any page run:
     - `eval(await (await fetch('/fx/run.js')).text())`
     - `__runAudit(['/android/…/'])`
     - wait about 20 s, then read `__R`.
   - Every page must report ok.
8. **Write** `website/reviews/android-phaseN-findings.md`, then run `venv/bin/python website/tools/update_readme.py` to refresh the README progress table.
9. **Commit.** No AI attribution in messages.
10. **Review.** Start an independent reviewer with a self-contained brief. Previous briefs asked for:
    - findings only;
    - a build only in a `/tmp` copy made with `git archive`;
    - checks for technical accuracy, restated original errors, findings correctness, internal consistency, note placement and concision.

## Before declaring the Android section complete

- Apply the open review items, Phase 3 first because it has the P1s.
- Apply the Phase 4 review items (`review-phase4-todo.md`).
- Uncommitted Phase 3 review edits exist in the working tree (13 blends plus `reviews/pending-android-phase3-teaching.blend`, made after ce58ead, author unconfirmed). Review them before committing.
- Update the counts in `website/README.md` (Verification scope, figures and steppers) and in the root `README.md`.
- Optionally add preservation self-tests for an original's inner H1 and a missing hero H1, as Phase 3 review suggested.
- Report to the owner: what is rendered, every findings file awaiting approval, what was and wasn't verified, and that nothing is pushed.
