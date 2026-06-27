# Optimize for Change

## Overview

**Optimize for change** is the principle that the only certain property of software requirements is that they will change, so the highest-leverage thing architecture can do is make change cheap and reversible. A great system is not one that predicts the future correctly — that's impossible — but one that **doesn't punish you when the future turns out different from your guess**.

Two interpretations follow:

1. **Cheap to change**: when a requirement shifts, the cost of adapting the code is small. The cost is measured in lines touched, files modified, modules rebuilt, tests rewritten, regressions risked.
2. **Cheap to reverse**: when a change ships and turns out wrong, you can roll it back without redeploying. Feature flags, kill switches, staged rollouts, and reversible migrations all exist to convert "I shipped a mistake" from a 48-hour disaster into a 30-second config flip.

The principle is often confused with two siblings: "make everything configurable" (which adds complexity and rarely pays off) and "predict every future need" (the YAGNI anti-pattern). Optimize-for-change is neither. It's about **avoiding decisions that are expensive to revisit** and **keeping the cheap-to-revisit decisions actually cheap**. Jeff Bezos's "one-way doors vs two-way doors" framing captures it: identify which decisions are one-way (hard or impossible to reverse, like a database choice, a public API contract, a vendor lock-in) and which are two-way (easy to reverse, like an internal abstraction, a default value, a UI tweak). Spend the time you'd have spent on speculative flexibility on the one-way doors; let the two-way doors be quick.

---

## Why It Exists

Two empirical observations drive the principle:

1. **Requirements always change.** Studies of software projects (Standish, McKinsey, internal data at every large tech company) consistently show that 30–60% of requirements as initially specified are wrong or incomplete. Some change because the business changes. Some change because the customer changes. Some change because the *engineer's understanding* changes after they build the first version. There is no project where the original spec survives unscathed.
2. **Reversing a deployed mistake is hugely expensive.** A bug shipped in an APK takes days to fix and roll out. A user-facing schema migration that turns out wrong can cost weeks of recovery and data correction. A vendor decision made in Q1 might be unwindable only after a year of contractual notice.

The principle says: **design assuming you will be wrong about specifics, and ensure that being wrong is recoverable**. This is the engineering analog of risk management. You don't pretend the future is predictable; you minimize the cost of any single wrong guess.

The hardest part is distinguishing "real optionality that will pay off" (worth the upfront cost) from "speculative flexibility that adds complexity for nothing" (YAGNI). The honest answer is that you usually only know in retrospect, and the discipline is to bias toward keeping things simple and small until you have evidence of needing more.

---

## Historical Context

1. **Parnas's information hiding (1972).** David Parnas's *On the Criteria To Be Used in Decomposing Systems into Modules* argued that modules should be drawn around "design decisions likely to change," hiding the changeable parts behind stable interfaces. The first formal statement of optimize-for-change as a software-engineering principle.
2. **Pragmatic Programmer (1999).** Hunt and Thomas's "DRY" (Don't Repeat Yourself) is partly a change-cost argument: duplication multiplies the cost of any change to the duplicated concept.
3. **Kent Beck, *Extreme Programming Explained* (1999).** "Embrace change" as the central XP value. Practices like continuous integration, refactoring, and TDD all serve the same goal: lower the cost of change.
4. **Bezos's "one-way / two-way doors" framing (2015 shareholder letter).** Distinguishing decisions that are easy vs hard to reverse, and arguing that fast organizations let two-way decisions be made quickly with limited deliberation.
5. **Continuous Delivery (Humble & Farley, 2010).** Deployment pipelines, feature flags, staged rollouts — the operational toolkit for cheap-to-reverse production changes.
6. **Mobile-specific evolution.** Mobile compounds the cost of mistakes: a bad release takes hours to days to roll forward (Play/App Store review delays) and weeks to fully propagate as users update. This makes feature flags, server-driven config, and kill switches especially important on mobile — they let you change behavior server-side without shipping an APK.

The arc: from "modules hide changeable decisions" (Parnas, code-level) to "feature flags hide changeable behavior" (Continuous Delivery, operational-level), with the same underlying observation that change is constant and the cost of reversing should be small.

---

## First Principles

### 1. Identify one-way vs two-way doors

