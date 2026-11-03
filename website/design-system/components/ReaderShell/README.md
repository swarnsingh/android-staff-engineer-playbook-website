# ReaderShell

The shared reader's page layout, teaching primitives, reading preferences, sequence styling, learning paths and navigation live here. The build emits the established `styles.css`, `blend.css`, `theme.css`, `sequence.css`, `learning-path.css` and `navigation.css` URLs from these sources. Moving source ownership preserves their exact bytes and URL-relative font paths.

The shared sources consume colour, typography, spacing and layout tokens. Remaining legacy layout constants are being brought into the same token ownership as FigureMap geometry. Lessons contribute content and declared data parameters, including column counts and timeline positions; they do not supply styles.

The design-system gallery and every real lesson consume these emitted bundles. Changes are verified with the shared frame, theme, navigation and full-site audit suites. Source relocation alone does not change reader behavior or visual dimensions.
