# Maps + Location System (Google Maps-style)

> A 45-60 minute mobile system-design walkthrough for a maps + location app (Google Maps, Apple Maps): map rendering, location streaming, search, turn-by-turn nav. The tile server and routing engine are server problems — bulk is on-device.

---

## 1. Gathering Requirements (~5 min)

> **Interviewer:** "Design a Maps + Location app."
> **Candidate:** "The interesting mobile problems are: continuous location with battery discipline, map tile cache, offline maps, and turn-by-turn navigation lifecycle. I'll deep-dive turn-by-turn nav."

### Functional Requirements
- **Show user's location** on a map with accuracy halo.
- **Search for places** (POIs).
- **Routes** (driving, walking, transit).
- **Turn-by-turn nav** with voice + visual cues.
- **Offline maps** for a downloaded region.

### Non-Functional Requirements
- **Battery**: nav can run for hours; don't drain phone.
- **Accuracy** under 50 m city, 100 m highway.
- **Offline tolerance** — downloaded region works without signal.
- **Smooth pan/zoom** — 60 Hz interaction.
- **Privacy** — location only when needed; surface why.

### Out of Scope
- Tile server / map data ingestion
- Routing algorithm internals (server)
- POI data freshness pipeline
- Reviews / ratings UX
- Local guide / contributor flows
- AR walking nav (Live View)

---

## 2. Clarifying Questions (~3 min)

| Question | Why it matters |
|---|---|
| Map SDK (Google, Mapbox, HERE)? | Architecture choices |
| Offline map size budget? | Disk strategy, format |
| Voice nav languages? | TTS engine selection |
| Background nav (driving over screen-off)? | Foreground service required |
| Battery target during nav (% per hour)? | Sampling cadence |
| Lane guidance / AR? | UI complexity |
| Wear / Auto / CarPlay? | Multi-surface architecture |

> **Candidate:** "Google Maps SDK, 1-2 GB offline regions, multilingual TTS, background nav supported, < 8% battery/hour, no AR, Auto considered."

---

## 3. High-Level Diagram (~10 min)

```
        Mobile Client (this talk)
   ┌──────────────────────────────────┐
   │  MapView + render layers         │
   │  LocationSource (Fused)          │
   │  Offline tile cache              │
   │  NavSession (turn-by-turn)       │
   │  TTS engine                      │
   └──────────────┬───────────────────┘
                  │ HTTPS
                  ▼
   ┌──────────────────────────────────┐
   │ BFF / Routing API (black box)    │
   │  /tiles, /search, /directions    │
   └──────────────────────────────────┘
```

**Components:**
- **`MapView`** — SDK-provided; we control layers, markers, polylines.
- **`LocationSource`** — Fused; same as `ride-hailing.md`.
- **`OfflineTileCache`** — pre-downloaded regions; disk-backed.
- **`NavSession`** — state machine for an active route.
- **`TTS`** — `TextToSpeech` for spoken cues.

---

## 4. API Contract

### Search

```http
GET /v1/search?q=coffee&lat=37.77&lng=-122.42&radius=2000
{ "places": [ { "id": "p_1", "name": "Blue Bottle", "lat": ..., "lng": ..., "rating": 4.5 } ] }
```

### Directions

```http
POST /v1/directions
{ "from": {"lat": 37.77, "lng": -122.42}, "to": {"lat": 37.79, "lng": -122.40}, "mode": "driving" }

{
  "routes": [{
    "polyline": "encoded:abc123...",
    "distanceMeters": 3420, "durationSec": 540,
    "steps": [
      { "instruction": "Head north on Main St", "polyline": "...", "distanceM": 120, "maneuver": "STRAIGHT" },
      ...
    ],
    "warnings": [], "trafficSummary": "Light"
  }]
}
```

### Tile download (offline region)

```http
GET /v1/tiles/download?bbox=...&zoomRange=10-17
{ "bundleUrl": "https://cdn/.../tiles_8f7a.mbtiles", "sizeBytes": 248_000_000 }
```

---

## 5. Mobile App Architecture

### Module structure

```
:app
:feature:map
:feature:nav
:feature:offline-maps
:core:network
:core:database
:core:location           ← from ride-hailing.md
:core:tts
:data:directions
:data:tiles
```

