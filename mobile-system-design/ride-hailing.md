# Ride-Hailing (Uber / Lyft-style)

> A 45-60 minute mobile system-design walkthrough for a ride-hailing client (Android-first). The dispatch algorithm, H3 hexagonal indexing, and surge engine live on the backend — the bulk of this file is what the *Android apps* (rider + driver) do: location streaming, foreground service discipline, the trip state machine, and battery survival.

---

## 1. Gathering Requirements (~5 min)

> **Interviewer:** "Design a ride-hailing app like Uber."
> **Candidate:** "Two clients, very different battery profiles: rider is bursty, driver streams location continuously. I'll deep-dive driver location streaming + the trip state machine, since that's the hard mobile problem."

### Functional Requirements
- **Rider:** request a ride, see nearby cars on a map, get matched, track driver, complete trip.
- **Driver:** go online, receive offers, accept/decline, navigate to pickup, complete trip.
- **Both apps:** real-time location updates, in-trip ETAs, push notifications for state changes.

### Non-Functional Requirements
- **Driver app must work all day** (8-12 hours) on a single charge — battery is critical.
- **Trip state machine must be authoritative server-side**, with both apps converging on the same state.
- **Location accuracy** under 50 m in city, under 100 m on highway.
- **Offline tolerance** — queue location pings; don't lose a trip if a tunnel kills signal for 2 minutes.
- **Compliance** — show driver earnings, surge transparency, post-trip receipts.

### Out of Scope
- Pricing / surge calculation (server-side)
- Background fare estimation
- Driver onboarding, document verification
- In-app chat (separate file — see `chat-messaging.md`)
- Payment (separate file — see `payment-flow.md`)
- Route optimization internals (we call the routing SDK as a black box)

---

## 2. Clarifying Questions (~3 min)

| Question | Why it matters |
|---|---|
| Rider or driver app focus? | Different lifecycle, different battery profile |
| Geography / market? | GPS accuracy expectations vary by density |
| Android API floor? | Foreground service rules, location permission tiers |
| Trip density per driver per hour? | Local cache, push frequency |
| Two-way chat in scope? | Reuse chat module or scope out |
| Maps SDK? | Google Maps SDK, Mapbox, or HERE |
| Routing/navigation in-app or hand off? | If in-app, +ExoPlayer-style architecture for the map |
| Fleet partner integrations? | Identity, trip handoff |

> **Candidate:** "Focus on driver app primarily, rider as secondary. Google Maps SDK + Routes API, urban + suburban, 1-2 trips/hour for a typical driver, Android 9+, in-app chat reuses the messaging stack."

---

## 3. High-Level Diagram (~10 min)

```
   ┌────────────┐         ┌────────────┐
   │ Rider App  │         │ Driver App │
   │ (this talk)│         │ (this talk)│
   └─────┬──────┘         └─────┬──────┘
         │ HTTPS / WSS          │ HTTPS / WSS + frequent POSTs
         └──────────┬───────────┘
                    ▼
       ┌──────────────────────────┐
       │     BFF / Trip API       │
       │ (auth, rate limit, fan)  │
       └──┬─────────┬───────┬─────┘
          │         │       │
    ┌─────▼──┐ ┌────▼───┐ ┌─▼─────┐
    │Location│ │Dispatch│ │ Push  │
    │ Index  │ │ Engine │ │ (FCM) │
    └────────┘ └────────┘ └───────┘
```

**Server-side (named, not designed):**
- **BFF / Trip API** — auth, trip CRUD, websocket fan-out.
- **Location Index** — H3 hex index of online drivers (black box).
- **Dispatch Engine** — picks driver for rider request (black box).
- **Push (FCM)** — high-priority offers, state changes.

---

## 4. API Contract

### Driver location upstream (frequent)

```json
POST /v1/driver/location          // batch, every 4s online
{
  "pings": [
    { "lat": 37.7749, "lng": -122.4194, "accuracy": 5.2,
      "speed": 12.3, "bearing": 95, "t": 1750000000123 },
    { "lat": 37.7751, "lng": -122.4192, "accuracy": 4.8, ..., "t": 1750000004123 }
  ],
  "tripId": "t_42"   // null if not on trip
}
```

### Trip state (server → both apps, via WebSocket)

```json
{ "type": "trip.update", "tripId": "t_42",
  "state": "DRIVER_EN_ROUTE",       // OFFERED, ACCEPTED, DRIVER_EN_ROUTE, ARRIVED, IN_TRIP, COMPLETED, CANCELLED
  "driver": { "lat": ..., "lng": ..., "eta": 240, "bearing": 95 },
  "v": 7                              // monotonic version
}
```

### Rider request (REST)

