# Content direction: one story, progressively deeper

Status: agreed product direction for design/planning. This document records the owner's requirements; it does not implement or approve a content migration. The current prototype is only a sample adaptation of part of the coroutine chapter.

## The reading experience

Each topic should read as one coherent story. Begin in language a beginner can follow, develop a progressively deeper analysis in the middle, and finish with staff-level engineering reasoning. Accessibility of language must continue as technical depth increases. Do not replace depth with simplification, or equate staff-level writing with jargon.

Keep the same motivating problem or running example through the progression where useful. Each new section should answer a question raised by the previous one. Introduce terms near their first meaningful use and connect an analogy to the real mechanism and its limits.

### Beginning: make the problem understandable

Start with a concrete situation and an observable problem. Establish why the reader should care and link genuinely required prerequisites. Explain the central idea in plain language, introduce essential vocabulary, and offer a small visual model or minimal code example. A beginner should understand what happens and why before encountering implementation internals. Prerequisite links should support learning without turning the chapter into an encyclopedia of every related concept.

### Middle: explain the mechanism in depth

Build on the same problem with progressively richer examples. Explain the mechanism, observable output, relevant internals, edge cases, limitations, and common misconceptions. Expand the diagram or animation as the model grows. Use code blocks that are complete enough for their stated purpose, distinguish runnable examples from pseudocode, and explain important changes between versions. Separate actual execution from illustrative simulations. Use comparisons and tables when the reader needs to choose or contrast alternatives; use bullets for genuinely parallel points or sequences.

### Ending: reason at staff level

Extend the established model into production and system decisions. Depending on the topic, examine ownership and lifetime, failure boundaries, durability, resource budgets, performance, observability, security, testing, operational recovery, rollout, and organisational/API consequences. Select the concerns that actually matter to this topic rather than repeating a generic checklist. State decision criteria, trade-offs, what evidence would support a choice, and when the choice should be revisited. End with an applied scenario or reasoning question that connects back to the opening problem.

## Presentation supports the story

- Prose provides the narrative and explanation.
- Code blocks demonstrate behaviour and show concrete implementation choices.
- Animations explain time, causality, state changes, concurrency, and failure/recovery sequences where those are difficult to see statically.
- Diagrams make ownership, relationships, and boundaries visible.
- Tables compare meaningful alternatives on explicit criteria.
- Bullet points make parallel facts, steps, and checkpoints easier to scan.
- Q&A helps readers retrieve and apply the ideas; answers explain the reasoning.
- Resources support claims and further exploration through appropriate sources.

Do not require every format in every section. Each element must answer a reader's question. Avoid decorative motion, excessive cards, unexplained code dumps, and a wall of bullets. Keep the complete story easy to navigate on phones, tablets, foldables, desktops, and split-screen windows, including enlarged text. Readers should be able to pause or step through teaching animations and learn from an equivalent static/text explanation.

Progressive depth should not be implemented as disconnected beginner/intermediate/staff summaries or a mode switch that hides essential explanations. Short orientation labels and a useful outline may help readers find their place while preserving the continuous chapter.

## Example narrative: coroutines

Opening: a profile screen needs two results while the app remains responsive. Explain a pausable task and a thread in plain language; show a small, accurate example.

Middle: trace suspension and resumption, concurrent work, the parent-child job relationship, cancellation and cleanup, and then introduce the relevant dispatcher/context and compiler mechanisms. Correct the misconception that `suspend` automatically moves blocking work off the main thread. Keep visible behaviour connected to the mechanism throughout.

Ending: decide who owns the screen load, whether optional and required results should fail together, how to observe and test cancellation, and which work needs durability beyond an in-memory scope. Make the trade-offs explicit and connect them to the original screen experience. The exact section sequence should be checked for prerequisite coherence during chapter design.

This is a candidate narrative to review, not a claim that the current sample covers the complete topic.

## Future: narrated visual explanation

A separate Video explanation tab may later offer more extensive animation and voice-over, inspired by the reference channel's explanatory approach. This is future scope. Do not add a non-working tab or start video production during the current planning/draft review. The written lesson, code, diagrams, and interactive explanations should be independently useful. If video is later added, plan captions/transcripts and alignment with the chapter so technical corrections do not leave the two explanations inconsistent.

## What reviewers should assess now

Evaluate how well the current sample demonstrates this intended progression, where the story jumps ahead or loses continuity, whether language remains accessible as depth increases, and which specific code/visual/presentation changes would improve it. Distinguish missing material in the intentionally partial prototype from a proposed production decision to omit depth. Keep suggestions focused on the draft experience; no migration plan, framework selection, or implementation is requested.

## Clarifications applied in draft 02

The repository's `content-rulebook.md` is the current authority for authoring. Necessity must precede unfamiliar machinery: problem/constraint, need, solution, mechanism, result, limits and trade-offs. Preserve real internals through a coverage inventory, deeper sections and verified canonical routes; explicitly record gaps. This is not a rigid format for every topic. System design can instead follow requirements, constraints, request/data journeys, failure scenarios, and design decisions.

Draft 02 demonstrates the coroutine mechanism route. It adds a substantive middle, continuation/state-label pseudocode, observable runnable traces, inline answers, four stepped visual scenarios, and a coverage map. It remains a local sample adaptation, not the complete canonical reference. The original coroutine chapter is unchanged.
