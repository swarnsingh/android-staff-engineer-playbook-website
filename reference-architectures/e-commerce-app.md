# E-Commerce App — Reference Architecture

> An illustrative blueprint for a transactional shopping client. The defining trade-off: **every screen optimizes for conversion**. Cart durability, checkout reliability, payment idempotency, and search-to-buy latency matter more than feed engagement metrics. Evaluate checkout changes alongside safety, accessibility, customer outcomes and operating cost.

---

## Scope and Assumptions

The server owns catalog prices, inventory, carts and payment/order state. The Android app may queue reversible cart edits, but checkout requires server reconciliation. Timing, retention and capacity numbers below are example budgets. PSP capabilities and compliance scope depend on the selected integration.

## Requirements

### Functional

- Product catalog browsing: home, category, search, recommendations.
- Product detail with rich media (gallery, video, variant selection).
- Cart (persistent across devices and sessions).
- Checkout: address selection, shipping options, payment method, place order.
- Order history, tracking, returns.
- Wishlist, saved-for-later.
- Multiple payment methods: cards, provider-supported digital wallets (for example, Google Pay on Android), BNPL, COD where regional.
- Promotions: coupons, vouchers, flash sales (high-traffic spike events).
- Account management, addresses, payment methods.

### Non-Functional

- **Conversion-first metrics.** Every architectural decision is evaluated by its impact on add-to-cart rate, checkout-completion rate, and time-to-purchase.
- **Cart durability.** Cart survives uninstall (server-backed), survives device switch, survives 30 days idle.
- **Checkout reliability.** Idempotency keys on every payment call. Double-charge prevention is non-negotiable.
- **Search latency.** p95 < 400ms for typeahead suggestions; p95 < 800ms for full search results page.
- **Flash sale capacity.** Architecture must withstand 10-100× normal traffic without degrading checkout for non-sale users.
- **Cellular-friendly.** Product images tiered by network class; defer high-res until tap.
- **Regulatory.** PCI DSS (cards), GDPR / CCPA (data), country-specific tax/invoice rules.

---

## Architecture

```mermaid
flowchart TB
    UI["Compose UI<br/>catalog + cart + checkout"] --> VM[ViewModels]
    VM --> CatalogRepo[CatalogRepository]
    VM --> CartRepo[CartRepository]
    VM --> CheckoutRepo[CheckoutRepository]
    VM --> SearchRepo[SearchRepository]
    CatalogRepo --> Pager[Paging 3]
    Pager --> CatalogApi[Catalog BFF]
    CartRepo --> CartRoom[(Room cart cache)]
    CartRepo --> CartApi["Cart BFF<br/>server-backed"]
    CheckoutRepo --> PaymentApi[Payments BFF]
    CheckoutRepo --> PSP["PSP SDK<br/>provider-supported UI"]
    PaymentApi --> Provider[PSP backend]
    PSP --> Provider
    SearchRepo --> SearchApi[Search BFF]
    CatalogApi --> Recommend["Recommendations<br/>ML, black box"]
```

The defining property: **the cart is server-side state with a local cache, not local state with server sync**. Cart durability across devices is a feature, not an offline trade-off. The local Room cache is a performance optimization; the source of truth is the cart service.

---

## Modules

### Catalog (browsing)

- Home, categories, search-results — all powered by Paging 3 + RemoteMediator.
- Stable cursor pagination; Room caches the latest page set for offline browsing of recent results.
- Image loading via Coil 3 with `MemoryCache.Builder().maxSizePercent(context, 0.25).build()`. Disk cache 300-500 MB; product images are touch-heavy and frequently revisited.
- Product detail screens lazy-load full-resolution images and variant-specific assets.

### Cart

**The most architecturally interesting module in this app.**

- The cart is **server-side state** with cross-device sync. The user adds an item on mobile; the same item appears on the desktop session.
- Locally, Room caches the cart for fast UI render. The cache is a *view* into the server cart, not an independent source of truth.
- On every add / remove / quantity change: the app sends the mutation to `/v1/cart` with an `Idempotency-Key`; server returns the canonical cart state; local cache is reconciled.
- Optimistic UI is allowed for visual responsiveness (item bounces into cart icon immediately), but the canonical state always wins on the next render.
- Offline: cart mutations are queued in an outbox. UX clearly signals "Will sync when online." Cart is fully usable for review; checkout is blocked offline.

### Checkout

The highest-stakes flow in the app. Borrows heavily from [`mobile-system-design/payment-flow.md`](../mobile-system-design/payment-flow.md):

