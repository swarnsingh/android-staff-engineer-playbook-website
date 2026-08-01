# Media3 & ExoPlayer: Player Architecture

Media playback is one of the few Android subsystems where a staff engineer routinely designs a *platform within the app*: one player stack shared by feed autoplay, full-screen playback, picture-in-picture, background audio, and offline downloads. Media3 (the successor packaging of ExoPlayer under `androidx.media3`, current stable 1.10.x as of mid-2026) is the assumed substrate; the interview and the production questions are about how you compose its pieces and what you own around them.

## 1. The Component Model

`ExoPlayer` is the default implementation of the `Player` interface — and that separation is the first architectural lever. UI, `MediaSession`, and your own orchestration code should depend on `Player`, not `ExoPlayer`; that keeps test fakes cheap and lets you wrap or swap implementations (e.g., a cast player) behind one contract.

An `ExoPlayer` instance is assembled from injectable components, each with a default you replace only with cause:

| Component | Job | Staff-level reason to touch it |
|---|---|---|
| `MediaSource` | Loads and parses the media (DASH, HLS, progressive) | Custom manifest handling, ad insertion, cache composition |
| `Renderer` | Decodes and renders one track type to output | Rarely — custom formats, audio processing chains |
| `TrackSelector` | Picks audio/video/text tracks per constraints | ABR caps (data saver, autoplay tiles at 360p), device-capability policy |
| `LoadControl` | Decides when to buffer more and when playback may start | Buffering economics — see below |

**Buffering economics.** `DefaultLoadControl` exposes the buffer policy via `setBufferDurationsMs(minBuffer, maxBuffer, bufferForPlayback, bufferForPlaybackAfterRebuffer)`: how much media must be buffered before starting, how much before resuming after a stall, and the range the player maintains during playback. The trade-off is genuinely two-sided: bigger buffers reduce rebuffering but raise startup latency, memory pressure, and wasted bytes when the user scrolls past an autoplaying video after two seconds. A feed player and a movie player should not share a `LoadControl` — small start-fast buffers for tiles, deep buffers for lean-back playback.

## 2. Session Layer: Background Playback and External Control

The `MediaSession` layer is what makes your player a citizen of the OS rather than a widget in one Activity:

- `MediaSessionService` hosts playback beyond your UI's lifecycle (background audio, the media notification).
- `MediaLibraryService` additionally serves a browsable content tree — this is the same surface Android Auto and Wear controllers browse.
- `MediaController` / `MediaBrowser` connect UI processes (or other apps, or the system) to the session.
- **Audio Focus:** Delegate focus management to Media3 with `player.setAudioAttributes(attributes, true)`. The player then ducks or pauses when another app takes focus and may resume after a transient focus loss; it does not automatically resume after permanent focus loss.

The architectural rule: **the session owns the player; UIs own controllers.** Activities connect and disconnect; playback continuity lives in the service. Most "playback stops when I rotate / background the app" bugs are ownership bugs, not player bugs.

## 3. Caching and Offline Downloads

Two distinct mechanisms that beginners conflate:

- **Streaming cache:** `CacheDataSource` layered over the network `DataSource`, backed by a `SimpleCache` — replays and scrub-backs hit disk instead of the network. This is transparent and best-effort.
- **Offline downloads:** `DownloadManager` manages durable, resumable downloads (with a `DownloadService` for progress and constraints). This is user-visible state with its own lifecycle — pause/resume, storage eviction policy, license renewal for DRM content — and deserves its own repository-layer treatment, not an afterthought inside the player module.

Design both against the same cache instance so a completed download also serves as the streaming cache for that item — double-downloading the same bytes is the classic waste here. Note `SimpleCache` allows only one instance per directory at a time (the class enforces a folder lock), and for the shared download cache the playback-side `CacheDataSource.Factory` should be read-only (`setCacheWriteDataSinkFactory(null)`) so streaming non-downloaded content doesn't silently populate the download store.

## 4. DRM

Widevine ships in two effective flavors: **L1** (hardware-backed pipeline — required by licensors for HD/UHD) and **L3** (software — typically capped to SD by content policy). `DefaultDrmSessionManager` handles license acquisition and renewal; your decisions are policy:

- **Fallback:** on devices where L1 is broken or unavailable, do you fall back to L3 at reduced resolution or fail playback? (Almost always: fall back, cap the track selection, log the device.)
- **Offline licenses:** downloaded content needs persistent licenses with their own expiry — renewal is a background-work problem (WorkManager), and a library full of downloaded video with expired licenses is a support-ticket generator.
- The pairing of DRM level and track selection is enforced in the `TrackSelector`: don't offer 1080p renditions to an L3 session.

## 5. Adaptive Streaming

DASH and HLS support is native; the player's ABR logic shifts renditions with throughput. What you own is the *constraint envelope*: maximum resolution by surface (a 200 dp feed tile never needs 1080p), by network class (metered vs unmetered — see [NetworkCallback & Metered Networks](../networking-and-security/networkcallback-metered-vpn-captive-portal.md)), and by user setting (data saver). Serving fewer bytes than the algorithm would happily fetch is usually the biggest cost and battery win available in a media app.

## 6. Player-as-Platform: the Single-Instance Question

Decoders are a constrained hardware resource; every live `ExoPlayer` holds one or more. The standard scaled architecture is a small **player pool** (often size 1–2) owned by a playback module:

- Feed autoplay acquires a pooled player, binds it to the visible tile, releases on scroll-away.
- Full-screen playback *transfers* the same player (position, buffered data, and state travel with it) instead of re-preparing — this is what makes tile→full-screen transitions instant.
- `release()` is not optional; leaked players exhaust codecs for the whole device, and the failure shows up in *other* apps too.

## 7. Observability

Instrument the player, not just the app: startup time (prepare→first frame), rebuffer ratio (stall time / play time), ABR distribution (time at each rendition), DRM failures by device model, and download success rates. Media3's analytics listener surface exists for exactly this — wire it into your [Telemetry SDK](../../mobile-system-design/telemetry-sdk.md) rather than logging ad hoc. Rebuffer ratio and startup time are the two numbers worth an SLO; both regress silently with CDN or manifest changes, not app releases, so alert on them independently of release monitoring.

## 8. Compose Integration

Media3 1.10 added a Compose UI layer split across two artifacts: **`media3-ui-compose-material3`** provides the out-of-the-box widgets — the `Player` composable with controls, `ProgressSlider`, `PlayPauseButton`, and the other Material 3-styled components — while the core **`media3-ui-compose`** holds the unstyled surface layer (`PlayerSurface`, `ContentFrame`) and state holders. Depend on the Material 3 artifact for ready-made player UI; drop to the core module when you're theming from scratch. Either way it beats hand-wrapping `PlayerView` in `AndroidView` for new surfaces. Older codebases embedding `PlayerView` via `AndroidView` interop should migrate surface-by-surface following [View Interop & Compose Migration](../compose/view-interop-and-migration.md).

## Further Reading

- [Media3 ExoPlayer overview](https://developer.android.com/media/media3/exoplayer) — component model, customization points
- [Media3 releases](https://developer.android.com/jetpack/androidx/releases/media3) — current versions and release notes
- [Media3 1.10 announcement](https://android-developers.googleblog.com/2026/03/media3-110-is-out.html) — Compose playback widgets, dynamic scheduling
- [YouTube / Video Streaming design](../../mobile-system-design/youtube-video-streaming.md) — the system-design view this file implements
