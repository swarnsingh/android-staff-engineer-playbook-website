# Computer Science fact-check corrections

**Owner approval, 29 October 2026:** "Apply all, publish." This report covers applying the 44 corrections from the Computer Science fact-check, which the owner requested before the data-structures interview round.

## What changed

- **New file:** `website/content/corrections-computer-science.json` holds 44 approved corrections. They are applied through the website correction overlay, so the original chapter Markdown is unchanged.
- **Fingerprints:** the file is listed in the publication-gate fingerprints in `check_completion.py`, so a later edit to it requires fresh audit evidence. This matches how the Engineering Fundamentals corrections are tracked.
- **Findings record:** the rationale and sources for each correction are in [the findings file](../computer-science-factcheck-findings.md) and in the machine-readable proposal list beside it.

## Where the corrections are

| Chapter | Corrections |
|---|---:|
| Hashing | 11 |
| System Complexity | 13 |
| Trees | 9 |
| Graphs | 8 |
| Arrays and Strings | 1 |
| Sorting and Searching | 1 |
| Heaps and Priority Queues | 1 |

There are 15 high-severity corrections. Among them:

- `String.hashCode()` is not randomized in Java 8, contrary to the old text (two passages).
- The birthday bound for 32-bit hashes was misstated.
- 2^256 was compared incorrectly with the atom count of the universe.
- OkHttp pins public keys, not whole certificates.
- App Links verify at install time, and since Android 12 a failed check falls back to the browser.
- Git hardened SHA-1 after SHAttered, and Bitcoin never used SHA-1.
- Several Trees mechanics were wrong:
  - `git commit --amend` does not rewrite later commits;
  - measure and layout do not run every frame;
  - the trie autocomplete example is not constant time.
- Several System Complexity claims were wrong:
  - a self-contradictory defect ratio;
  - Accelerate was misattributed;
  - the cognitive-complexity counting rules were wrong;
  - Compose skipping was tied to function complexity instead of parameter stability.

Three corrections change code inside fenced blocks:

- the MD5 example digests;
- the two path comparisons in the Konsist architecture test, which previously matched no files and so could never fail.

## Verification

- **Exact match:** each correction's original text was checked to occur exactly once in its chapter before approval. The build enforces this again on every run.
- **Rendering:** a script checked all 44 rendered pages for the replacement text. The withdrawn `String.hashCode()` randomization claim no longer appears.
- **`dev.py build`** passes, and preservation still checks every original unit in order (159 pages and 19,767 units, no problems).
- **Other checks:** `dev.py frames` and `dev.py ci` were run, and the six browser audits ran on this build. Their results are in this folder, and the publication gate requires them to pass.

## Limits

- **Unsourced figures left in place:** for example, hash-speed comparisons and the Floyd–Warshall practical size. They cannot be shown wrong, so they were left for an editorial pass rather than corrected.
- **Original repository:** the corrections are not yet proposed as a pull request against the original playbook repository. That would be a separate change if wanted.
