> Superseded status: the owner subsequently authorized full corrections, public GitHub Pages publishing and source PR updates. See [the completion report](completion/REPORT.md) for the current result; the original handover below is historical.

# Handover to Codex: Android reader and Playbook Design System

> Continuation, 2026-10-26: publication instructions below are historical. The owner now requires all website work and publication configuration in the single website repository, with both source and preview private. See rulebook section 19, [the deployment guide](../DEPLOYMENT.md) and [round-4 review](design-system-review-round4.md) for the current fixes, validation and publication status. Do not update the Claude artifacts or create a separate hosting repository.

Written 2026-10-26 by Claude, on the owner's request, so Codex can continue from exactly here.

- **Repo:** `/Users/swaransinghaulakh/AndroidStudioProjects/android-staff-engineer-playbook-website`
- **Branch:** `codex/android-completion`, 27 local commits on top of `main` (`d9cae81`). The latest is `7c3b0cc`.
- **Nothing is pushed, merged or deployed.** Pushing and merging need the owner's explicit approval.

## Standing rules (from the owner)

- **Original chapters are read-only.** The original chapter Markdown is never edited. The site is the original plus a website-only teaching layer.
- **Corrections need approval.** Errors found in the originals are flagged on the page with an "Under review" note. The note names the passage and says "is under technical review. A correction is pending the owner's approval." It never states the replacement. Corrections are applied only after the owner approves them.
- **Verify, don't trust memory.** Android claims are checked against developer.android.com, AOSP or androidx source. Only small pure-Kotlin examples are compiled.
- **Q&A placement.** Q&A content (probing questions, answer keys, checkpoints) lives only in the Q&A tab, each answer under an "Answer" heading on its own line.
- **No AI attribution** in commits or PRs.
- **Previews stay private.** They are claude.ai artifacts owned by the owner.
- **Token budget is tight.** Keep work lean: run one browser audit per batch, not after every change.

## 1. Android teaching layer: done

| What | Status | Why it was done this way |
|---|---|---|
| All 101 Android chapters in 9 phases as blended lessons | Done | Each lesson adds an opening story, redrawn diagrams, step-throughs, visuals, staff notes and checkpoints, while preserving every unit of the original. The build's preservation check reports 0 problems. |
| Independent review per phase | Done (Phases 1–9) | Each phase was reviewed by a separate agent; the fixes are applied. Phase 8 was reviewed last (`7206913`). |
| Findings in the originals | Listed, **not applied** | One file per phase: `reviews/android-phaseN-findings.md`. Each finding has an Under review note on its page. They await the owner's approval. |
| Handover and recipe | `reviews/ANDROID-HANDOVER.md` | The per-phase status, the recipe and the design-system section. |

**Open follow-ups:**
- Seven Phase 9 KMP blends still follow a shared template.
- The Phase 7 staff notes are generic.
- Candidate findings KS4 and KS5 (Phase 8) and KO2 and KC8 (Phase 9) have no on-page notes yet.

## 2. Playbook Design System: done and applied

- **Source of truth:** `website/design-system/`. It holds the tokens, README, motion rules, components with previews and guidelines, the runtime `components/bundle.js` and `bundle.css`, and self-hosted fonts.
- **Published copy:** a private artifact, https://claude.ai/artifact/FgfrtGzSi6cnxtj31nPJkP
- **Reviews:** four Codex rounds. Their dispositions with evidence are in `reviews/design-system-review-disposition.md`. The round-4 brief is in `reviews/design-system-review-brief-round4.md`.

| Decision | Why |
|---|---|
| **Tokens with Compose-style roles** (`canvas`, `sheet`, `accent`, `event`, `warn`…) in light, dark, sepia and high contrast | The owner wanted a theme defined like a Compose design system. All four themes are designed, and text contrast is at least 4.5:1 and outlines at least 3:1. |
| **Reading sheet:** 880px sheet, 760px text column, tinted canvas; rails from 1440px (curriculum) and 1181px (outline) | The owner liked AlgoInsight's centred column. The old layout ran full width. The breakpoints come from the space the sheet needs. |
| **Fonts:** Inter for body, Source Serif 4 for titles, JetBrains Mono with ligatures off, Patrick Hand for diagrams, Shantell Sans for the reader's handwritten setting; all self-hosted | Readable long-form text, with the personality in the diagrams. Shantell Sans is about 25% wider, so diagrams stay in Patrick Hand to fit their boxes. There is no font CDN. |
| **Dark theme:** navy canvas `#0a0f1e`, slate sheet, two faint glows | The owner's request (AlgoInsight style). Text is at least 7.29:1 and outlines at least 3.22:1 on every dark surface. |
| **Callouts are tints with a capital label**, with no side bar | Avoids boxes inside boxes. High contrast swaps tints for borders. |
| **Colour meaning: green forward, blue back, orange stuck**, plus line pattern and packet shape | Green and blue are about 1.08:1 apart in lightness, so hue is never the only cue. |
| **Motion only where direction, rate or order is the lesson.** One moving diagram at a time; it pauses off screen; a Pause button; the OS or reader reduced-motion setting is read live | WCAG 2.2.2, and Codex review findings. |
| **Moving diagrams on phones get a stacked layout,** chosen from the minimum rendered text size (handwritten ≥15px, other ≥12px) | Cause and effect must stay on screen together. Codex round 2 caught text that became too small. |
| **Static diagrams scroll sideways at a readable size** | The owner's decision. Nothing moves, so scrolling loses nothing. Mermaid figures render at no less than 0.75 of their drawn width. |
| **Code cards show an overflow cue,** and wrapping is a reader setting | Codex finding: long lines were cut off silently. |

