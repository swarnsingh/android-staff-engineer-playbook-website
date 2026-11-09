# Platform Engineering: Design Systems Architecture

> Without a design system, 10 product teams ship 15 shades of blue, 8 button radii, and 4 typography scales. With one, a rebrand is a one-PR change to a tokens file. The design system is the highest-leverage UI investment a Platform team makes: every screen in the app inherits its quality bar.

---

## What a Design System Is (and Isn't)

A design system is **not** a folder of `CompanyButton.kt` components. It is a vocabulary shared between designers and engineers that compresses thousands of independent UI decisions into a small set of typed tokens.

It has three layers:

1. **Tokens** — typed values (colors, spacing, typography, motion). The vocabulary.
2. **Components** — opinionated building blocks (Button, TextField, Card) that consume tokens.
3. **Patterns** — composed screens / interactions (EmptyState, ErrorScreen, OnboardingStep) that consume components.

The leverage is in layer 1. If your tokens are wrong, no amount of component polish recovers it.

---

## The Three-Tier Token Architecture

```mermaid
graph TD
  Global["Global / Primitive<br/>color_blue_500 = #0052CC"]
  Semantic["Semantic / Alias<br/>colorPrimary = color_blue_500"]
  Component["Component<br/>buttonPrimaryBg = colorPrimary"]
  Global --> Semantic --> Component
```

**Global tokens** are raw values. They have no opinion. Engineers should not consume them directly in feature code.

**Semantic tokens** carry intent. `colorPrimary`, `colorError`, `colorOnSurface`. Dark mode is implemented here — a single dark-mode alias map remaps `colorSurface → color_neutral_900` without touching feature code.

**Component tokens** scope a semantic token to a specific use. `buttonPrimaryBackground`, `chipDisabledBorder`. They let designers tweak one component without affecting the rest.

### Why three tiers, not one

```kotlin
// One tier — hardcoded everywhere:
Button(modifier = Modifier.background(Color(0xFF0052CC)))  // 200 occurrences

// Two tiers — a rebrand is one line (colorPrimary = color_red_500), but you
// can't restyle only the button without changing every consumer of colorPrimary:
Button(modifier = Modifier.background(colorPrimary))

// Three tiers — the rebrand is still one semantic line, and a button-only
// change is one component-token line:
Button(modifier = Modifier.background(buttonPrimaryBg))
// buttonPrimaryBg = colorPrimary   ← retarget this line to restyle buttons alone
```

The second tier is what makes a rebrand a one-line change; the third tier is what lets designers change one component from Figma without touching every other consumer of the same semantic token.

---

## Tokens in Code: Compose-First

```kotlin
// :core:design-system/src/main/kotlin/.../theme/Tokens.kt
@Immutable
data class CompanyColors(
    val primary: Color,
    val onPrimary: Color,
    val surface: Color,
    val onSurface: Color,
    val error: Color,
    val onError: Color,
    val outline: Color,
    // ... ~25 semantic tokens, not 200 primitives
)

@Immutable
data class CompanyTypography(
    val displayLarge: TextStyle,
    val titleLarge: TextStyle,
    val bodyLarge: TextStyle,
    val labelSmall: TextStyle,
)

@Immutable
data class CompanySpacing(
    val xs: Dp = 4.dp, val sm: Dp = 8.dp, val md: Dp = 16.dp,
    val lg: Dp = 24.dp, val xl: Dp = 32.dp,
)

@Immutable
data class CompanyShapes(
    val small: Shape, val medium: Shape, val large: Shape,
)
```

`@Immutable` states the contract: once built, these values never change, so Compose may compare them with `equals()` and skip composables whose token arguments are equal. Classes whose properties are all `val`s of stable types (`Color`, `Dp`, `TextStyle`, `Shape`) are usually inferred stable anyway; the annotation matters when a property type can't be inferred (for example, a `List`). With strong skipping (on by default since Kotlin 2.0.20), composables with unstable parameters still skip, but compare those parameters by instance (`===`), so a freshly allocated but equal bundle would not skip.

### Wiring via `CompositionLocal`

