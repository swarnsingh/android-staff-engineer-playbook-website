# Engineering Fundamentals rollout and shared reading layout

Owner approval:29 October 2026. Publication target: the existing public website repository and its GitHub Pages workflow. The original private playbook remains private. Source changes are offered for owner review in [PR58](https://github.com/swarnsingh/android-staff-engineer-playbook/pull/58); they are not automatically merged.

## Delivered scope

The website now renders all 13 Engineering Fundamentals chapters and their learning path, alongside22 Kotlin chapters,101 Android chapters and their two learning paths. The complete reader inventory is139 pages, plus the home page and design-system gallery. The new track follows its original guided order, grouped into core vocabulary, state and coordination, and production failure behavior. Navigation starts in the current track; the entire catalog remains available.

Each Fundamentals chapter has a concise, labelled teaching layer. Static diagrams explain structure, ownership, comparisons or decisions. Four temporal scenes explain blocking versus suspension, lost acknowledgement and retry, bounded-buffer policies, and Lamport message causality. Captions identify actions and outcomes; arrows carry direction and labels. Queue contents change explicitly. Color supplements text and shapes. These additions do not replace the original chapter or its questions and answers.

## Content corrections

The 293 approved exact replacements in `website/content/corrections-engineering-fundamentals.json` were verified against official project documentation, owning implementations, standards or original papers. Batch records retain the sources and reasons. The same inventory replays into the13 original source chapters, with verification references appended there. Across the existing canonical 743 replacements and this new inventory, the website and source branch match exactly in97 corrected chapters, excluding appended reference sections.

Review fixed complete answer paragraphs rather than inserting revised answers above obsolete ones. The reader keeps answers immediately beneath their corresponding questions. Correction details remain in optional history, rather than repeated warnings throughout the lesson.

## Shared layout

The owner approved the screenshot draft before implementation. Prose now fills the established760px reading column inside the880px sheet. Wide visuals extend symmetrically by at most 120px per side and up to 1000px total, further limited by viewport and navigation rails. Rounded frames,24px desktop padding,16px phone padding, shared surfaces and restrained shadows connect the wider visual to surrounding text. Overflowing code and tables expand only when necessary. Nested list examples retain local scrolling.

All new layout dimensions come from `website/design-system/tokens.json`; ReadingSheet behavior and styles live once in the shared component bundle. Individual lessons do not own width fixes. The rulebook and component documentation record this requirement for future contributors.

## Verification and boundaries

The final evidence files in this folder record browser preservation, seven viewport widths, four themes, enlarged text, scene states, readable code, answer pairing, motion behavior, navigation and negative preservation fixtures. The static preservation gate checks 17,330 source units in 139 pages. The checker suites cover 15 renderer/model tests and 31 website documentation tests. The original source docs gate and 15 tests also pass.

Exact corrected Lamport, vector-clock, HLC, LRU and retry fragments compile with Kotlin 2.4.21, coroutines 1.11.0 and JDK 17; 27 contract assertions pass. Android/platform adapters and conceptual network/storage examples retain explicit assumptions; this is not a complete application build. Existing Android runtime evidence remains separately recorded in the completion baseline.

The initial browser run exposed incorrectly classified teaching diagrams and undersized queue-item labels; both shared causes were repaired before final verification. One initial Activity image-readiness failure passed its isolated retry. Two teaching tables also needed a shared local-scroll boundary. The full139-page run and the targeted rerun of both matching pages are retained; final `browser.json` contains139 passing pages and1058 passing original answer pairs. All other focused suites pass. Publication is gated by these current results and input fingerprints.

Full manual mobile review remains deferred until every website topic tree is integrated, as the owner requested. Current work uses automated mobile regressions and manual desktop/tablet inspection. Browser checks do not certify physical devices, other browser engines or screen-reader behavior. Independent Gemini review remains useful after publication, with its findings treated as new evidence rather than presumed completed work.

Independent PR58 review follow-up: fixed all reported example/question contradictions, the Android vitals TTID reference, clock hierarchy and formatting, mathematical notation and duplicate reading links. The seven changed chapters pass a targeted browser rerun. The final inventory contains293 exact replacements; source PR58 includes commit7d56159.

Final owner-requested text follow-up: the immediate-completion answer and immutable-values pronoun are corrected in source commit e5336a7 and the website overlay. The two changed pages pass the targeted browser check.
