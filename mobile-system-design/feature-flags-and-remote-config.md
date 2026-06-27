# Platform Design: Feature Flags & Remote Config

## The Prompt

*"Design the internal Feature Flag architecture for a 100+ engineer mobile team. The system must allow Product Managers to instantly turn features on/off for millions of users without an App Store update, support targeted rollouts (e.g., '10% of users in Canada'), and guarantee the app will not crash if the network fails during startup."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Evaluate boolean flags (`is_new_checkout_enabled`).
- Evaluate string/integer configs (`checkout_timeout_seconds = 15`).
- Target flags based on user properties (Geography, App Version, OS, User ID).

### Non-Functional Requirements (NFRs)
- **Zero Startup Blocking (Priority 0):** The app must *never* block the user on a loading screen while waiting for feature flags to download.
- **Consistency:** If a user opens the app and sees the "New Checkout" UI, they cannot suddenly see the "Old Checkout" UI 5 seconds later because the network request finally finished. (No UI flashing).
- **Scale:** 100 million Daily Active Users querying flags simultaneously.

## 2. High-Level Architecture (Client-Side Evaluation)

A Junior engineer designs a system where the app sends `userId=99` to the server, and the server replies `{"is_new_checkout": true}`.
A Staff engineer knows this **Server-Side Evaluation** fails on mobile. It requires a network request for every session, breaks offline, and causes the UI to flash.

We use **Client-Side Evaluation** (The LaunchDarkly / Firebase Remote Config approach).

```mermaid
graph TD
    subgraph Mobile App (Android)
        Disk[(SharedPreferences / DB)]
        Engine[Flag Engine]
        UI[App UI]
    end
    
    subgraph Backend
        ConfigSvc[Remote Config API]
        CDN[(Global CDN)]
        Rules[(Targeting Rules DB)]
    end
    
    ProductManager -->|Updates Rule| Rules
    Rules -->|Bakes to JSON| CDN
    
    Engine -->|1. Read INSTANTLY| Disk
    Disk --> UI
    
    Engine -.->|2. Async Fetch| CDN
    CDN -.->|3. Save for NEXT launch| Disk
```

## 3. The Core Flows (Deep Dive)

### Flow 1: The "Next Launch" Sync Strategy (Preventing UI Flashing)
*Interviewer:* "The user opens the app. The old UI renders. 2 seconds later, the feature flags download. The app suddenly switches to the new UI. The user gets confused and taps the wrong button. Fix it."

**Staff Answer:**
"We must completely divorce the network fetch from the UI evaluation.
1. When the app launches, the `FlagEngine` reads the flags from the local disk cache (which takes 2ms). The UI renders immediately based on these cached flags.
2. In the background, the `FlagEngine` fires an async HTTP request to fetch the newest flags from the CDN.
3. When the network request returns 2 seconds later, we save the new flags to disk, but we **DO NOT** notify the UI. We intentionally ignore the new flags for the current session.
4. The next time the user kills and restarts the app, the UI will read the new flags from disk and render the new UI instantly.
This guarantees 0ms latency and mathematically prevents UI flashing mid-session."

### Flow 2: Client-Side Targeting (The Rule Engine)
*Interviewer:* "We want to enable a feature for '10% of users in Canada on Android 14'. If the server doesn't evaluate the rules, how does the app know if it is part of the 10%?"

**Staff Answer:**
"The backend does not send the final boolean. The backend sends the **Ruleset**.
The CDN hosts a static JSON file that contains the logic:
```json
{
  "is_new_checkout": {
    "default": false,
    "rules": [
      {
        "conditions": {
          "country": "CA",
          "os_version": ">=14"
        },
        "rollout_percentage": 10,
        "value": true
      }
    ]
  }
}
```
The Android SDK downloads this JSON. When the UI asks `FlagEngine.getBoolean("is_new_checkout")`:
1. The SDK checks the local device's Locale (`CA`) and OS version (`14`).
2. It matches the rule.
3. It performs a **Deterministic Hash** to calculate the 10% rollout (see Flow 3).
The evaluation happens in microseconds on the CPU, with zero network calls."

### Flow 3: Deterministic Rollouts (MurmurHash)
*Interviewer:* "How do you ensure that if User A is in the 10% rollout group today, they are still in the 10% group tomorrow? You can't use `Math.random()`, because they might flip to the 90% group on the next launch."

