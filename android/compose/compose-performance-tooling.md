# Compose Performance Tooling

## Overview

Compose performance is not fixed by sprinkling `remember` everywhere. You need a measurement loop:

1. Reproduce the user journey.
2. Measure in a release-like build.
3. Locate the phase: composition, layout, draw, image decode, binder, IO, or GC.
4. Fix the smallest real cause.
5. Protect the journey with benchmarks and regression thresholds.

## Measurement Stack

| Tool | Best for | Avoid using it for |
|---|---|---|
| Compose compiler metrics | Stability/skippability diagnostics | End-user jank numbers |
| Layout Inspector recomposition counts | Local debugging | Proving production performance |
| Macrobenchmark | Startup, scrolling, frame timing, trace capture | Micro-optimizing a pure function |
| Perfetto/system trace | Scheduler, frames, CPU, binder, GC, GPU clues | Guessing without a scenario |
| JankStats | Field jank telemetry | Root cause by itself |
| Baseline Profiles | Startup and hot path precompilation | Masking bad UI architecture |
| Android Studio Profiler | CPU/memory exploration | CI regression gates |

## Release-Like Builds

Debug builds are useful for development and terrible for performance judgment. Compose debug builds have extra checks, less optimization, and different compiler/runtime behavior.

Performance measurements should use:

- `minifyEnabled true` or equivalent release optimization path.
- Baseline profiles installed.
- `profileable` enabled for local tracing when needed.
- Real devices, not emulators, for decision-making.
- Stable data fixtures and network control.

If a team debates Compose performance from debug builds, stop the debate and build a benchmark.

## Compose Compiler Reports

Compiler reports help answer:

- Which composables are skippable?
- Which parameters are unstable?
- Which classes need stronger immutability contracts?
- Where are lambdas or collections defeating skip logic?

Typical Gradle configuration:

```kotlin
composeCompiler {
    reportsDestination = layout.buildDirectory.dir("compose/reports")
    metricsDestination = layout.buildDirectory.dir("compose/metrics")
}
```

Staff-level use:

- Track aggregate stability trends by module.
- Review unstable public UI model types.
- Fail CI only on agreed high-signal checks, not every raw metric.
- Pair reports with Macrobenchmark results. Stability does not automatically mean smooth frames.

## Recomposition Debugging

Recomposition is not inherently bad. Unnecessary recomposition that performs expensive work is bad.

Look for:

- Expensive calculations inside composables.
- New unstable objects created for child parameters.
- Lambdas capturing frequently changing state.
- State read too high in the tree.
- Lazy list items without stable keys.
- Backwards writes: writing state after reading it in the same composition.

```kotlin
@Composable
fun SearchResults(items: List<Item>, query: String) {
    val filtered = remember(items, query) {
        items.filter { it.matches(query) }
    }

    LazyColumn {
        items(
            items = filtered,
            key = { it.id }
        ) { item ->
            ResultRow(item)
        }
    }
}
```

`remember` caches work during composition. It does not make bad state ownership correct. If filtering is domain logic or large enough to affect frames, move it out of the composable.

## Defer State Reads

Read frequently changing state as low as possible and as late as possible.

```kotlin
// Worse: parent recomposes for every scroll pixel.
val offset = listState.firstVisibleItemScrollOffset
Header(offset = offset)

// Better: child reads through lambda or derived state at the needed phase.
Header(offsetProvider = { listState.firstVisibleItemScrollOffset })
```

For modifier values that change often, prefer lambda-based modifiers where available:

```kotlin
Modifier.offset {
    IntOffset(x = 0, y = scrollOffsetProvider())
}
```

This can move reads toward layout instead of composition, reducing work in the composition phase.

## `derivedStateOf`

Use `derivedStateOf` when a high-frequency input changes more often than the UI result should.

```kotlin
val showBackToTop by remember {
    derivedStateOf {
        listState.firstVisibleItemIndex > 0
    }
}
```

Do not use it as a default wrapper around every expression. It has overhead and should be tied to a real reduction in recompositions.

## Lazy Layouts

Lazy layouts need stable identity.

```kotlin
LazyColumn {
    items(
        items = messages,
        key = { it.id },
        contentType = { it.type }
    ) { message ->
        MessageRow(message)
    }
}
```

Use:

- `key` to preserve item state and avoid mismatched reuse.
- `contentType` to help reuse compatible item compositions.
- Paging placeholders carefully, with stable IDs when possible.

Avoid:

- Nesting same-direction scrollables without a bounded height.
- `itemsIndexed` with index keys for mutable lists.
- Heavy image decode or date formatting in row composition.
- Passing unstable `Painter` objects when a URL or resource ID would do.

## Images and Graphics

Image performance issues often look like Compose issues.

Checklist:

- Load images at the displayed size.
- Prefer image loading libraries that handle caching, sampling, and `prepareToDraw`.
- Avoid passing `Painter` as a public composable parameter when a URL or drawable resource ID is stable enough.
- Do not decode bitmaps on Main.
- Watch GPU upload cost for large images entering the viewport.
- Verify memory churn in long scrolling sessions.

## Trace the User Journey

Use custom trace sections around app-owned work.

```kotlin
trace("FeedRepository.transform") {
    rows.map { it.toUiModel() }
}
```

In a Perfetto trace, correlate:

- `Choreographer#doFrame`
- Compose recomposition/layout/draw sections
- Binder calls
- Image decode/upload
- GC pauses
- Main thread blocked time
- RenderThread and GPU work

A trace without a named product journey is just a beautiful spreadsheet.

## Metrics That Matter

| Journey | Metric | Guardrail |
|---|---|---|
| Cold start | `timeToInitialDisplayMs`, `timeToFullDisplayMs` | p50 and p95 by device tier |
| Feed scroll | slow frames, frozen frames, frame p95 | release benchmark and field JankStats |
| Search typing | input latency, dropped frames | benchmark with deterministic fixture |
| Image grid | memory growth, GC count, frame time | low-RAM and mid-tier devices |
| Checkout | end-to-end tap latency | trace sections around validation/network/UI |

Staff engineers set budgets by product journey and device tier, not by generic averages.

## CI Strategy

Start with a small benchmark suite:

- Startup benchmark.
- One critical scroll.
- One high-value interaction.
- One image-heavy screen if the app has media.

Run on pinned physical devices where possible. Store JSON results. Compare against rolling baselines with tolerance bands rather than brittle single-run thresholds.

## Staff Engineer Review Checklist

- Are performance claims backed by release-like measurements?
- Does every critical journey have a benchmark or field metric?
- Are Compose compiler reports reviewed for public UI model stability?
- Are lazy lists using stable keys and content types?
- Is high-frequency state read low in the tree?
- Are images decoded, cached, sampled, and uploaded intentionally?
- Are custom trace sections present around app-owned expensive work?
- Are baseline profiles generated from real user journeys?
- Are metrics segmented by device tier and form factor?
- Does CI catch regressions without becoming noisy?

## Further Reading

- [Android Developers: Jetpack Compose performance](https://developer.android.com/develop/ui/compose/performance)
- [Android Developers: Compose performance best practices](https://developer.android.com/develop/ui/compose/performance/bestpractices)
- [Android Developers: Compose stability](https://developer.android.com/develop/ui/compose/performance/stability)
- [`stability.md`](stability.md) - Compose stability model.
- [`../performance/macrobenchmark-and-perfetto.md`](../performance/macrobenchmark-and-perfetto.md) - benchmark and trace workflow.
