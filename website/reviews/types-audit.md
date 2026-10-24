# Kotlin type-system and compiler-feature audit

Reviewed 2026-10-25 for the website adaptation. Canonical Markdown is unchanged. The correction overlay preserves each chapter's concepts, questions, examples and answers, while correcting confirmed claims; a modified example remains in the same teaching position.

## Chapters read

- `kotlin/type-system/generics.md` — read in full.
- `kotlin/type-system/variance.md` — read in full.
- `kotlin/compiler-features/inline-functions.md` — read in full.
- `kotlin/compiler-features/reified-types.md` — read in full.

The 49 exact replacements are in `website/content/corrections-types.json`. Each includes its original excerpt, replacement, reason, and primary-source URLs. All replacements were checked to match exactly once, sequentially, against the current source. This is a first technical audit, not a claim that every fragment or platform combination was compiled.

## Confirmed corrections

The function-variance example reversed return covariance: `(Animal) -> Number` cannot satisfy `(Dog) -> Int`. The corrected assignment accepts an Animal and returns Int, and is usable as `(Dog) -> Number`.

The generic chapter contradicted its own correct covariance explanation by calling standard `List<Dog>` invariant. It also said `List<Any?>` accepts arbitrary writes, although read-only List has no add/set API. The correction distinguishes standard List from MutableList and distinguishes projected element restrictions from immutability.

The multiple-bound validation fragment compared T to String even though its bound requires Comparable<T>. It now accepts a minimum of T. The UnsafeVariance example put a type annotation on a value parameter; it now annotates the parameter's type. A missing-service cast now happens after the null check, preserving the intended error.

The Dagger explanation incorrectly attributed an unresolved parameterised binding to blanket runtime erasure. Dagger operates on declared compile-time keys. Compose stability guidance now treats annotations as contracts and acknowledges strong skipping rather than recommending blanket Immutable annotations.

Java wildcard output now distinguishes parameter positions from return positions. The LiveData explanation states its invariant declaration without claiming that any mutable subtype inherently forbids a covariant parent.

Inline allocation assertions were contradicted by local compiler output: Kotlin/JVM 2.2.21 uses invokedynamic for the shown noncapturing lambda, and class-mode output uses a cached INSTANCE. The original per-call new-object listing is retained as a labelled conceptual alternative, rather than claimed as measured output. Invented allocation counts, OOM/jank certainty and universal line-count performance rules are removed while retaining the bytecode and performance discussion. Public inline visibility rules are distinguished from private inline functions, which can access private state.

Reified explanations now distinguish concrete operations at expanded call sites from retained erased JVM method artifacts and from richer `typeOf<T>()` tokens. Kotlin's inline requirement is described as its language design, rather than a mathematical limitation across possible VM/API designs. A public inline wrapper cannot call a private worker, so the helper visibility guidance is corrected.

## Execution evidence

Used cached Kotlin/JVM compiler 2.2.21 with OpenJDK 17.0.19; invoked K2JVMCompiler directly, without Gradle or modifications to a project build.

- Compiled the original reversed function assignment: rejected with expected Function1<Dog, Int>, actual Function1<Animal, Number>.
- Compiled the corrected assignment, covariance of List<Dog> to List<Animal>, and a private inline member reading a private property: accepted; runtime checks passed.
- Compiled the original generic validation: rejected because String is not the required T. The corrected T/minimum form compiled and returned true for `validate("z", "a")`.
- Compiled the original UnsafeVariance annotation: rejected for incorrect target and input-position conflict. The corrected type-use annotation compiled.
- Inspected `javap -c -p` for the non-inline math function and reified helper. Default lambda code uses invokedynamic. The generic reified helper method still exists with reification markers alongside the concrete String check in its caller.
- Recompiled with `-Xlambdas=class`: the noncapturing lambda is loaded from its cached INSTANCE rather than allocated with new on every call.
- Executed the two-element list runtime-class example: both printed java.util.Arrays$ArrayList, rather than EmptyList.

Temporary raw evidence: `/var/folders/lv/zt4jc7bx2m1912fqnq_63rhw0000gn/T/kotlin-types-audit-fnpcoopi`. This directory is not an artifact dependency and is not committed. The report records the results needed to assess these narrow corrections.

## Primary sources

- [Kotlin generics and variance](https://kotlinlang.org/docs/generics.html)
- [Inline functions and public API restrictions](https://kotlinlang.org/docs/inline-functions.html)
- [Kotlin/JVM lambda generation since 2.0](https://kotlinlang.org/docs/whatsnew20.html#generation-of-lambda-functions-using-invokedynamic)
- [Kotlin-to-Java wildcard translation](https://kotlinlang.org/docs/java-to-kotlin-interop.html#variant-generics)
- [UnsafeVariance type annotation](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-unsafe-variance/)
- [typeOf runtime type representation](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.reflect/type-of.html)
- [Dagger compile-time binding keys](https://dagger.dev/semantics/)
- [Compose stability and strong skipping](https://developer.android.com/develop/ui/compose/performance/stability/fix)
- [LiveData API declaration](https://developer.android.com/reference/androidx/lifecycle/LiveData)

## Limits and remaining review

Android/Hilt/Compose-shaped fragments were inspected and checked against contracts, but not compiled as an Android application. No claim is made about runtime allocation rates, ART/R8 optimisations, exact APK impact, or future compiler output. The original illustrative snippets depend on app-defined classes and imports; they must retain appropriate fragment/pseudocode labels in the website. Opinionated API preferences were retained where they did not make a false technical assertion.
