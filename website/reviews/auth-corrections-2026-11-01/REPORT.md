# Auth and SLO source corrections

## Scope and reader impact

Publishes three owner-merged playbook changes on the pages that show them:

- **PR #73** (`1f50858`): `observability/slos.md` snapshot, hash and figure `diagram` key. The figure's drawing and caption already matched the corrected outcomes.
- **PR #74** (`8e152a8`): `mobile-system-design/authentication.md` snapshot and hash. `android/networking-and-security/ktor-vs-retrofit.md` stays frozen and receives an approved correction whose result equals the merged source bytes.
- **Lesson additions on the authentication page.** The chapter no longer uses an app-scope refresh, so the step-through, figure caption and recap now teach a caller-owned refresh, `NonCancellable` rotation, one retry for bodyless reads only, and session end only on a confirmed `invalid_grant`.

PR #74's `patterns/decorator.md` and PR #75's `security/auth-on-mobile.md` and `reference-architectures/banking-app.md` belong to unpublished trees. No page changed here links to them, so their snapshots are unchanged.

## Lesson additions changed

The authentication page's teaching layer was written against an older chapter, so a snapshot refresh alone would have left it contradicting the text beside it. These edits follow the merged chapter:

- The "Caller cancelled" step no longer describes `appScope.async`. A started rotation now finishes under `NonCancellable`, and the cancellation reaches the caller after the commit.
- The "Rotation saved" step no longer says the rotated token is never lost. It says a lost response or process death can leave recovery to the identity provider's policy.
- The "Retry once" step and the figure caption limit the follow-up to a bodyless read. A write's 401 returns to its caller.
- The recap now says only a confirmed `invalid_grant` ends the session, that only that login's data is cleared, and that a transient failure keeps its tokens.
- The figure's node and caption use `SessionAuthInterceptor`, and its `diagram` key matches the new Mermaid source.

## Gate change

`check_completion.py` allows only a known set of Kotlin and Android corrections. It now also expects the one PR #74 replay. The new check is as strict as the existing PR #72 check: it fixes the path, pull request and merge commit, requires approval and sources, and requires the replayed chapter to hash to the merged source bytes. No existing requirement was removed.

## Link targets

The three changed pages link to six files in unpublished trees: `security/secure-storage-on-android.md`, three `backend-for-mobile` chapters, `milestones.md` and `release-engineering/crash-rate-gating.md`. All six snapshots match source `main`, so no linked-source refresh was needed.

The authentication page has four fewer audited code checks than the previous run, because the merged chapter has two fewer code blocks. No other page's count changed.

## Validation

`dev.py build`, `figures` (167 models), `frames` (200 pages) and `ci` pass. Preservation found 0 problems across 207 pages and 26,272 original units. The audit passes: browser 207/207, code 7,108/7,108, Q&A 1,299/1,299, binder 560/560, motion 13/13, refinement 69/69, UX 278/278, tampering 31/31.

Two earlier audit runs each failed one unrelated, unchanged page: `kotlin/version-updates/kotlin-2-4-update` (null click) and `engineering-fundamentals` (readiness timeout). The third run passed without changes. The machine was under heavy load from unrelated processes, which is the likely cause but was not proven.

The Ktor retry, 401 and logout cases were executed from the chapter's factory against a mock engine.

## Limits

Safari, Firefox, screen readers and physical devices were not tested. Nothing ran against a real identity provider, real TLS or durable Keystore storage.