**How it reaches the site:**
- **Tokens:** `build.py` compiles `tokens.json` into `dist/tokens.css`. The old variable names (`--bg`, `--text`…) are aliases.
- **Site layer:** `theme.css` applies the sheet, callouts, code font, breakpoints and high contrast.
- **Runtime:** `flow.css` and `flow.js` are copied from the design system.
- **Glue:** `blend.js` sizes Mermaid figures, adds the code overflow cue, and mounts the diagrams.

## 3. Animations

| Scope | Status | Why |
|---|---|---|
| **Binder lesson** | **FlowScene pilot:** one stepped system with Synchronous and `oneway` tracks, where packets land and change state | Inspired by SeeItFlow: one system that evolves, with consequences when a packet arrives. Captions are marked "illustrative run" and checked against the AOSP AIDL docs. |
| **All 137 step-throughs on the 125 pages** | **Handoff packets:** Next sends a packet from the previously active box to the newly active box (orange for warn or error); Back and Reset jump without motion; Pause, reduced motion and leaving the screen cancel the packet | Gives every topic motion without inventing flows. It reuses each step-through's own state data. |
| **Full FlowScenes for the remaining 15–20 movement lessons** | **Pending** | Each needs its own drawing and doc-checked captions. A template would risk teaching flows that don't exist. Do them in batches of 4–5, with one audit and a Codex review per batch. |

**Candidate lessons for full FlowScenes:** Threads & Looper, Flow / StateFlow / SharedFlow, coroutines under the hood, OkHttp/Retrofit interceptors, WorkManager, Paging, Room invalidation, Zygote fork, Intent resolution, Broadcast receivers, ActivityManager process lifecycle, Gradle build phases, KSP pipeline, Compose recomposition, Media3 player.

**Known risk for Codex to check:** the handoff rule (previously active → newly active) may suggest a flow in some step-throughs where the active box changes for an unrelated reason. Find those, so they can opt out with a `data-no-handoff` flag, which is still to be added.

## 4. Verification state

- **Build:** 125 pages, 15,572 original units, 0 preservation problems.
- **Browser audit:**
  - The last completed run (before `7c3b0cc`) passed 124 of 125 pages: 137/137 steppers, 93/93 diagrams, 1,000 layout checks.
  - The one failure was the Kotlin Coroutines page at 320px with the handwritten font at 22px: Shantell Sans was wider, and the part header pushed the page 7px sideways.
  - That is fixed in `7c3b0cc`: diagrams always use Patrick Hand, and part headers wrap. The page was confirmed fixed.
  - **A final full run was started on `7c3b0cc` and had not reported when this was written.** Re-run it to confirm.
- **Full-lesson review of Binder:**
  - 390px light, 768px dark, 1440px sepia, and 390px high contrast with the handwritten font at 22px.
  - No overflow in Content or Q&A; 13/13 Answer labels; scene text at or above the floors.
- **Not verified:** Safari's sideways-swipe Back gesture on a physical iPhone (WebKit bug 240183, open); other browser engines; real devices.

## 5. How to build, audit and preview

```bash
cd /Users/swaransinghaulakh/AndroidStudioProjects/android-staff-engineer-playbook-website
/Users/swaransinghaulakh/AndroidStudioProjects/android-staff-engineer-playbook/venv/bin/python website/scripts/build.py
python3 website/tools/prepare_browser_audit.py website/.cache/browser-qa
```

- **Audit:** serve `website/.cache/browser-qa`, open `/audit.html` and press Start audit. Every page must report `ok: true`. In a hidden browser pane it runs at about 4 pages a minute.
- **Design-system previews:** run `python3 website/tools/build_design_system_preview.py`, then open `website/.cache/design-system-preview/index.html`.
- **Private site preview:** run `python3 website/tools/make_artifact_preview.py website/dist <out>/site`, which makes a relative-link copy (about 243 files), then publish it with its landing page as an artifact. The current preview is https://claude.ai/artifact/GLRv4vR5R69M1k1QRFieCd; it is one fix behind `7c3b0cc`.

## 6. Pending, in order

1. **Confirm the final audit** on `7c3b0cc`, then republish the site preview.
2. **Codex round-4 review** (`reviews/design-system-review-brief-round4.md`). Apply its fixes, and add `data-no-handoff` for step-throughs where the packet misleads.
3. **The owner's review** of the Binder lesson on phone, tablet and desktop.
4. **Full FlowScenes** for the 15–20 movement lessons, in batches of 4–5.
5. **The owner's approval** of the original-chapter findings, phase by phase. Apply only what is approved.
6. **Follow-ups:** the KMP template blends, the Phase 7 staff notes and the candidate findings.
7. **Push and PR,** only on the owner's explicit approval.
