# Mobile System Design: Offline Sync pilot

**Owner request, 30 October 2026:** publish the interview-walkthrough prototype. The owner approved the format for this prototype after three browser and content reviews (Codex). This publishes the Mobile System Design learning path and one chapter, Offline Sync. The other 34 chapters keep linking to the source repository until the format is rolled out.

## What is published

- **Tree registration, as a pilot.** `TREES` uses `phases: [4]` and `pilot: ['mobile-system-design/offline-sync.md']`. Registration follows the Computer Science shape: snapshot hashes, the review-data tree list, audit choices and the completion pair split.
- **InterviewWalkthrough component** (`website/scripts/walkthrough.py`, the `bundle.css`/`bundle.js` tail, four layout tokens, a README and a gallery entry). It derives everything from the chapter:
  - a compact interview timeline from the numbered sections and their time hints;
  - a pacing bar that sticks from 1181px, and a step chip in the "On this page" summary below that width;
  - try-first prompts, whose content is in `content/walkthrough-layout.json`;
  - the trade-off tables restyled as decision cards;
  - "Interviewer pushes back" labels on the follow-up questions.

  A chapter uses the layout only when the manifest lists it and its headings match; otherwise it renders as a normal chapter.
- **Offline Sync teaching layer:**
  - three FigureMaps: the high-level architecture, the layered app architecture and the learning-path diagram;
  - a 9-step outbox replay using the shared stepper and relationship map;
  - a six-line recap, labelled as added by this site.
- **No Mermaid pictures.** The build passes without `--pending`.

## Source corrections

Review surfaced four problems in the original chapter. All were corrected at source, not on the website:

- PR #61 (OS1, OS2): `KEEP` instead of `REPLACE`; a `clientId` on every op; foreground and periodic outbox sweeps.
- PR #62 (OS3, OS4): one op per note per batch; rebasing the next op onto the acknowledged version; clearing `dirty` only when no op remains; compaction of never-sent upserts, with the attempted marker committed before sending; and a conflict policy for later queued edits.

The website copy of `offline-sync.md` is byte-identical to source merge commit `de5815b` (current source `main`), and `source-snapshot.json` records its hash. Details are in [the findings file](../mobile-system-design-offline-sync-findings.md).

## Accuracy

- **WorkManager.** The claims about persistence across restarts and reboots, and about `REPLACE` cancelling existing work, were checked against the official Android Developers guides.
- **Offline-first.** The source-of-truth and queued-write guidance was checked against the official offline-first guide.
- **Everything else** in the recap and step captions follows the corrected chapter.
- **Try-first hints** are generic interview guidance. They make no claims about this chapter.

## Verification

- `dev.py build` (without `--pending`) passes. Preservation: 161 pages and 20,011 original units, with no problems.
- `dev.py figures`: 92 models, with no problems.
- `dev.py frames`: 155 pages, with no problems.
- `dev.py ci`: all pass.
- Manual preview in the built-in browser:
  - desktop at 1440px and phone at 375px, with no page-wide sideways scroll;
  - the no-JS HTML contains every feature;
  - with reduced motion, Play is disabled and nothing advances by itself;
  - the gallery entry renders.
- Six browser audits: see "Audit results" below.

## Audit results

All six audits passed on this build:

| Audit | Result |
|---|---|
| Browser | 161/161 pages; code 5,664/5,664; Q&A pairs 1,194/1,194 |
| Binder | 560/560 |
| Motion | 13/13 |
| Refinement | 69/69 |
| UX | 278/278 |
| QA tampering | 31/31 |

## Limits

- **Pilot only.** One chapter is published. The other 26 full-template chapters need their FigureMaps, a step-through, a recap and an intro line each.
- **Practice mode** (collapsing original answers behind a reveal) is not built. It is an open owner decision.
- **Wide relationship maps** in the step-through scroll sideways inside their own frame on phones, as elsewhere on the site.
- **The consolidated manual mobile review** stays deferred until the whole site is complete (§20).