Some decisions are inherently expensive to reverse:

- **Public API contracts.** Every consumer depends on the signature. Reversing requires every consumer to upgrade.
- **Database schema for production data.** Reversing requires migration and risks data loss.
- **Vendor choice with deep lock-in.** Reversing requires re-implementing on a different platform.
- **Wire format (proto definitions, REST URLs).** Reversing breaks deployed clients.
- **Library versions exposed in your own public API.** Reversing forces consumer upgrades.

These deserve careful upfront design. Get them wrong and the recovery cost is months.

Other decisions are cheap to revisit:

- **Internal abstractions.** Refactor when the use case sharpens.
- **Default configuration values.** Change via config.
- **Variable names.** IDE rename.
- **Algorithm choice for an internal computation.** Swap behind the same interface.

These deserve fast iteration. Spending two weeks debating an internal class name is a waste.

The skill is recognizing which is which. Most planning meetings should sort decisions into the two buckets and spend time accordingly.

### 2. Information hiding behind stable interfaces

Parnas's insight: **draw module boundaries around the things likely to change**. Inside the module, change is local. Outside the module sees only the stable interface.

```kotlin
// The decision likely to change: which payment gateway
interface PaymentGateway {
    suspend fun charge(amount: Money): Result<Receipt>
}

class StripeGateway(private val client: StripeClient) : PaymentGateway { ... }
class BraintreeGateway(private val client: BraintreeClient) : PaymentGateway { ... }

// Consumers depend only on the interface
class CheckoutViewModel(private val payment: PaymentGateway) { ... }
```

Switching from Stripe to Braintree changes one DI binding. No business logic touches anywhere else.

### 3. Reversibility via feature flags

```kotlin
class CheckoutViewModel(
    private val payment: PaymentGateway,
    private val flags: FeatureFlags
) : ViewModel() {
    fun submit() {
        if (flags.isEnabled("new_checkout_flow")) {
            newCheckoutFlow()
        } else {
            oldCheckoutFlow()
        }
    }
}
```

Both flows exist in production simultaneously. Flag set on the server controls which runs. A bug in the new flow? Flip the flag off; old flow runs again for 100% of users in seconds. This is reversibility at the **runtime** level — you didn't have to redeploy.

### 4. YAGNI as the counter-discipline

*You Aren't Gonna Need It* is the brake on speculative flexibility. Building a `PaymentProcessor` abstraction with five hooks "in case we want to plug in alternative processors" before there's a second processor is YAGNI violation. The hooks add complexity, slow comprehension, and frequently don't fit when the actual second processor arrives.

The right move: write the Stripe code directly. When Braintree appears, the *refactor* to introduce the interface is easy (extract method, extract interface, swap binding). The cost of doing it later is small; the cost of building the wrong abstraction upfront is large.

### 5. Optionality has a cost

Every layer of indirection, every config knob, every feature flag adds:

- More code to read
- More test paths to cover
- More failure modes to debug
- More documentation to maintain

The right amount is **just enough** to cover the changes you're confident will happen, not the ones you're speculating about.

---

## Mental Model

Think of architecture as a **set of contracts** spanning different time horizons. Some contracts are with people: customers, integrators, partners. Some are with code: existing callers, future maintainers. Some are with operations: deployment pipelines, monitoring tools, on-call.

Changing a contract is expensive in proportion to **how many parties depend on it**. A private method has one party (you). A public API of a published library has thousands (every consumer). A database schema in production has every existing row of data.

The principle says: **make the highly-coupled contracts deliberately, slowly, and with reversibility built in. Make the lightly-coupled contracts fast and changeable.**

A useful image: think of the architecture as a city map. Some structures are skyscrapers — building them takes years; tearing one down takes longer. Others are pop-up shops — opened in a day, removed in a day. You site skyscrapers carefully; you put up pop-ups quickly.

The architectural mistake is treating every decision as a skyscraper ("we must make this design perfect") or every decision as a pop-up ("we'll just refactor later"). The wisdom is recognizing which decision is which.

---

## Internal Mechanics

### Dependency inversion as a change-cost mechanism

The dependency-inversion principle (DIP, the D in SOLID) says: depend on abstractions, not concretions. The mechanical consequence is that swapping the concretion doesn't touch the caller.

