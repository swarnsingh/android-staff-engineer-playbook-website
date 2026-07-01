# KMP Decision Matrix

## Overview

Kotlin Multiplatform is an architectural investment, not a checkbox. It can remove duplicate domain logic and improve consistency across Android and iOS, but it can also create slow builds, awkward APIs, platform resentment, and shared abstractions that fit neither platform well.

A Staff engineer should decide KMP scope from product risk, team topology, API surface, and platform constraints.

## Shareability Matrix

| Layer | Share? | Why |
|---|---|---|
| Pure domain rules | Strong yes | Highest consistency value, low platform coupling |
| DTO parsing and validation | Usually yes | Reduces backend contract drift |
| Use cases/interactors | Often yes | Good if dependencies are abstract and lifecycle-neutral |
| Persistence schema | Maybe | SQLDelight/Room KMP can help, but migrations and tooling matter |
| Networking client | Maybe | Ktor works well, but platform auth/proxy/TLS needs escape hatches |
| ViewModels/state machines | Maybe | Works when API is Swift-friendly and lifecycle is explicit |
| UI | Case-by-case | Compose Multiplatform maturity, design goals, platform expectations |
| Platform capabilities | Usually no | Camera, Bluetooth, payments, widgets, background execution differ deeply |

## Decision Scorecard

Score each dimension from 1 to 5.

| Dimension | Low score | High score |
|---|---|---|
| Business value | Cosmetic consistency | Critical logic consistency |
| Platform divergence | Android/iOS very different | Same rules and workflows |
| Team readiness | Separate teams, little Kotlin/iOS buy-in | Shared ownership and review |
| API stability | Rapid experimentation | Stable domain contracts |
| Tooling maturity | Unsupported libraries/plugins | Known CI, debugging, crash tooling |
| Interop quality | Awkward Swift API | Swift-friendly generated/wrapped API |
| Build cost | CI already fragile | Build graph can absorb KMP |
| Rollback ability | Hard to isolate | Module can be disabled/replaced |

Start with the highest-value, lowest-interop-risk module. Do not start with the entire app.

## Good First KMP Modules

- Money/date/eligibility rules.
- Feature flag evaluation.
- Checkout validation.
- Offline operation serialization.
- DTO parsing and error mapping.
- Analytics event schema validation.
- Shared networking models.
- Pure search/filter/sort logic.

These modules are easy to test on JVM and Native, and they expose small APIs.

## Risky First KMP Modules

- Full UI.
- Navigation.
- Auth session storage.
- Push notifications.
- Background execution.
- Camera/media capture.
- Bluetooth/location-heavy features.
- Complex database migrations.

These are platform-heavy. Share them only after the team has proven smaller modules and has escape hatches.

## API Surface Rule

The iOS API is the product. If Swift consumers hate the generated API, the KMP module has failed even if the Kotlin code is elegant.

KMP public APIs should:

- Use explicit return types.
- Avoid deeply nested generics at the boundary.
- Avoid exposing internal coroutine scopes.
- Prefer final DTOs and sealed result models with tested Swift representation.
- Expose suspend/Flow only with agreed Swift consumption patterns.
- Provide cancellation semantics.
- Keep errors explicit.

## Rollout Strategy

1. Pick one bounded domain module.
2. Write shared tests before platform integration.
3. Build a thin Android adapter and a thin iOS adapter.
4. Review generated Swift API with iOS engineers.
5. Add crash/log correlation from both platforms.
6. Release behind a feature flag or narrow path.
7. Measure build time, crash-free sessions, and team friction.
8. Expand only after ownership is healthy.

## Ownership Model

KMP fails when "shared" means "owned by no one."

Define:

- Code owners for shared modules.
- Android/iOS review requirements.
- Public API review process.
- Release and rollback owner.
- CI failure owner.
- Binary compatibility policy.
- Documentation and sample ownership.

## When Not to Use KMP

Do not use KMP when:

- The logic changes weekly and platform UX is still unknown.
- iOS team cannot review or debug the generated API.
- Critical libraries are missing or unstable.
- Build times are already blocking delivery.
- Platform-specific behavior is the essence of the feature.
- The team wants KMP mainly to reduce headcount.

KMP is leverage, not a staffing trick.

## Staff Engineer Review Checklist

- Is there a written reason this module should be shared?
- Does the module have a small public API?
- Are Swift API examples reviewed and accepted?
- Are platform escape hatches designed?
- Are shared tests run on every target?
- Is crash/telemetry attribution available per platform?
- Is build-time impact measured?
- Is rollback possible without app-wide rewrites?
- Are binary/source compatibility expectations documented?
- Is ownership clear across Android and iOS?

## Further Reading

- [Android Developers: Kotlin Multiplatform](https://developer.android.com/kotlin/multiplatform)
- [Kotlin Multiplatform documentation](https://kotlinlang.org/docs/multiplatform.html)
- [`foundations/architecture-and-module-boundaries.md`](foundations/architecture-and-module-boundaries.md) - KMP module boundaries.
- [`tooling/swift-interop.md`](tooling/swift-interop.md) - Swift API surface and export.
- [`binary-compatibility-api-evolution.md`](binary-compatibility-api-evolution.md) - evolving shared APIs safely.