### Layered diagram

```
   MapScreen (Compose) ──► MapViewModel
                                 │
                                 ├─► LocationSource (Fused stream)
                                 ├─► DirectionsRepo (REST)
                                 ├─► OfflineRegionsRepo (DAO + download manager)
                                 └─► NavSession (state)
                                          │
                                          ├─► TtsEngine (announcer)
                                          ├─► RerouteController
                                          └─► ForegroundService (when actively navigating)
```

### Key class signatures

```kotlin
class NavSession(private val route: Route, private val location: LocationSource, ...) {
    val state: StateFlow<NavState>
    fun start()
    fun stop()
    fun onLocation(loc: Location)
}

sealed class NavState {
    object Idle : NavState()
    data class Navigating(val currentStepIndex: Int, val distanceToTurnM: Float, val etaSec: Int) : NavState()
    data class Rerouting(val reason: RerouteReason) : NavState()
    data class Arrived(val arrivedAt: Long) : NavState()
}
```

---

## 6. Local Storage

```kotlin
@Entity(tableName = "offline_regions")
data class OfflineRegion(
    @PrimaryKey val id: String, val name: String,
    val bboxJson: String, val zoomMin: Int, val zoomMax: Int,
    val sizeBytes: Long, val downloadedAt: Long, val ttlDays: Int = 90
)

@Entity(tableName = "recent_places")
data class RecentPlace(@PrimaryKey val id: String, val name: String, val lat: Double, val lng: Double, val lastUsedAt: Long)

@Entity(tableName = "saved_places")
data class SavedPlace(@PrimaryKey val id: String, val label: String, val name: String, val lat: Double, val lng: Double)
```

Tiles themselves live in an MBTiles / SQLite file outside Room, in `filesDir/offline/<regionId>.mbtiles`.

---

## 7. Deep Dive: Turn-by-Turn Navigation (~15 min)

> *I'd pick this as the deep dive because nav combines location streaming, route progress, TTS announcements, reroute logic, and foreground-service discipline — almost every mobile concern in one feature.*

### NavSession state machine

```kotlin
class NavSession @Inject constructor(
    private val ttsEngine: TtsEngine,
    private val location: LocationSource,
    private val routing: DirectionsRepository,
) {
    private val _state = MutableStateFlow<NavState>(NavState.Idle)
    val state = _state.asStateFlow()

    private var activeRoute: Route? = null
    private var currentStep = 0

    suspend fun start(route: Route) {
        activeRoute = route
        currentStep = 0
        _state.value = NavState.Navigating(0, distanceToTurnM = route.steps[0].distanceM.toFloat(), etaSec = route.durationSec)
        location.stream(intervalMs = 1_000, accuracy = Priority.HIGH_ACCURACY)
            .collect { loc -> onLocation(loc) }
    }

    fun onLocation(loc: Location) {
        val route = activeRoute ?: return
        val step = route.steps[currentStep]
        val distanceToTurn = step.distanceFromCurrentPosition(loc)

        if (distanceToTurn < ARRIVAL_THRESHOLD_M && currentStep == route.steps.size - 1) {
            _state.value = NavState.Arrived(clock.now())
            return
        }

        if (distanceToTurn < ADVANCE_TO_NEXT_STEP_M) {
            currentStep++
            announce(route.steps[currentStep].instruction)
        } else if (distanceToTurn < UPCOMING_ANNOUNCE_M && !announcedUpcoming) {
            announce("In ${(distanceToTurn / 100).roundToInt() * 100} meters, ${step.instruction}")
            announcedUpcoming = true
        }

        if (loc.distanceTo(route.expectedPosition(currentStep)) > OFF_ROUTE_THRESHOLD_M) {
            triggerReroute(loc, route.destination)
            return
        }

        _state.value = NavState.Navigating(currentStep, distanceToTurn, recomputeEta(route, currentStep, loc))
    }

    private suspend fun triggerReroute(loc: Location, destination: LatLng) {
        _state.value = NavState.Rerouting(RerouteReason.OFF_ROUTE)
        val new = routing.directions(from = loc.toLatLng(), to = destination)
        activeRoute = new
        currentStep = 0
        _state.value = NavState.Navigating(0, ..., ...)
    }
}
```

