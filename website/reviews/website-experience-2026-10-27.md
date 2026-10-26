# Website experience and illustrated scenes — 27 October 2026

The owner asked for more beautiful, colourful and understandable animations, then clarified that the reference websites should inform the whole learning experience. This pass changes the shared design system and all 17 authored scenes. It preserves the source chapters and the existing one-repository publication contract.

## Reference review

[ByteByteGo's chat-system lesson](https://bytebytego.com/courses/system-design-interview/design-a-chat-system) demonstrates recognizable devices and servers, distinct component colours, numbered paths and progressively introduced detail. The inspected diagrams were static; the useful design principle is visual clarity rather than adding movement everywhere.

[Cloudmash Learn's load-balancer lesson](https://cloudmash.dev/learn/hld/load-balancing-and-traffic-management/what-a-load-balancer-does/) combines a structured learning route, navigation, reading controls and an interactive failure experiment. In the browser, killing server B first left it in rotation and subsequently removed it; the controls expose a delayed consequence. These are references for the website's teaching approach, not artwork or prose to copy.

Rulebook section 20 records the website-wide standard: a problem-first route, consistent visual language, visible consequences, meaningful alternatives, progressive detail, reading comfort and shared implementation. Existing phase navigation, search, section outlines, Q&A, reading preferences and previous/next links remain part of that experience. A new control is justified by a lesson's mechanism, rather than by a requirement to imitate a reference page.

## Implemented design

The token file defines four additional actor roles: blue devices, purple execution, teal stored data and rose queued work. Transfer direction retains its separate token colours and line patterns. Written status, arrowheads and badges supplement colour. The actor renderer uses original SVG objects: phones, servers, workers, document trays, databases, clocks, parcels, memory pages, source files, network clouds, state values, code windows and video players.

All 17 scene datasets explicitly choose their objects and visual states. Queue contents change, generated files appear, collectors disappear, cached values remain, a child memory page changes and video playback persists after a surface detaches. Room's authored two-user and three-user examples have numeric badges. Generic database scenes do not invent exact row totals. Schematic phone rows represent a view rather than a measured count.

Payloads use envelopes, row lists, files, command symbols or video-frame symbols. The renderer follows the existing authored relationships; it does not infer a transfer from a node becoming active. Responsive compositions give illustrated actors room and wrap full labels. Numbered navigation lets readers compare final states without animation. Instructions and a visual key are optional disclosures; every scene keeps its caption transcript, Previous, Next, Play/Pause and Reset.

The build generates `design-system/index.html` from the actual Room, Binder, Zygote and Flow sections. This gallery shares tokens, fonts, CSS, runtime and data with the lessons. It includes four theme choices and reduced motion. It is included in the private GitHub Actions package, rather than published as a separate agent-owned artifact. The design-system README now describes the implemented state; older standalone component previews are identified as historical samples.

## Coverage and limits

The 17 illustrated lessons are Binder, Looper, Room, WorkManager, OkHttp, Flow sharing, StateFlow/SharedFlow, coroutine internals, Paging, Zygote, Intent resolution, broadcasts, process lifecycle, Gradle, KSP, Compose runtime and Media3. The other 122 legacy state steppers retain their authored diagrams. They are not claimed as full illustrated scenes. No original-chapter correction was approved or applied by this design pass.

The static build checks all 125 pages and 15,572 original units, including order and source hashes. The browser sweep checks Content and Q&A at seven widths with enlarged Shantell Sans; scene states also cover four themes and four widths. Bounds checks use screen coordinates so nested SVG illustration groups are measured correctly, including vertical containment. Motion regressions cover ownership, Pause, reduced motion and the new numbered navigation. The generated gallery is inspected separately because it is a design reference rather than a source chapter.

## Verification and publication

Current verification results and the identified commit/build URL are recorded below after the final run. Publication stays in the private website repository on `codex/android-completion`, using existing draft PR #1. The review package is a downloadable GitHub Actions artifact. It does not establish a live private website; no public Pages deployment or repository visibility change is authorized.

### Final local result

- Static build: 125 pages, 15,572 original units, zero preservation problems; 125 source hashes verified.
- Browser sweep: 124 of 125 initially passed. Media3 had one phone actor title extending outside its node; shortening it to “Service player” passed the focused repeat at all four scene widths and themes. The integrated result covers 125 passing pages, 1,750 reading layouts and 1,808 scene states. Raw sweep, focused repeat and integrated evidence are committed separately.
- Motion: 12 of 12 checks passed, including numbered jumps backwards and forwards without motion.
- Documentation gates and their 15 unit tests passed.
- Gallery: navy theme and real scene controls inspected in Chrome. During this check, self-referential CSS aliases were found to invalidate the existing accent, line and button colours. The compiler now omits aliases whose source and destination match; generated CSS was checked for remaining self references. This colour correction followed the geometry sweep and is checked separately in the gallery.
- Package: includes the generated design gallery, relative links and no disposable QA harness. The previous 448-combination Binder font matrix remains historical evidence; this pass rechecked Binder through the full scene sweep rather than claiming that matrix was repeated.

The privacy constraint still means the GitHub deliverable is a downloadable build. Open `design-system/index.html` inside its extracted site folder for the interactive design system. A live private GitHub website is not configured.
