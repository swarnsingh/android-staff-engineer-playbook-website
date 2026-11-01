# Computer Science language tabs — complete tree review

The Computer Science tree now pairs all 74 portable JVM examples with explicit
Java 17 counterparts and the preserved Kotlin 2.0 source. Java is selected
initially and each card switches independently. The Big-O bridge contains no
code fences. Twelve Android/Compose/Konsist examples retain Kotlin and have
explicit framework/application labels, following the requested Kotlin direction
for Android framework code.

## Code verification

The checked-in validator compiles the exact displayed Java text with
`javac --release 17 -Xlint:all -Werror`, using the documented imports and chapter
types. All 74 compile. Forty-eight snippets have executable behaviour fixtures;
all pass with assertions enabled. The exact 74 matching Kotlin fences also
compile with language/API version 2.0 and JVM target 17, using the Kotlin 2.2.0
compiler, with their documented surrounding types and fragment prerequisites.
Compilation verifies syntax and API resolution within those fragment contexts,
not a standalone Android app.

Source hashes bind each pair to its corrected Kotlin fence. Missing pairs,
unregistered Kotlin-only exceptions, and changed source fences fail verification.
Java compilation and behaviour now run in local CI and the publication workflow.
Both snippets remain readable without JavaScript.

## Primary references checked

- [Java 17 ArrayDeque](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/ArrayDeque.html)
- [Java 17 Comparator](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Comparator.html)
- [Java 17 Stream](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/stream/Stream.html)
- [Java 17 PriorityQueue](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/PriorityQueue.html)
- [Java 17 MessageDigest](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/security/MessageDigest.html)
- [Java 17 ByteBuffer](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/nio/ByteBuffer.html)
- [Guava 33.4.6 Hashing](https://guava.dev/releases/33.4.6-jre/api/docs/com/google/common/hash/Hashing.html)
- [Compose Kotlin APIs](https://developer.android.com/develop/ui/compose/kotlin)
- [WAI-ARIA tabs](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/)

The deliberately broken comparator is labelled as a counterexample. The Murmur
block-mixing example is labelled as an incomplete fragment, with its Kotlin
little-endian helper prerequisite. The Guava Java variant uses the fixed UTF-8
implementation and declares the Guava dependency.

## Website verification

- Build: 207 pages, 26,272 original units, zero preservation errors.
- Figures: 167 models, zero problems.
- Frames: 200 chapter pages, 166 figures, 138 maps, 3,304 labels, zero problems.
- CI: 20 website tests, 31 docs tests, docs gate, Java checks and browser syntax pass.
- Fresh browser evidence is stored beside this report. Every code card is tested
  for Java default, Kotlin switching, ArrowLeft/Home/End, active copy target and
  independence from neighbouring examples before the preservation audit.
- All six audits pass: browser 207/207 pages, code readability 7,400/7,400,
  Q&A pairing 1,299/1,299, binder 560/560, motion 13/13, refinement 69/69,
  UX 278/278 and tampering fixtures 31/31.

The 12 Android/Kotlin application fragments are outside the JVM counterpart
compilation scope. No source chapter snapshot was edited.
