# <System Class> — Reference Architecture

## Requirements

Functional and non-functional requirements that shape this architecture.

## Architecture

The high-level architecture. Diagram-first. Show the system boundary and ownership, then state the takeaway in text. Validate platform-specific behavior against a primary source.

## Modules

The major modules and their responsibilities.

## Data Flow

How data moves through the system end-to-end. Mermaid sequence diagrams preferred. Keep retries, duplicate handling, offline behavior, and failure paths consistent with the prose.

## Offline Strategy

How the system behaves when the network is degraded or absent.

## Security

Threat model and mitigations specific to this class of system.

## Observability

What is measured. What pages whom. Link to `observability/` canonical files.

## Failure Modes

What can break, how it's detected, how it's recovered.

## Scaling

How this architecture scales — both up (load) and out (new tenants/features).

## Release Strategy

How changes are rolled out safely. Link to `release-engineering/` canonical files.

> If dedicated probing or review questions help this topic, put each answer immediately below its question, using `### Question 1` and `#### Answer` under `## Probing Questions`. Ordinary operational checklists do not require an answer per item.