| Method | Path | Use |
|---|---|---|
| `POST` | `/v1/trips` | Request a ride (`Idempotency-Key` header) |
| `GET` | `/v1/trips/{id}` | Poll/recover canonical state |
| `POST` | `/v1/trips/{id}/cancel` | Idempotent cancel |
| `GET` | `/v1/drivers/nearby?lat=…&lng=…` | Map ghosts (rate-limited) |

### Driver offer (FCM data message)

```json
{ "type": "ride.offer", "tripId": "t_42", "expiresAt": 1750000020000,
  "pickup": {"lat": ..., "lng": ...}, "estPay": "$8.50" }
```

> **Idempotency:** rider's `POST /v1/trips` uses an `Idempotency-Key` so a retry after a dropped response doesn't create two trip requests.

---

## 5. Mobile App Architecture (~10 min)

### Module structure (shared across two apps)

```
:app-rider
:app-driver
:feature:map               ← shared map composable
:feature:trip              ← shared state-machine UI
:feature:driver-online     ← driver-only: go-online toggle
:feature:rider-request     ← rider-only: pickup/dropoff entry
:core:network              ← OkHttp + Retrofit + WebSocket
:core:database             ← Room
:core:location             ← Fused + foreground service
:core:notifications        ← FCM + MessagingStyle
:core:work                 ← LocationFlushWorker
:domain:trip
:data:trip
```

### Layered diagram

```
   Compose UI ──► TripViewModel ──► TripRepository
                                       │
                                       ├─► TripSocket (WebSocket, StateFlow<TripUpdate>)
                                       ├─► TripApi (REST, idempotency)
                                       ├─► LocationSource (FusedLocationProvider)
                                       │      └─► LocationFgService (driver) / one-shot (rider)
                                       └─► Room (active trip, location buffer)
```

### Key class signatures

```kotlin
interface TripRepository {
    fun activeTrip(): Flow<Trip?>
    suspend fun request(pickup: LatLng, dropoff: LatLng): Result<Trip>
    suspend fun cancel(tripId: String): Result<Unit>
    fun connectionState(): StateFlow<ConnectionState>
}

interface LocationSource {
    fun stream(intervalMs: Long = 4_000, accuracy: Priority): Flow<Location>
    suspend fun lastKnown(): Location?
}
```

---

## 6. Local Storage (Room)

```kotlin
@Entity(tableName = "trips")
data class TripEntity(
    @PrimaryKey val id: String,
    val state: TripState, val role: Role,           // RIDER, DRIVER
    val pickupLat: Double, val pickupLng: Double,
    val dropoffLat: Double, val dropoffLng: Double,
    val driverId: String?, val riderId: String?,
    val version: Int, val updatedAt: Long
)

@Entity(tableName = "location_buffer")
data class LocationPing(
    @PrimaryKey val id: String, val tripId: String?,
    val lat: Double, val lng: Double, val accuracy: Float,
    val speed: Float, val bearing: Float, val t: Long,
    val sent: Boolean
)
```

> **Probing Q:** "Why buffer locations in Room and not in memory?" Because tunnels exist. A driver going under a 90-second tunnel must not lose their location trail — the worker drains the buffer on reconnect.

---

## 7. Deep Dive: Driver Location Streaming + Trip State Machine (~15 min)

> *Driver-side location is a continuous foreground operation. Getting it wrong drains the battery, gets the app killed by OEMs, or — worst — drops the trip mid-route. The state machine is the second pillar: both apps must converge on the same authoritative state from the server.*

### Foreground service for active drivers

```kotlin
class DriverLocationService : LifecycleService() {

    override fun onCreate() {
        super.onCreate()
        ServiceCompat.startForeground(
            this, NOTIF_ID, buildOngoingNotification(),
            FOREGROUND_SERVICE_TYPE_LOCATION
        )
        lifecycleScope.launch {
            locationSource.stream(intervalMs = 4_000, Priority.HIGH_ACCURACY)
                .collect { loc ->
                    bufferDao.insert(loc.toEntity(tripId = activeTripId))
                    flushIfDue()
                }
        }
    }
}
```

`FOREGROUND_SERVICE_TYPE_LOCATION` is mandatory on Android 14+. The service runs only while the driver is online or on a trip — never otherwise.

### LocationSource over Fused Provider

```kotlin
class FusedLocationSource @Inject constructor(
    private val client: FusedLocationProviderClient,
) : LocationSource {
    override fun stream(intervalMs: Long, accuracy: Priority): Flow<Location> = callbackFlow {
        val request = LocationRequest.Builder(intervalMs)
            .setPriority(accuracy.toFused())
            .setMinUpdateDistanceMeters(5f)
            .setWaitForAccurateLocation(false)
            .build()
        val cb = object : LocationCallback() {
            override fun onLocationResult(r: LocationResult) {
                r.locations.forEach { trySend(it) }
            }
        }
        client.requestLocationUpdates(request, cb, Looper.getMainLooper())
        awaitClose { client.removeLocationUpdates(cb) }
    }
}
```

