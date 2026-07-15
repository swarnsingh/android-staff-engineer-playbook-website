# Custom Lint Rules & Static Analysis as Platform Leverage

A design review reaches the ten people in the room. A lint rule reaches every engineer, on every keystroke, forever. That asymmetry is why custom static analysis is one of the highest-leverage tools a platform team owns: it converts architectural decisions from documents people must remember into checks machines enforce. This file covers Android Lint specifically — the only analyzer that runs natively in the IDE, in AGP builds, and understands Android resources, manifests, and Gradle files together.

## 1. When a Lint Rule Is the Right Tool

Write a custom rule when a decision is:

- **Mechanically checkable** — "don't call `Runtime.exec`", "every `@Composable` screen takes a `Modifier`", "no `kotlinx.coroutines.GlobalScope`", "feature modules must not import `internal-billing`".
- **Repeatedly violated** — the same PR comment written three times is a detector spec.
- **Owned** — someone maintains it when the API it checks evolves.

Don't write one for style (formatters own that), for one-off migrations (a structured `grep` or OpenRewrite pass is cheaper), or for anything requiring whole-program semantics beyond what the AST gives you.

The strategic framing: your architecture rules — module boundaries from [Modularization Strategies](../android/architecture/modularization-strategies.md), API bans from incident postmortems, [design-system](design-systems-architecture.md) component mandates — are only real if violating them breaks the build.

## 2. Anatomy of a Check

Three pieces, all from `com.android.tools.lint`:

```kotlin
class GlobalScopeDetector : Detector(), SourceCodeScanner {
    override fun getApplicableMethodNames() = listOf("launch", "async")

    override fun visitMethodCall(context: JavaContext, node: UCallExpression, method: PsiMethod) {
        // UAST node inspection: is the receiver GlobalScope?
        // context.report(ISSUE, node, context.getLocation(node), "…", quickFix)
    }

    companion object {
        val ISSUE = Issue.create(
            id = "GlobalScopeUsage",
            briefDescription = "GlobalScope launches outlive their screen",
            explanation = "…why, and what to do instead…",   // shown in the IDE
            category = Category.CORRECTNESS,
            severity = Severity.ERROR,
            implementation = Implementation(GlobalScopeDetector::class.java, Scope.JAVA_FILE_SCOPE)
        )
    }
}
```

- **Detector + scanner interfaces.** `SourceCodeScanner` gives callbacks over Kotlin/Java (method calls by name, class extensions, imports); `XmlScanner` walks layouts/manifests; `GradleScanner` walks build files. One detector can implement several.
- **UAST, not PSI.** Detectors analyze the Unified AST so one rule covers Kotlin and Java; drop down to PSI only for language-specific details.
- **IssueRegistry + service loader.** A registry class lists your issues and declares `api = CURRENT_API` (and `minApi`) for lint-framework compatibility; it's discovered via `META-INF/services/com.android.tools.lint.client.api.IssueRegistry`.

## 3. Distribution — the Part Teams Get Wrong

Two Gradle configurations with confusingly similar names:

- **`lintChecks`** — wires a checks module into the *consuming module's own analysis*. Use it inside your repo: `lintChecks(project(":lint-rules"))`, typically applied everywhere via a [convention plugin](../android/os-internals/convention-plugins.md) so no module can opt out.
- **`lintPublish`** — *embeds* the checks as `lint.jar` inside your AAR, so external consumers of your library get your rules automatically with a plain `implementation` dependency. This is how an SDK or design-system team ships guardrails with the artifact ([SDK Distribution](sdk-distribution.md)).

The platform-leverage move is both: internal enforcement via `lintChecks` in the convention plugin, external enforcement via `lintPublish` on the libraries you distribute.

## 4. Testing

Lint rules are code; untested rules rot into false-positive generators that teach engineers to `@Suppress` reflexively. The `lint-tests` artifact makes tests declarative:

```kotlin
lint().files(
    kotlin("""
        import kotlinx.coroutines.GlobalScope
        fun leak() = GlobalScope.launch { }
    """).indented()
).issues(GlobalScopeDetector.ISSUE)
 .run()
 .expect("src/test.kt:2: Error: GlobalScope launches outlive their screen…")
```

Test the negative cases as hard as the positive ones — every false positive costs org-wide trust in the whole rule set. And provide **quick fixes** (`LintFix`) wherever mechanical: a rule that fixes itself in the IDE gets adopted; a rule that only complains gets suppressed.

## 5. Rollout: the Severity Ratchet

Turning a new rule on as `error` across a large codebase with 400 existing violations is how platform teams lose political capital. The working sequence:

1. **Baseline** the existing violations (`baseline = file("lint-baseline.xml")`) — new code is held to the rule, old code is grandfathered debt.
2. Ship at `warning` (or `informational`) for a release cycle; watch the false-positive reports.
3. Ratchet to `error` once the signal is proven; burn down the baseline as touched files get cleaned (never let the baseline file grow — that's the ratchet direction check for CI).
4. Severity overrides live in the `lint {}` DSL / `lint.xml`, so app teams can escalate faster than the platform default but not below it — encode the floor in the convention plugin.

`checkDependencies = true` on app modules makes the report span the module graph, which is what you want for the org dashboard: violations per module over time is the platform team's adoption metric.

## 6. The Broader Static-Analysis Portfolio

Lint is one layer. A staff engineer places each tool where it's strongest: **Kotlin compiler warnings as errors** (`allWarningsAsErrors`, per-module escape hatches) for language misuse; **detekt** for Kotlin-idiom and complexity budgets when you want non-Android JVM coverage; **Konsist or module-graph assertions in unit tests** for architecture rules that are about the dependency graph rather than call sites; **binary-compatibility-validator** for public API surface of published libraries ([Binary Compatibility & API Evolution](../android/kotlin-multiplatform/binary-compatibility-api-evolution.md)). The failure mode to avoid is three overlapping tools flagging the same thing with different severities — one owner, one rule per concern, one place engineers look for the "why" (the `explanation` field, which should link the ADR that motivated it).

## Further Reading

- [Lint API guide](https://googlesamples.github.io/android-custom-lint-rules/api-guide.html) — the canonical authoring reference (detectors, UAST, registries, testing)
- [Improve your code with lint checks](https://developer.android.com/studio/write/lint) — configuration, baselines, `lint {}` DSL
- [android-custom-lint-rules samples](https://github.com/googlesamples/android-custom-lint-rules) — working detector examples
