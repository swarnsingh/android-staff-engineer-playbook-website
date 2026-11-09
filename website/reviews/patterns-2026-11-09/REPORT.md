# Patterns reader rollout

## Scope and source

The Patterns index and all 12 chapters match the merged playbook at [source PR #81](https://github.com/swarnsingh/android-staff-engineer-playbook/pull/81), commit `45201470a80d644a12eac0d9ff787e34f09062a2`. The website records all 13 source hashes and that commit in `source-snapshot.json`. It renders the original sections, snippets, tables and 65 Q&A pairs in the established reader.

The learning path keeps the two groups and chapter order in the source. Boundaries and object collaboration starts with Repository. Resilience and distributed recovery starts with Retry. Each phase card opens that first lesson. Short hero summaries orient the reader and the openings give a distinct situation to follow in the chapter.

## Teaching notes and figures

Each lesson adds one short decision note. Repository and Adapter distinguish caller-visible outcomes from local storage and provider errors. Factory, Builder, Strategy and Decorator focus on construction ownership, snapshot boundaries, policy selection and wrapper order. Observer and State separate observed state, UI acknowledgement and effect execution. Command, Retry, Circuit Breaker and Saga follow the saved identities and outcomes needed when work is interrupted.

Five original diagrams have shared FigureMap redraws for strategy selection, hot and cold flows, reducer inputs and outputs, breaker state and saga compensation. The saga sequence labels confirmed failure before compensation and explains why a missing reply must be reconciled first. Numbered arrows have labels and the figures retain their original diagram source disclosures.

## Evidence and limits

- The build preserved 32,739 original units in order across 274 pages. The 22 preservation tampering fixtures passed.
- Figure validation passed 237 original diagram models and 197 teaching models.
- The 1440 px and 375 px frame checks passed across 261 lesson pages, covering 308 figures, 137 relationship maps and 4,660 labels at each width. An initial phone run flagged two checks on one existing Complexity Analysis figure. Three focused reruns and the full phone rerun passed. The figure, renderer and reader styles match the merged build.
- Local CI passed 64 website tests, 31 docs tests, the docs gate, 74 Computer Science Java examples and 15 browser-script syntax checks.
- Desktop checks followed both phase links, confirmed a distinct opening on each lesson, checked the five figures in all four themes and opened original-diagram disclosures on three sampled pages.

Desktop captures show the [learning path](patterns-learning-path-desktop.png), [observer comparison](observer-figure-desktop.png), [circuit breaker states](circuit-breaker-figure-desktop.png) and [saga sequence](saga-figure-desktop.png). Cropped figures omit sticky viewport controls. The checks exercise the reader and content preservation. The original Android and provider code retains the execution boundaries recorded in source PR #81. Phone checks are automated until the consolidated manual review.

## Full site audit

All six audit suites passed on the combined site. The browser checked 274 pages, 8,856 code readability cases and 1,652 original Q&A pairs, including the 65 Patterns pairs. The Binder suite passed 560 checks, motion 13, refinement 69, UX 278, and Q&A tampering 31. The publication gate binds the evidence to the lesson inputs and checks preservation at the GitHub Pages project path.
