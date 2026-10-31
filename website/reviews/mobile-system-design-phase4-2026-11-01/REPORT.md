# Mobile System Design Phase 4 publication review

## Scope and source

This milestone adds the three remaining Phase 4 chapters to the reader website: News Feed, Chat / Messaging and Collaborative Editing. They join Phases 1, 2 and 3 and Offline Sync, which completes Phase 4. Each one is a timed design problem, so all three use the interview walkthrough layout, in the `full-apps` group. Phases 5 and 6 stay linked to the Markdown on GitHub.

The three website copies were refreshed from original playbook merge commit `49620c3` (source [PR #68](https://github.com/swarnsingh/android-staff-engineer-playbook/pull/68)), and their hashes in `source-snapshot.json` were updated. The other Mobile System Design chapter copies already matched playbook `main`. The website doesn't edit or rearrange the original text. The build's preservation check verifies the original units in order, and the original Mermaid source stays available in labelled disclosures beside the designed figures.

## Source corrections

An audit checked each chapter's checkable claims and Further Reading links against current official documentation, specifications and library source. PR #68 corrected what those sources contradict, along with code samples that contradicted the chapters' own failure tables. Codex review then found design gaps that changed the chapters' guidance:

- **Collaborative Editing:** a row now stays in the op log until a committed snapshot contains it, and remote ops are logged too.
- **Chat:** recovery is scheduled before the socket send, and the server chooses FCM priority by what the user will see.
- **All three:** cached personal data now has an account boundary.

The PR changed no Mermaid diagram.

This teaching layer was written after the merge, from the merged text. No caption or recap departs from the chapters on purpose.

## Added teaching layer

The three chapters contain 7 Mermaid diagrams. Each now has a FigureMap model with labelled arrows, role legends, a caption that makes its point, and official sources. Six are maps, and the Chat send flow is a sequence. Where a Mermaid arrow has no label, the label is added and adds no new relationship.

Each chapter has a new intro line and a recap labelled as added by this site. Each also has one manual step-through with text captions and controls; nothing plays automatically. The step-throughs are:

| Chapter | Step-through |
| --- | --- |
| News Feed | `initialize()` checking the cache, a transactional refresh, a failed append, bounded video, a like and its schedule, a fetch landing before the op drains, a system kill, a hint and a sign-out |
| Chat / Messaging | A saved row, recovery scheduled first, a socket send, an ack, no ack and a REST retry, the server choosing a priority, seconds on the recipient's device, receipts and a sign-out wipe |
| Collaborative Editing | Apply, persist, show and send; an ack that doesn't delete; a crash and offline restart; a reconnect; a logged remote op; a snapshot transaction; presence; foreground service limits; and sign-out or revocation |

Every caption, recap bullet and intro line was checked against the chapter's storage section, §7 deep dive, failure modes, §9 concerns and §10 follow-ups at `49620c3`. Each says what the design doesn't promise: a message can end `FAILED`, a push can be dropped, sign-out loses queued work, and a like can be dropped by a non-retryable error. Intro lines don't claim a chapter's latency numbers.

Three statements go beyond the chapter text:

- News Feed's recap says far-position scroll restore needs a device test, matching the Pagination recap. It isn't a platform claim.
- Chat's recap says SQLCipher doesn't cover Coil's disk cache. The chapter only encrypts the database.
- News Feed's APPEND caption says the mediator runs when Room runs out, from the [Paging network and database guide](https://developer.android.com/topic/libraries/architecture/paging/v3-network-db).

Figure and step-through sources are the pages used in the source audit, including [FCM message priority](https://firebase.google.com/docs/cloud-messaging/android-message-priority), [OkHttp `WebSocket`](https://github.com/square/okhttp/blob/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/WebSocket.kt), [Yjs document updates](https://docs.yjs.dev/api/document-updates), [`y-indexeddb`](https://github.com/yjs/y-indexeddb/blob/master/src/y-indexeddb.js) and [foreground service timeouts](https://developer.android.com/develop/background-work/services/fgs/timeout).

## Verification

All four local checks pass:

| Check | Result |
| --- | --- |
| `dev.py build` (non-pending) | 185 pages; 23,583 original units preserved in order; no rendered Mermaid pictures remain |
| `dev.py figures` | 136 models |
| `dev.py frames` | 179 pages, 135 figures, 138 maps and 2,831 labels; no overflow or clipping |
| `dev.py ci` | website tests, docs tests, docs checker and browser-script syntax |

## Browser audit

All six fresh browser audits passed on this build:

| Audit | Result |
| --- | --- |
| Browser preservation | 185/185 pages; code 6,676/6,676; Q&A pairs 1,194/1,194 |
| Binder | 560/560 |
| Motion | 13/13 |
| Refinement | 69/69 |
| UX | 278/278 |
| QA tampering | 31/31 |

## Limits and next milestone

This release publishes Phases 1 to 4, which is 25 of the 35 Mobile System Design chapters. Browser emulation doesn't certify physical devices, other engines or screen-reader behaviour. Practice mode remains an owner decision, and the full manual mobile review remains deferred under rulebook §20. The News Feed and Chat step-through maps are tall, about 1,730 and 1,550 px at desktop width, because the layout stacks their owner boundaries. They pass the frame checks and keep their labels at full size.

The samples in these chapters are pseudocode and weren't compiled; only the op log rules ran, as a small Kotlin model. Open owner questions on the source chapters:

- Chat orders by a client `sentAt`, so clock skew can misorder messages.
- Chat's Coil disk cache isn't encrypted while signed in.
- News Feed's §3 diagram says "FCM / socket" while §8 picks FCM.
- "Wakes app from killed state" and "`LazyColumn` announces position" aren't sourced.

The next milestone is Phase 5, starting with a source audit.
