# Versioning & Backward Compatibility

## Overview

A Junior Engineer deletes a column from the backend database, deploys the server, and goes to sleep. The next morning, the company has lost $500,000. 

Why? Because unlike a Website (where you refresh the browser and instantly get the new HTML), **a Mobile App is a compiled binary physically installed on a user's device.** You cannot force a user to update their app. A user might be running an APK that is 4 years old. If your backend stops returning the JSON shape that the 4-year-old app expects, the app crashes.

A Staff Engineer understands that **Backward Compatibility** is the most difficult and permanent constraint in Mobile System Design. Once an API contract is shipped to a mobile client, it is etched in stone for years.

## Why It Matters

Imagine a Ride-Hailing app (Uber/Lyft).
- **V1 (2020):** The app expects `driver_name` as a single String: `"John Doe"`.
- **V2 (2024):** The Product team wants to separate names. The backend team deletes `driver_name` and replaces it with `first_name` and `last_name`.
- **The Disaster:** The millions of users who haven't updated their app from V1 still expect `driver_name`. When the V2 API payload arrives without it, the V1 app's JSON parser throws a `NullPointerException` and crashes. The user is stranded on the street.

## First Principles

1.  **The Immutable Contract:** Once a mobile app consumes an API in production, that API endpoint cannot change its shape, delete fields, or rename fields until the app is forcibly retired.
2.  **Add-Only Evolution:** You can *add* new fields to an API (the old app will safely ignore them). You can *never* delete or rename old fields.
3.  **Force Update (Kill Switch):** A mechanism built into the mobile app from Day 1 that allows the server to permanently block the user from entering the app, forcing them to go to the Play Store to update.
4.  **API Versioning:** Structuring backend endpoints (e.g., `/v1/users` vs `/v2/users`) so different app versions can hit different server logic simultaneously.

## Mental Model

Think of a Mobile App as a **Space Probe sent to Mars**.
- When you launch the probe (publish the APK to the Play Store), it takes 7 months to get there.
- You can send instructions to the probe (API responses), but you **cannot physically change the hardware** on the probe once it has launched.
- If NASA's control center (The Backend) decides to change the communication protocol from English to French, the Mars probe will not understand it and will die in the vacuum of space.
- The control center must continue to speak English to the old probe for the next 10 years, even while they build a new probe that speaks French.

## Internal Mechanics

### 1. The Force Update (Kill Switch)

Every single mobile app must have a Force Update mechanism implemented *before* the first version is ever released. If you forget to add it to V1, you can never kill V1.

**The Architecture:**
1. At app startup (e.g., during the Splash Screen), the app makes a `GET /config` request.
2. The payload contains the `min_supported_version`.
```json
{
  "min_supported_version": 145, // versionCode 145
  "latest_version": 150,
  "force_update_message": "A critical security update is required."
}
```
3. The app compares its own `BuildConfig.VERSION_CODE` against the payload.
4. If `120 < 145`, the app throws up a massive, un-dismissible Dialog box with a button that links directly to the `market://` URL for the Play Store. The app does not allow the user to proceed.

*Staff Note:* Force updating a user destroys their UX. It is a nuclear option, used only for critical security flaws or when the backend maintenance of an old API becomes financially unviable (e.g., after 3 years).

### 2. API Versioning Strategies

When the Backend *must* change the contract entirely, how do you manage it?

- **URL Versioning (The Standard):** `GET /v1/profile` vs `GET /v2/profile`.
    - The V1 Android App hits `/v1/`. The V2 Android App hits `/v2/`.
    - *Burden:* The backend team must now maintain two completely different code paths in their server codebase for years.
- **Header Versioning:** `GET /profile` with header `Accept-Version: v1`.
    - Functionally the same as URL versioning, but keeps the URLs cleaner.
- **GraphQL (The Evolution):**
    - GraphQL completely eliminates the need for `/v1/` and `/v2/`. Because the client *asks* for the exact fields it wants, the backend just keeps adding new fields to the GraphQL schema. The V1 app asks for `driver_name`. The V2 app asks for `first_name`. Both work perfectly against the exact same endpoint forever. (See [GraphQL](../android/networking-and-security/graphql.md)).

## Tradeoffs

**Backend Maintenance vs Mobile User Retention**

- **Aggressive Deprecation (Backend Wins):** You Force-Update users every 3 months. The backend codebase is incredibly clean because they constantly delete old `/v1/` code.
- **The Mobile Reality (Mobile Wins):** Many users in emerging markets do not have Wi-Fi. They cannot download a 100MB app update. If you Force Update them, they will uninstall the app and use a competitor. You lose the customer permanently.

