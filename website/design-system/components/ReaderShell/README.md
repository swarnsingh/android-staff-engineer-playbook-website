# ReaderShell

The shared reader's page layout, teaching primitives, reading preferences, sequence styling, learning paths and navigation live here. The build emits the established `styles.css`, `blend.css`, `theme.css`, `sequence.css`, `learning-path.css` and `navigation.css` URLs from these sources.

Dimensions, typography, timing, opacity and breakpoints are owned by `componentCss` in `design-system/tokens.json`. A source declaration such as `padding: {{reader-theme-main-sheet-pad}}` expands at build time through `scripts/design_tokens.py`; the emitted CSS keeps its original value, relative unit, variable reference and cascade position. Use the token's name and `usage` selector to find its owner. Existing shared colour and type variables continue to work normally.

Build-time expansion is deliberate: a composite value containing `var(--actor)` or another local custom property must resolve on its consuming element. A custom property defined on the root resolves its references before inheritance, which would change that behavior. See the [CSS Variables specification](https://www.w3.org/TR/css-variables-1/#cycles). Media-query breakpoints use the same build-time tokens.

The build rejects unknown macros and raw component dimensions. Structural zeroes, full-size percentages and single fractional tracks remain literal. Column counts, timeline positions and component state selectors are content parameters rather than design defaults. Lessons contribute these declared parameters and text; they do not supply styles.

The design-system gallery and every real lesson consume the emitted bundles. The November token extraction preserves all seven compiled stylesheet sources byte-for-byte, including the FigureMap section in `bundle.css`. Shared frame, theme, navigation and full-site audits verify the consuming pages.