```kotlin
// Caller depends on the abstraction
class CheckoutViewModel(private val payment: PaymentGateway) { ... }

// At wire-up time, you pick a concretion
val viewModel = CheckoutViewModel(StripeGateway(client))
```

If Stripe is later swapped for Braintree, only the wire-up site changes. The ViewModel, its tests, and every caller of the ViewModel are untouched.

### Feature flags: runtime branching with config control

```kotlin
class FeatureFlags(private val remoteConfig: RemoteConfig) {
    fun isEnabled(flag: String): Boolean = remoteConfig.getBoolean(flag, false)
}
```

Flags are evaluated at runtime against the latest config. The config can be updated server-side (Firebase Remote Config, LaunchDarkly, in-house systems) without an app release. Properties:

- **Reversibility**: flip in seconds.
- **Targeting**: enable for 1% of users, then 10%, then 100%.
- **Kill switches**: a flag that can disable a feature entirely if it misbehaves.
- **Decoupling release from feature exposure**: code can ship months before exposure.

### Server-driven UI for reversible UI changes

For UI components rendered from server config (server-driven UI), the change is just a server config update:

```kotlin
// Server returns:
// { "type": "banner", "title": "Welcome back", "ctaText": "Continue" }

// Client renders dynamically based on type
@Composable
fun ServerDrivenComponent(config: ComponentConfig) {
    when (config.type) {
        "banner" -> Banner(config.title, config.ctaText)
        "card" -> Card(config.title, config.ctaText)
        ...
    }
}
```

A messaging change is a server-side text change. A layout tweak is a server-side type change. No app release.

### Database migrations: reversible vs irreversible

```sql
-- Reversible: add a nullable column
ALTER TABLE users ADD COLUMN nickname TEXT;
-- Reverse: ALTER TABLE users DROP COLUMN nickname;

-- Irreversible: drop a column with data
ALTER TABLE users DROP COLUMN deprecated_field;
-- Reverse: data is gone; can only restore from backup
```

The first migration is two-way; the second is one-way. A schema change strategy that runs irreversible migrations only after careful soak time, with backups verified, is the operational form of optimize-for-change.

### Refactoring as a continuous activity

Code that's been touched many times tends to acquire crud — unused parameters, defunct paths, mismatched abstractions. Continuous refactoring (small, in-the-flow improvements as you work) keeps the change cost low. Periodic big refactors are usually a symptom of skipping the small ones.

---

## Architecture

```mermaid
flowchart TB
    subgraph Decisions["Architectural decisions"]
        OneWay["One-way doors:<br/>public APIs, schemas, vendors"]
        TwoWay["Two-way doors:<br/>internal classes, defaults, names"]
    end

    subgraph Investment["Where to invest design effort"]
        Careful["Careful upfront design<br/>+ reversibility tools<br/>(feature flags, abstractions)"]
        Fast["Fast iteration<br/>+ refactor as evidence appears"]
    end

    OneWay --> Careful
    TwoWay --> Fast

    Careful -.->|costs of speculative flexibility| YAGNI["YAGNI brake:<br/>only build what's evidenced"]
    Fast -.->|temptation to lock in| YAGNI
```

---

## Production Example

### Vendor abstraction for payment processing

A mobile app integrates with Stripe. Six months later, the business adds Apple Pay. Twelve months later, they explore Razorpay for India. Each addition is a one-way door if hard-coded; each is a small swap if abstracted.

```kotlin
interface PaymentGateway {
    suspend fun charge(amount: Money, method: PaymentMethod): Result<Receipt>
}

class StripeGateway(...) : PaymentGateway { ... }
class ApplePayGateway(...) : PaymentGateway { ... }
class RazorpayGateway(...) : PaymentGateway { ... }

class CheckoutViewModel @Inject constructor(
    private val gateway: PaymentGateway     // injected; bound per build flavor or region
) : ViewModel() { ... }
```

The cost of building the abstraction the first time was maybe two hours. The savings on each new gateway are months of refactoring.

The discipline: **introduce the abstraction when the second implementation appears**, not before. Premature abstraction guesses wrong about the shared interface and gets in the way.

### Feature flag for risky redesign

