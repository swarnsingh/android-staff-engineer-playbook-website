# Kotlin language-core technical audit

Reviewed on 25 October 2026. All eight source chapters were read in full: Variables, Null Safety, Functions, Extensions, Data Classes, Value Classes, Sealed Classes and Interfaces, and Delegation. The canonical Markdown was not edited. Website corrections live in `website/content/corrections-language.json`, with an exact source excerpt, replacement, reason, and primary-source links for each change. Each replacement was checked to match exactly once, including after earlier replacements were applied.

The audit preserves topics, examples, questions, and answers. A correction can change a false premise in an interview question or its answer; retaining a known false statement would not preserve its learning objective.

## Material corrections

- Properties: top-level/local lateinit is legal; read-only collections do not guarantee immutability; public constants still have reflection-visible fields; changing an inlined constant's value differs from removing a binary signature.
- Lazy initialization: JVM SYNCHRONIZED lazy has a volatile initialized fast path, not a lock on every subsequent read. Lazy evaluation does not generally solve cyclic definitions.
- Null safety: current Kotlin/JVM parameter checks throw NullPointerException, StateFlow may hold null when its type permits it, and JSONObject distinguishes a missing key from explicit JSON null.
- Coroutines inside language examples: suspending runCatching wrappers must preserve CancellationException.
- Data classes: they can extend eligible ordinary or sealed classes; implementing equals does not automatically suppress hashCode generation; data classes and List do not enforce deep immutability.
- Compose: strong skipping allows unstable parameters and memoizes lambdas with unstable captures. A List field or mutable capture does not by itself force the whole UI tree to recompose.
- Sealed types: Kotlin 1.7+ requires exhaustive sealed-subject statements by default. Same-package/module rules apply to direct subclasses. An Unknown branch does not automatically absorb newly introduced subclasses.
- Delegation: SharedPreferences normally reads its loaded in-memory map; rememberSaveable uses saved-instance-state infrastructure rather than SavedStateHandle; Delegates.notNull throws IllegalStateException; an unconstrained generic T cannot back lateinit storage.
- Extensions: shadowed extensions produce a compiler warning; internal is module visibility, and top-level internal extension names need not be module-mangled. Static mocking is supported by tools such as MockK, although an explicit injected boundary can be clearer.
- JVM function representation: ordinary Kotlin/JVM lambdas default to invokedynamic from Kotlin 2.0. Allocation, caching, inlining, and bound-reference cost are contextual rather than one-object-per-call guarantees.
- Value classes: boxing is a representation rule of thumb, not an exact universal nullable-type rule. Referential equality is prohibited. Current Java interoperability includes experimental boxed exposure as well as JvmName bridges.

## Executed evidence

Local probes used Kotlin/JVM compiler **2.2.21**, its matching standard library, and OpenJDK **17.0.19**. They were isolated from repository source and did not run Gradle or alter project dependencies.

A successful compilation and run demonstrated:

```text
lateinit=initialized/local
inherits=parent
onlyEquals=true; hashes=1,2
listOf=[9, 2]
notNull=java.lang.IllegalStateException
nullParameter=java.lang.NullPointerException
member=member
```

The data-class probe overrode only equals. javap still showed a generated hashCode, demonstrating why matching custom equality/hash implementations matter. The list probe changed a two-element JVM listOf result through a mutable interface cast; this is implementation evidence, not a recommendation to cast read-only collections.

Separate compilations confirmed these diagnostics:

```text
Unconstrained lateinit T: error, nullable upper bound.
Non-exhaustive sealed when statement: error, missing branch.
Shadowed extension: warning, extension is shadowed by a member.
Empty data class: error, primary constructor parameter required.
```

javap also showed an invokedynamic instruction for an ordinary non-inline lambda, a java.lang.String parameter for a nullable value class wrapping non-null String, and an unmangled public static method for an internal top-level extension.

## Evidence sources and limits

The correction records link the relevant official Kotlin/Android documentation, Kotlin stdlib implementation, Gson guidance, and MockK documentation. Core references include [data classes](https://kotlinlang.org/docs/data-classes.html), [properties](https://kotlinlang.org/docs/properties.html), [Kotlin 1.7 compatibility](https://kotlinlang.org/docs/compatibility-guide-17.html), [JVM lambda generation](https://kotlinlang.org/docs/whatsnew20.html#generation-of-lambda-functions-using-invokedynamic), and [Compose strong skipping](https://developer.android.com/develop/ui/compose/performance/stability/strongskipping).

This was a source audit plus targeted probes, not compilation of every snippet or a guarantee that no technical errors remain. Android, Hilt, Room, Compose, serialization, and network fragments require their surrounding application types and dependencies; they were not compiled as Android applications. Performance rankings and exact allocation counts were not benchmarked. The probe compiler is older than the current documentation's Kotlin 2.4 series, so implementation observations are explicitly tied to 2.2.21. No physical devices or other Kotlin backends were tested.
