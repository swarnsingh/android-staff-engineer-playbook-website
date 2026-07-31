# Greedy Algorithms and Intervals

## Overview

A **greedy algorithm** makes the locally best choice at each step and never revisits it. An **interval problem** deals with ranges: time windows, byte ranges, screen spans, cache TTLs, booking slots, media segments, rollout windows, or analytics sessions.

Greedy algorithms are powerful when the local choice can be proven safe. They are dangerous when they merely "feel right." Staff engineers use greedy thinking constantly in scheduling, caching, batching, rate limiting, media buffering, and release windows.

---

## Why It Matters

1. **Mobile systems are full of intervals.** Sessions, timeouts, sync windows, video segments, calendar events, geofences, and staged rollouts.
2. **Greedy is often the production choice.** It is simple, fast, explainable, and memory-light.
3. **Correctness needs proof.** A greedy algorithm without a correctness argument is a bug with confidence.
4. **Line sweep scales.** Many range-overlap problems become sorting plus a single pass.

---

## Greedy First Principles

Greedy works when:

- **Greedy-choice property:** a locally optimal choice can be part of a globally optimal solution.
- **Optimal substructure:** after making that choice, the remaining problem has the same shape.

Classic example: activity selection. To schedule the maximum number of non-overlapping intervals, always pick the interval that ends earliest.

Why? Ending earliest leaves the most remaining room for future intervals. Any optimal solution that picks a later-ending first interval can swap in the earlier-ending interval without reducing the number of future intervals.

That swap argument is the proof.

---

## Interval Representation

Use half-open intervals for most engineering systems:

```text
[start, end)
```

This means start is included, end is excluded. Benefits:

- Adjacent intervals do not overlap: `[10, 20)` and `[20, 30)`.
- Duration is `end - start`.
- Empty interval is `[x, x)`.

```kotlin
data class Interval(
    val start: Long,
    val end: Long
) {
    init {
        require(start <= end)
    }

    fun overlaps(other: Interval): Boolean =
        start < other.end && other.start < end
}
```

---

## Core Patterns

### Merge Overlapping or Adjacent Intervals

```kotlin
fun mergeIntervals(input: List<Interval>): List<Interval> {
    if (input.isEmpty()) return emptyList()

    val sorted = input.sortedWith(compareBy<Interval> { it.start }.thenBy { it.end })
    val result = mutableListOf<Interval>()
    var current = sorted.first()

    for (next in sorted.drop(1)) {
        if (current.end >= next.start) {
            current = Interval(current.start, maxOf(current.end, next.end))
        } else {
            result += current
            current = next
        }
    }
    result += current
    return result
}
```

For half-open intervals, `current.end == next.start` means the intervals touch but do not overlap. Many systems still coalesce them because the combined interval has no gap. Use strict `current.end > next.start` if product policy must preserve adjacency.

Use for availability windows, cached byte ranges, offline map regions, media buffered segments, and rollout schedules.

### Maximum Non-Overlapping Intervals

```kotlin
fun maxNonOverlapping(intervals: List<Interval>): List<Interval> {
    val sorted = intervals.sortedBy { it.end }
    val result = mutableListOf<Interval>()
    var lastEnd = Long.MIN_VALUE

    for (interval in sorted) {
        if (interval.start >= lastEnd) {
            result += interval
            lastEnd = interval.end
        }
    }
    return result
}
```

Greedy by earliest finish time.

### Minimum Rooms / Concurrent Intervals

Line sweep:

```kotlin
fun maxConcurrent(intervals: List<Interval>): Int {
    val events = mutableListOf<Pair<Long, Int>>()
    for (i in intervals) {
        events += i.start to 1
        events += i.end to -1
    }

    val sorted = events.sortedWith(
        compareBy<Pair<Long, Int>> { it.first }
            .thenBy { it.second } // end (-1) before start (+1) for half-open intervals
    )

    var active = 0
    var maxActive = 0
    for ((_, delta) in sorted) {
        active += delta
        maxActive = maxOf(maxActive, active)
    }
    return maxActive
}
```

Use for maximum concurrent sessions, overlapping uploads, calendar rooms, visible media windows, and resource planning.

### Jump Game Greedy

```kotlin
fun canReachEnd(maxJump: IntArray): Boolean {
    var farthest = 0
    for (i in maxJump.indices) {
        if (i > farthest) return false
        farthest = maxOf(farthest, i + maxJump[i])
    }
    return true
}
```

The greedy state is "farthest reachable index so far." You do not need all paths.

