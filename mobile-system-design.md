# Mobile System Design

## Purpose

Three clusters: the design framework and non-functional requirements (the meta-skills), worked design problems (the reasoning exercises), and platform/SDK design topics (the building blocks).

## Why It Matters

Design is the highest-leverage skill at Staff level. The framework and NFRs are lenses applied to every problem; the worked problems train pattern recognition; the platform/SDK topics are the components real systems are assembled from.

## Learning Order

Framework + NFRs first — they apply to everything below. Then alternate between worked problems and the platform/SDK topics they exercise.

---

## Framework & Non-Functional Requirements

The meta-skills. Lenses applied to every problem.

- [Design Framework](mobile-system-design/design-framework.md) — SCADET + the requirements → estimation → API → high-level → deep-dive process
- [Non-Functional Requirements](mobile-system-design/non-functional-requirements.md)
- [Performance (as an NFR)](mobile-system-design/performance.md)
- [Accessibility](mobile-system-design/accessibility.md)
- [Localization & Internationalization](mobile-system-design/localization-and-internationalization.md)
- [Security & Privacy (as an NFR)](mobile-system-design/security-and-privacy.md)
- [Versioning & Backward Compatibility](mobile-system-design/versioning-and-backward-compatibility.md)

---

## Worked Design Problems

Each is a full topic file. Image Loading appears once here, not also in Platform & SDK Design.

- [Offline Sync](mobile-system-design/offline-sync.md)
- [News Feed](mobile-system-design/news-feed.md)
- [Chat / Messaging](mobile-system-design/chat-messaging.md)
- [Google Maps / Location System](mobile-system-design/google-maps-location-system.md)
- [YouTube / Video Streaming](mobile-system-design/youtube-video-streaming.md)
- [Stock Trading App](mobile-system-design/stock-trading-app.md)
- [Ride-Hailing](mobile-system-design/ride-hailing.md)
- [File Downloader](mobile-system-design/file-downloader.md)
- [Image Loading](mobile-system-design/image-loading.md)
- [Caching Library](mobile-system-design/caching-library.md)
- [Typeahead / Autocomplete Search](mobile-system-design/typeahead-autocomplete-search.md)
- [Collaborative Editing (CRDT / OT)](mobile-system-design/collaborative-editing.md)
- [Notification System](mobile-system-design/notification-system.md)
- [Payment Flow](mobile-system-design/payment-flow.md)
- [Pagination](mobile-system-design/pagination.md)
- [Search](mobile-system-design/search.md)

---

## Platform & SDK Design

- [Feature Flags & Remote Config](mobile-system-design/feature-flags-and-remote-config.md)
- [Telemetry SDK](mobile-system-design/telemetry-sdk.md)
- [Analytics SDK](mobile-system-design/analytics-sdk.md)
- [App Startup](mobile-system-design/app-startup.md)
- [Authentication](mobile-system-design/authentication.md)
- [Push Notifications](mobile-system-design/push-notifications.md)
- [Deep Links & Universal Links](mobile-system-design/deep-links-and-universal-links.md)
- [A/B Testing Infrastructure](mobile-system-design/a-b-testing-infrastructure.md)
- [Experimentation Platform](mobile-system-design/experimentation-platform.md)

Release strategy is **not** in this tree — it folds into [`release-engineering.md`](release-engineering.md).

---

## Every Design Topic Must Include

- Requirements (functional + non-functional)
- Back-of-envelope estimation
- APIs
- Data Model
- Failure Modes
- Monitoring
- Security
- Rollout

## Note on Device Lifecycle

Lifecycle, background processing, battery-aware design, threading safety, and memory footprint are documented in the [Android tree](android.md). Cross-link to them as architecture-shaping design constraints rather than duplicating.
