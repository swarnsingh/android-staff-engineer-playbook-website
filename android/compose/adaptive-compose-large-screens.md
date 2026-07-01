# Adaptive Compose and Large Screens

## Overview

Adaptive Compose is not "tablet support." It is the discipline of building one product model that can render well across phones, foldables, tablets, desktop windowing, ChromeOS, external displays, and multi-window.

A Staff engineer's job is to make the app resilient to changing window size, posture, input mode, density, font scale, and lifecycle while preserving navigation correctness and state.

## First Principles

| Axis | What changes | Staff-level risk |
|---|---|---|
| Window size | Width and height can change continuously | Recreating navigation or losing scroll/detail state |
| Posture | Foldables can be flat, half-open, tabletop, or book-like | Content hidden under hinge or split in the wrong place |
| Input | Touch, mouse, keyboard, trackpad, stylus | Controls are reachable but not efficient |
| Density/font scale | More pixels does not mean more readable content | Text clipping, cramped controls, broken hit targets |
| Multi-window | Activity can be resized while running | Assuming portrait phone dimensions forever |
| External displays | Display metrics and window ownership can differ | UI tied to device screen instead of app window |

Adaptive UI should respond to the current window, not to device names.

## Window Size Classes

Use window size classes for broad layout decisions, then use local constraints for fine-grained placement.

```kotlin
@Composable
fun InboxRoute(
    viewModel: InboxViewModel,
    windowSizeClass: WindowSizeClass
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    when (windowSizeClass.windowWidthSizeClass) {
        WindowWidthSizeClass.Compact -> InboxCompact(state, viewModel::onAction)
        WindowWidthSizeClass.Medium -> InboxMedium(state, viewModel::onAction)
        WindowWidthSizeClass.Expanded -> InboxExpanded(state, viewModel::onAction)
    }
}
```

Window size class is a policy input. It should not replace layout constraints inside reusable components.

```kotlin
@Composable
fun MessageCard(message: Message, modifier: Modifier = Modifier) {
    BoxWithConstraints(modifier) {
        val showMetadataInline = maxWidth >= 360.dp
        MessageCardContent(
            message = message,
            showMetadataInline = showMetadataInline
        )
    }
}
```

Rule: use window classes for screen architecture; use constraints for component internals.

## Canonical Layout Patterns

| Pattern | Use when | Example |
|---|---|---|
| List-detail | A collection item opens persistent detail | Email, settings, tickets |
| Supporting pane | Secondary content enriches primary content | Map + place details, editor + outline |
| Feed | Content remains single primary stream | News, social, marketplace |
| Grid | Items benefit from parallel scanning | Photos, catalog, dashboards |
| Navigation rail/drawer | Destinations need persistent access | Admin/productivity apps |

Do not create a custom adaptive pattern before evaluating canonical layouts. Custom layouts are expensive to test across posture, multi-window, accessibility, and state restoration.

## Navigation Architecture

Large screens often expose two destinations at once. That does not mean you have two independent app states.

```kotlin
data class InboxUiState(
    val messages: List<MessageSummary>,
    val selectedMessageId: MessageId?,
    val detail: MessageDetail?
)
```

Compact layout:

```text
Inbox list -> navigate to detail screen
```

Expanded layout:

```text
Inbox list | selected detail pane
```

Same state, different rendering.

Avoid encoding layout into routes:

```text
Bad:
/tablet/inbox/detail/123
/phone/inbox/detail/123

Better:
/inbox/detail/123
```

The route should represent product state. The layout decides whether that state renders as one pane or two panes.

## State Preservation

Adaptive transitions must preserve:

- Selected item.
- Scroll position in each pane.
- Text input state.
- Nested navigation back stacks.
- Pending effects and dialogs.

Use stable IDs and save state at the owner that survives the transition.

```kotlin
class InboxViewModel(
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    private var selectedMessageId: String?
        get() = savedStateHandle["selectedMessageId"]
        set(value) {
            savedStateHandle["selectedMessageId"] = value
        }

    fun selectMessage(id: String) {
        selectedMessageId = id
    }
}
```

