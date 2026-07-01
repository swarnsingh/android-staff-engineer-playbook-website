# Macrobenchmark and Perfetto

## Overview

Macrobenchmark tells you whether a user journey got faster or slower. Perfetto tells you why. Staff-level performance work needs both.

Use Macrobenchmark to repeatedly measure startup, scrolling, and critical interactions in release-like conditions. Use Perfetto/system traces to inspect frames, threads, scheduling, binder calls, GC, GPU work, and app-defined trace sections.

## Macrobenchmark vs Microbenchmark

| Tool | Measures | Use for | Avoid for |
|---|---|---|---|
| Macrobenchmark | Whole app journey from outside the process | Startup, scroll, frame timing, compilation effects | Pure algorithm throughput |
| Microbenchmark | Small code path inside process | Parser, mapper, serializer, allocation hot path | UI jank or startup |
| JankStats | Field frame telemetry | Real-user monitoring | Local root cause alone |
| Perfetto | System trace | Explaining a regression | Stable pass/fail threshold by itself |

## Benchmark Module Shape

Macrobenchmarks live in a separate test module that launches the target app like a user would.

```kotlin
@LargeTest
@RunWith(AndroidJUnit4::class)
class StartupBenchmark {
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()

    @Test
    fun coldStartup() = benchmarkRule.measureRepeated(
        packageName = TARGET_PACKAGE,
        metrics = listOf(StartupTimingMetric()),
        iterations = 10,
        startupMode = StartupMode.COLD
    ) {
        pressHome()
        startActivityAndWait()
    }
}
```

Use enough iterations to reduce noise. Do not chase tiny differences from one run.

## Frame Timing Benchmark

```kotlin
@Test
fun feedScroll() = benchmarkRule.measureRepeated(
    packageName = TARGET_PACKAGE,
    metrics = listOf(FrameTimingMetric()),
    iterations = 5,
    setupBlock = {
        pressHome()
        startActivityAndWait()
        device.waitForIdle()
    }
) {
    val list = device.findObject(By.res(TARGET_PACKAGE, "feed_list"))
    list.fling(Direction.DOWN)
    device.waitForIdle()
}
```

Benchmark the journey users actually feel:

- First feed load.
- Scroll through media-heavy content.
- Open detail from list.
- Type in search.
- Checkout submit.
- Camera preview start.

## Compilation Modes

Compilation mode changes what you are measuring.

| Mode | Use when | Meaning |
|---|---|---|
| `CompilationMode.None()` | Worst-case JIT/cold path analysis | No precompilation |
| `CompilationMode.Partial()` | Baseline profile validation | Common production-like mode |
| `CompilationMode.Full()` | Upper bound for compiled code | Not representative of normal install path |
| `CompilationMode.Ignore()` | You control compilation separately | Advanced benchmarking workflows |

If you generate Baseline Profiles, benchmark both with and without them at least once so the team knows the profile's value.

## Perfetto Trace Workflow

Macrobenchmark produces trace files for iterations. Open the trace when the number changes.

Trace-reading order:

1. Identify the measured time window.
2. Find slow or frozen frames.
3. Inspect Main thread around those frames.
4. Check RenderThread and GPU track.
5. Look for app trace sections.
6. Check binder calls, disk IO, GC, image decode, and scheduler gaps.
7. Confirm whether work belongs to app code, framework, or system pressure.

Do not start with a random search for "Compose." Start with the frame or startup interval that regressed.

## Custom Trace Sections

Use trace sections around app-owned expensive work.

```kotlin
trace("FeedRepository.toUiModels") {
    rows.map { it.toUiModel() }
}
```

For coroutines:

```kotlin
suspend fun loadFeed() = trace("Feed/load") {
    withContext(ioDispatcher) {
        api.fetchFeed()
    }
}
```

Names should be stable and product-readable:

- `Checkout/validateCart`
- `Feed/imageDecode`
- `Search/renderResults`
- `Outbox/drainBatch`

Avoid IDs or PII in trace names.

## Startup Metrics

Startup is not one number.

| Metric | Meaning | Common cause |
|---|---|---|
| Time to initial display | First frame with app UI | Application init, first Activity, theme, main thread |
| Time to full display | Content actually ready | network/cache, first query, image load |
| First frame jank | Early UI missed deadlines | heavy composition/layout/draw |
| Startup CPU | CPU saturation during launch | DI graph, reflection, JSON, database open |

Call `reportFullyDrawn()` when the screen is meaningfully ready. Otherwise "startup" can look fast while users stare at placeholders.

## CI and Regression Policy

Good CI policy:

- Runs on pinned physical devices.
- Uses release-like variant.
- Stores raw JSON and traces as artifacts.
- Compares against rolling baseline.
- Uses tolerance bands and repeated failures before paging.
- Segments startup and scroll thresholds by device tier.

Bad CI policy:

- Uses emulator numbers as product truth.
- Fails every PR on noisy one-off variance.
- Hides traces, only shows a red number.
- Benchmarks debug builds.

## Device Selection

Use at least:

- Low-end supported device.
- Mid-tier high-volume device.
- High-refresh device if your users have them.
- Tablet/foldable for adaptive UI journeys.

Performance budgets should be tied to the lowest device tier you promise, not the developer's flagship phone.

## Common Failure Modes

- Benchmark interacts with unstable network data.
- Test app uses debug build or missing R8.
- Benchmark starts in a dirty app state.
- UIAutomator selector is brittle.
- Trace contains no app-defined sections.
- Metrics improve because content did not load.
- Baseline profile benchmark never validates scroll path.
- Team optimizes p50 and ignores p95/p99.

## Staff Engineer Review Checklist

- Is each benchmark tied to a named product journey?
- Is the build release-like and profileable?
- Are Baseline Profiles installed and measured?
- Are traces retained as CI artifacts?
- Does every regression include a trace analysis?
- Are custom trace sections placed around app-owned work?
- Are thresholds segmented by device tier and form factor?
- Are results stable enough to gate CI without noise?
- Does the benchmark validate that real content loaded?
- Is field telemetry used to choose benchmark journeys?

## Further Reading

- [Android Developers: Write a Macrobenchmark](https://developer.android.com/topic/performance/benchmarking/macrobenchmark-overview)
- [Android Developers: System tracing overview](https://developer.android.com/topic/performance/tracing)
- [Perfetto documentation](https://perfetto.dev/docs/)
- [`jank.md`](jank.md) - frame deadlines and jank.
- [`baseline-profiles.md`](baseline-profiles.md) - profile-guided startup and runtime speed.
