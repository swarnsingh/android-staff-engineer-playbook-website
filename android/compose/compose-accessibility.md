# Compose Accessibility

## Overview

Accessibility is part of UI correctness. A screen that is visually polished but unusable with TalkBack, large text, switch access, keyboard, or reduced motor precision is not complete.

Compose gives strong defaults through semantics, but custom components, complex layouts, canvases, and animated state require explicit design.

## Accessibility Model

Compose exposes a semantics tree to accessibility services and tests. Semantics describe what UI means:

- Text/content description.
- Role.
- State.
- Actions.
- Selection.
- Error.
- Heading.
- Traversal order.

The semantics tree is not the same as the composition tree. Decorative nodes can be hidden. Child nodes can be merged into one accessible element.

## Use Built-In Components First

Material components usually provide correct roles, states, and touch target behavior.

```kotlin
Button(onClick = onSubmit) {
    Text("Submit")
}
```

If you build a clickable `Box` instead, you own the missing semantics:

```kotlin
Box(
    modifier = Modifier
        .minimumInteractiveComponentSize()
        .semantics {
            role = Role.Button
            contentDescription = "Submit"
        }
        .clickable(onClick = onSubmit)
)
```

Prefer the built-in component unless product requirements truly need a custom surface.

## Content Descriptions

Content descriptions should identify purpose, not pixels.

```kotlin
Icon(
    imageVector = Icons.Default.Delete,
    contentDescription = "Delete message"
)
```

Decorative images should pass `null` so they are ignored by accessibility services.

```kotlin
Icon(
    imageVector = Icons.Default.ChevronRight,
    contentDescription = null
)
```

Do not repeat visible text as content description unless needed. TalkBack already reads text nodes.

## Merging Semantics

Use merged semantics when several visual children form one logical control.

```kotlin
Row(
    modifier = Modifier
        .clickable(onClick = onOpen)
        .semantics(mergeDescendants = true) {
            role = Role.Button
        }
) {
    Icon(Icons.Default.Email, contentDescription = null)
    Column {
        Text(message.sender)
        Text(message.subject)
    }
}
```

Use `clearAndSetSemantics` when child semantics would be misleading.

```kotlin
Canvas(
    modifier = Modifier.clearAndSetSemantics {
        contentDescription = "Storage used: 74 percent"
        progressBarRangeInfo = ProgressBarRangeInfo(
            current = 0.74f,
            range = 0f..1f
        )
    }
) {
    drawArc(...)
}
```

## State and Error Semantics

Expose state transitions explicitly.

```kotlin
Switch(
    checked = enabled,
    onCheckedChange = onEnabledChange,
    modifier = Modifier.semantics {
        stateDescription = if (enabled) "Enabled" else "Disabled"
    }
)
```

For form errors:

```kotlin
OutlinedTextField(
    value = email,
    onValueChange = onEmailChange,
    isError = emailError != null,
    supportingText = {
        if (emailError != null) Text(emailError)
    },
    modifier = Modifier.semantics {
        if (emailError != null) error(emailError)
    }
)
```

Errors should be reachable, announced at the right time, and tied to the field or action that caused them.

## Traversal and Focus

Visual order, focus order, and accessibility traversal should usually match.

Use traversal groups for complex panes:

```kotlin
Column(
    modifier = Modifier.semantics {
        isTraversalGroup = true
    }
) {
    Header()
    Content()
    Actions()
}
```

Design keyboard focus separately from TalkBack traversal when workflows require it.

```kotlin
Modifier.focusProperties {
    next = nextFieldRequester
    previous = previousFieldRequester
}
```

## Large Text and User-Scalable Content

Large font support is not optional.

Review:

- Text wraps instead of clipping.
- Buttons can grow vertically.
- Icon-only controls still have accessible names.
- Two-pane layouts degrade when text scale makes panes too cramped.
- Dialogs scroll when content exceeds height.
- Important actions remain reachable without overlapping.

Avoid hard-coded heights around text-heavy content.

```kotlin
Button(
    onClick = onClick,
    modifier = Modifier.defaultMinSize(minHeight = 48.dp)
) {
    Text(text = label, maxLines = 2)
}
```

## Touch Targets

Small visual elements can still have large hit targets.

```kotlin
IconButton(onClick = onClose) {
    Icon(Icons.Default.Close, contentDescription = "Close")
}
```

If building custom controls, preserve minimum interactive size:

```kotlin
Modifier
    .minimumInteractiveComponentSize()
    .clickable(onClick = onClick)
```

## Live Regions

Use live regions for important dynamic changes that should be announced.

```kotlin
Text(
    text = snackbarMessage,
    modifier = Modifier.semantics {
        liveRegion = LiveRegionMode.Polite
    }
)
```

Do not overuse live regions. Too many announcements make the app noisy and unusable.

## Testing

Compose tests can assert semantics:

```kotlin
composeTestRule
    .onNodeWithContentDescription("Delete message")
    .assertHasClickAction()
```

Add accessibility checks for:

- Missing labels.
- Touch target size.
- Duplicate confusing descriptions.
- Traversal order.
- Large text screenshots.
- TalkBack manual scripts for critical flows.

For Compose semantics, enable checks with `composeTestRule.enableAccessibilityChecks()` and invoke them at a stable UI state with `composeTestRule.onRoot().tryPerformAccessibilityChecks()` on supported Android API levels. Espresso's `AccessibilityChecks.enable()` inspects View hierarchies, so reserve it for View-based or Compose/View interoperability tests rather than treating it as Compose coverage.

Automated checks catch classes of bugs. They do not replace using the app with assistive technologies.

## Production Failure Modes

- Icon buttons with `contentDescription = null`.
- Decorative images announced as "image."
- Custom cards clickable but missing role.
- Text clipped at font scale 1.3 or 2.0.
- Canvas charts with no semantic equivalent.
- Error text visible but not tied to field semantics.
- Traversal jumps between panes unpredictably.
- Merged semantics hide required child actions.
- Touch target matches icon size instead of control size.

## Staff Engineer Review Checklist

- Are built-in accessible components used where possible?
- Does every icon-only action have an accessible name?
- Are decorative visuals hidden from accessibility services?
- Are custom components assigned role, state, and actions?
- Are complex rows merged into logical announcements?
- Do forms expose errors semantically?
- Does large text work without clipping or overlap?
- Does keyboard focus order match workflow?
- Are critical flows manually tested with TalkBack?
- Are accessibility checks part of CI or release qualification?

## Further Reading

- [Android Developers: Accessibility in Jetpack Compose](https://developer.android.com/develop/ui/compose/accessibility)
- [Android Developers: Semantics in Compose](https://developer.android.com/develop/ui/compose/accessibility/semantics)
- [Android Developers: Test accessibility in Compose](https://developer.android.com/develop/ui/compose/accessibility/testing)
- [`custom-layout-measurement.md`](custom-layout-measurement.md) - preserving semantics in custom layouts.
- [`adaptive-compose-large-screens.md`](adaptive-compose-large-screens.md) - adaptive layouts with large text and input modes.
