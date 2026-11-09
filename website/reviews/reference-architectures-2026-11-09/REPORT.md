# Reference Architectures reader rollout

## Scope and source

The learning path and all 8 chapters match the merged playbook byte for byte at [source PR #81](https://github.com/swarnsingh/android-staff-engineer-playbook/pull/81), commit `45201470a80d644a12eac0d9ff787e34f09062a2`. The website records the hashes of all 9 source files and their provenance in `source-snapshot.json`.

Compare ownership and failure recovery across eight mobile products. The guided order starts with the consumer baseline, moves through e-commerce and merchant operations, then covers local durability, banking, real-time trips, social feeds and streaming. The phase cards open their first lessons. The chapter order, examples and source links are preserved.

## Teaching layer

Each blueprint adds a concrete opening and a note tied to a failure decision. The notes distinguish observed local state from server authority, a durable operation from a transport attempt, and buffered playback from recovery after reconnect. The bank example distinguishes local authentication from backend validation and initiated transfers.

The 27 FigureMaps cover architecture and data flows. The two payment maps put verified approval, pending processing and confirmed failure on separate branches. The merchant map labels offline risk when it is accepted, and the e-commerce map keeps the cart on failure. The full source sequences are preserved in disclosures. Other figures retain ordered actions and explicitly labelled alternatives. Each figure uses the shared design system and preserves the source diagram in a disclosure.

## Validation

- The build preserved 34,009 original units in order across 283 pages. All 22 preservation tampering fixtures passed. The figure checker passed 264 original models and 197 teaching models.
- Desktop and 375 px frame checks passed across 269 lesson pages. Desktop checked 335 figures and 5,089 labels. Phone checked 335 figures and 5,089 labels.
- Local CI passed 64 website tests, 31 docs tests, 74 Computer Science Java examples, the docs gate and 15 browser-script syntax checks.
- The topic preview followed each phase link, checked distinct opening text, confirmed source diagram disclosures and exercised 108 figure and theme combinations. The browser reported no page exceptions.
- All six browser audit suites passed. The browser checked 283 pages, 8,868 code readability cases and 1,652 Q&A pairs. The remaining audit counts were Binder 560, Motion 13, Refinement 69, UX 278, Q&A tampering 31.

Desktop captures are available for [e commerce app figure](e-commerce-app-figure-desktop.png), [merchant app figure](merchant-app-figure-desktop.png), [offline first app figure](offline-first-app-figure-desktop.png), [reference architectures learning path](reference-architectures-learning-path-desktop.png). Cropped figure captures omit sticky viewport controls. Phone evidence here is automated.

These illustrations exercise the reader and preserve the blueprint examples. They make no live payment, banking, location or media requests. Provider behaviors remain scoped to the linked documentation and the examples’ contracts. Timing and workload numbers in the original chapters are examples, and the new notes keep that scope. The publication gate ties the browser evidence to the exact inputs and checks the build at the GitHub Pages project path.