A team wants to ship a new checkout UI. The risk is non-trivial:

```kotlin
class CheckoutScreenSelector(private val flags: FeatureFlags) {
    @Composable
    fun render() {
        if (flags.isEnabled("checkout_v2")) {
            CheckoutScreenV2()
        } else {
            CheckoutScreenV1()
        }
    }
}
```

Both V1 and V2 ship in the same APK. The flag is rolled out: 1% on Monday, 5% on Tuesday, 50% by Friday. Conversion rate drops on Tuesday — the flag is flipped off in minutes, fix the bug, roll out again next week. Without the flag, the same recovery is a hotfix release with 48-hour Play Store review.

### Schema evolution with backward compatibility

```kotlin
// Old API response
data class UserV1(val id: Long, val name: String, val email: String)

// New API adds optional fields
data class UserV2(
    val id: Long,
    val name: String,
    val email: String,
    val nickname: String? = null,
    val avatarUrl: String? = null
)
```

Old clients still parse the response (extra fields are ignored). New clients use the new fields when present. The schema change is reversible because no field was removed or renamed.

Removing a field requires a deprecation cycle: mark the field deprecated, wait for clients to stop using it, then remove. Premature removal is a one-way door that breaks deployed clients.

---

## Android Example

### Build variants for region-specific differences

```kotlin
// build.gradle.kts
android {
    flavorDimensions += "market"
    productFlavors {
        create("us") { dimension = "market"; ... }
        create("india") { dimension = "market"; ... }
        create("global") { dimension = "market"; ... }
    }
}
```

Each variant gets its own resources, dependency wiring, and entry points. Switching a region's payment gateway is changing one variant's `Gradle` config — not a code change in the shared core.

### Remote Config for runtime kill switches

```kotlin
@HiltViewModel
class HomeViewModel @Inject constructor(
    private val flags: RemoteConfig,
    private val analytics: Analytics
) : ViewModel() {

    init {
        if (!flags.getBoolean("home_recommendations_enabled")) {
            // The recommendation system is killed; show plain feed only
        }
    }
}
```

A recommendation system that's misbehaving on Samsung Galaxy S20s can be disabled for that audience via Remote Config rules — without redeploying.

### Refactor-friendly code patterns

```kotlin
// Adding a parameter without breaking callers
fun loadUser(
    id: UserId,
    options: LoadOptions = LoadOptions.DEFAULT
): User
```

Default-argument parameters can be added without breaking existing callers. Compare this to Java's mandatory overload-flood pattern. Kotlin's default arguments make the "add an option" change a two-way door rather than a one-way door.

---

## Tradeoffs

**Advantages**

- **Lower cost of recovering from mistakes.** A reversible mistake is a small mistake.
- **Faster experimentation.** Feature flags + safe defaults let teams try multiple approaches and pick the winner.
- **Decoupled release cycles.** Vendor swaps, UI redesigns, algorithm changes can happen without app updates.
- **Better incident response.** Kill switches let on-call disable broken features without code deploys.

**Disadvantages**

- **Speculative abstraction adds cost.** Wrong-guess abstractions are worse than no abstraction. YAGNI violations harm both speed and clarity.
- **Configuration complexity.** Every flag, every variant, every config knob adds combinations to test. Combinatorial explosion is real.
- **Feature flag debt.** Flags shipped for a launch can linger for years, accumulating complexity in code paths.
- **Configuration-as-code drift.** Config changes server-side without a code review can subtly change behavior.

**When not to apply**

- For internal class names, file structure, algorithm choices in non-public code — refactor freely; don't pre-build flexibility.
- For experimental prototypes — the cost of the abstraction outweighs the benefit.
- For decisions that genuinely will not change — don't build optionality for a fundamental that's set in stone.

---

## Failure Modes

**Premature abstraction.** Building a `Strategy` for a problem with one variant. The abstraction usually doesn't fit when the second variant appears. Mitigation: introduce abstraction at the second occurrence (the "Rule of Three" is overcautious; two is fine for most cases, but never one).

**Feature flag debt.** A flag shipped for a launch is never removed; six months later the code has two parallel paths, neither fully tested. Mitigation: every flag has an explicit removal date and an owner. Track flags as tech debt with a deadline.