```kotlin
val LocalCompanyColors = staticCompositionLocalOf<CompanyColors> {
    error("No CompanyColors provided. Wrap your content in CompanyTheme.")
}
val LocalCompanyTypography = staticCompositionLocalOf<CompanyTypography> {
    error("No CompanyTypography provided.")
}
// ...same for spacing/shapes

object CompanyTheme {
    val colors: CompanyColors @Composable @ReadOnlyComposable get() = LocalCompanyColors.current
    val typography: CompanyTypography @Composable @ReadOnlyComposable get() = LocalCompanyTypography.current
    val spacing: CompanySpacing @Composable @ReadOnlyComposable get() = LocalCompanySpacing.current
    val shapes: CompanyShapes @Composable @ReadOnlyComposable get() = LocalCompanyShapes.current
}

@Composable
fun CompanyTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val colors = if (darkTheme) DarkColors else LightColors
    CompositionLocalProvider(
        LocalCompanyColors provides colors,
        LocalCompanyTypography provides DefaultTypography,
        LocalCompanySpacing provides CompanySpacing(),
        LocalCompanyShapes provides DefaultShapes,
        content = content,
    )
}
```

`staticCompositionLocalOf` (not `compositionLocalOf`) — because reading colors should not be observed for recomposition (we never change them in flight; we re-provide the entire theme). Compose doesn't track reads of a static local; changing its value recomposes the whole content lambda where it is provided. Android's guidance is to use it when the value is highly unlikely to change, for the performance benefit.

Engineers then consume tokens by name:

```kotlin
Text(
    text = "Hello",
    color = CompanyTheme.colors.onSurface,
    style = CompanyTheme.typography.titleLarge,
    modifier = Modifier.padding(CompanyTheme.spacing.md),
)
```

No hex codes. No `8.dp`. Refactoring the entire visual language is now mechanical.

---

## Components: Slot APIs Over Boolean Soup

The temptation: as designers add variants, the component grows parameters.

```kotlin
// BAD — every new variant adds a boolean. 16 booleans = 65,536 combinations.
@Composable
fun CompanyButton(
    text: String,
    onClick: () -> Unit,
    icon: ImageVector? = null,
    isLeadingIcon: Boolean = true,
    isLoading: Boolean = false,
    isDestructive: Boolean = false,
    isFullWidth: Boolean = false,
    isCompact: Boolean = false,
    // ...
)
```

The fix: **slot APIs**. The component owns the container (background, ripple, padding, accessibility) and exposes `@Composable` lambdas for content.

```kotlin
@Composable
fun CompanyButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    style: CompanyButtonStyle = CompanyButtonStyle.Primary,
    content: @Composable RowScope.() -> Unit,   // <-- the slot
) {
    Surface(
        onClick = onClick,
        modifier = modifier.heightIn(min = 48.dp),
        enabled = enabled,
        shape = CompanyTheme.shapes.medium,
        color = style.containerColor(enabled),
        contentColor = style.contentColor(enabled),
    ) {
        Row(
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(horizontal = CompanyTheme.spacing.md),
            content = content,
        )
    }
}

// Caller composes content freely:
CompanyButton(onClick = { /* */ }) {
    Icon(Icons.Default.Add, contentDescription = null)
    Spacer(Modifier.width(CompanyTheme.spacing.xs))
    Text("Add item")
}
```

Plus a `sealed class CompanyButtonStyle` (Primary, Secondary, Destructive, Ghost) for the *opinionated* variations. Slot for content; sealed enum for visual style. Together they cover the matrix without exploding parameter lists.

---

## Module Strictness: Banning Raw Material Components

Feature modules must depend on `:core:design-system`, never on `androidx.compose.material3` or `android.widget.*` directly.

```kotlin
// :feature:cart/build.gradle.kts
dependencies {
    implementation(project(":core:design-system"))
    // implementation(libs.androidx.compose.material3)   // BANNED — design-system already re-exports what's needed
}
```

Enforce with a Lint rule:

