# Computer Science tree, lean release

The owner prioritised the Computer Science tree ahead of interview rounds that cover data structures and algorithms. This release publishes the tree as a lean version: all 12 original chapters rendered in full with designed figures. The problem-first teaching layer follows in a later release. One LLM owns this topic from registration to publication, following the topic-ownership rules in `AGENTS.md`.

## Delivered scope

- **Registration.** `computer-science` is a website tree, following the tree index's guided reading sequence in three phases:
  - **Data structures:** Big-O, arrays and strings, linked lists/stacks/queues, hashing, trees, graphs, heaps.
  - **Algorithms:** sorting and searching, recursion and backtracking, dynamic programming, greedy and intervals.
  - **Systems:** system complexity.
- **Navigation.** The tree appears under Foundations in the catalog. Each chapter, and the learning path, has a one-line intro in `content/computer-science.json`.
- **Read-only source.** The chapters are recorded in `source-snapshot.json`, and the review-data check verifies their hashes on every build. No original chapter was edited.
- **Designed figures.** The tree's five Mermaid diagrams are FigureMap models in `content/diagram-models/figures/computer-science.json`:
  - graph variants and their algorithms;
  - what a hash function is for;
  - how complexity compounds;
  - a modular app's module graph;
  - tree variants and where they run.

  Each has role colours, numbered labelled arrows, a legend, a numbered caption, a text version and official sources. The two system-complexity diagrams originally drew arrows between groups. They are modelled as level cards, so every arrow joins two actors.
- **Gate support.** The Q&A pairing check keeps its fixed Kotlin/Android and Fundamentals counts and requires every new tree's pairs to pass. Browser-audit preparation accepts the new tree.
- **Work in progress.** `dev.py build --pending` allows local builds while a topic's figures are unfinished. The gate and CI never use it, so nothing with a Mermaid picture can publish.

## Verification

- `dev.py figures`: 84 models, with no problems.
- `dev.py frames`: 148 pages, 84 figures, 118 relationship maps and 1,842 labels. No element sits outside its box, nothing scrolls sideways at desktop width, and every label fits its shape.
- `dev.py build` passes the design-boundary check, the no-Mermaid check and preservation for every page, including the 12 new chapters.
- The six browser audits ran on this build; their results are in this folder. The publication gate requires all of them to pass before the release is pushed.
- Website unit tests, documentation tests, the docs check and browser-script syntax checks are run as part of the release chain.

## Limits

- This is the lean release. Problem-first openings, plain-language guides, practice checks and step-through scenes for these chapters are not yet written; they belong to the next Computer Science release.
- Figure sources cite stable references: NIST's Dictionary of Algorithms and Data Structures, FIPS 180-4, the JDK and SQLite documentation, the Android modularization guide and the RocksDB overview. They support the figures' structure, not new technical claims.
- On phones, wide figures scroll sideways inside their frame. The full manual mobile review remains deferred until the whole website is integrated (§20).
