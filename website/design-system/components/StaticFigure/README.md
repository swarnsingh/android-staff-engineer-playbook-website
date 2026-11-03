# StaticFigure

Existing teaching comparisons and timelines retain their words and grouping while gaining explicit role colours, border patterns, a title, a legend and a numbered caption. Relationship diagrams use FigureMap rather than relying on card order to imply a transfer.

Models live in `website/content/static-figures.json`. Each is bound to the complete source figure's SHA-256, chapter path and figure number. A model declares one role per node; a chart without cards declares its overall role. The renderer rejects missing, stale and mismatched models. Pending local builds may retain unfinished figures; publication may not.

A `map` model supplies explicit endpoint numbers and relationship labels. Its cards are extracted from the existing titles and details and its text version retains those descriptions. Optional groups identify actual logical boundaries. A `comparison` or `timeline` keeps the original HTML structure. No relationship is inferred from adjacency.

All styling is in `components/bundle.css`. Tokens are `static-card-stroke`, `static-card-strong-stroke`, `static-card-double-stroke`, `static-role-tint` and `static-key-tint`, with existing role, figure typography, spacing and surface tokens. Roles follow FigureMap: clients, execution, stored data, queued work and sources/structure. Border patterns and written descriptions retain the meaning without colour.

The migration covers 197 teaching figures: 75 relationship maps and 122 comparisons or timelines. The gallery includes backing-state relationships, a stack/heap comparison and a binding-initialization timeline. The gallery uses actual lesson data; no separate hand-maintained illustration is required.
