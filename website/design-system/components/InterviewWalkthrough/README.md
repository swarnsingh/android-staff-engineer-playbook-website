# InterviewWalkthrough

The page layout for system-design chapters written as timed interview walkthroughs (the 12-section template in `mobile-system-design/`). Status: prototype on one chapter, Offline Sync, awaiting owner approval of the format.

## What it adds

All of it is derived from the chapter, by `website/scripts/walkthrough.py`:

- **Interview timeline.** One linked step per numbered H2 section, with the chapter's own `(~N min)` hint or "No time hint". The note says the times are pacing guidance, not a schedule.
- **Pacing bar.** The timed steps only, sized by their minutes. Below it, "Now" names the step being read. It sticks under the lesson tabs from 1181px; narrower screens use the compact "On this page" outline instead, so no extra bar stacks on phones. The bar is `aria-hidden`; the linked list is the accessible version.
- **Try first.** Added prompts before the requirements, clarifying-questions and API-contract sections. Their wording and "What a strong answer covers" hints are content in `website/content/walkthrough-layout.json`. The chapter's own answer below stays fully visible.
- **Decision cards.** Each table in the trade-offs section, with the same cells in the same order, laid out one card per option. Column names come from the header row; the chosen option (the only bold option, or a verdict starting "Pick") gets a solid accent border, and the others a dashed one.
- **Pushback checks.** Each `> **Q: …**` follow-up gets an added "Interviewer pushes back" label. The question and the chapter's answer stay visible.

Per chapter, a blend file can add a recovery step-through (`:: animation`, the shared stepper) and an end recap (`:: recap`, labelled "Interview recap · added by this site").

## When it applies

Only to chapters listed in a `"layout": "walkthrough"` group of `website/content/walkthrough-layout.json`, and only when the chapter has at least eight consecutively numbered H2 sections, at least one time hint and a requirements section. Otherwise the chapter renders in the normal layout. Each role (try-first targets, trade-offs, follow-ups) is found by its heading words and skipped when absent.

## Preservation

Original text is not moved, retyped, hidden or folded. Tables and blockquotes keep their markup and gain only attributes (`role`, `data-label`, `data-cell`, `data-chosen`) and labelled `.blend` tags, so `check_preservation.py` reads them as before.

## Tokens

`walkthrough-sticky-top`, `walkthrough-progress-height`, `walkthrough-step-min`, `walkthrough-card-min`, with the shared `space-*`, `radius-*`, `ui-*`, `accent`, `accent-soft`, `line`, `line-strong`, `sheet`, `sheet-sunken`, `ink-muted` and `scene-runtime`.

## Not yet done

- A gallery entry (`design-system/gallery.html`).
- An optional reader-controlled practice mode (an open owner decision).
