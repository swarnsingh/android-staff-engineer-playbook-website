> Historical review record. Current completion, public publication and candidate dispositions are in [completion/REPORT.md](completion/REPORT.md). Earlier pending/private-hosting statements below are superseded.

# Status of the two owner-supplied reviews

The verified issues from the reports are now corrected in the website, with matching changes in [source PR #57](https://github.com/swarnsingh/android-staff-engineer-playbook/pull/57). The owner explicitly requested fixes, publication and a PR in the original repository on 27 October 2026. The detailed [official-source verification report](OFFICIAL-CONTENT-VERIFICATION-2026-10-27.md) records the evidence, validation scope and exact correction inventory.

The resubmitted attachments are byte-identical to `incoming/2026-10-27-website-review.txt` and `incoming/2026-10-27-topic-audit.txt`. Their broad statements that every chapter was audited were not accepted as proof. Each named issue was compared with the actual source passage and a primary reference. Some report claims pointed to the wrong chapter, described text already corrected in the current source, or proposed an inaccurate replacement.

## Website and teaching-layer requests

| Request | Current disposition |
|---|---|
| AirBridge hierarchy, callout roles and spacing | Implemented in the shared theme and tokens. |
| Sticky outline and scrollspy | Already existed and retained; the reading-position bar is now implemented and tested. |
| Phone scene and state controls | 48px targets implemented and checked. |
| 320px labels and diagrams | Full rerun passes; two actual structure-table overflows were fixed. |
| Kotlin annotations, modifiers and type highlighting | Implemented with source-text preservation. |
| SharedFlow heading says three ways but has two modes | Heading now names StateFlow and SharedFlow; no invented third-mode delivery guarantee. |
| Lifecycle-aware effects collection | Corrected with STARTED gating and an explicit no-subscriber event-loss caveat. |
| tryEmit default-buffer qualification | Already present before the original bullets; no duplicate clarification added. |
| Blanket replacement of conditional LaunchedEffect(Unit) | Not adopted without a demonstrated lifecycle/delivery defect. |
| General Kotlin Playground embedding | Optional feature, not implemented in this correction pass. The existing runnable coroutines example remains available. |

## Verified technical corrections

There are 86 approved replacements across 31 chapters: 76 targeted records in `corrections-verified-review.json` plus ten existing `corrections-language.json` proposals for the named Kotlin issues. The published active text uses the corrected explanation. The website's original Markdown snapshot, Git history and expandable correction disclosures retain earlier wording for traceability; retaining history does not keep the old explanation active. The source PR changes the original repository's chapter files directly on its isolated branch, with citations. Main is not merged and unrelated local changes are untouched.

The correction set covers modern multi-resume, in-process ViewModelStore retention, process-scoped Binder limits, the actual Navigation 2.7 error in Modularization Strategies, RoomDatabase transaction ownership, relation batching and table invalidation, Hilt component ownership and Dagger binding caching. It also corrects strong-skipping explanations and repeated compiler-report advice, offset placement, nullable delegated-property smart casts, Flow context and lifecycle collection, expedited work, exact alarms, Looper shutdown, Retrofit request construction, Apollo response types, coroutine-test deadlines and bounded collection, ANR timeout categories, Gradle output/cache distinctions, DEX compilation stages and Kotlin memory/type semantics.

The reports were not applied verbatim. Their foreground/background execute-service values were reversed. Their offset description incorrectly skipped layout placement. The current WebView and Swift-export chapters already contain the claimed modern behavior. The KMP decision matrix already permits shared ViewModels; the remaining prohibition was in Recomposition and State, which is now corrected. The current Swift-export documentation confirms Flow-to-AsyncSequence support while retaining Alpha status and a dispatcher caveat. Exact source links and replacements make these decisions reviewable without trusting another model's summary.

## Validation and remaining scope

Source documentation gates, all 15 checker tests and 298 Mermaid renders passed, including GitHub CI for source PR #57. Focused Kotlin/compiler regressions passed. The website passed 125 pages, 1,750 reading layouts, 8,880 illustrated states and 1,808 full-scene states, plus the final Apollo focused recheck, Binder, motion and interaction fixtures. All 31 source-PR chapters match the website correction text before the source PR's added reference lists.

Framework-dependent examples were checked against official API/source contracts rather than built as a complete Android application. The approved set closes the verified issues from these two reports; unrelated historical phase findings and older correction proposals are not automatically approved. General Playground integration remains optional. [The publication guide](../DEPLOYMENT.md) identifies the one website repository and GitHub Pages delivery path.