- **Idempotency.** Persist a key per logical mutation (create-order, attach-payment, confirm) before sending it. Reuse it for unchanged retries within the server's documented deduplication window; changed parameters require a deliberately new operation.
- **PCI scope reduction.** Card details captured by the PSP SDK (Stripe `PaymentSheet`, Adyen Drop-In, Razorpay Checkout). Use the provider's approved card-entry flow and keep raw card data out of application-owned fields/logs. SDK use can reduce PCI scope; it does not automatically establish SAQ-A eligibility or compliance.
- **3DS / SCA challenge handling.** Use the PSP SDK's supported authentication and result contract; its UI can vary by payment method. Persist the order/attempt identifier before launch and reconcile with the backend after return or process recreation.
- **Single-tap recovery.** If the user is interrupted (call, app kill, OS update prompt), the checkout state survives. On return, reload the pending order and authoritative payment status; inventory, prices or the cart may have changed and may require explicit reconfirmation.

See [`security/auth-on-mobile.md`](../security/auth-on-mobile.md) for the session flow that wraps checkout.

### Search

- **Typeahead** with `debounce(120ms)` + `flatMapLatest` cancellation. Local trie for recent searches + popular catalog terms; remote BFF for personalised + canonical results.
- **Search Results Page (SRP)** built on Paging 3 + facet sidebar. Facets (brand, price range, rating) drive query refinement.
- **Click-through telemetry** with `queryId` correlation so server-side ranker learns from interaction signal.

See [`mobile-system-design/search.md`](../mobile-system-design/search.md), [`mobile-system-design/typeahead-autocomplete-search.md`](../mobile-system-design/typeahead-autocomplete-search.md).

### Recommendations

- Server-driven. Client receives a sorted list of product IDs hydrated with metadata.
- Multiple slots per screen (home, PDP "similar items," post-checkout "you might also like").
- Each slot tagged with a `recommendation_id` for attribution; downstream order data feeds the next training cycle.

### Flash Sale (Burst Capacity)

- **Server-side capacity gate.** Client queues for a slot during high-traffic launches. UX: a countdown screen with "You're #4,237 in line."
- **Pre-checkout warm-up.** The app pre-fetches user's address and payment method tokens before the sale opens to minimize click-to-checkout time.
- **Server-driven UX for sale-only screens.** Layout JSON for sale banners means marketing can iterate without an app release.

---

## Data Flow

### Add to Cart

```mermaid
sequenceDiagram
    participant UI
    participant VM as CartViewModel
    participant Repo as CartRepository
    participant Local as Room (cart_cache)
    participant Out as Outbox
    participant Api as Cart BFF

    UI->>VM: addItem(productId, qty=1, variantId)
    VM->>Repo: addItem(...)
    Repo->>Local: BEGIN transaction
    Repo->>Local: INSERT account-scoped cart_item (status=PENDING)
    Repo->>Out: INSERT mutation + stable idempotency key
    Repo->>Local: COMMIT transaction
    Local-->>VM: emit updated cart (Flow)
    VM->>UI: pending cart update
    Out->>Api: POST /v1/cart/items (Idempotency-Key)
    Api-->>Out: 200 OK canonical cart state
    Out->>Local: UPSERT items from canonical state
    Local-->>VM: emit reconciled cart
```

The optimistic insert is visually immediate; the server reconciliation arrives within 200-500ms and adjusts (e.g., if the item is out of stock, the optimistic add is undone with a snackbar).

### Checkout — Place Order

```mermaid
sequenceDiagram
    participant UI
    participant VM as CheckoutViewModel
    participant Repo as CheckoutRepository
    participant Api as Checkout BFF
    participant PSP as PSP SDK
    participant Room

    UI->>VM: placeOrder()
    VM->>Repo: createIntent(cartId)
    Repo->>Room: persist checkout operation + stable key
    Repo->>Api: POST /v1/orders (Idempotency-Key)
    Api-->>Repo: { orderId, paymentIntentClientSecret, requires3DS: false }
    Repo->>Room: persist intent (status=PENDING)
    Repo->>PSP: confirmPayment(clientSecret)
    alt 3DS challenge
        PSP->>UI: present provider-supported challenge
        UI-->>PSP: completion result
    end
    PSP-->>Repo: success | failure
    Repo->>Api: reconcile order/payment status
    Note over Api,PSP: Backend verifies provider status/webhooks
    Api-->>Repo: canonical status + orderId
    alt Verified PAID
        Repo->>Room: UPDATE intent (status=PAID)
        Repo-->>UI: Receipt
    else PENDING or processing
        Repo->>Room: retain pending operation/order
        Repo-->>UI: Payment status screen (not paid)
        Note over Repo,Api: Resume reconciliation on status updates/reconnect/resume
    else Failed or declined
        Repo->>Room: record failure and keep cart intact
        Repo-->>UI: Payment-failed recovery
    end
```

The backend binds the checkout operation to the order and verifies provider events/status independently of the client callback. Reconciliation on resume: if the app dies between `confirmPayment` and the next call, the Room-persisted operation and order ID let the app query authoritative state. On next launch, the Checkout screen detects a PENDING intent and queries `/v1/orders/{id}` for canonical state.

