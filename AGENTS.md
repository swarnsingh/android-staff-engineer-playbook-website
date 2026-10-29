# Start here (any AI agent or contributor)

This repository holds the playbook's chapters (read-only for website work) and the reader website in `website/`, which is published to GitHub Pages from `main`. Read this page first; open other docs only when your task needs them.

## Spend tokens wisely

- Use the commands below. They print short PASS/FAIL summaries and keep full logs in `website/.cache/logs/`. Open a log only when a step fails.
- Read only the rulebook section your task needs (see the map below). Do not read whole large files or JSON evidence; search them.
- Prefer text checks to screenshots. Take a screenshot only to judge appearance.
- Run long jobs (audits take about 5 minutes) in the background and read only their summary.
- Do one milestone per chat. When it is finished, start a new chat rather than continuing a long one.

## Commands

Use a Python with `website/requirements.txt` installed (the owner's venv: `../android-staff-engineer-playbook/venv/bin/python`).

| Need | Command |
|---|---|
| Local build (all checks except the publication gate) | `python3 website/tools/dev.py build` |
| Check every FigureMap diagram model | `python3 website/tools/dev.py figures` |
| In Chrome: nothing outside its box, no sideways scroll, labels fit (after `build`) | `python3 website/tools/dev.py frames` |
| Everything CI runs (tests, docs check, script syntax) | `python3 website/tools/dev.py ci` |
| Fresh browser evidence (six audits) | `python3 website/tools/dev.py audit <review-folder>` |
| Refresh the gate and run the real build | `python3 website/tools/dev.py gate <review-folder>` |
| Preview locally | `python3 -m http.server 4177 --directory website/dist` after `build` |

## Publishing a change to shared reader files

Shared reader files are CSS, JS, templates, design tokens, `build.py` and diagram models. After changing any of them, the publication gate fails until fresh evidence exists:

1. Run `dev.py build`, `dev.py figures`, `dev.py frames` and `dev.py ci`.
2. Run `dev.py audit <topic>-<date>`. Fix anything that fails.
3. Write `website/reviews/<topic>-<date>/REPORT.md`, a short summary of the scope, results and limits.
4. Run `dev.py gate <topic>-<date>`.
5. Commit, then push to `main`. That deploys GitHub Pages; confirm the workflow run succeeds.

Content-only edits to blend files also change fingerprints, so they follow the same steps.

## Parallel work: one LLM owns one whole topic

- **Ownership.** Each chat or LLM owns one topic tree (for example `computer-science` or `platform-engineering`) from start to publish. A topic is never split between LLMs.
- **Branches.** Work on a branch named `<tree>-site`, cut from the latest `main`.
- **Registering a topic** touches these shared files; copy how `computer-science` is registered:
  - `TREES` and `phases()` in `website/scripts/build.py`;
  - the tree entry in `website/nav-data.js`;
  - `website/content/<tree>.json` (one intro line per chapter and for the learning path);
  - the `<tree>_sha256` hashes in `source-snapshot.json`;
  - the tree list in `website/scripts/check_review_data.py`;
  - the `--tree` choices in `website/tools/prepare_browser_audit.py`;
  - the pair-count split in `website/scripts/check_completion.py`.
- **Topic files** are `website/content/blend/<tree>/*.blend` and `website/content/diagram-models/figures/<tree>.json`. Every original Mermaid diagram needs a FigureMap model there.
- **While building**, use `dev.py build --pending` until all of your figures exist. Never publish with pending figures.
- **Publishing happens one topic at a time:**
  1. Run `git pull --rebase` from `main` and resolve conflicts in the shared files by keeping both topics.
  2. Run `dev.py audit <tree>-<date>`, write the `REPORT.md`, then run `dev.py gate <tree>-<date>`. The evidence must cover the latest `main` plus your topic.
  3. Push to `main` and confirm the deploy.

  If `main` moves while you are publishing, repeat from step 1.

## Rulebook map (`content-rulebook.md`)

| Topic | Section |
|---|---|
| Original chapters are never edited for website work; layered additions only | §17 |
| Diagrams: no Mermaid, no colourless diagrams, no ordinary animation; styling only in the design system | §20 "Designed visuals only" |
| Diagram meaning: labelled arrows, true owners, colour never the only cue | §20 "Approved diagram direction" |
| Layout widths and frames live in shared tokens and components | §20 "Shared layout ownership" |
| Only content is per topic; every style, layout, box, animation, diagram, size and font comes from the design system | §20 "Content is the only per-topic layer" |
| Lesson quality: concise additions, labelled fragments, exactness | §18 |
| Animation and accessibility basics | §8, §9 |
| Mobile review timing (consolidated review only at the end) | §20 "Mobile review timing" |
| Review workflow and definition of ready | §13 |

## Where things live

- **Diagrams.** Drawn by FigureMap (`website/scripts/figure_maps.py`).
  - Models: `website/content/diagram-models/figures/*.json` for original-diagram redraws; `website/content/diagram-models/*.json` for step-through relationship maps.
  - Guide: `website/design-system/components/FigureMap/README.md`.
- **Lesson additions.** `website/content/blend/**/*.blend`; the format is in `website/README.md`, "Writing a blend file".
- **Corrections to original text.** `website/content/corrections-*.json`.
- **Design system.** Tokens are in `website/design-system/tokens.json`; components are in `website/design-system/components/bundle.css` and `bundle.js`.
- **Evidence.** `website/reviews/<topic>-<date>/`; the latest folder is named by `ux_review` in `website/reviews/completion/validation.json`.

## Known open work

- **Centralization debt (§20 "Content is the only per-topic layer"):**
  - 318 inline styles in lesson files (227 grid column counts, 83 timeline positions, 8 raw margins or widths);
  - 458 CSS lines outside the design system, with 72 hard-coded colours in `styles.css`;
  - about 50 raw px font sizes;
  - FigureMap geometry constants in Python rather than in `tokens.json`.

- 181 teaching-layer HTML diagrams in Kotlin and Android lessons still use neutral cards. Under §20 they need role colours, legends and numbered captions.
- Some lessons may exceed the §18 length target; review them before trimming.
- Wide figures scroll sideways on phones; there are no dedicated phone layouts yet.