**Speculative configuration.** Making everything configurable produces a config schema that no one fully understands. Mitigation: configure what evidence demands; defaults handle the rest.

**Over-rolled-back rollouts.** A staged rollout halts at 5% on every release because the team is risk-averse. Velocity drops. Mitigation: define clear rollout criteria (crash rate < X, conversion within Y of baseline) and execute mechanically.

**Vendor lock-in via "deep integration."** Choosing a vendor for their full-featured SDK and using every feature ties the codebase to the vendor. Mitigation: use the vendor SDK behind a small interface; pay the abstraction cost upfront to keep the door reversible.

**Schema-irreversible migration.** A migration that drops a column with data is irreversible. Mitigation: a two-phase migration — mark the field deprecated in v1, remove in v2 after the data confirms no one uses it.

**Architectural perfectionism.** Every code review demands "what if X changes?" considerations until the code is paralyzed by speculative flexibility. Mitigation: enforce YAGNI as a code-review heuristic; if a flexibility hook doesn't have a concrete near-term use, defer it.

---

## Performance Considerations

- **Feature flag lookups have a cost.** A flag check on a hot frame loop is noticeable. Cache flag values in memory and re-read on app launch or remote-config update.
- **Indirection through abstractions has a virtual-call cost.** Negligible in 99% of cases; in hot paths, the JIT usually inlines. Reserve micro-optimizations for measured hotspots.
- **Configuration parsing on startup.** Loading and parsing remote config on cold start adds latency. Cache locally and refresh in the background.
- **Server-driven UI's flexibility costs render performance.** Dynamic component dispatch is slower than hardcoded composition. Reserve for components that genuinely need server-driven control.

---

## Reliability Considerations

- **Kill switches as a reliability tool.** Every risky new feature should have a kill switch from day one. The cost is small; the value at incident time is enormous.
- **Default to the safe behavior.** When a flag is unset or unreachable, fall back to the known-safe path. Never block a critical flow on flag availability.
- **Test both flag paths.** A flag has two production paths; both must be tested. CI matrix should run with the flag on and off.
- **Reversible deploys.** A deploy that can be rolled back in minutes is reliability infrastructure. Mobile deploys are nearly irreversible — rely on server-side flags as the actual reversibility mechanism.

---

## Security Considerations

- **Flag-controlled features must be authorized at the server.** A client flag check is bypassable; server-side feature exposure is the actual control.
- **Vendor abstraction limits supply-chain blast radius.** When a SaaS vendor is compromised, the abstracted code is easier to switch off.
- **Config changes are deployment changes.** Treat remote config edits with the same review process as code deploys — they have the same blast radius.
- **Feature flag values are PII in some jurisdictions.** Flag states keyed to user IDs may be classified as profiling data under GDPR. Audit.

---

## Observability

- **Flag exposure metrics.** Log every flag evaluation: which flag, which user segment, which value. Lets you correlate behavior changes with flag rollouts.
- **A/B test instrumentation.** When a flag controls an experiment, instrument both arms with the same events for clean attribution.
- **Rollout dashboards.** Show flag-on % vs key business metrics over time. Spike in error rate after 5% rollout → halt and investigate.
- **Vendor abstraction lets you instrument the boundary.** Wrap the gateway calls with latency/error metrics; if you switch vendors, the metrics keep working.

---

## Staff Engineer Thinking

**Sort decisions by reversibility cost.** In any design review, ask of each decision: "what does it cost to reverse this in 6 months?" Spend the discussion proportionally.

**Build feature flags as platform infrastructure, not per-feature.** A single robust flag service used across the app is cheaper to maintain than ad-hoc booleans scattered everywhere.

**Maintain a flag lifecycle policy.** Flags shipped with code must have removal dates. Track flags as tech debt with an owner and a deadline. Aged flags become structural debt.

**Resist mocking out everything for "flexibility."** Abstracting a stable dependency just because "we might swap it" is YAGNI. Abstract when the second consumer arrives.

**Pay the upfront cost on one-way doors.** A bad API contract published to consumers is the most expensive mistake a team can make. Get those right with care, design reviews, and explicit deprecation/versioning strategies.

