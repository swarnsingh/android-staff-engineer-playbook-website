# System Design: Payment Flow

## The Prompt

*"Design a secure payment flow for an E-Commerce application. The user adds items to a cart, taps 'Checkout', and enters their credit card details. The system must process the payment securely, prevent double-charging if the network drops, and comply with PCI-DSS regulations."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Collect Credit Card (CC) information.
- Process the transaction via a Payment Gateway (e.g., Stripe, Braintree).
- Update the backend database (Order Status: Paid).

### Non-Functional Requirements (NFRs)
- **Security (Priority 0):** Absolute compliance with PCI-DSS. The backend database must *never* touch raw credit card numbers.
- **Resilience:** The "Double Charge" problem. If the user's cellular connection drops precisely when they tap 'Pay', they must not be charged twice when they tap it again.
- **Data Integrity:** The payment state on the client, the backend, and the Payment Gateway must be perfectly synchronized.

## 2. High-Level Architecture (The Tokenization Pattern)

A Junior engineer sends the Credit Card number to their own backend API.
A Staff engineer knows this violates PCI compliance and opens the company to massive legal liability. We must use **Tokenization**.

```mermaid
graph TD
    Client[Android App] -->|1. Send raw CC details| Gateway[Stripe/Braintree API]
    Gateway -->|2. Return secure Token 'tok_123'| Client
    
    Client -->|3. POST /checkout with 'tok_123'| Backend[Company Backend]
    
    Backend -->|4. Charge 'tok_123'| Gateway
    Gateway -->|5. Success (Money Transferred)| Backend
    
    Backend -->|6. HTTP 200 Order Confirmed| Client
```

## 3. Data Model & API

### The Idempotency Key (The Shield)

The most critical component of the API design is the `Idempotency-Key` header. It mathematically prevents double-charging.

```http
// 3. POST /checkout
POST /api/v1/checkout HTTP/1.1
Host: api.mycompany.com
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "cart_id": "cart_991",
  "payment_token": "tok_123",
  "amount_cents": 1500,
  "currency": "USD"
}
```

*Staff Rule:* The `Idempotency-Key` MUST be generated on the Android client (using `UUID.randomUUID()`), bound to the specific checkout attempt.

## 4. The Core Flows (Deep Dive)

### Flow 1: The Happy Path
1. The user types their credit card into the Stripe Android SDK UI.
2. The Stripe SDK talks directly to Stripe servers. Stripe validates the card and returns a one-time use string: `"tok_123"`.
3. The Android app generates an `Idempotency-Key` (e.g., `UUID_A`).
4. The app sends `{"token": "tok_123", "cart": "991"}` + `UUID_A` to the Company Backend.
5. The Backend receives the request, stores `UUID_A` in a Redis cache, and tells Stripe to charge the money associated with `tok_123`.
6. Stripe charges the card.
7. Backend updates the SQL database (`Order = PAID`).
8. Backend returns `HTTP 200 OK` to the Android app.

### Flow 2: The Network Drop (Preventing Double Charge)
*Interviewer:* "Step 6 succeeds. Stripe takes the money. The Backend updates SQL. But at Step 8, the user's train goes into a tunnel. The Android app throws a `SocketTimeoutException`. The user sees an error, so they tap 'Pay' again. What happens?"

**Staff Answer:**
1. The user taps 'Pay' again.
2. The Android app re-uses the exact same `Idempotency-Key` (`UUID_A`) because the checkout session hasn't changed.
3. The app sends the request to the Company Backend.
4. The Backend checks the Redis cache for `UUID_A`. It finds it! It sees that this exact request was already processed successfully 10 seconds ago.
5. The Backend completely skips the Stripe charge and skips the SQL insert.
6. The Backend immediately returns the exact same `HTTP 200 OK` response as before.
7. The Android app receives success. The user is only charged once.

### Flow 3: 3D Secure (SCA - Strong Customer Authentication)
In Europe, PSD2 regulations require 2-Factor Authentication for payments (3D Secure).
1. The Backend attempts to charge Stripe.
2. Stripe says "This card requires 3D Secure verification."
3. The Backend returns `HTTP 402 Payment Required` with a `client_secret` to the Android app.
4. The Android app passes the `client_secret` to the Stripe SDK.
5. The SDK opens a WebView. The user's bank sends them an SMS code. The user types it into the WebView.
6. The WebView closes. The Android app polls the Backend to confirm the payment succeeded.