### Foreground service (driving over screen-off)

```kotlin
class NavForegroundService : LifecycleService() {

    @Inject lateinit var session: NavSession

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        ServiceCompat.startForeground(
            this, NOTIF_ID,
            buildNavNotification(session.state.value),
            FOREGROUND_SERVICE_TYPE_LOCATION
        )
        lifecycleScope.launch {
            session.state.collect { state ->
                NotificationManagerCompat.from(this@NavForegroundService).notify(NOTIF_ID, buildNavNotification(state))
                if (state is NavState.Arrived) stopSelf()
            }
        }
        return START_REDELIVER_INTENT
    }
}
```

Persistent notification with current instruction + distance. User can return to nav from any screen.

### TTS announcements

```kotlin
class TtsEngine @Inject constructor(@ApplicationContext ctx: Context) {
    private val tts = TextToSpeech(ctx, ::onInit)
    private val queue = MutableSharedFlow<String>(replay = 0, extraBufferCapacity = 32)

    private fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            tts.language = Locale.getDefault()
            tts.setSpeechRate(1.0f)
        }
    }

    fun speak(text: String, priority: Priority = Priority.NORMAL) {
        tts.speak(text, if (priority == Priority.HIGH) QUEUE_FLUSH else QUEUE_ADD, null, text.hashCode().toString())
    }
}
```

Voice ducking: lower music volume during announcement via `AudioFocusRequest`.

### Map rendering

The SDK does most of the lifting. We overlay:
- Current location marker (animated rotation by `bearing`).
- Route polyline (decoded from server response).
- Step markers at each maneuver.
- ETA / instruction card pinned at top.

### Battery discipline

- Adaptive location interval: 1s while approaching turn, 4s straight road, 10s stationary.
- TTS only at announcement points, not continuous.
- Don't redraw polyline every location update; animate marker only.

### Offline regions

```kotlin
class OfflineRegionsRepository @Inject constructor(
    private val workManager: WorkManager,
    private val dao: OfflineRegionDao,
    private val downloader: DownloadManager,
) {
    suspend fun downloadRegion(bbox: BoundingBox, name: String, zoomRange: IntRange) {
        val regionId = UUID.randomUUID().toString()
        dao.insert(OfflineRegion(regionId, name, bbox.toJson(), zoomRange.first, zoomRange.last, sizeBytes = 0, downloadedAt = 0))
        val descriptor = api.requestOfflineBundle(bbox, zoomRange)
        downloader.enqueue(DownloadRequest(
            url = descriptor.bundleUrl,
            destFile = File(filesDir, "offline/$regionId.mbtiles"),
            constraints = Constraints(networkType = NetworkType.UNMETERED, requiresStorageNotLow = true),
        ))
    }
}
```

Reuses the `file-downloader.md` library.

### Failure modes

| What breaks | Behavior |
|---|---|
| Tunnel / no GPS | Last known location dimmed; "GPS lost" badge; nav pauses until signal back |
| Off route | Reroute triggers; "Recalculating" announcement |
| TTS engine unavailable | Visual cues only; haptic at turns |
| Foreground service killed by OEM | Persistent notification + STIRR; user warned in onboarding |
| Offline region expired (TTL) | Show "update available"; downgrade quality if missing tiles |
| Routing API down | Use cached recent route to destination if available; otherwise error |
| Battery critical | Reduce location frequency; warn user |

---

## 8. Trade-offs

### Map SDK

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **Google Maps SDK** | Comprehensive; navigation toolkit | Cost at scale; GMS dependency | Pick for most apps |
| Mapbox | Customizable styling; offline support | Cost; smaller ecosystem | Strong alternative |
| HERE Maps | Enterprise / fleet | License complexity | Niche |
| OSMDroid | OSS; OSM data | Limited polish | When GMS unavailable |

### Offline format

| Option | Verdict |
|---|---|
| **MBTiles (SQLite)** | Pick — single file, transactional |
| Individual PNG tiles | Many small files; FS pressure |
| Vector tiles (`.pbf`) | Better; supported by Mapbox |

### Location stream