**Make changes additive whenever possible.** Adding a field to a response is safer than renaming one. Adding a method to an interface is safer than changing its signature. Default arguments and nullable fields are your friends.

**Treat refactoring as a daily activity.** Continuous small improvements keep the change cost low. Code that hasn't been refactored in two years usually can't be — it's accumulated too much friction.

**Plan for the rollback.** Every shipped change should answer the question "how would we undo this if it's wrong?" If the answer is "redeploy" or "hotfix," the change is risky. If the answer is "flip a flag," the change is safe.

---

## Common Misconceptions

**"Optimize-for-change means making everything abstract."** No. It means making the *expensive* things abstract and the *cheap* things simple. Speculative abstraction is anti-optimize-for-change.

**"Feature flags are for A/B testing."** A/B testing is one use. The bigger one is reversibility — letting any feature be disabled without a release.

**"YAGNI is the opposite of optimize-for-change."** They're complementary. Optimize-for-change says make the right things flexible; YAGNI says don't make the wrong things flexible.

**"Build one, throw it away."** Sometimes accurate, but pessimistic. Aim to build one that's flexible at the joints you expect to revisit and rigid elsewhere.

**"Reversibility is for big changes."** It's just as important for small ones. A tiny UI tweak behind a flag is a small change; a tiny UI tweak in a release is a small change you can't reverse for 48 hours.

**"Architecture should predict the future."** It shouldn't predict; it should *absorb*. The future will surprise you. Design to minimize the cost when it does.

---

## Probing Questions

1. Distinguish a one-way decision from a two-way decision with three examples from a typical Android codebase.
2. A team is choosing between Stripe and Braintree for a new app. What questions about reversibility should drive the choice?
3. Explain why introducing a `PaymentGateway` interface on day one might be worse than introducing it when the second gateway arrives.
4. A feature flag has been in production for 14 months. Both paths are still in the code. What's the cost of leaving it, and how do you decide when to remove it?
5. Why are nullable fields and default-argument parameters reversibility tools?
6. A schema migration drops a column. Walk through how you'd convert this to a reversible two-phase change.
7. What's the operational cost of a 100-flag system at a mid-sized mobile org? How do you keep it manageable?
8. Why is "make everything configurable" usually the wrong response to a feature being "too rigid"?
9. A risky redesign is being shipped behind a flag. Define three rollout milestones and three abort triggers.
10. The Stripe SDK has a new "great" feature that's tightly coupled to their APIs. The product team wants to use it. What's the conversation about reversibility?

---

## Further Reading

In this repository:

- [`simplicity.md`](simplicity.md) — simplicity is itself a reversibility tool; complex code is hard to change.
- [`prefer-deletion.md`](prefer-deletion.md) — deleted code is the most reversible code there is.
- [`design-for-failure.md`](design-for-failure.md) — reversibility is the operational arm of designing for failure.
- [`make-invalid-states-impossible.md`](make-invalid-states-impossible.md) — invariants reduce the surface for incorrect changes.
- [`../patterns/strategy.md`](../patterns/strategy.md) — the canonical way to make a behavior swappable.
- [`../patterns/circuit-breaker.md`](../patterns/circuit-breaker.md) — automated reversibility on failures.
- [`../release-engineering/staged-rollouts.md`](../release-engineering/staged-rollouts.md) — operational reversibility.
- [`../release-engineering/kill-switches.md`](../release-engineering/kill-switches.md) — the explicit kill-switch playbook.
- [`../mobile-system-design/feature-flags-and-remote-config.md`](../mobile-system-design/feature-flags-and-remote-config.md) — the design of the flag platform itself.

External:

- David Parnas, *"On the Criteria To Be Used in Decomposing Systems into Modules"* (1972) — the founding paper on information hiding for change.
- Kent Beck, *Extreme Programming Explained* (1999) — embrace change as the central value.
- Jeff Bezos, *2015 Letter to Shareholders* — the one-way/two-way doors framing.
- Martin Fowler, *"Feature Toggles (aka Feature Flags)"* (martinfowler.com) — a comprehensive treatment.
- *Continuous Delivery* by Jez Humble and David Farley — the operational toolkit for cheap changes.
- *Accelerate* by Forsgren, Humble, Kim — empirical evidence that change-cost-optimized organizations outperform.
