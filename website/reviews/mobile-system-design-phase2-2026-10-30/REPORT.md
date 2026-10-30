# Mobile System Design Phase 2 publication review

## Scope and source

This milestone adds the seven Phase 2 chapters to the reader website: App Startup, Authentication, Deep Links & Universal Links, Push Notifications, Feature Flags & Remote Config, Telemetry SDK and Analytics SDK. They join Phase 1 and the Offline Sync pilot, which are already live. Each Phase 2 chapter presents a timed design problem with trade-offs and follow-up questions, so all seven use the interview walkthrough layout, in the `sdk-and-platform-features` group. Phases 3 to 6 stay linked to the Markdown on GitHub.

Original playbook merge commit `b7bbcf3` (source PR #65) corrected the JankStats threshold example in the Telemetry SDK chapter. The website copy of `telemetry-sdk.md` was refreshed from that commit, and its hash in `source-snapshot.json` was updated. PR #65 changed no other chapter, so the other six Phase 2 copies still match `5ff8d44` byte for byte. The website does not edit or rearrange the original text. The build's preservation check verifies the original units in order, and the original Mermaid source stays available in labelled disclosures beside the designed figures.

## Added teaching layer

The Phase 2 chapters contain 14 Mermaid diagrams, not the 15 estimated in the Phase 1 plan. Each now has a FigureMap model with labelled arrows, owner boundaries where they help, role legends, a caption that makes its point, and official sources. Thirteen are maps. The Feature Flags fetch lifecycle is a sequence; its alternative branches are written as a note, because the sequence model has no `alt` frame.

Each chapter has a new intro line and a recap labelled as added by this site. Each also has one manual step-through with text captions and controls; nothing plays automatically. The step-throughs are:

| Chapter | Step-through |
| --- | --- |
| App Startup | A cold start from tap to TTID and TTFD, deferred SDKs, a Baseline Profile and a CI gate |
| Authentication | Two concurrent 401s, a single-flight refresh, a cancelled caller and the rotation saved in the app scope |
| Deep Links | A signed-out user's protected link through verification, the router, the saved pending route and post-login navigation |
| Push | A background chat data message through the dispatcher, the worker, Room, `MessagingStyle` and a secured tap |
| Feature Flags | A kill switch applied live while a next-session flag is staged and applied at the session boundary |
| Telemetry | A crash written to a flat file before process death, imported on the next launch and flushed first |
| Analytics | `track()`, the interceptors, a durable write, a 413 batch halving, delete after acknowledgement and an `APPEND_OR_REPLACE` follow-up |

Every caption and recap bullet was checked against the chapter's §7 deep dive and failure modes at `b7bbcf3`. Two platform facts that the chapters do not state were checked against their primary sources: the [JankStats default multiplier of two](https://developer.android.com/reference/androidx/metrics/performance/JankStats) and the RFC 9110 name for 413, ["Content Too Large"](https://www.rfc-editor.org/rfc/rfc9110#section-15.5.14). Some values are illustrative because the chapter does not give them. The checkout crash and the `new_checkout` flip are labelled as illustrative in their blend header comments. The `GET /orders` request in the Authentication step-through is illustrative too.

## Verification

All four local checks pass:

| Check | Result |
| --- | --- |
| `dev.py build` (non-pending) | 175 pages; 22,108 original units preserved in order; no rendered Mermaid pictures remain |
| `dev.py figures` | 113 models |
| `dev.py frames` | 169 pages, 112 figures, 128 maps and 2,354 labels; no overflow or clipping |
| `dev.py ci` | website tests, docs tests, docs checker and browser-script syntax |

In a browser preview at 1440 and 375 CSS pixels, all seven Phase 2 step-throughs reached their final step, and so did the Performance and Offline Sync step-throughs. There was no page-wide sideways scroll, no step node overflowed, and the console showed no errors. All 14 Phase 1 and Phase 2 pages and Offline Sync render locally.

## Browser audit

All six fresh browser audits passed on this build:

| Audit | Result |
| --- | --- |
| Browser preservation | 175/175 pages; code 6,280/6,280; Q&A pairs 1,194/1,194 |
| Binder | 560/560 |
| Motion | 13/13 |
| Refinement | 69/69 |
| UX | 278/278 |
| QA tampering | 31/31 |

## Limits and next milestone

This release publishes Phases 1 and 2 plus the Offline Sync pilot, which is 15 of the 35 Mobile System Design chapters. Practice mode, which would hide original answers until the reader reveals them, remains an owner decision; for now the original answers are visible. The full manual mobile review remains deferred under rulebook §20 until the complete website is integrated. The next milestone is Phase 3.