| Sampling | When |
|---|---|
| 1 s, HIGH_ACCURACY | Active nav, approaching turn |
| 4 s, HIGH_ACCURACY | Active nav, straight road |
| 10 s, BALANCED | Stationary detected |
| One-shot | Search results, "my location" button |

### Foreground service vs background nav

| Option | Verdict |
|---|---|
| **Foreground service while nav active** | Pick — required for reliable background updates |
| Plain background | OS will kill, especially on aggressive OEMs |
| Wake-locks | Don't; FGS handles wake correctly |

### Routing transport

| Option | Verdict |
|---|---|
| **REST polling for reroute** | Pick — simple |
| WebSocket for live traffic | Use only if features warrant |
| Local routing | Possible offline; usually too large to ship |

---

## 9. Major Concerns

- **Battery during nav.** Adaptive intervals, no wakelocks, FGS only when needed. Target < 8%/hour.
- **Permission UX.** ACCESS_FINE_LOCATION + ACCESS_BACKGROUND_LOCATION explained separately. Honour "approximate only" by degrading accuracy.
- **OEM kill.** FGS + persistent notification + `FOREGROUND_SERVICE_TYPE_LOCATION` minimize. Educate user during onboarding.
- **TTS robustness.** Honour audio focus; duck music; handle missing voices gracefully.
- **Privacy.** Location only while nav active. Don't log raw lat/lng; aggregate to H3 cell.
- **Process death.** Nav session state in Room; resume on foreground service restart.
- **Offline expiration.** Auto-prompt to refresh expired regions when on Wi-Fi.
- **Accessibility.** Voice cues + haptics for vision-impaired drivers; large buttons; readable in glance.
- **Data usage.** Tile prefetch only on Wi-Fi by default; user-overridable.

---

## 10. Follow-up Questions

> **Q: User goes into a long tunnel mid-nav — what happens?**
> Location stream stalls; UI shows "GPS lost" but doesn't say "rerouting". Nav state stays at current step. On exit, location resumes, distance-to-turn recalculates, nav continues seamlessly. Announce nothing during the gap to avoid confusion.

> **Q: How is "you're off route" detected?**
> Project current location onto the route polyline; compute perpendicular distance. If > threshold (e.g., 50 m) for > 5 s, trigger reroute. Don't fire on a single bad GPS sample.

> **Q: How do you handle multi-screen (phone + Android Auto)?**
> Auto has its own `CarAppService` + `TemplateAPI`. NavSession is the model; both UIs subscribe. Phone-side notification mirrors what Auto shows.

> **Q: How are voice prompts kept reasonable?**
> Distance-based: "In 500 m, turn left" → "In 200 m, turn left" → "Turn left now." Don't repeat the current step. Pause music with audio ducking, not stopping.

> **Q: What about lane guidance and complex intersections?**
> Server returns per-step `lanes` (array of preferred lanes). UI renders chevrons. Out of detailed scope here.

> **Q: How are routes cached for offline reuse?**
> Last 3 routes per destination cached for 24h. If the user starts the same route while offline, we use the cached polyline + steps. Reroute won't work without network.

---

## 11. Out of Scope (defended)

- **Tile server / data pipeline** — backend.
- **Routing algorithm internals** — server (graph search, traffic-weighted edges).
- **POI freshness** — data engineering side.
- **AR navigation (Live View)** — separate stack.
- **Reviews / ratings UX** — separate feature.

---

## 12. Further Reading

- [Google Maps SDK for Android](https://developers.google.com/maps/documentation/android-sdk/overview) — official.
- [Mapbox Maps SDK Android](https://docs.mapbox.com/android/maps/guides/) — alternative SDK.
- [FusedLocationProvider best practices](https://developer.android.com/develop/sensors-and-location/location) — battery-aware location.
- [MBTiles spec](https://github.com/mapbox/mbtiles-spec) — offline tile format.
- [Android Developers — Android Auto](https://developer.android.com/training/cars) — multi-surface nav.

---

> **Closing in the interview:** "Turn-by-turn was my deep dive because it stitches together location, route, TTS, and foreground service discipline. Happy to dig into offline-region downloads, Auto integration, or the reroute heuristic next."