*Staff Decision:* A Staff Engineer fights to protect the user. I mandate that all APIs must be supported for a minimum of **24 months** (or whatever the APM analytics say covers 99% of our revenue). The backend team must absorb the technical debt of maintaining the old endpoints.

## Failure Modes

- **The Silent Parsing Crash:**
  The backend sends a new field: `{"status": "PENDING"}`. The V1 app's JSON parser uses an Enum `enum class Status { ACTIVE, INACTIVE }`. Because `PENDING` doesn't exist in the V1 codebase, the `Gson` parser throws an `IllegalArgumentException` and crashes the app.
  *(Fix: Mobile API contracts must use `@Json(name = "UNKNOWN")` fallback mechanisms for Enums, allowing the parser to safely default to a known value instead of crashing when encountering future backend additions).*
- **The Required Field Trap:**
  The V2 mobile app starts sending a new field in a `POST` request: `{"address": "123 Main St"}`. The backend team makes `address` a **required** column in the SQL database.
  *(Failure: The V1 app doesn't know what `address` is, so it doesn't send it. The backend database rejects the V1 request with a `500 Internal Server Error`. The V1 app is now completely broken. Fix: Backend database migrations MUST make new fields `nullable` or provide a default value).*

## Staff Engineer Thinking

When reviewing an API design, a Staff engineer focuses entirely on the "What happens to the V1 app?" question.

1.  **The "Add-Only" Rule:** If a backend PR renames `userId` to `user_id`, I block the PR. The mobile app cannot handle renames. You must leave `userId` alone, and *add* `user_id` as a duplicate field for the V2 app to use.
2.  **Graceful Degradation for Unknown Types:** If we build a feed (like Instagram), the backend returns a list of components: `Type: IMAGE`, `Type: VIDEO`. What happens next year when we invent `Type: 3D_MODEL`? The V1 app will crash trying to render it. I design the mobile app's polymorphic parser to silently discard any `Type` it doesn't recognize. The V1 app won't see the 3D model, but it won't crash.
3.  **Analytics-Driven Deprecation:** Backend engineers often hate maintaining old APIs and will beg to delete them. I do not guess when it is safe. I use Firebase/New Relic to query: *"How many DAU (Daily Active Users) are currently hitting the `/v1/` endpoint?"* If that number generates more than $5,000 of revenue a day, the endpoint stays. Engineering purity never trumps revenue.

## Common Misconceptions

- **"Users have auto-update turned on, so everyone will get the new app."** A massive misconception. Auto-update only triggers on Wi-Fi, when the phone is plugged in, and when there is sufficient storage space. Millions of phones worldwide are permanently full (0 MB storage left) and will *never* auto-update your app.
- **"Semantic Versioning (SemVer) solves API compatibility."** SemVer (v1.2.0) is a naming convention. It does not stop a backend engineer from accidentally merging a breaking database change. Only rigorous integration testing against the actual V1 Android APK during the backend CI/CD pipeline guarantees compatibility.

## Probing Questions

1.  Explain the fundamental difference in deployment cadence between a Web Application and a Mobile Application, and how this dictates API design.
2.  What is a "Force Update" (Kill Switch) mechanism, and why is it a catastrophic failure if an engineering team forgets to include it in version 1.0 of their app?
3.  Describe the "Add-Only" rule for API evolution and why renaming a JSON key is considered a breaking change.
4.  How does a GraphQL architecture elegantly bypass the need for `/v1/` and `/v2/` URL versioning?
5.  Explain the "Silent Parsing Crash" that occurs when a backend introduces a new Enum value, and how a mobile engineer designs Kotlin data classes to prevent it.
6.  Why must a backend database migration strictly use `nullable` columns or default values when adding new required fields for a V2 mobile app?
7.  Describe the concept of "Graceful Degradation" when a V1 mobile app encounters a completely new payload type (e.g., a new UI component in a Server-Driven UI architecture).
8.  How does a Staff Engineer use telemetry (DAU/Revenue metrics) to settle a dispute with the backend team over when to deprecate an old API endpoint?
9.  Why is relying on the Google Play Store's "Auto-Update" feature an invalid strategy for ensuring all users migrate to your V2 API?
10. Think of the "Space Probe" analogy. If an API contract is etched in stone, how does this change the amount of time a Staff Engineer spends reviewing an API Swagger/OpenAPI spec before the first line of code is written?

## Further Reading

- [`api-design-for-mobile.md`](../backend-for-mobile/api-design-for-mobile.md) — How to design APIs that evolve rather than version.
- [`graphql.md`](../android/networking-and-security/graphql.md) — The ultimate solution to the API versioning problem.
- [`bff-pattern.md`](../backend-for-mobile/bff-pattern.md) — How the BFF absorbs the complexity of maintaining V1 and V2 APIs.
