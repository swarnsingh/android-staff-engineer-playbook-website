# Blueprint: The Ride-Hailing App (Real-Time Bi-Directional)

## 1. Architectural Signature
A Ride-Hailing App (e.g., Uber, Lyft, Grab) is optimized for **Real-Time Geospatial Synchronization, Bi-Directional Communication, and State Machine Consistency**.
The architecture is vastly different from a standard REST-based app. It relies on persistent, low-latency connections (WebSockets, SSE, or gRPC) because the backend must push rapid location updates to the client, and the client must stream its GPS coordinates back.

**Core Trade-off:** Battery/CPU Efficiency vs Real-Time Location Accuracy.

## 2. Component Blueprint

### Presentation Layer (The Map & The State)
- **Framework:** Compose or Views, anchored around a massive, stateful Map Component (Google Maps SDK / Mapbox).
- **Pattern:** MVI (Model-View-Intent). The UI is a pure reflection of a complex global state machine (Idle -> Requesting -> Driver Assigned -> Arriving -> In Transit -> Completed).
- **Animations:** Extensive use of interpolators to smoothly animate the car marker across the map between discrete GPS updates, preventing "teleportation" jitter.

### Domain Layer (The Dispatcher)
- **Location Engine:** A dedicated module wrapping the FusedLocationProviderClient. It manages dynamic sampling rates (e.g., sample every 10 seconds when idle, sample every 1 second when in transit).
- **State Machine Validator:** Prevents illegal state transitions (e.g., A driver cannot transition from "Arriving" to "Completed" without going through "In Transit").

### Data Layer (The Socket)
- **Network Strategy:** **WebSockets or gRPC Streams (Priority 0)**. REST polling (HTTP GET every 2 seconds) is banned because it destroys battery life and chokes the backend.
- **Protocol:** Protocol Buffers (protobuf) or FlatBuffers for the binary payload. JSON is often too large and slow to parse for high-frequency location streaming on low-end devices.
- **Connection Resiliency:** The Socket manager must handle sudden network drops (e.g., driving through a tunnel) with exponential backoff and seamless reconnection logic, playing catch-up with buffered events.

## 3. Infrastructure & DevOps
- **Telemetry:** Extremely deep integration with network latency and battery consumption metrics. A regression that increases CPU usage by 5% will drain a driver's battery before their shift ends.
- **Rollouts:** Phased by geographical region (City-by-City), not just by a random 10% global percentage. A routing bug might only manifest in a city with complex tunnel networks (e.g., Boston or London).

## 4. Scaling Bottlenecks & Staff Solutions

### Bottleneck 1: The GPS Battery Drain (Driver App)
*Problem:* The driver app streams GPS coordinates to the backend every 1 second. After 3 hours, the driver's phone dies. They cannot complete the ride.
*Solution:* **Dynamic Adaptive Tracking & Geofencing**.
1. When the driver is idle, the app uses standard REST/FCM to receive dispatch requests. Location is polled passively.
2. When the driver is approaching a passenger, the app uses Android Geofencing. It only wakes up the GPS aggressively when the driver breaches the 1-mile radius of the pickup spot.
3. The app implements a `Foreground Service` to ensure the OS does not kill the GPS tracker when the driver switches to their music app.

### Bottleneck 2: The "Ghost Car" (Rider App)
*Problem:* The rider sees the car marker driving through buildings and teleporting backwards on the map.
*Solution:* **Kalman Filters and Route Snapping**.
Raw GPS data is incredibly noisy, bouncing around by 20-50 meters due to urban canyons (tall buildings).
1. The backend (or client) applies a Kalman Filter to mathematically predict the true trajectory based on velocity and previous points.
2. The client uses the Google Maps "Snap to Roads" API. Instead of drawing the car at the raw GPS coordinate (which might be inside a building), it mathematically snaps the marker to the nearest logical vector on the road network.
3. The UI animates (interpolates) the movement smoothly between the snapped points.

### Bottleneck 3: The Disconnected Dispatch (State Desync)
*Problem:* The rider requests a ride. The backend assigns Driver A. The backend sends a WebSocket message to the rider: "Driver A assigned". The rider drives through a tunnel and drops connection. The backend realizes Driver A cancelled, and assigns Driver B. The rider exits the tunnel and still thinks Driver A is coming.
*Solution:* **Event Sourcing & Revision IDs**.
The app cannot just listen to raw events; it must maintain a synchronized State Machine.
Every state update from the backend includes a `revision_id`.
When the rider reconnects, the app sends `sync(last_revision_id = 5)`.
The backend responds: "You missed revisions 6, 7, and 8. Here is the compacted current state: You are now on revision 8, and Driver B is assigned." The app instantly forces a UI reconciliation to the new truth.

## 5. Summary of Technologies
- **UI:** Google Maps SDK, Mapbox, Compose.
- **Data:** WebSockets, gRPC, Protocol Buffers.
- **Location:** FusedLocationProviderClient, Geofencing, Foreground Services.
- **Architecture:** MVI, Event Sourcing, Strict State Machines.

## Further Reading
- [`ride-hailing.md`](../mobile-system-design/ride-hailing.md) (The system design interview version of this blueprint).
- [`google-maps-location-system.md`](../mobile-system-design/google-maps-location-system.md) (Deep dive into FusedLocationProvider and Battery).
- [`battery-optimizations.md`](../android/concurrency/battery-optimizations.md) (How Foreground Services bypass Doze Mode).
