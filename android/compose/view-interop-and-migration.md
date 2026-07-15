# View Interop & Compose Migration Strategy

Most production Android codebases are hybrids: a decade of View-based screens with Compose arriving feature by feature. The interop APIs are small; the staff-level problem is the *strategy* — which direction to embed, where the seams cost you, and how to sequence a migration measured in years without freezing feature work. This file owns the interop mechanics; pure-Compose topics live in their own files ([Recomposition & State](recomposition-and-state.md), [Stability](stability.md)).

## 1. Compose in Views: `ComposeView`

The forward direction — new Compose UI inside existing screens:

```kotlin
class FeatureFragment : Fragment() {
    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, saved: Bundle?) =
        ComposeView(requireContext()).apply {
            setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed)
            setContent { FeatureScreen() }
        }
}
```

The API everyone gets wrong is **`ViewCompositionStrategy`** — *when the composition is disposed*:

| Strategy | Use when |
|---|---|
| `DisposeOnDetachedFromWindowOrReleasedFromPool` (default) | `ComposeView` in a plain View hierarchy or `RecyclerView` — pooling-aware |
| `DisposeOnViewTreeLifecycleDestroyed` | Fragments (lifecycle not known at construction) — the standard fragment choice |
| `DisposeOnLifecycleDestroyed` | You hold a known `Lifecycle` explicitly |
| `DisposeOnDetachedFromWindow` | Deprecated — superseded by the pool-aware default |

The classic bug: the default strategy inside a fragment disposes composition on every detach while the fragment view survives, silently resetting `remember {}` state. In fragments, set `DisposeOnViewTreeLifecycleDestroyed`. And when a layout hosts multiple `ComposeView`s, each needs a unique `android:id` for `savedInstanceState` restoration to work.

## 2. Views in Compose: `AndroidView`

The reverse direction — legacy or SDK-only Views inside Compose:

```kotlin
AndroidView(
    factory = { context -> MapView(context).apply { /* one-time setup, listeners */ } },
    update = { view -> view.zoom = state.zoom },   // re-runs when State read here changes
    onReset = { view -> view.clear() },            // opt-in to reuse inside LazyColumn
)
```

The contract: **`factory` runs once** (construct, wire listeners — events flow up through them); **`update` re-runs whenever a `State` it reads changes** (data flows down). Accidental extra reads in `update` mean extra passes over a View that may re-measure expensively — treat `update` like a recomposition scope. In lazy containers, provide `onReset` so instances are reused rather than re-inflated per scroll; hold no View references in `remember {}` outside the `AndroidView` — construction belongs to `factory`.

`AndroidViewBinding(ExampleLayoutBinding::inflate)` (from `androidx.compose.ui:ui-viewbinding`) embeds whole XML layouts, and `AndroidFragment<MyFragment>()` embeds fragments — both are explicitly transitional tools for migration windows, not architecture.

Framework access from Compose goes through `CompositionLocal`s (`LocalContext`, `LocalView`, `LocalConfiguration`) and lifecycle-safe effects (`DisposableEffect` + `rememberUpdatedState` for receivers and callbacks).

## 3. The Cost of Seams

Every interop boundary buys migration progress and pays for it:

- **Double state ownership.** A screen half in each world needs its state hoisted above both — the `ViewModel` becomes the neutral ground, and screens that kept state in custom Views must extract it first. This is often the real migration work; the UI translation is mechanical.
- **Theming duplication.** Until a screen is fully Compose, colors/typography live in both XML themes and `MaterialTheme`; drift between them is a visual-QA tax. Centralize tokens (the [design system](../../platform-engineering/design-systems-architecture.md) owns them) and generate both.
- **Measurement mismatches.** `wrap_content`-style negotiation across the boundary (a View that sizes to its Compose child sizing to its View parent) is where the odd 0-height bugs live; give the boundary fixed or constrained dimensions when you can.
- **Tooling blind spots.** Recomposition tooling stops at `AndroidView`; View hierarchy tools stop at `ComposeView`. Profile hybrid screens with both lenses before blaming either side.

## 4. Migration Strategy (the part reviews actually probe)

The officially recommended sequence, which also matches what works organizationally:

1. **New features in Compose first.** Whole new screens via `ComposeView`-in-fragment. This builds team fluency on greenfield ground where regressions can't hide in legacy behavior.
2. **Component library before screen rewrites.** Port the design-system atoms (buttons, cells, chips) once, as the single source of truth — otherwise every migrated screen re-solves styling and the codebase accumulates three button implementations.
3. **Screens one at a time, simplest first.** Static screens (settings, confirmations) before list-heavy or animation-heavy ones. For screens already mixed, migrate **bottom-up** — leaf components first, the screen shell last.
4. **Navigation last.** Keep the Fragment-based Navigation component while fragments remain; move to Navigation Compose only when screens are screen-level composables. Swapping the navigation layer mid-migration doubles the risk surface for no user value.
5. **UI tests as the regression harness.** Screenshot tests (Paparazzi et al. — see [UI Testing](../testing/ui-testing.md)) before/after each screen migration; behavior parity is asserted, not assumed.

**The finish line matters:** a fully-Compose app drops the View machinery from the APK and its build; a permanently 50/50 codebase pays both costs forever. Staff judgment includes naming the screens that should *never* migrate (a complex custom-View editor with ten years of edge cases may earn a permanent `AndroidView` wrapper) and making that an explicit decision rather than entropy.

## 5. Review Checklist

- Fragment `ComposeView` without `DisposeOnViewTreeLifecycleDestroyed`? State-loss bug waiting.
- `AndroidView` in a lazy list without `onReset`? Inflation churn on scroll.
- State living inside a wrapped custom View? Hoist before migrating the siblings.
- Is this migration PR also changing behavior? Split it — parity first, improvements after.
- Does the screen have screenshot coverage before the rewrite starts?

## Further Reading

- [Using Compose in Views](https://developer.android.com/develop/ui/compose/migrate/interoperability-apis/compose-in-views) — `ComposeView`, `ViewCompositionStrategy`
- [Using Views in Compose](https://developer.android.com/develop/ui/compose/migrate/interoperability-apis/views-in-compose) — `AndroidView`, `AndroidViewBinding`, `AndroidFragment`
- [Migration strategy](https://developer.android.com/develop/ui/compose/migrate/strategy) — the phased plan this section expands
