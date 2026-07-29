# Reference Architectures

## Purpose

Settled architectural blueprints — the "if I had to build Uber tomorrow, where do I start?" reference.

## Distinction From Worked Design Problems

A design problem in [`mobile-system-design/`](mobile-system-design.md) is the *reasoning exercise* (how you'd think it through under pressure). A reference architecture is the *blueprint you'd actually build*. Hold this line consciously; cross-link the two rather than duplicating — the design topic links to the blueprint and vice versa.

## Why It Matters

Every architecture has solved problems baked in. Reading a clean blueprint compresses years of mistakes other people made.

## What This Folder Helps You Do

- See what a complete mobile architecture looks like after the design interview is over and real implementation constraints arrive.
- Compare product archetypes: consumer, merchant, banking, e-commerce, ride-hailing, social, video streaming, and offline-first apps.
- Study how priorities change by domain: conversion, compliance, offline durability, real-time location, feed scale, playback quality, operational continuity, and reliability.
- Reuse proven blueprints as starting points while still adapting them to your own product constraints, org structure, and backend maturity.

## Guided Reading Sequence

Prerequisite: complete at least the core [Mobile System Design](mobile-system-design.md) framework and two worked problems. Each file follows the [blueprint template](templates/blueprint.md). Read from general product architecture toward domains with stronger offline, compliance, real-time, scale, and media constraints.

1. [Consumer App](reference-architectures/consumer-app.md) — general baseline.
2. [E-commerce App](reference-architectures/e-commerce-app.md) — catalog, cart, checkout, and payment boundaries.
3. [Merchant App](reference-architectures/merchant-app.md) — operational workflows and business data.
4. [Offline-First App](reference-architectures/offline-first-app.md) — durable local writes and convergence.
5. [Banking App](reference-architectures/banking-app.md) — high-security and regulated workflows.
6. [Ride-Hailing App](reference-architectures/ride-hailing-app.md) — real-time location and trip state.
7. [Social Media App](reference-architectures/social-media-app.md) — feed, media, engagement, and scale.
8. [Video Streaming App](reference-architectures/video-streaming-app.md) — playback, media delivery, and QoE.

**Finish:** compare two blueprints and explain which constraints—not product names—caused their architectural differences.
