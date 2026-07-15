# Release Engineering

## Purpose

How code safely reaches users. Owns the canonical treatment of app bundles and release strategy.

## Why It Matters

Mobile release engineering is harder than web — you can't roll back instantly, and your users live with whatever you shipped until they update. The discipline is staged rollouts, kill switches, and crash gating.

## What This Folder Helps You Do

- Ship Android apps safely when rollback is slow, app updates are user-controlled, and bad releases can remain installed for weeks.
- Design staged rollouts, crash gates, kill switches, code signing, Play Store workflows, app bundles, and CI/CD checks as one release system.
- Decide when to halt, hotfix, remote-disable, force-upgrade, or continue rollout based on user impact and observability.
- Communicate release risk with product, support, backend, and leadership teams before a bad release becomes an incident.

## Learning Order

CI/CD and code signing first (the substrate), then the rollout mechanics (staged rollouts, kill switches, crash gating), then the distribution layer (Play Store, app bundles), then release strategy as the synthesis.

## Topics

- [Staged Rollouts](release-engineering/staged-rollouts.md)
- [Kill Switches](release-engineering/kill-switches.md)
- [Crash-Rate Gating](release-engineering/crash-rate-gating.md)
- [CI/CD for Mobile](release-engineering/ci-cd-for-mobile.md)
- [Code Signing](release-engineering/code-signing.md)
- [Play Store Internals](release-engineering/play-store-internals.md)
- [16 KB Page Sizes (native-code compliance gate)](release-engineering/16kb-page-sizes.md)
- [App Bundles & Dynamic Delivery](release-engineering/app-bundles.md) — canonical owner
- [Release Strategy](release-engineering/release-strategy.md) — canonical owner; `mobile-system-design.md` cross-links