## 5. Failure Modes & Bottlenecks

### Bottleneck: Floating Point Math
*Interviewer:* "The user buys a $10.99 item and a $4.01 item. Your total is $15.00. The backend rejects the payment due to a mismatch. Why?"

**Staff Answer:**
"A junior engineer used `Float` or `Double` for currency. `10.99f + 4.01f` in binary floating-point math often equals `14.9999999f`.
**The Fix:** Currency must ALWAYS be represented as an `Integer` or `Long` of the smallest denomination (e.g., Cents). We pass `1500` to the API. The UI formats it as `$15.00`. We never use floats for money."

### Bottleneck: Polling for Webhooks
*Interviewer:* "Sometimes Stripe takes 5 seconds to process the charge. The Android HTTP request times out. How do you handle asynchronous payment processing?"

**Staff Answer:**
"We must decouple the client from the synchronous payment processing.
1. The Android app sends the `POST /checkout`.
2. The Backend instantly returns `HTTP 202 Accepted` with a `transaction_id`. It does *not* wait for Stripe.
3. The Android app opens a 'Processing...' UI and begins Polling (or opens a WebSocket) listening for that `transaction_id`.
4. Stripe processes the payment and sends a Webhook to the Backend.
5. The Backend updates the database.
6. The Android app's next Poll returns `status: SUCCESS`. The UI advances."

## 6. Staff Engineer Thinking: Security & Compliance

When dealing with money, a Staff engineer focuses on the legal and security boundaries.

1.  **PCI-DSS Scope:** If the Android app's code touches the raw 16-digit credit card number, the company's entire backend infrastructure might fall under PCI-DSS compliance audits (which are brutally expensive). I mandate the use of third-party SDKs (Stripe Elements / Braintree Drop-in) where the UI fields are actually rendered by the SDK, ensuring the raw numbers bypass our memory space entirely.
2.  **Screenshot Protection:** The checkout screen where the user types their card must have `WindowManager.LayoutParams.FLAG_SECURE` applied to the Activity/Window. This turns the screen black if a malicious background app tries to record the screen, and blocks screenshots.
3.  **App Attestation (Play Integrity):** To prevent scripted bots from testing thousands of stolen credit cards against our API (Carding attacks), I require a Google Play Integrity token to be passed with every checkout request. The backend verifies the token to ensure the request is coming from an un-tampered, genuine app binary.

## 7. Probing Questions (For Practice)

1.  Explain the concept of "Tokenization" in payment processing. Why does it drastically reduce a company's PCI-DSS compliance burden?
2.  Describe the "Double Charge" problem. Walk through exactly how a client-generated Idempotency Key prevents it during a network dropout.
3.  Why is it mathematically dangerous to use floating-point numbers (`Float` or `Double`) to represent currency in a payment payload?
4.  Explain the architectural difference between a Synchronous payment flow (waiting for Stripe on the initial HTTP request) and an Asynchronous webhook flow.
5.  What is 3D Secure (SCA), and how does it force the mobile application to handle mid-flow authentication interruptions?
6.  Why must an Android Engineer apply `FLAG_SECURE` to the checkout Activity, and what exact attack vector does it mitigate?
7.  If a user taps the "Pay" button 5 times rapidly because the UI didn't show a loading spinner, how does the Idempotency Key protect the user?
8.  Describe how the Google Play Integrity API can prevent a botnet from using your Android app's endpoints for "Carding" attacks.
9.  Why should the Android client generate the Idempotency Key (UUID) instead of the Backend server generating it?
10. In an Asynchronous webhook flow, what is the fallback mechanism if the Android app loses cellular connection while polling for the transaction result?

## Further Reading

- [`idempotency.md`](../distributed-systems/idempotency.md) — The deep mathematical proof behind Idempotency Keys.
- [`security-and-privacy.md`](../mobile-system-design/security-and-privacy.md) — How `FLAG_SECURE` and Play Integrity work.
- [`push-vs-poll-vs-sse-vs-websockets.md`](../backend-for-mobile/push-vs-poll-vs-sse-vs-websockets.md) — How to wait for the asynchronous Webhook via SSE.
