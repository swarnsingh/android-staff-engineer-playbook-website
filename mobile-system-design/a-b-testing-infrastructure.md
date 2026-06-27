# Platform Design: A/B Testing Infrastructure

## The Prompt

*"Design the A/B Testing infrastructure for a massive E-Commerce app. The Product Manager wants to test a Red 'Buy' button vs a Green 'Buy' button. Half the users should see Red, half should see Green. The Data Science team needs to know exactly which users saw which button to calculate if the Green button increased revenue."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Assign users to distinct experimentation buckets (Control vs Variant).
- Provide the UI with the correct configuration (Red vs Green).
- Log assignment events to the Analytics pipeline.

### Non-Functional Requirements (NFRs)
- **Consistency (Priority 0):** If User A sees the Green button on Monday, they *must* see the Green button on Tuesday. If the color flips back and forth, the experiment is statistically ruined.
- **Performance:** Checking an A/B test bucket must be instantaneous (microseconds) and never block the Main Thread or wait for the network.
- **Offline Support:** The app must be able to assign buckets and run the experiment even if the device has no internet connection.

## 2. High-Level Architecture (Deterministic Hashing)

A Junior engineer makes an HTTP request: `GET /ab-test/buy-button?userId=123`. The backend generates a random number and returns `variant_green`. This requires the backend to store the assignment in a database, fails offline, and blocks the UI.

A Staff engineer uses **Client-Side Deterministic Hashing**, completely eliminating the backend database and the network bottleneck.

```mermaid
graph TD
    subgraph Mobile App (Android)
        Config[(Ruleset JSON / SharedPreferences)]
        HashEngine[Deterministic Hashing Engine]
        UI[Checkout UI]
        Analytics[Analytics SDK]
    end
    
    subgraph Backend
        PM[Product Manager] -->|Defines Test| CDN[(Static JSON CDN)]
        DataScience[Data Science Pipeline]
    end
    
    CDN -.->|Async Download| Config
    UI -->|Ask for Variant| HashEngine
    HashEngine -->|Reads Config| Config
    HashEngine -->|1. Returns 'Green'| UI
    HashEngine -->|2. Fire 'Exposure' Event| Analytics
    Analytics -.->|Batch Upload| DataScience
```

## 3. The Core Flows (Deep Dive)

### Flow 1: Client-Side Assignment (MurmurHash)
*Interviewer:* "How does the mobile app figure out if the user is in the Control group or Variant group without asking the server?"

**Staff Answer:**
"We use the exact same algorithm as Feature Flags: **Deterministic Hashing**.
The app downloads a static JSON ruleset:
```json
{
  "experiment_id": "exp_buy_button_color",
  "rollout_percentage": 100,
  "variants": [
    { "id": "control_red", "weight": 50 },
    { "id": "variant_green", "weight": 50 }
  ]
}
```
When the UI needs the button color, the SDK calculates:
`hash = MurmurHash3("user123" + "exp_buy_button_color")`
This yields a massive integer. We take `hash % 100`.
If the result is `0 to 49`, the SDK returns `control_red`.
If the result is `50 to 99`, the SDK returns `variant_green`.
Because the math is deterministic, User 123 will *always* hash to the exact same bucket. No database is required."

### Flow 2: The "Exposure" Event (The Flaw of Assignment)
*Interviewer:* "You put 1 Million users into the 'Green' bucket. 50,000 of them bought an item. Data Science says the Green button increased conversion by 500%. But there's a fatal flaw in the math. What did you do wrong?"

**Staff Answer:**
"The flaw is that I counted users who *never saw the button*.
Just because a user was mathematically assigned to the 'Green' bucket at app startup doesn't mean they ever navigated to the Checkout screen. If I include users who never saw the button in the denominator, the conversion rate is mathematically polluted.
**The Fix:** We must log an **Exposure Event** (or 'Impression Event').
The Analytics SDK must only fire the `Experiment Viewed: Green` event at the *exact millisecond* the Green button is actually drawn on the screen (e.g., inside `onResume` or a Compose `LaunchedEffect`). Data Science must strictly join the Revenue data *only* against users who fired an Exposure event."

### Flow 3: Orthogonal Experiments (The Colliding Tests)
*Interviewer:* "You are running the Green Button test. Another team is simultaneously running a test offering 'Free Shipping'. User A gets both the Green Button and Free Shipping. They buy a lot of items. Which test caused the increase in revenue?"

