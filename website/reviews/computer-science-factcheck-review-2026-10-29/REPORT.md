# Computer Science corrections: independent review follow-up

**29 October 2026.** Codex reviewed the source pull request swarnsingh/android-staff-engineer-playbook#60, which proposes the 44 Computer Science corrections for the original playbook. It raised two findings, both against wording that this website had already published at commit cca9f88. Both were checked against primary sources and are correct, so the website and the pull request now carry the same revised text.

## Findings and fixes

### CSH08 (Hashing): treeification threshold

**Review finding.** The published replacement said a `HashMap` bin becomes a red-black tree "when it reaches 8 entries".

**What the source shows.** In OpenJDK's `putVal`, `binCount` starts at zero for the first node already in the bin. The `binCount >= TREEIFY_THRESHOLD - 1` check runs after the new node is appended, so treeification happens when a bin grows past eight entries, on the ninth `put` into it. The minimum table capacity of 64 slots and the `Comparable`-key condition were already right.

**Fix.** The replacement now reads "once it holds more than 8 entries, provided the table has at least 64 slots".

### CSG01 (Graphs): dependent recompilation

**Review finding.** The published replacement said a change to a widely used module "recompiles every module that depends on it". That ignores Gradle's compile avoidance, and it contradicts the Android build-tooling chapter.

**What the source shows.** Gradle's Java plugin documentation says changes to method bodies or private members are ABI-compatible and leave dependent compilation tasks up to date.

**Fix.** The replacement now limits recompilation to changes in the module's public API (its ABI) and says implementation-only changes let Gradle skip dependents. Gradle's compile-avoidance documentation is added to the sources.

## Records updated

- `website/content/corrections-computer-science.json`: the applied overlay.
- `website/reviews/computer-science-factcheck-2026-10-29.json` and `computer-science-factcheck-findings.md`: the review record, with the reason and sources revised.
- The pull request branch got the same two replacements, its review JSON, and a follow-up note in its description.

## Verification

- **Same text in both places.** Replaying the website overlay on the original Hashing and Graphs chapters produces exactly the text on the pull request branch.
- **Build.** `dev.py build` passes with preservation intact.
- **Audits and gate.** The six browser audits ran on this build. Their results are in this folder, and the publication gate requires them to pass.
- **Pull request.** The source docs gate and its 15 checker tests pass on the pull request branch.

## Limits

- **Not run on a JVM.** The treeification behaviour was confirmed by reading the current OpenJDK source, not by running it locally. The reviewer reports reproducing it on JDK 25.
- **No other changes.** The other 42 corrections are unchanged.