Keep this boring in production. `rememberSaveable`, `SavedStateHandle`, navigation saved state, and stable IDs are usually enough. Use custom savers only when a real state object cannot be represented by primitives or parcelables.

## Foldables and Hinges

Foldables introduce display features that can split the available area. A hinge can be:

- A physical occlusion.
- A posture signal.
- A natural boundary for panes.

Staff-level guidance:

- Do not place critical controls under or across a hinge.
- Treat posture as a layout input, not a navigation input.
- Test half-open and tabletop modes for media, camera, video call, maps, and editor flows.
- Keep touch targets away from awkward physical seams.

Decision pattern:

```kotlin
data class AdaptiveLayoutInfo(
    val widthClass: WindowWidthSizeClass,
    val heightClass: WindowHeightSizeClass,
    val hasSeparatingFold: Boolean
)

fun AdaptiveLayoutInfo.shouldUseTwoPane(): Boolean =
    widthClass != WindowWidthSizeClass.Compact && !hasSeparatingFold
```

If a separating fold exists, prefer placing panes on each side only when the product experience naturally maps to that split.

## Input Modes

Large screens often come with keyboards, mice, and trackpads.

Minimum expectations:

- Focus traversal is predictable.
- Keyboard shortcuts exist for high-frequency workflows.
- Hover and right-click affordances do not hide required actions.
- Drag-and-drop supports common file/content workflows where relevant.
- Touch targets remain usable even when mouse density is high.

Compose focus should be designed, not incidental.

```kotlin
val titleRequester = remember { FocusRequester() }

TextField(
    value = state.title,
    onValueChange = onTitleChange,
    modifier = Modifier
        .focusRequester(titleRequester)
        .focusProperties {
            next = bodyRequester
        }
)
```

## Testing Matrix

| Scenario | What to verify |
|---|---|
| Compact portrait | Single-pane navigation, bottom navigation, back stack |
| Compact landscape | Height constraints, keyboard overlap, scrollability |
| Medium width | Rail vs bottom bar, list-detail thresholds |
| Expanded width | Two-pane state, detail placeholder, navigation drawer/rail |
| Multi-window resize | No process restart assumptions, no lost form state |
| Fold posture change | Content avoids hinge, no duplicate navigation |
| Large font | Text wraps, buttons remain usable, no clipped controls |
| Keyboard/mouse | Focus traversal and shortcuts |
| Process death | Selected item and route restore |

## Production Failure Modes

- Tablet branch forks business logic instead of only layout.
- Navigation route includes device class.
- Detail pane has no empty state when nothing is selected.
- Selection disappears when width changes.
- `LocalConfiguration.current.screenWidthDp` is used everywhere instead of window-aware APIs.
- A list item click both selects detail and pushes a detail route on expanded screens.
- Landscape compact height is ignored.
- Large font turns a two-pane layout into clipped, unreadable panels.
- Pointer/keyboard users cannot reach overflow actions.

## Staff Engineer Review Checklist

- Is the domain state shared across compact and expanded layouts?
- Are window size classes used for screen-level architecture only?
- Are component decisions based on local constraints?
- Does back behavior remain product-correct across one-pane and two-pane modes?
- Are selected IDs stable across resize, rotation, and process death?
- Does the UI handle no-selection and deleted-selection states?
- Are fold features treated as constraints, not device names?
- Is keyboard and pointer input part of the acceptance criteria?
- Does QA test resize, multi-window, font scale, and fold posture?
- Are metrics segmented by window class/form factor?

## Further Reading

- [Android Developers: Get started with adaptive apps](https://developer.android.com/develop/ui/compose/layouts/adaptive)
- [Android Developers: Window size classes](https://developer.android.com/develop/ui/compose/layouts/adaptive/use-window-size-classes)
- [Android Developers: Canonical layouts](https://developer.android.com/develop/ui/compose/layouts/adaptive/canonical-layouts)
- [`compose-navigation.md`](compose-navigation.md) - route ownership and navigation boundaries.
- [`process-death-and-state-restoration.md`](../architecture/process-death-and-state-restoration.md) - durable UI state.
