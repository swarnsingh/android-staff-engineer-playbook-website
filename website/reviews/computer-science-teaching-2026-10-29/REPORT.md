# Computer Science teaching layer

**Owner request, 29 October 2026:** add the teaching layer to the Computer Science tree, which was published earlier the same day as original chapters with designed figures only. The tree is preparation material for a data-structures and algorithms interview round, so the layer favours pattern recognition and self-checks over long explanation.

## What was added

There are 12 new files in `website/content/blend/computer-science/`, one per chapter. The original Markdown is unchanged; preservation still checks every original unit in order.

Each full chapter now has:

- **A problem-first opening.** A short, concrete situation, often from Android, that the chapter's ideas solve. Examples: a contacts sort that crashes on a broken comparator, an image loader that needs a heap, and a Gradle module cycle that is really a graph.
- **One plain-words guide before the densest section.** It is a short list that maps the question's shape to the right pattern, with the costs that matter. Examples: choosing two pointers, a sliding window or prefix sums; a `PriorityQueue` cost table; the four steps of dynamic-programming state design.
- **Two or three "Check yourself" questions** with hidden answers. Each asks the reader to choose a pattern, predict an output or find a bug before opening the answer.
- **A "Staff lens" review question** where the chapter has a Staff Engineer Thinking section. These link to the matching Engineering Fundamentals chapters (Complexity Analysis, Backpressure, Coupling vs Cohesion, Caching) instead of repeating them.

Big-O is a 23-word cross-reference stub. It gets only a two-sentence opening; the stub already links to the full Complexity Analysis chapter.

## Length

Added prose stays within the rulebook's working target of about a quarter of each chapter. The shares run from 6% for the four long chapters (Hashing, Trees, Graphs, System Complexity) to 24% for Recursion and Backtracking and for Sorting and Searching. The Big-O stub is the only exception: any opening is longer than its 23 words.

## Accuracy

Every technical statement in the layer was checked against the standard definitions and the platform library's documented behaviour. This includes:

- `PriorityQueue` costs and iteration order;
- stable sorting in Kotlin's `sortedBy` and `sortedWith`;
- the TimSort contract exception;
- `List.binarySearch` return values;
- `tailrec` limits;
- tree-ified `HashMap` buckets;
- worked examples, such as coins {1, 3, 4} for amount 6 and the interval counterexamples, which were checked by hand.

The layer does not restate any claim that is under review.

**Finding SC1** (in [the findings file](../computer-science-teaching-findings.md)): the System Complexity chapter's defect-rate sentence gives a 4x ratio and then denies it, and cites no source. It is recorded only in the findings file: under the owner decision of 28 October 2026, published pages carry no review notices, and the gate rejects them. No correction was applied; the replacement wording needs the owner's approval.

## Verification

- `dev.py build` passes, including the design-boundary check. Preservation: 159 pages and 19,767 original units, with no problems.
- `dev.py figures`: 89 models, with no problems.
- `dev.py frames`: 154 pages, 89 figures, 118 maps and 1,892 labels. Nothing is outside its box, and nothing scrolls sideways.
- `dev.py ci`: website and docs unit tests, the docs check and browser-script syntax all pass.
- The rendered pages were checked directly: each of the 12 chapters has its opening, and the check answers render as disclosure elements. The cross-tree links resolve to the Engineering Fundamentals pages.
- The six browser audits ran on this build. Their results are in this folder, and the publication gate requires them to pass.

## Limits

- There has been no full fact-check of the Computer Science chapters. Only the claims touched by the layer were reviewed.
- The layer adds no new step-through animations. The designed figures from the earlier publication remain the visuals.
- Phone-width review of the new blocks relies on the shared components and the automated audits, not a manual pass.
