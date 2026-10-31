# Mobile System Design Phase 3 corrections review

## Scope and source

A Codex review of the live Phase 3 pages found content problems the automated checks can't catch. This change refreshes the Search and Caching Library copies from original playbook merge commit `1b19336` (source [PR #69](https://github.com/swarnsingh/android-staff-engineer-playbook/pull/69)), updates their hashes in `source-snapshot.json`, and corrects the teaching layer. PR #69 changed no Mermaid diagrams, so every FigureMap key still matches.

## Teaching-layer changes

| Chapter | Change |
| --- | --- |
| Image Loading | The intro and first figure title now say two cache tiers and a source fetch, not three tiers |
| File Downloader | The intro, first figure caption and relationship map say resume depends on what the server allows. The first figure caption names Range support and a strong ETag. The recap limits the 10-minute deadline to ordinary workers, and the process-death step no longer says nothing is lost |
| Caching Library | The step-through, caption, relationship map and recap follow the new disk queue, the skipped promotion and removal inside the queued read. The recap adds the builder's default TTL. A figure title that said "never staler" and a caption that said "durability" are softened |
| Pagination | The intro, process-death step and recap say the scroll index is saved, and that restoring a far position needs a device test |
| Search | The key includes the account. A new step and a recap bullet cover account switch and sign-out |
| Notification System | The intro says "many" rather than "most" failures, because the chapter has no data behind "most" |

Typeahead was scanned and needed no change.

These facts were checked against primary sources:

- [Long-running workers](https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/long-running): workers using `setForeground` can run longer than 10 minutes.
- [Kotlin functions](https://kotlinlang.org/docs/functions.html#parameters-with-default-values): an override uses the base method's default parameter values and can't declare its own.
- [Navigation](https://developer.android.com/guide/navigation/use-graph/programmatic): popping a destination destroys its lifecycle, stops saving its state and clears its `ViewModel` objects.

## Results

| Check | Result |
| --- | --- |
| Build | 182 pages, 23,108 original units in order, 0 problems |
| Figures | 129 models, 0 problems |
| Frames | 176 pages, 128 figures, 135 maps, 2,678 labels, no problems |
| CI | Tests, docs check and browser-script syntax pass |
| Browser audit | 182/182 pages, code 6,560/6,560, Q&A pairs 1,194/1,194 |
| Binder | 560/560 |
| Motion | 13/13 |
| Refinement | 69/69 |
| UX | 278/278 |
| QA tampering | 31/31 |

## Limits

- The two open device questions stay open: restoring a far scroll position has not been tested, and the Search account flow has not been run on a device.
- The Image Loading chapter's own text still says "three-tier cache". The site's added text now differs from it until the source is changed.
- These audits ran before merge on local pages. Other browser engines, physical devices and screen readers were not tested.