```kotlin
// :core:design-system-lint/src/main/kotlin/.../RawMaterialImportDetector.kt
// (a pure-Kotlin lint checks module, not build-logic)
class RawMaterialImportDetector : Detector(), Detector.UastScanner {
    override fun getApplicableUastTypes() = listOf(UImportStatement::class.java)
    override fun createUastHandler(context: JavaContext) = object : UElementHandler() {
        override fun visitImportStatement(node: UImportStatement) {
            val fqName = node.importReference?.asRenderString().orEmpty()
            if (fqName.startsWith("androidx.compose.material3.Button") ||
                fqName.startsWith("androidx.compose.material.Button")) {
                context.report(
                    ISSUE_RAW_BUTTON,
                    node,
                    context.getLocation(node),
                    "Use CompanyButton from :core:design-system instead of raw Material Button."
                )
            }
        }
    }
    companion object {
        val ISSUE_RAW_BUTTON = Issue.create(
            id = "RawMaterialButtonImport",
            briefDescription = "Importing raw Material Button",
            explanation = "Feature modules must use CompanyButton.",
            category = Category.CORRECTNESS,
            priority = 8,
            severity = Severity.ERROR,
            implementation = Implementation(
                RawMaterialImportDetector::class.java,
                Scope.JAVA_FILE_SCOPE,
            ),
        )
    }
}
```

Ship the lint check with the design-system module so it auto-applies wherever the design system is consumed: `lintPublish(project(":core:design-system-lint"))` in `:core:design-system` packages the checks as `lint.jar` inside its AAR, and lint applies them in every module that depends on the design system. Import-based checks miss wildcard imports and fully qualified calls; a production rule should also match resolved calls to the Material composables.

---

## Multi-Brand Support

If the app ships under two brands (parent + sub-brand, white-label, regional variants), the token tier separation pays off massively.

```kotlin
// :brand:default/Tokens.kt
val DefaultLightColors = CompanyColors(
    primary = Color(0xFF0052CC),
    // ...
)

// :brand:premium/Tokens.kt
val PremiumLightColors = CompanyColors(
    primary = Color(0xFFB8860B),
    // ...
)

// :app/MainActivity.kt — BRAND is a per-flavor buildConfigField; BuildConfig
// generation is off by default since AGP 8.0 (buildFeatures { buildConfig = true })
val colors = when (BuildConfig.BRAND) {
    "default" -> DefaultLightColors
    "premium" -> PremiumLightColors
    else -> error("Unknown brand")
}
CompositionLocalProvider(LocalCompanyColors provides colors) { App() }
```

Feature code never references the brand directly. The brand-pick lives at the app root; everything downstream consumes semantic tokens.

---

## Accessibility: Bake It Into the System

Every component in the design system must:

- Hit minimum tap target (48 × 48 dp).
- Expose proper `contentDescription` slots for icon-only variants.
- Honor `LocalContentColor` and contrast ratios (WCAG AA = 4.5:1 for body text).
- Respect text scaling: every `TextStyle` uses `sp`, not `dp`.
- Handle TalkBack focus order via `Modifier.semantics`.

The platform team's leverage: feature engineers inherit the component-level baseline (touch targets, contrast, semantics) as long as they use `CompanyButton`; they still own screen-level work such as content descriptions and focus order. The price of taking that leverage away (one team builds a raw Button) is one regression that ships to thousands of users.

Add a Compose Preview that renders every component at 200% text scale + dark mode + RTL:

```kotlin
@Preview(name = "200% scale", fontScale = 2.0f)
@Preview(name = "Dark", uiMode = UI_MODE_NIGHT_YES)
@Preview(name = "RTL", locale = "ar")
annotation class ComponentPreviews
```

Annotate each design-system component's preview function with `@ComponentPreviews` (multipreview annotations apply to `@Composable` preview functions, not to the components themselves), and add a Paparazzi snapshot test that fails CI if pixels drift.

---

## Figma ↔ Code: Token Sync Pipeline

The mature setup: designers maintain tokens in Figma (Tokens Studio, Figma Variables); a CI job pulls them and generates Kotlin.

```yaml
# .github/workflows/sync-tokens.yml
name: Sync design tokens
on:
  schedule: [{ cron: "0 6 * * 1" }]   # Monday 06:00 UTC
  workflow_dispatch:
permissions:
  contents: write        # push the sync branch
  pull-requests: write   # open the PR (also allow Actions to create PRs in repo settings)
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - run: ./gradlew :tools:token-sync:run
        env:
          FIGMA_TOKEN: ${{ secrets.FIGMA_TOKEN }}   # needs the file_variables:read scope
      - uses: peter-evans/create-pull-request@v8
        with:
          title: "chore(tokens): sync from Figma"
          branch: tokens-sync
          body: "Auto-generated from Figma. Review color/spacing diffs carefully."
```

The `:tools:token-sync` task:

