# BizBrew

## Definition

A multi-tenant Android platform serving multiple merchant brands from a single codebase. Key technical characteristics: tenant-aware theming and design tokens, per-tenant feature flags and remote config, an experimentation harness for A/B tests scoped by tenant, and a platform-engineering layer that decouples shared infrastructure (auth, networking, observability) from tenant-specific features.

> *TODO: scale numbers — tenant count, MAU, build matrix size, feature-flag count, experiment cadence.*

## Role In This Repo

BizBrew is an **anchor system**, not a portfolio project. It is the worked example that grounds abstract concepts in [multi-tenancy](platform-engineering.md), [Android](android.md), design systems, [platform engineering](platform-engineering.md), [release engineering](release-engineering.md), experimentation, and [leadership](leadership.md).

When a canonical topic gets too abstract, a BizBrew application file ties it to a real system.

## Application Files

Application files in [`bizbrew/`](bizbrew/) — each links back to its canonical owner and never redefines concepts.

> *Stubs to be populated as application topics are written.*

## Related Reference Architecture

- [`reference-architectures/multi-tenant-app.md`](reference-architectures/multi-tenant-app.md) — BizBrew is the anchor for this blueprint.