---

## Offline Strategy

- **Browsing: cached.** Recently-viewed categories and PDPs render from Room cache. New navigation is blocked offline (with a retry CTA).
- **Cart: read-locally, write-queued.** User can review cart and update quantities offline; mutations queue and sync on reconnect.
- **Checkout: blocked offline.** Placing an order requires a confirmed server transaction. Pre-checkout (selecting address, choosing payment method) can run offline if the data is already fetched.
- **Search: blocked offline.** Typeahead falls back to local recent-searches trie; remote results return an offline state.
- **Order history: cached.** Recently-viewed orders render from Room with a "showing offline data" badge.

The cart's offline write-queue is the most user-visible compromise. Tradeoff: enable browsing-only flows without network; require network for the money path.

---

## Security

- **Payment SDK isolation.** All card capture happens in the PSP SDK's surface; never in your app's TextField. The acquirer/compliance assessment determines the applicable PCI obligations; outsourcing capture does not prove eligibility.
- **Token storage.** Keep OAuth tokens in memory where possible; persist only a versioned ciphertext envelope protected by Android Keystore. Provider payment-method identifiers (for example, `pm_xxx`) are not necessarily short-lived credentials; keep their ownership and reuse server-controlled, and protect client secrets according to the provider contract.
- **Idempotency-Key on every mutation.** Cart-add, address-change, payment-confirm, refund-request.
- **Replay protection.** Server-issued nonces for high-value or sensitive actions.
- **HTTPS with normal certificate/hostname validation.** Optional pins on owned endpoints need a rotation/recovery policy; do not impose app-controlled pins on PSP SDK traffic without provider support. See [`security/certificate-pinning.md`](../security/certificate-pinning.md).
- **App Check / Play Integrity** to deter scripted checkout (sneaker bots in flash sales). Server-side verdict evaluation. See [`security/attestation.md`](../security/attestation.md).
- **No FLAG_SECURE by default**; some apps add it on the payment screen for privacy.
- **PII redaction** in logs and analytics. Address, phone, card-last-4 — all stripped. See [`mobile-system-design/security-and-privacy.md`](../mobile-system-design/security-and-privacy.md).
- **Coupon abuse defense.** Coupon codes server-validated; client never decides eligibility. Server enforces single-use, per-user limits.

---

## Observability

- **Funnel metrics**: PDP-view → add-to-cart → cart-view → begin-checkout → place-order. Each step has a conversion target and a regression alert.
- **Checkout abandonment** broken by stage (which step did they drop?). Each abandonment event carries the active cohort tags for experiment attribution.
- **Payment success rate** per PSP, per region, per payment method. A drop on a single card scheme is the canary for issuer changes.
- **Search latency** broken by query length and result set size.
- **Cart sync latency** — the time between local mutation and server ack. p95 < 500ms.
- **Flash sale capacity dashboard** — queue depth, slot grant rate, post-grant conversion. Real-time during sale events.

See [`observability/slis.md`](../observability/slis.md), [`observability/dashboards.md`](../observability/dashboards.md).

---

## Failure Modes

**Cart mutation succeeded server-side but ack lost in transit.** Idempotency key on retry returns the same canonical state; client UI reconciles. No double-add.

**Payment succeeded but the confirm-order API failed.** PSP charged the card; the app didn't get the order confirmation. *Mitigation:* Room-persisted intent + reconciliation on resume queries the canonical order state; the backend verifies provider status and reconciles the pending order. Show a receipt only after that confirmation; otherwise show processing/recovery status.

**Flash sale stampede crashes the BFF.** The catalog and the cart services share infrastructure; a sale brings down checkout for non-sale users. *Mitigation:* dedicated capacity for checkout vs sale-promo browsing; queueing UX absorbs spike client-side.

**Multiple cards declined; user retries with a third.** Distinguish a retry of the same attempt from an explicitly new payment attempt. Reconcile an unknown outcome before starting another charge; follow the provider's PaymentIntent/attempt contract. Server returns `payment_failed` with structured reason codes for UI mapping.

**Stock changes between cart-add and checkout-confirm.** Item out of stock at checkout time. *Mitigation:* checkout API returns `out_of_stock` with the affected line items; cart UI updates; user re-confirms.

**Coupon expires while user is checking out.** *Mitigation:* re-validate the coupon at the `confirm` step; if it expired, return error with new total; user re-confirms with updated price.

**Address validation fails post-payment.** *Mitigation:* validate address before payment; if validation must run server-side post-payment, do so on the *server* with a refund-and-retry path, never on the client.

**App killed during 3DS challenge.** OS killed the host activity. *Mitigation:* the provider may still be processing authentication. On resume, query the backend's order/payment state and complete any required action using the supported SDK flow; do not assume a browser or client callback preserves the whole checkout.