---

## Mobile Examples

### Media Buffer Ranges

Video players track buffered byte/time ranges. Merging intervals prevents duplicated network requests and lets the UI answer "is time T buffered?"

### Analytics Sessions

Sessionization is interval logic:

- User foregrounds at `t1`.
- Backgrounds at `t2`.
- If gap before next foreground is less than threshold, merge.
- Otherwise create a new session.

### Offline Map Tiles

Downloaded map regions overlap. Merging bounding/time ranges avoids redownloading identical tile windows.

### Staged Rollouts

Rollouts are time and cohort intervals. You need explicit overlap rules to avoid two experiments or two remote-config policies fighting over the same users.

---

## Greedy vs Dynamic Programming

| Question | Greedy | DP |
|---|---|---|
| Choice | Local best once | Explore reusable states |
| Speed | Usually O(n log n) or O(n) | Often O(n*m) or more |
| Memory | Low | Can be high |
| Proof | Exchange/cut argument | Recurrence correctness |
| Risk | Local choice may be wrong | State explosion |

If greedy is correct, it is usually preferred in production. If the local choice cannot be proven safe, consider DP or search.

---

## Failure Modes

| Failure | Cause | Fix |
|---|---|---|
| Off-by-one overlap | Mixing closed and half-open intervals | Standardize on `[start, end)` |
| Wrong greedy choice | Chose earliest start instead of earliest end | Prove with exchange argument |
| Double-count concurrency | Start processed before end at same timestamp | Tie-break end before start |
| Timezone bugs | Local time intervals across DST | Store instants; render local |
| O(n^2) overlap checks | Comparing every interval pair | Sort + sweep |
| Unclear product policy | "Overlap" not defined for edge contact | Document interval semantics |

---

## Staff Engineer Thinking

1. **Define interval semantics first.** Closed, open, or half-open? Timezone? Units?
2. **Require a greedy proof.** "Seems optimal" is not enough.
3. **Sort once, scan once.** Many interval problems are O(n log n) because of sorting, then O(n).
4. **Use line sweep for concurrency.** It scales and produces explainable metrics.
5. **Tie algorithm to product policy.** Adjacent sessions, overlapping experiments, and cached ranges are business decisions too.

---

## Probing Questions

1. Why are half-open intervals easier to reason about?
2. How do you test whether two intervals overlap?
3. Why does earliest-end greedy solve maximum non-overlapping intervals?
4. How does line sweep compute maximum concurrency?
5. What tie-breaker is needed when one interval ends exactly when another starts?
6. When is greedy unsafe and DP required?
7. How would you merge buffered video ranges?
8. How can timezone handling break interval logic?

## Answer Key

1. **Why are half-open intervals easier to reason about?**
   They prevent adjacent intervals from artificially overlapping, the duration is simply calculated as `end - start`, and empty intervals are cleanly represented as `[x, x)`.
2. **How do you test whether two intervals overlap?**
   For two intervals `A` and `B`, they overlap if `A.start < B.end` and `B.start < A.end`.
3. **Why does earliest-end greedy solve maximum non-overlapping intervals?**
   Picking the interval that finishes earliest mathematically leaves the maximum amount of remaining time/space available for subsequent intervals.
4. **How does line sweep compute maximum concurrency?**
   By flattening intervals into discrete start (+1) and end (-1) events, sorting them chronologically, and keeping a running sum of active intervals as you iterate.
5. **What tie-breaker is needed when one interval ends exactly when another starts?**
   For half-open intervals, process end events (-1) before start events (+1) at the exact same timestamp to avoid momentarily double-counting concurrency.
6. **When is greedy unsafe and DP required?**
   When making a locally optimal choice locks you out of a globally optimal combination (e.g., in the knapsack problem, picking the best value-to-weight ratio first might leave unusable wasted space).
7. **How would you merge buffered video ranges?**
   Sort the ranges by their start times, then iterate through and merge the current range with the next if `current.end >= next.start`.
8. **How can timezone handling break interval logic?**
   Wall-clock time intervals can overlap or have gaps during Daylight Saving Time transitions; logic should always execute using absolute UTC instants.

## Further Reading

- [`dynamic-programming.md`](dynamic-programming.md)
- [`sorting-and-searching.md`](sorting-and-searching.md)
- [`../mobile-system-design/youtube-video-streaming.md`](../mobile-system-design/youtube-video-streaming.md)
- [`../mobile-system-design/experimentation-platform.md`](../mobile-system-design/experimentation-platform.md)
