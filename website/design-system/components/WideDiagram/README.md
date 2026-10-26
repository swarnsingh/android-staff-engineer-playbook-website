# WideDiagram

A static diagram that keeps a readable size and scrolls sideways inside its own box on narrow screens, instead of shrinking or reflowing.

## When to use

Use it for anything that does not move: redrawn Mermaid diagrams, architecture and module graphs, layer maps and wide comparison grids. Code blocks and tables already scroll the same way.

Do not use it for FlowDiagram or FlowScene. Those need cause and effect on screen together, and a packet must never travel out of view, so they switch to a stacked phone layout instead.

## Rules

- **Readable minimum width.** Give the drawing a `min-width` so that, at that width, labels render at 15px or more and sub-labels at 12px or more: minimum width = viewBox width × target size ÷ authored size, whichever is larger. The preview's graph is 900 units wide with 19-unit labels and 15-unit sub-labels, so it has `min-width: 740px` (labels 15.6px, sub-labels 12.3px). On desktop it fills the sheet without scrolling, up to `max-width` = 1.2 × the viewBox width (1080px here), so labels never grow far past their drawn size.
- **Only the box scrolls.** The page never scrolls sideways. `overscroll-behavior-x: contain` asks the browser to keep a sideways swipe inside the box. Chrome and Firefox honour it; Safari may still treat the swipe as Back or Forward navigation ([WebKit bug 240183](https://bugs.webkit.org/show_bug.cgi?id=240183), open). Treat it as containment where supported, not a guarantee, and test the gesture on a real iPhone before relying on it.
- **Show that there is more.** A soft fade appears on any edge that has hidden content, and a one-line hint ("Scroll sideways to see the whole graph →") shows only while the box actually overflows.
- **Keyboard and screen readers.** Only while the box overflows does the runtime make it a focusable named region (`tabindex="0"`, `role="region"`, `aria-label` = the box's `data-label` + ", scrolls sideways"), so arrow keys scroll it. When the drawing fits, all three are removed and the box is plain content.
- **Text alternative.** The SVG's `aria-label` describes the relationships, not the picture.

## Behaviour

The runtime (`Playbook.WideDiagram`, mounted by `mountAll` on `[data-pb-wide]`) toggles `is-scrollable`, `at-start` and `at-end` as the box scrolls or resizes. These classes drive the fades and the hint.

## Tokens

`sheet-sunken`, `grid-dot`, `sheet`, `line-strong`, `ink`, `ink-muted`, `focus`, `radius-md`.
