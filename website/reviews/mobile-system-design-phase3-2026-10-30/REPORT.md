# Mobile System Design Phase 3 publication review

## Scope and source

This milestone adds the seven Phase 3 chapters to the reader website: Image Loading, File Downloader, Caching Library, Pagination, Typeahead / Autocomplete Search, Search and Notification System. They join Phases 1 and 2 and the Offline Sync pilot. Each one is a timed design problem, so all seven use the interview walkthrough layout, in the `infrastructure-components` group. The rest of Phase 4 and Phases 5 and 6 stay linked to the Markdown on GitHub.

All seven website copies already matched original playbook `main` at `c1f26bb` byte for byte, so no chapter copy or hash changed in this release. The website does not edit or rearrange the original text. The build's preservation check verifies the original units in order, and the original Mermaid source stays available in labelled disclosures beside the designed figures.

## Source errors found

These seven chapters had not yet had the full source review that Phases 1 and 2 received. Reading them against the teaching layer found claims that primary sources contradict, and code samples that contradict the chapter's own failure tables. They are listed in original playbook [PR #67](https://github.com/swarnsingh/android-staff-engineer-playbook/pull/67), which is open and awaits the owner's review.

**Until that PR merges, the original text on these pages still contains those errors.** The teaching layer does not repeat them, so on these points a page's added material and its original text disagree:

| Chapter | The original text says | The teaching layer says |
| --- | --- | --- |
| File Downloader | Code appends a 200 response; the table says restart the chunk | A 200 starts at byte 0, is never appended, and the download restarts as one chunk |
| Pagination | Relaunch resumes from the last known cursor | `LAUNCH_INITIAL_REFRESH` refreshes first; `SKIP_INITIAL_REFRESH` continues from the stored cursor |
| Typeahead | Under 100 ms and under 50 ms latency, with a 120 ms debounce | Local results come after the debounce, at least 120 ms after the last keystroke |
| Typeahead | An interceptor cancels the OkHttp call | A Retrofit `suspend` call cancels it |
| Notification System | `areNotificationsEnabled()` suppresses an offline category opt-out | The app's stored preference suppresses it |
| Notification System | Promotions are opt-in under CAN-SPAM | CAN-SPAM requires an unsubscribe mechanism, not prior opt-in |

When PR #67 merges, the seven copies and their hashes must be refreshed from it, followed by fresh audits and a gate run. It changes no Mermaid diagram, so the FigureMap bindings stay valid. The figure captions were written to hold either way.

## Added teaching layer

The Phase 3 chapters contain 16 Mermaid diagrams. Each now has a FigureMap model with labelled arrows, role legends, a caption that makes its point, and official sources. Fifteen are maps. The Image Loading request pipeline is a sequence, and its memory-hit branch is written as a note, because the sequence model has no `alt` frame.

Each chapter has a new intro line and a recap labelled as added by this site. Each also has one manual step-through with text captions and controls; nothing plays automatically. The step-throughs are:

| Chapter | Step-through |
| --- | --- |
| Image Loading | A memory miss, a disk miss and fetch, decode to size, a second size that hits disk only, a memory hit on scroll-back, and a row that leaves mid-request |
| File Downloader | A durable enqueue, a one-time plan, parallel ranges, a dropped network, a resume from the ledger, servers that ignore or reject a range, and assembly with a checksum |
| Caching Library | A put to memory, death before the flush, an atomic disk write, a memory hit, a cold read that promotes, and an expired or unreadable entry as a miss |
| Pagination | Cached rows first, a transactional refresh, prefetch from Room, a cursor-based append, a failed append, a bounded memory window and process death |
| Typeahead | Fast typing that starts nothing, local results after a pause, a remote request, cancellation by a newer query, a merge, remote trouble that stays quiet, and a tap |
| Search | A query formed from inputs, a new paging generation, the mediator filling a key, a change of mind, a filter as a new query, a dead network and a click |
| Notification System | A trigger, a duplicate stopped, preferences resolved, quiet hours by category, localized rendering, a channel that is down, and the device's inbox |

Every caption and recap bullet was checked against the chapter's §7 deep dive and failure modes at `c1f26bb`, not only its headline requirements. Intro lines avoid the chapters' unsupported latency numbers.

These platform facts come from outside the chapters and were checked against primary sources:

- [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110#section-14.2): a server may ignore `Range`.
- [WorkManager](https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/manage-work): the 10-minute execution deadline, and the ignored `Result` of a stopped worker.
- [Define work](https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started/define-work): a lost constraint stops the worker, and the work is retried when constraints are met again.
- [Long-running workers](https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/long-running): `setForeground`.
- [Paging network and database guide](https://developer.android.com/topic/libraries/architecture/paging/v3-network-db): when the mediator runs, and how Room invalidates its source.
- [`PagingConfig` source](https://github.com/androidx/androidx/blob/androidx-main/paging/paging-common/src/commonMain/kotlin/androidx/paging/PagingConfig.kt): `maxSize` is best effort.
- [Retrofit `KotlinExtensions`](https://github.com/square/retrofit/blob/trunk/retrofit/src/main/java/retrofit2/KotlinExtensions.kt): cancelling the coroutine cancels the call.
- [FCM message types](https://firebase.google.com/docs/cloud-messaging/customize-messages/set-message-type): the 4096-byte payload limit.
- [Coil 2 upgrade guide](https://coil-kt.github.io/coil/upgrading_to_coil2/): `BitmapPool` was removed.
- [FTC CAN-SPAM guide](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business): recipients must be able to opt out.

Some values are illustrative because the chapter does not give them. The 12 MB file with three 4 MB chunks and the promo at 23:30 say so in their captions. The `user:42` key and the typing rhythm are recorded as illustrative in their blend header comments.

## Verification

All four local checks pass:

| Check | Result |
| --- | --- |
| `dev.py build` (non-pending) | 182 pages; 23,083 original units preserved in order; no rendered Mermaid pictures remain |
| `dev.py figures` | 129 models |
| `dev.py frames` | 176 pages, 128 figures, 135 maps and 2,678 labels; no overflow or clipping |
| `dev.py ci` | website tests, docs tests, docs checker and browser-script syntax |

In a browser preview at 1440 and 375 CSS pixels, all seven Phase 3 step-throughs reached their final step. There was no page-wide sideways scroll, and no step node overflowed. The console showed one 404 per page load. All 14 of the page's own linked resources load; `/favicon.ico` returns 404 on the local server and is the likely request, though this was not confirmed.

## Browser audit

All six fresh browser audits passed on this build:

| Audit | Result |
| --- | --- |
| Browser preservation | 182/182 pages; code 6,556/6,556; Q&A pairs 1,194/1,194 |
| Binder | 560/560 |
| Motion | 13/13 |
| Refinement | 69/69 |
| UX | 278/278 |
| QA tampering | 31/31 |

## Limits and next milestone

This release publishes Phases 1, 2 and 3 plus the Offline Sync pilot, which is 22 of the 35 Mobile System Design chapters. Browser emulation does not certify physical devices, other engines or screen-reader behaviour. Practice mode, which would hide original answers until the reader reveals them, remains an owner decision; for now the original answers are visible. The full manual mobile review remains deferred under rulebook §20 until the complete website is integrated. The next milestone is the rest of Phase 4.
