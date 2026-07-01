# Custom Layout and Measurement

## Overview

Compose layout is a constraint negotiation. Parents pass constraints down, children choose sizes within those constraints, and parents place children. Custom layouts are powerful because they let you define that negotiation directly.

They are also risky. A bad custom layout can cause clipped content, broken RTL, inaccessible hit targets, poor intrinsic behavior, and frame-time spikes.

## Layout Pipeline

Every layout node goes through three steps:

1. Measure children.
2. Decide its own size.
3. Place children.

Compose enforces an important rule: a child may be measured only once during a measurement pass. If you need more than one measurement strategy, use intrinsic measurements, subcomposition, or a different layout design.

## Constraint Basics

`Constraints` contains:

- `minWidth`
- `maxWidth`
- `minHeight`
- `maxHeight`

Children must return a size inside those bounds. Parents should coerce their own size into incoming constraints.

```kotlin
@Composable
fun BadgeLayout(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
    badge: @Composable () -> Unit
) {
    Layout(
        modifier = modifier,
        content = {
            content()
            badge()
        }
    ) { measurables, constraints ->
        val contentPlaceable = measurables[0].measure(constraints)
        val badgePlaceable = measurables[1].measure(
            constraints.copy(minWidth = 0, minHeight = 0)
        )

        val width = maxOf(
            contentPlaceable.width,
            contentPlaceable.width + badgePlaceable.width / 2
        ).coerceIn(constraints.minWidth, constraints.maxWidth)

        val height = maxOf(
            contentPlaceable.height,
            badgePlaceable.height
        ).coerceIn(constraints.minHeight, constraints.maxHeight)

        layout(width, height) {
            contentPlaceable.placeRelative(0, 0)
            badgePlaceable.placeRelative(
                x = width - badgePlaceable.width,
                y = 0
            )
        }
    }
}
```

## `Modifier.layout`

Use `Modifier.layout` when one child needs custom measurement or placement.

```kotlin
fun Modifier.firstBaselineToTop(firstBaselineToTop: Dp) =
    layout { measurable, constraints ->
        val placeable = measurable.measure(constraints)
        val firstBaseline = placeable[FirstBaseline]
        check(firstBaseline != AlignmentLine.Unspecified)

        val placeableY = firstBaselineToTop.roundToPx() - firstBaseline
        val height = placeable.height + placeableY

        layout(placeable.width, height) {
            placeable.placeRelative(0, placeableY)
        }
    }
```

This is ideal for custom padding, alignment, offsets, and baseline-aware text placement.

## `Layout`

Use `Layout` when you need to measure and place multiple children.

```kotlin
@Composable
fun OverlappingRow(
    overlap: Dp,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    Layout(modifier = modifier, content = content) { measurables, constraints ->
        val overlapPx = overlap.roundToPx()
        val placeables = measurables.map { measurable ->
            measurable.measure(constraints.copy(minWidth = 0, minHeight = 0))
        }

        val width = placeables.foldIndexed(0) { index, acc, placeable ->
            acc + placeable.width - if (index == 0) 0 else overlapPx
        }.coerceIn(constraints.minWidth, constraints.maxWidth)

        val height = placeables.maxOfOrNull { it.height }
            ?.coerceIn(constraints.minHeight, constraints.maxHeight)
            ?: constraints.minHeight

        layout(width, height) {
            var x = 0
            placeables.forEachIndexed { index, placeable ->
                placeable.placeRelative(x, 0)
                x += placeable.width - if (index == 0) 0 else overlapPx
            }
        }
    }
}
```

## Intrinsic Measurements

Intrinsic measurements answer questions like "how tall would this be at a given width?" before normal measurement.

Use them sparingly:

- Baseline alignment.
- Text-heavy custom layouts.
- Components that must size relative to sibling intrinsic dimensions.

Avoid using intrinsics as a way to measure children twice. Intrinsics can be expensive and can hide unclear layout contracts.

## SubcomposeLayout

Use `SubcomposeLayout` when content to compose depends on measured constraints or previous measurement results.

Common use cases:

- Lazy layouts.
- Tabs/indicators dependent on measured tab sizes.
- Tooltips/popups anchored to measured content.
- Layouts that need to choose different child composition after measuring available space.

Staff warning: `SubcomposeLayout` is advanced. It can add composition work during layout, which makes performance harder to reason about. Reach for it only when ordinary `Layout`, `BoxWithConstraints`, or canonical layout primitives cannot express the requirement.

## Lookahead and Animated Layout

Lookahead APIs can help animate layout changes by knowing target layout positions. Use them for polished transitions where size/position changes are part of the product experience.

Do not use lookahead to paper over unstable state or constantly changing constraints. If every frame recomputes a complex layout, animation will amplify the cost.

## RTL and Layout Direction

Prefer `placeRelative` for directional layouts. Use `place` only when absolute positioning is correct regardless of RTL.

```kotlin
layout(width, height) {
    icon.placeRelative(0, 0)
    text.placeRelative(icon.width + spacing, 0)
}
```

Review custom layouts with Arabic/Hebrew locales and with mirrored icons where appropriate.

## Accessibility and Hit Targets

Custom measurement can accidentally shrink semantics bounds or touch targets.

Checklist:

- Minimum touch target is preserved.
- Semantics describe the merged component, not each decorative child.
- Traversal order matches visual order.
- Focus bounds match visible content.
- Large font does not clip text.

```kotlin
Modifier
    .minimumInteractiveComponentSize()
    .semantics(mergeDescendants = true) {
        role = Role.Button
    }
```

## Performance Failure Modes

- Measuring expensive text or images in custom layout without caching upstream.
- Allocating large collections on every measure pass.
- Reading mutable state in measure that changes every frame.
- Using `SubcomposeLayout` for simple conditional UI.
- Ignoring `contentType` in lazy custom item systems.
- Violating constraints and relying on clipping side effects.
- Using absolute `place` when `placeRelative` is needed.

## Testing Custom Layouts

Test custom layouts with:

- Compact and expanded widths.
- RTL layout direction.
- Font scale 1.3 and 2.0.
- TalkBack semantics inspection.
- Screenshot tests for representative constraints.
- Macrobenchmark for animated or scrolling layouts.

Compose UI tests can assert positions for critical layout contracts:

```kotlin
composeTestRule
    .onNodeWithTag("badge")
    .assertIsDisplayed()
```

For pixel-perfect layout, screenshot tests are more useful than broad semantic assertions.

## Staff Engineer Review Checklist

- Is a custom layout actually necessary?
- Is each child measured exactly once?
- Are constraints respected and coerced?
- Is `placeRelative` used where direction matters?
- Are intrinsics justified and tested?
- Is subcomposition avoided unless measurement must drive composition?
- Does the layout survive large font and RTL?
- Are semantics and touch targets correct?
- Is allocation inside measure/layout minimal?
- Is the layout benchmarked if it appears in scrolling or animation paths?

## Further Reading

- [Android Developers: Custom layouts](https://developer.android.com/develop/ui/compose/layouts/custom)
- [Android Developers: Intrinsic measurements](https://developer.android.com/develop/ui/compose/layouts/intrinsic-measurements)
- [Android Developers: Alignment lines](https://developer.android.com/develop/ui/compose/layouts/alignment-lines)
- [`modifiers-and-layout.md`](modifiers-and-layout.md) - layout modifier fundamentals.
- [`compose-performance-tooling.md`](compose-performance-tooling.md) - measuring layout cost.