### Batching + upstream flush

| Condition | Action |
|---|---|
| Buffer ≥ 5 pings AND online | POST batch immediately |
| Network drops | Stop POSTing; pings accumulate in Room |
| Reconnect | Flush oldest-first; `sent=true` on success |
| App backgrounded but on trip | Service stays alive (notification visible) |
| Trip ends | Stop service after final ping flushed |

### Battery discipline

- **Adaptive interval:** 4 s normal, 10 s when stationary (speed < 1 m/s for 60 s), 1 s when ETA < 30 s to next state transition.
- **Doze + App Standby Buckets:** foreground service exempts the app while on trip. Off-trip, the location worker uses periodic WorkManager — not a service.
- **Wake lock:** none. The foreground service notification + system location callbacks are sufficient.
- **CPU:** all map drawing on the GPU surface; never decode polylines on the main thread.

### Trip state machine

```
OFFERED ──accept──► ACCEPTED ──driver depart──► DRIVER_EN_ROUTE
                                                       │
                                            driver arrives at pickup
                                                       ▼
                                                    ARRIVED
                                                       │
                                                rider boards / driver swipes
                                                       ▼
                                                   IN_TRIP
                                                       │
                                                dropoff reached
                                                       ▼
                                                  COMPLETED
                                                       │
                                            (CANCELLED can branch from any non-terminal state)
```

The **server is authoritative**. Both apps receive `trip.update` over WebSocket; if local optimistic state diverges from `v` versioning, server wins.

```kotlin
@Composable
fun TripScreen(vm: TripViewModel = hiltViewModel()) {
    val trip by vm.trip.collectAsStateWithLifecycle()
    when (trip?.state) {
        OFFERED          -> OfferSheet(trip, vm::accept, vm::decline)
        ACCEPTED, DRIVER_EN_ROUTE -> NavigateToPickupMap(trip)
        ARRIVED          -> WaitingForRider(trip)
        IN_TRIP          -> NavigateToDropoffMap(trip)
        COMPLETED        -> ReceiptSheet(trip)
        CANCELLED        -> CancelledSheet(trip)
        null             -> HomeMap()
    }
}
```

### WebSocket lifecycle (driver app on duty)

| Event | Action |
|---|---|
| Driver toggles "go online" | Start foreground service + connect socket |
| App backgrounded but on trip | Keep socket; service maintains foreground state |
| App backgrounded + offline (idle driver) | Disconnect; rely on FCM `ride.offer` data push |
| Socket drop | Exponential backoff with jitter (1, 2, 4, 8 s, capped at 30 s) |
| Network restored | Reconnect, request `/v1/trips/{id}` to reconcile any missed state |
| Driver goes offline | Disconnect socket, stop service |

### Failure modes

| What breaks | Behavior |
|---|---|
| Tunnel (60-120 s no signal) | Buffer pings in Room; flush on reconnect; trip resumes |
| OEM kills the service | Foreground notification + `FOREGROUND_SERVICE_TYPE_LOCATION` minimize this; warn driver in onboarding |
| Process death mid-trip | On launch, `activeTrip()` Flow restores UI; reconcile via REST |
| GPS lost (urban canyon) | Show stale-location badge; fall back to network location |
| Driver rejects offer twice in a row | Server takes them off the queue briefly |
| Rider cancels after pickup | State → CANCELLED; driver app shows reason |

---

## 8. Trade-offs

### Location API

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **FusedLocationProviderClient** | Best accuracy/battery balance, batching | Google Play Services dependency | Pick this |
| `LocationManager` (raw) | No GMS | Worse accuracy, more battery | Last-resort |
| Periodic WorkManager | Battery-friendly | Not real-time enough for active trip | Use when idle |
| FLP `getCurrentLocation` | One-shot fix | Not a stream | Use for one-shots |

### Background execution

| Option | When |
|---|---|
| **Foreground Service (LOCATION)** | Driver on duty / on trip |
| **WorkManager periodic** | Driver idle but waiting for offers (rare; usually FCM) |
| Plain background | Forbidden by platform for high-frequency location |
| Geofence APIs | "Driver arrived near pickup" event (low-power) |

### Real-time trip updates

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **WebSocket** | Low latency, bidirectional | Battery in deep background | Pick — foreground while on duty |
| **FCM data push** | Reaches killed app | Throttled | Pick — for ride offers |
| Polling | Trivial | Awful latency + battery | Skip |
| SSE | One-way | Can't send acks on same channel | Skip |

### Map SDK