---

## Scaling

### Scaling user base

- Per-region BFFs for catalog, search, cart. Reduces latency and supports regional compliance.
- CDN-served images and product videos.
- Search queries served from a regional Elasticsearch / similar; cart writes serialized through the canonical cart service.

### Scaling catalog

- Multi-million SKU catalogs. Cursor/keyset pagination is often a good fit for changing catalogs; evaluate ordering, snapshot consistency and random-access needs. Paging 3 also supports positional/offset sources.
- Server-side ranking and filtering keeps client lean.
- Long-tail SKUs lazy-load image variants.

### Scaling flash sales

- Pre-warm: register interest in advance; backend pre-allocates capacity per region.
- Client-side queueing UX (countdown, queue position).
- Reserved checkout pool isolates from normal traffic.

### Scaling internationally

- Localized payment methods (UPI in India, iDEAL in NL, PIX in BR). PSP SDK varies; the `:core:psp` boundary swaps under the same `CheckoutRepository` interface.
- Localized tax engines server-side.
- App Bundle language splits for locale resources.
- Address formats per country (validated server-side).

---

## Release Strategy

- **Weekly release train** with crash-rate gating at 99.5%. See [`release-engineering/staged-rollouts.md`](../release-engineering/staged-rollouts.md).
- **Payment flow has tighter gates.** Crash-free target on the checkout module is 99.9%. A regression on checkout halts even if global metrics look fine.
- **Server-driven home + sale layouts.** The marketing team iterates without app releases via a layout-JSON service.
- **Kill switches** for every payment method, every promotion engine, every recommendation slot. See [`release-engineering/kill-switches.md`](../release-engineering/kill-switches.md).
- **Feature flags** for new checkout flows; old flow remains hot until 100% of users are on new.
- **In-app updates API** for security fixes (high-priority); flexible updates for feature releases.

---

## Summary of Technologies

| Layer | Choice | Why |
|---|---|---|
| UI | Jetpack Compose | Modern; rich product detail screens |
| State | ViewModel + StateFlow | Standard |
| Catalog pagination | Paging 3 + RemoteMediator | Cursor-based, offline cache |
| Images | Coil 3 | Compose-friendly, bounded memory |
| Persistence | Room | Cart cache, order history, recent searches |
| Cart truth | Server (BFF + canonical cart service) | Cross-device durability |
| Payment | PSP SDK (Stripe / Adyen / Razorpay) | PCI scope reduction |
| Network | OkHttp + Retrofit | Mature; Idempotency-Key interceptor |
| Tokens | Private ciphertext envelope | Direct Android Keystore key |
| DI | Hilt | Standard |
| Background | WorkManager | Outbox drain, analytics flush |
| Push | FCM (data + notification messages) | Order updates, promotions |
| Analytics | In-house SDK | Funnel attribution |

---

## Further Reading

- [Stripe Android payment integration](https://github.com/stripe/stripe-android)
- [Verify payment status and webhook outcomes](https://docs.stripe.com/payments/payment-intents/verifying-status)
- [Stripe idempotency contract and retention](https://docs.stripe.com/api/idempotent_requests)
- [PCI integration scope is assessed, not inferred](https://docs.stripe.com/security/guide)
- [PCI SSC SAQ eligibility criteria](https://www.pcisecuritystandards.org/faqs/1443/)
- [Coil image loader configuration](https://coil-kt.github.io/coil/image_loaders/)
- [SQLite transaction boundaries](https://www.sqlite.org/lang_transaction.html)
- [PagingSource models](https://developer.android.com/topic/libraries/architecture/paging/v3-paged-data)

---

## Related

- [`mobile-system-design/payment-flow.md`](../mobile-system-design/payment-flow.md) — checkout reasoning exercise.
- [`mobile-system-design/search.md`](../mobile-system-design/search.md), [`mobile-system-design/typeahead-autocomplete-search.md`](../mobile-system-design/typeahead-autocomplete-search.md) — search subsystem.
- [`mobile-system-design/pagination.md`](../mobile-system-design/pagination.md) — Paging 3 patterns.
- [`distributed-systems/idempotency.md`](../distributed-systems/idempotency.md) — why every mutation carries a key.
- [`security/attestation.md`](../security/attestation.md) — bot defense for flash sales.
- [`consumer-app.md`](consumer-app.md) — sibling blueprint; same scale, different trade-offs.

---

> **In short:** E-commerce optimizes for conversion. Cart durability is server-side; checkout is reconciliation-safe through idempotency keys and Room-persisted intents; payment capture lives in the PSP SDK to keep PCI scope minimal; flash sales get dedicated capacity. Where consumer apps optimize for engagement velocity, e-commerce optimizes for the money path.
