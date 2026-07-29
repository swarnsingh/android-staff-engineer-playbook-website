# Topic — As Applied To <System>

## Canonical Owner

Link to the canonical file(s) this application depends on.

Example:
- Mechanics: `../engineering-fundamentals/state-machines.md`
- Idempotency model: `../distributed-systems/idempotency.md`

This file does not re-teach those concepts. If you find yourself explaining what idempotency *is*, stop and link instead.

---

## Context

Which system, which subsystem, which problem inside that system. One paragraph.

---

## Application

How the canonical concept is applied here. Concrete, specific, with diagrams.

Use Mermaid for component and runtime flows. Follow each diagram with the takeaway it proves, and link the primary source when the visual depends on versioned platform behavior.

Include code only if it sharpens the explanation; otherwise, prose and diagrams.

---

## Decisions Made Here

The specific choices made for this application (knob settings, thresholds, library picks). For larger decisions, link to a Decision file co-located with the relevant topic (e.g., `android/data-and-di/room-vs-datastore.md` for a storage choice) rather than re-deriving them inline. See [`decision.md`](decision.md) for the Decision-file template.

---

## Failure Modes Observed

What actually broke or could break in this specific system, distinct from the generic failure modes in the canonical file.

---

## Observability Hooks

The specific metrics, logs, traces, and dashboards used for this application. Link to `observability/` canonical files for the concepts.

---

## Cross-References

Other application files that exercise the same canonical concept, so the reader can compare.