1. Reads Figma's REST API (`GET /v1/files/:file_key/variables/local`). The Variables REST API is available only to members of Enterprise organizations; on other plans, export tokens with a plugin such as Tokens Studio instead.
2. Maps Figma variables → checked-in Kotlin source, such as `:core:design-system/src/main/kotlin/.../tokens/GeneratedTokens.kt`. It must not write under `build/`: that directory is ignored by Git, so the pull request would contain nothing.
3. Runs `./gradlew spotlessApply` to format.

Result: designers never wait on engineers to push a token change. Engineers never type a hex code.

---

## Versioning the Design System as a Public API

Treat `:core:design-system` as a public SDK consumed by your own feature teams. Every change is a potential break.

| Change type | SemVer | Process |
|---|---|---|
| New component or new token | MINOR | Add, ship, announce |
| New optional parameter on existing component | MINOR only if the old signature survives | A default value keeps source compatibility, but the JVM signature changes; keep the old overload (hidden) or the change breaks already-compiled callers |
| Renaming an existing API | MINOR to add the new name and deprecate the old; MAJOR to remove it | `@Deprecated(replaceWith = ...)`: warning, then error, then hidden; remove only in a major release |
| Changing default behavior (e.g., button height 44dp → 48dp) | MAJOR | Coordinate rollout; flag in release notes |
| Removing a component | MAJOR | Six-month deprecation; migration tool |

Publish the design system as a versioned artifact (even internally) using the [`library-versioning.md`](library-versioning.md) playbook. Use ABI validation to detect accidental ABI breaks: the Kotlin Gradle plugin's experimental [`abiValidation`](https://kotlinlang.org/docs/gradle-binary-compatibility-validation.html), or [binary-compatibility-validator](https://github.com/Kotlin/binary-compatibility-validator), which is now in maintenance mode.

---

## Governance: Who Decides

Without governance, every team adds tokens for their use case and the system becomes the union of all features' wishlists.

| Decision | Owned by |
|---|---|
| New semantic token | Design system maintainers + Design lead |
| New component | Design system maintainers; feature team writes the PR |
| Tweak to component default | Design system maintainers; gated by snapshot diff review |
| Brand-level color change | Brand team; auto-propagates via tokens |
| Adding a *primitive* color | Designer + DS lead — rare; primitives are stable |

Run a weekly "Design Systems Sync" with 1 designer + 2 engineers. PRs queued through it. The bottleneck is intentional — design-system changes ripple too far to ship without review.

### Adoption metrics

The design system is only leverage if feature teams use it.

| Metric | Target | Enforcement |
|---|---|---|
| Feature modules depending on `:core:design-system` | 100% for UI modules | Build graph audit |
| Raw Material component imports | 0 in feature modules | Lint error |
| Hardcoded colors/spacing | 0 outside DS module | Lint + review |
| Component snapshot coverage | 100% for public components | CI |
| Accessibility preview coverage | 100% for public components | Paparazzi/Compose preview tests |
| Deprecated component usage | 0 after migration window | Lint warning -> error |

Publish adoption like any platform metric. If only half the org uses the design system, the problem is either missing components, weak enforcement, or a paved road that is harder than the dirt road.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| 15 shades of blue ship in production | Hardcoded `#xxxxxx` everywhere | Lint rule banning `Color(0xFF...)` outside `:core:design-system` |
| Dark mode broken on one screen | Feature team used a primitive, not semantic, token | Three-tier discipline + lint |
| Buttons grew to 32 parameters | No slot APIs | Refactor to slot + sealed enum styles |
| Every release breaks 5 feature modules | DS treats itself as internal, not a public API | SemVer + ABI validator + deprecation cycles |
| Designers tweak a color, engineers don't notice | No automated sync | Token-sync CI job → PR |
| Half the org uses DS, half doesn't | No enforcement | Lint rule fails CI on raw Material imports |
| DS team has 20 open PRs nobody reviews | No governance cadence | Weekly sync; named maintainers |

---

## Common Pitfalls

- **Designing tokens around components, not intent.** `loginButtonColor` is wrong — it's a component token masquerading as semantic. Use `colorPrimary`.
- **The system as a wall, not a kitchen.** If feature teams can't extend, they fork. Provide slot APIs and a clear "how to propose a new component" path.
- **No accessibility baseline.** Then a screen reader regression slips through and the brand pays for it. Bake AA contrast and 48dp targets into the components themselves.
- **Hex codes still appearing in feature code.** Means the lint rule isn't enforced, or the available tokens don't cover a real use case. Investigate before fighting.
- **One-person ownership.** When that engineer leaves, the system rots. Always two named maintainers and documented governance.