**Staff Answer:**
"This is an Experiment Collision. To prevent this, the hashing algorithm must ensure **Orthogonality**.
If we just used `MurmurHash("user123")`, User 123 would be in the Variant group for *every single test* in the app.
By combining the User ID and the Experiment ID (`MurmurHash("user123" + "exp_buy_button")`), the hash distributes the user uniquely for every test. 
User A might be Variant for the Button test, but Control for the Shipping test. The Data Science backend uses statistical models (ANOVA) to separate the overlapping variance, provided the assignments are perfectly randomized and orthogonal."

## 4. Failure Modes & Bottlenecks

### Bottleneck: The Simpson's Paradox (App Versioning)
*Interviewer:* "The Green Button code only exists in App Version 2.0. Users on Version 1.0 download the JSON config. They hash into the 'Green' bucket, but they don't have the code. They see Red. Now your Data Science numbers are completely destroyed."

**Staff Answer:**
"The JSON ruleset must support **Client-Side Targeting**.
The JSON must explicitly state: `"min_app_version": "2.0.0"`.
When the A/B testing SDK runs the evaluation on a device running Version 1.0, the SDK sees it fails the targeting rule. It immediately short-circuits and returns a neutral `fallback_red` state, and crucially, it *does not fire an Exposure event*. The user is entirely excluded from the experiment."

### Bottleneck: The Flickering UI (The Asynchronous Wait)
*Interviewer:* "A Junior dev writes: `fetchAbTestFromNetwork { color -> button.setColor(color) }`. What happens?"

**Staff Answer:**
"The button is drawn invisibly, or it is drawn Red, and 500ms later it suddenly flashes Green. This breaks the fundamental law of A/B testing: The user must not know they are in a test.
**The Fix:** A/B tests must *never* be evaluated asynchronously. The SDK must read the cached JSON ruleset synchronously from disk/memory in 0ms. If the JSON hasn't downloaded yet (e.g., very first install), the user simply gets the Control experience until their next session."

## 5. Staff Engineer Thinking: Device ID vs User ID

A Staff Engineer understands that Identity is the hardest part of A/B testing.

If you hash based on `DeviceID`, a user gets the Green button on their phone. When they log in on their tablet, the tablet has a different `DeviceID`. They get the Red button. The user is confused, and the experiment is ruined because their purchase is split across two experiences.

If you hash based on `UserID`, the math works perfectly—but only *after* the user logs in. What color do you show them when they are browsing anonymously before checkout?

**The Solution:** The A/B Test SDK must support a concept of **Sticky Identity**.
When the user is anonymous, we hash on `DeviceID`. When the user logs in and we know their `UserID`, the SDK must *continue to use the originally assigned bucket* for the duration of that specific experiment, rather than blindly re-hashing with the new UserID and flipping the button color mid-session. The Analytics pipeline handles the complex ID-stitching on the backend.

## 6. Probing Questions (For Practice)

1.  Explain the fundamental difference between evaluating an A/B test via a backend API request versus using Client-Side Deterministic Hashing.
2.  Walk through the math of MurmurHash. How does taking the modulo (`% 100`) distribute users into an exact 50/50 split?
3.  Describe the "Exposure Event". Why is it mathematically invalid to assume a user was exposed to an experiment just because they downloaded the ruleset payload?
4.  How does combining the User ID and the Experiment ID in the hashing function ensure that multiple simultaneous experiments remain statistically orthogonal?
5.  Explain how Client-Side Targeting (e.g., filtering by app version) prevents older, unsupported app versions from polluting the experiment data.
6.  Why is asynchronous network fetching strictly forbidden when rendering an A/B tested UI component on the screen?
7.  Walk through the "Identity Problem". What happens if you hash based solely on `DeviceID`, and what happens if you hash based solely on `UserID`?
8.  How does an Analytics Backend stitch an anonymous `DeviceID` to a known `UserID` after the user logs in?
9.  If a Product Manager wants to test a completely new Checkout Flow that involves 5 different screens, how does the Android architecture enforce that the user stays in the Variant group across all 5 screens?
10. Describe the difference between a Feature Flag and an A/B Test. Why does an A/B Test require an Exposure Event while a Feature Flag typically does not?

## Further Reading

- [`feature-flags-and-remote-config.md`](feature-flags-and-remote-config.md) — The mechanical foundation of Client-Side Evaluation.
- [`analytics-sdk.md`](analytics-sdk.md) — How Exposure Events are reliably queued and transmitted offline.
- [`app-startup.md`](app-startup.md) — Ensuring the JSON ruleset is loaded into memory fast enough for synchronous UI rendering.
