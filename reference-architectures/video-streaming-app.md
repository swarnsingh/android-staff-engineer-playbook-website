# Blueprint: The Video Streaming App (OTT / VOD)

## 1. Architectural Signature
A Video Streaming App (e.g., Netflix, YouTube, Disney+) is optimized for **Bandwidth Adaptation, Hardware Decoding, and Digital Rights Management (DRM)**.
The architecture is fundamentally a giant media player. UI screens exist solely to funnel the user into the Player Activity. Network reliability is not just about REST APIs; it is about sustaining a massive, continuous download stream of binary video chunks.

**Core Trade-off:** Video Quality (Resolution) vs Buffer Latency (Stuttering).

## 2. Component Blueprint

### Presentation Layer (The Player & The Feed)
- **Framework:** Compose for the Catalog, but the actual Video Player is usually deeply tied to `SurfaceView` or `TextureView` for hardware-accelerated rendering.
- **Orientation Mastery:** The app must flawlessly handle `Activity` configuration changes (portrait to landscape). The naive approach destroys and recreates the `ExoPlayer` instance, causing the video to buffer and stutter. The Staff approach retains the player instance across configuration changes.
- **Server-Driven UI (SDUI):** The homepage is an infinite grid of movie recommendations, completely dictated by the backend (Multi-Armed Bandits) to test ML algorithms without app updates.

### Domain Layer (The ABR Engine)
- **Adaptive Bitrate (ABR) Logic:** The core brain of the app. It constantly monitors the user's internet speed. If the speed drops from 50Mbps (Wi-Fi) to 2Mbps (3G), the ABR engine dynamically switches the video stream from 4K to 480p mid-stream to prevent the video from pausing to buffer.
- **DRM License Manager:** Fetches and manages Widevine encryption keys securely to decrypt the video chunks on the fly.

### Data Layer (The Chunked Stream)
- **Network Strategy:** **HLS (HTTP Live Streaming) or MPEG-DASH**. The app does not download an `.mp4` file. It downloads a `.m3u8` manifest file, which points to 5-second chunks of video (`.ts` or `.m4s` files).
- **Offline Downloads:** A complex database structure linking metadata (Room) with physical video chunks on disk (File System), heavily integrated with Android's `DownloadManager` or ExoPlayer's offline cache.

## 3. Infrastructure & DevOps
- **Device Certification (Widevine):** High-end video (4K, HDR) is fundamentally blocked on Android unless the physical hardware is certified for **Widevine L1**. The app must query the OS DRM APIs; if the device is L3 (software decoding only), the app must architecturally cap the stream to 480p to prevent CPU melting and copyright theft.
- **Release Strategy:** Features roll out slowly, but ML configurations roll out instantly.
- **Telemetry:** "Time to First Frame" (TTFF) and "Rebuffer Rate" are the primary KPIs.

## 4. Scaling Bottlenecks & Staff Solutions

### Bottleneck 1: The Screen Rotation Buffer
*Problem:* The user starts watching a video in portrait. They turn their phone to landscape. The screen goes black, the loading spinner appears for 3 seconds, and the video resumes from 5 seconds earlier.
*Solution:* **Player Instance Retention**.
A Junior engineer lets the Android OS destroy the `Activity` on rotation.
A Staff engineer does one of two things:
1. Adds `android:configChanges="orientation|screenSize"` to the Manifest, taking manual control of the layout transition (fastest, but difficult to maintain complex UIs).
2. Uses a `ViewModel` or a global singleton to hold the `ExoPlayer` instance. When the `Activity` is destroyed, the player is merely detached from the old `SurfaceView`. When the new `Activity` is created 10ms later, the player is instantly attached to the new `SurfaceView`. Playback never stops.

### Bottleneck 2: The Offline Download Expired Key
*Problem:* The user downloads a 2-hour movie for a flight. They put their phone in Airplane mode. They try to play the movie. The app crashes because the DRM license requires network validation.
*Solution:* **Offline Widevine Licenses**.
When the user downloads the video chunks, the app must also explicitly request an *Offline* DRM License from the backend. This key is cryptographically stored in the device's hardware Keystore. The app must architect the UI to handle the "Key Expiration" (e.g., the key expires in 30 days, or 48 hours after pressing Play) and clearly communicate this to the user *before* they board the plane.

### Bottleneck 3: Background Playback (Picture-in-Picture & Audio)
*Problem:* The user is watching a YouTube video. They press the Home button to check a text message. The video stops completely.
*Solution:* **MediaSession and Service Migration**.
To support Picture-in-Picture (PiP) or Background Audio:
1. **PiP:** The app must intercept the `onUserLeaveHint()` lifecycle callback and immediately call `enterPictureInPictureMode()`. The OS handles shrinking the `SurfaceView` into a floating window.
2. **Background Audio:** The app must decouple the `ExoPlayer` from the `Activity` entirely. The player must live inside a `MediaBrowserServiceCompat` (or `MediaLibraryService` in Media3). When the UI dies, the Service stays alive, bound to a Foreground Notification (the media controls), allowing continuous playback while the app is technically "closed".

## 5. Summary of Technologies
- **UI:** Compose, `SurfaceView`, Picture-in-Picture API.
- **Media:** ExoPlayer (Media3), Widevine DRM.
- **Protocols:** HLS, MPEG-DASH.
- **Architecture:** Server-Driven UI (for the catalog), `MediaSession` (for background playback).

## Further Reading
- [`youtube-video-streaming.md`](../mobile-system-design/youtube-video-streaming.md) (The system design interview variant).
- [`experimentation-platform.md`](../mobile-system-design/experimentation-platform.md) (How Multi-Armed Bandits build the homepage UI).