**Staff Answer:**
"We use a fast, deterministic hashing algorithm, like **MurmurHash3**.
1. We concatenate the User's ID and the Flag Key: `hash("user123_is_new_checkout")`.
2. The hash produces a massive integer.
3. We take the modulo: `hash % 100`.
4. This yields a number between 0 and 99.
5. If the number is `< 10`, they get the feature.
Because the User ID and Flag Key never change, the hash is mathematically permanent. User A will always fall into the exact same bucket. We do not need the server to remember who is in the 10%."

## 4. Failure Modes & Bottlenecks

### Bottleneck: CDN Thundering Herd
*Interviewer:* "You send a Push Notification to 50 million users. They all open the app. The app instantly requests the latest Feature Flag JSON. Your API Gateway is annihilated. How do you survive?"

**Staff Answer:**
"Feature Flags must never hit a dynamic API Gateway.
1. The ruleset is compiled into a static JSON file and hosted on a massive Edge CDN (Cloudflare/Fastly). The CDN absorbs the 50 million requests.
2. We configure the Android client to respect HTTP `Cache-Control` headers (e.g., `max-age=3600`).
3. We implement **Client-Side Jitter**. If the cache expires, the app waits a random delay `(0 to 60 seconds)` before requesting the CDN. This smears the 50 million requests over a full minute."

### Bottleneck: Technical Debt (The Dead Flag Graveyard)
*Interviewer:* "After 2 years, your codebase has 500 `if(FlagEngine.getBoolean("is_holiday_sale"))` statements scattered everywhere. Half of them are for features that launched a year ago. The code is unmaintainable."

**Staff Answer:**
"Feature Flags incur massive technical debt. A Staff Engineer implements process controls:
1. **Mandatory Expiration:** When a PM creates a flag, they must set an expiration date (e.g., 90 days). After 90 days, the backend forcibly disables the flag, forcing the team to make a permanent decision.
2. **Linting Rules:** I will write a custom Detekt/Lint rule. If an engineer references a Flag Key in the codebase that has been marked 'Expired' in our flag registry, the CI build breaks. You cannot merge PRs until you delete the dead `if/else` block."

## 5. Staff Engineer Thinking: Configuration vs Architecture

A Junior engineer uses Remote Config for *everything* (e.g., trying to use it as a real-time database to push Chat Messages).
A Staff engineer fiercely defends the boundaries of Remote Config.
- **Acceptable:** Toggling UI variations, changing timeout integers, enabling new API endpoints.
- **Unacceptable:** Sending PII, sending secrets/API keys (the JSON is readable by anyone who inspects the network traffic), or sending massive arrays of data (e.g., the list of 50,000 cities for a search bar). Remote Config JSON must stay under ~100KB to ensure fast parsing.

## 6. Probing Questions (For Practice)

1.  Explain why "Server-Side Evaluation" of feature flags causes catastrophic user experience issues (UI flashing, offline failures) on mobile devices.
2.  Describe the "Next Launch" sync strategy. Why must the Android app explicitly ignore newly downloaded flags until the user restarts the app?
3.  Walk through the concept of "Client-Side Evaluation". How does the Android app determine if it is part of a 10% Canadian rollout without asking the server?
4.  Explain why `Math.random()` cannot be used for percentage rollouts, and exactly how MurmurHash provides deterministic bucket targeting.
5.  Why must the Feature Flag ruleset be hosted as a static JSON file on an Edge CDN rather than evaluated by a dynamic backend microservice?
6.  Describe the "Thundering Herd" problem when 50 million users open a Push Notification. How does Client-Side Jitter mitigate it?
7.  How does a custom Detekt/Lint rule prevent a multi-year codebase from turning into an unmaintainable graveyard of dead `if/else` feature flag statements?
8.  Why is it a critical security vulnerability to put third-party API Keys (e.g., a Stripe Secret Key) into a Firebase Remote Config JSON payload?
9.  If a Product Manager wants to immediately disable a broken feature and demands the change happens *mid-session* without waiting for a restart, how do you handle the architectural compromise?
10. Differentiate between a Feature Flag (Boolean toggle) and a Remote Config (String/Int payload). Why should a Remote Config payload never be used to deliver large datasets (like an entire application's translation strings)?

## Further Reading

- [`staged-rollouts.md`](../release-engineering/staged-rollouts.md) — How Feature Flags integrate with Play Store rollouts.
- [`caching-library.md`](caching-library.md) — The caching strategies used to store the ruleset JSON offline.
- [`a-b-testing-infrastructure.md`](a-b-testing-infrastructure.md) — How the Deterministic Hashing extends into Experimentation.