---

## Probing Questions

1. Why three tiers (primitive → semantic → component) instead of two?
2. Why `staticCompositionLocalOf` rather than `compositionLocalOf` for tokens?
3. Walk through how you'd implement dark mode such that no `if (isDarkTheme)` appears in feature code.
4. A feature team needs a new button variant the DS doesn't have. Walk through the decision tree.
5. How do you prevent the design system from becoming the dumping ground for every team's bespoke component?
6. A rebrand drops on Q3. Walk through the engineering rollout plan.
7. The Figma source of truth and the Kotlin generated code drift. How do you detect and fix it?
8. Multi-brand: when does a token belong at the brand layer vs the global layer?

---

## Answer Key

1. **Why three tiers (primitive → semantic → component) instead of two?**
   Three tiers allow designers to tweak a specific component (e.g., `buttonPrimaryBg`) without affecting the global semantic meaning of the color (e.g., `colorPrimary`). This isolation prevents accidental regressions across the entire app.
2. **Why `staticCompositionLocalOf` rather than `compositionLocalOf` for tokens?**
   `staticCompositionLocalOf` assumes the provided value changes rarely (like a theme swap). When it does change, the entire sub-tree recomposes. Since token values aren't animated or changed frequently, this avoids the overhead of tracking individual token reads, improving performance.
3. **Walk through how you'd implement dark mode such that no `if (isDarkTheme)` appears in feature code.**
   Define a semantic color token contract (e.g., `CompanyColors`). Create two instances: `LightColors` and `DarkColors`. At the root `CompanyTheme` composable, evaluate `isSystemInDarkTheme()` and provide the corresponding instance via `LocalCompanyColors provides colors`. Feature code only references `CompanyTheme.colors.surface`.
4. **A feature team needs a new button variant the DS doesn't have. Walk through the decision tree.**
   First, can it be built using the existing slot API? If yes, build it in feature code. If no, is it a one-off or a reusable pattern? If one-off, they build a custom component locally. If reusable, they propose it in the Design Systems Sync, and if approved, they PR the change into the DS.
5. **How do you prevent the design system from becoming the dumping ground for every team's bespoke component?**
   Implement strict governance: require PR reviews from DS maintainers and design leads. Reject components that lack reusability across multiple features. Force teams to use composition (slot APIs) rather than adding highly specific configuration flags.
6. **A rebrand drops on Q3. Walk through the engineering rollout plan.**
   Update the primitive and semantic tokens in the `Tokens.kt` file (ideally via an automated Figma sync). Run snapshot tests to review visual diffs across all components. Release the DS as a new minor version, and have feature teams adopt the new version.
7. **The Figma source of truth and the Kotlin generated code drift. How do you detect and fix it?**
   Run a CI job that pulls the latest tokens from the Figma API and compares them to the repository's tokens. If there's a diff, auto-generate a PR and require review to reconcile the drift, ensuring the code always matches design.
8. **Multi-brand: when does a token belong at the brand layer vs the global layer?**
   Brand layer tokens handle visual identity (colors, typography, specific border radii). Global layer tokens are structural and brand-agnostic (accessibility tap targets, fundamental spacing steps, structural layout rules).

## Further Reading

- [`build-graph-scaling.md`](build-graph-scaling.md) — keeping `:core:design-system` from becoming a build bottleneck.
- [`library-versioning.md`](library-versioning.md) — versioning the DS as a public API.
- [`sdk-distribution.md`](sdk-distribution.md) — if the DS ships beyond your org.
- [`../android/compose/recomposition-and-state.md`](../android/compose/recomposition-and-state.md) — why `@Immutable` matters for token bundles.
- [`../android/compose/modifiers-and-layout.md`](../android/compose/modifiers-and-layout.md) — modifier composition patterns the DS exposes.
- [Material Design 3 — Design tokens](https://m3.material.io/foundations/design-tokens/overview) — Google's reference vocabulary.
- [Tokens Studio for Figma](https://tokens.studio/) — token authoring and export.
- [Now in Android — DS module](https://github.com/android/nowinandroid/tree/main/core/designsystem) — Google's canonical Compose DS structure.