| Option | Verdict |
|---|---|
| **Google Maps SDK + Routes API** | Pick for most regions — mature, polylines, traffic |
| Mapbox | Strong for custom styling, fewer GMS dependencies |
| HERE | Useful in fleet / enterprise contexts |
| OSMDroid | Acceptable if you must avoid Google but lacks polish |

### Idempotency for trip request

| Option | Verdict |
|---|---|
| **Client UUID `Idempotency-Key`** | Pick — same retry, same trip |
| Server-generated trip ID after creation | Doesn't help with retries before ID exists |

---

## 9. Major Concerns

- **Battery.** Adaptive intervals, foreground service only when on duty, no wake locks. Driver should see < 10% drop per active hour on a modern device.
- **OEM kill.** Xiaomi/OPPO/Vivo aggressively kill location services. Mitigations: foreground service + persistent notification, in-app guide to whitelist the app, FCM offers as backup wake.
- **Permissions UX.** Request `ACCESS_FINE_LOCATION` + `ACCESS_BACKGROUND_LOCATION` separately. Explain *why* in the rationale dialog. Handle "Approximate only" gracefully (degrade to coarse markers).
- **Process death mid-trip.** Room is the truth. On launch, `activeTrip()` Flow rehydrates UI. Service auto-restarts via `START_REDELIVER_INTENT`.
- **Map performance.** Tile cache + polyline simplification. Don't redraw the polyline every location update — animate marker only.
- **Network partition during state change.** WebSocket dropped between ACCEPTED and DRIVER_EN_ROUTE? On reconnect, fetch `/v1/trips/{id}` for canonical state. Don't trust local optimistic state across reconnects.
- **Privacy.** Location only transmitted while on duty. Don't log lat/lng in analytics; aggregate to H3 cell at L7 if you must.
- **Compliance.** Surge transparency, fare breakdown, refund flow, cancellation policy — all server-driven.
- **Accessibility.** Voice cues for driver (navigation runs over Bluetooth audio focus), large buttons, color-blind-friendly map markers.

---

## 10. Follow-up Questions

> **Q: Driver enters a 2-minute tunnel — what happens?**
> Service keeps running; location pings buffer to Room. Socket drops; backoff timer starts. On exit: pings flush oldest-first, socket reconnects, REST reconciles trip state. From the rider's perspective the dot pauses then jumps; we smooth client-side with interpolated marker animation.

> **Q: How do you prevent two trips for the same request?**
> `Idempotency-Key` on `POST /v1/trips`. Server returns the same `tripId` on retry. Client-side single-flight guard on the request button.

> **Q: Driver accepts, then app crashes — does the rider still see them?**
> Yes. Server already accepted. On driver-side launch, `activeTrip()` Flow rehydrates the active trip from Room (server pushed it before crash). UI lands on the navigation screen. Location service restarts on process boot.

> **Q: Why FCM for offers but WebSocket for trip updates?**
> Offers happen when driver may be idle/backgrounded — FCM wakes the app reliably. Once on a trip, the foreground service holds the socket open at low cost. WebSocket is lower-latency for the burst of updates during the trip.

> **Q: How is the foreground service notification designed?**
> Persistent (low priority), shows trip state ("En route to pickup"), tappable to open trip screen. On Android 13+, requires `POST_NOTIFICATIONS` permission separately. Notification channel for "Trip" cannot be disabled while on trip (we explain why in onboarding).

> **Q: What about driver app on Android Auto?**
> Out of scope for this round; if asked, mention Android Auto SDK + Templates API; the data model already supports it because state is server-authoritative.

---

## 11. Out of Scope (defended)

- **Surge pricing logic** — pure backend.
- **Driver onboarding / KYC** — separate flow.
- **In-app chat** — reuses the `chat-messaging.md` stack.
- **Payment flow** — reuses `payment-flow.md`.
- **Route optimization internals** — Routes SDK is the black box.
- **Fleet / aggregator integrations** — separate, partner-specific.

---

## 12. Further Reading

- [weeeBox/mobile-system-design](https://github.com/weeeBox/mobile-system-design) — reference format.
- [Android Developers — Foreground services](https://developer.android.com/develop/background-work/services/foreground-services) — official guidance, including type=LOCATION.
- [FusedLocationProvider — best practices](https://developer.android.com/develop/sensors-and-location/location) — adaptive sampling, accuracy tiers.
- [Uber Engineering — H3 hexagonal index](https://www.uber.com/blog/h3/) — server-side spatial indexing (context only).
- [Android Developers — Background location guidance](https://developer.android.com/training/location/background) — permission UX and limits.

---

> **Closing in the interview:** "Driver location + trip state was my deep dive because it's the hardest mobile problem in this product. Happy to take rider-side ETA polling, the offer accept/decline race, or the FCM-to-foreground-service handshake next."
