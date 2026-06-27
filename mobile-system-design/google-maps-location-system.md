# System Design: Location Tracking System (Google Maps / Uber)

## The Prompt

*"Design the continuous location tracking system for a Ride-Hailing app (Uber Driver) or a Navigation app (Google Maps). The app must transmit the driver's location to the backend in real-time so the rider can see the car moving on a map. The system must not drain the driver's battery in 2 hours, and it must survive network dropouts (tunnels, rural areas)."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Capture device GPS coordinates continuously.
- Transmit coordinates to the backend in real-time (visible movement).
- Cache coordinates offline during network dropouts and upload them in bulk when reconnected.

### Non-Functional Requirements (NFRs)
- **Battery Life (Priority 0):** Polling the GPS hardware is the #2 biggest battery drain on a phone (behind the Screen). Polling the cellular radio is #3. The architecture must minimize both.
- **Data Integrity:** The backend needs the full path for accurate billing/routing. If the network drops for 5 minutes, we cannot lose 5 minutes of distance data.
- **Latency:** The rider must see the driver's location update with < 2 seconds of latency to feel "real-time".

## 2. High-Level Architecture

The architecture separates the **Hardware Poller** (getting location from satellite) from the **Network Transmitter** (sending to the server).

```mermaid
graph TD
    subgraph Android OS
        GPS[GPS Chip / FusedLocationProvider]
    end
    
    subgraph Driver App (Foreground Service)
        LocService[Location Tracking Service]
        Buffer[(In-Memory Buffer / Room)]
        NetworkEngine[Transmission Engine]
    end
    
    subgraph Backend
        WebSocket[WebSocket Gateway]
        Kafka[Kafka Stream]
        Redis[(Redis - Last Known Loc)]
        Cassandra[(Cassandra - Path History)]
    end
    
    GPS -->|1Hz Update| LocService
    LocService -->|Save| Buffer
    Buffer -->|Batch Send Every 5s| NetworkEngine
    NetworkEngine <-->|WebSocket| WebSocket
    WebSocket --> Kafka
```

## 3. The Core Flows (Deep Dive)

### Flow 1: Bypassing OS Restrictions (Foreground Services)
*Interviewer:* "In Android 8.0+, if the user backgrounds your app to check a text message, the OS will kill your background location tracking within 1 minute. The rider will see the driver freeze. How do you prevent this?"

**Staff Answer:**
"Continuous tracking is impossible in a standard background thread on modern Android. I must launch a **Foreground Service**.
1. The app calls `startForegroundService()`.
2. Within 5 seconds, the service must call `startForeground(ID, Notification)`.
3. This places a permanent, un-dismissible notification in the user's status bar (e.g., 'Uber Driver is tracking your location').
4. The OS recognizes this as a user-aware action and exempts the app from background execution limits, allowing the GPS to poll indefinitely."

*(Staff Note: On Android 10+, you also strictly need the `ACCESS_BACKGROUND_LOCATION` permission, and on Android 14+, you must declare the Foreground Service Type as `location` in the AndroidManifest).*

### Flow 2: The Hardware Poller (Battery Optimization)
*Interviewer:* "You are polling the GPS every 1 second (1Hz). The driver's battery dies in 2 hours. How do you optimize the hardware usage?"

**Staff Answer:**
"I will use Google's **FusedLocationProviderClient**. It intelligently combines GPS, Wi-Fi, and Cellular triangulation.
1.  **Adaptive Accuracy:** If the driver is on the highway going 60mph, I use `PRIORITY_HIGH_ACCURACY` (GPS). If they are stuck in traffic for 10 minutes, I degrade to `PRIORITY_BALANCED_POWER_ACCURACY` (Cellular/Wi-Fi).
2.  **Displacement:** I configure `setSmallestDisplacement(10f)`. The OS will *only* wake up my app if the driver physically moves more than 10 meters. If they are parked at a red light for 2 minutes, the GPS sleeps, saving massive amounts of battery."

### Flow 3: The Network Transmitter (Batching & WebSockets)
*Interviewer:* "You are sending an HTTP POST request to the backend every 1 second. The overhead of establishing the TCP/TLS connection 60 times a minute drains the battery and melts the API Gateway. Fix it."

**Staff Answer:**
"We decouple the GPS hardware from the Network.
1.  **The Transport:** We use a persistent **WebSocket** (or gRPC stream). The TCP/TLS handshake happens exactly once.
2.  **The Batching Algorithm:** The GPS polls every 1 second. We do *not* send every 1 second. We buffer the coordinates in an array. Every 4 or 5 seconds, we send the array of the last 5 coordinates over the WebSocket.
3.  **The Interpolation:** The backend receives the batch. To make it look 'real-time' to the Rider, the Rider's app uses **Linear Interpolation**. It receives the coordinates and smoothly animates the car icon from Point A to Point B over the next 4 seconds. The human eye perceives real-time movement, but the network is only used every 5 seconds."

### Flow 4: The Tunnel (Network Dropouts)
*Interviewer:* "The driver enters a tunnel for 5 minutes. The WebSocket disconnects. The GPS still works (or the FusedProvider uses dead reckoning). When they exit the tunnel, how do you prevent losing that 5-minute route?"

**Staff Answer:**
"The In-Memory Buffer is upgraded to a local SQLite database (Room).
1. Every GPS point is written to Room.
2. The Transmission Engine reads from Room, sends over the WebSocket, and upon receiving an `ACK` from the server, deletes the points from Room.
3. When the tunnel disconnects the WebSocket, the GPS points simply accumulate in Room.
4. When the WebSocket reconnects, the app performs a **Bulk Upload** of all accumulated points in Room. The backend calculates the accurate route distance, and the driver is paid correctly for the tunnel distance."

## 4. The Backend Constraint (Why Kafka & Redis?)

A Staff Mobile Engineer must know where their data goes.
If 1 Million Uber drivers send a location update every 5 seconds, that is 200,000 writes per second.
- A standard PostgreSQL database will instantly crash.
- The WebSocket gateway dumps the raw coordinate stream into **Kafka**.
- Kafka acts as a shock absorber.
- A consumer reads from Kafka and updates **Redis** with the driver's *current* location (for the Rider to query).
- Another consumer reads from Kafka and batches the writes into **Cassandra** (for the historical trip receipt and billing).

## 5. Failure Modes & Bottlenecks

### Bottleneck: Location Spoofing (Fraud)
*Interviewer:* "A driver uses a Fake GPS app to spoof their location, making it look like they drove 50 miles, and charges the rider $100. How do you detect this on the client?"

**Staff Answer:**
"Android provides tools to detect spoofing.
1. In the `Location` object, I check `location.isFromMockProvider()`. If true, I flag the data.
2. I cross-reference the GPS speed with the device's physical sensors (Accelerometer/Gyroscope). If the GPS says the car is moving 60mph, but the Accelerometer shows zero vibration (the phone is sitting on a desk), it is fraud.
3. I send the raw sensor data alongside the GPS coordinates, and the Backend Machine Learning fraud detection models analyze it."

### Bottleneck: The Zig-Zag Path (Inaccurate GPS)
*Interviewer:* "In downtown Manhattan, the GPS bounces off skyscrapers (Urban Canyon effect). The reported coordinates zig-zag across city blocks. The calculated distance is 15 miles instead of 2 miles."

**Staff Answer:**
"Client-side smoothing is required.
1.  **Kalman Filtering:** I apply a Kalman filter algorithm on the Android client. It uses the device's current velocity and trajectory to predict where the car *should* be, and smooths out wild GPS anomalies.
2.  **Snap-to-Road:** The raw coordinates are sent to the backend. The backend uses Google Maps APIs to 'Snap' the raw, zig-zagging points to the actual physical road vectors before calculating the billing distance."

## 6. Probing Questions (For Practice)

1.  Explain why a standard background coroutine or thread will fail to track location continuously on modern Android, and detail the OS mechanics of a Foreground Service.
2.  Describe the exact steps required to launch a Foreground Service, including the user-facing Notification and AndroidManifest requirements.
3.  Why is the `FusedLocationProviderClient` fundamentally superior to the raw `LocationManager` for battery optimization?
4.  Explain the concept of `setSmallestDisplacement()` and how it mathematically prevents battery drain when a vehicle is stopped in traffic.
5.  Walk through the architecture of "Decoupling Hardware from Network". Why is batching coordinates and sending every 5 seconds superior to sending every 1 second?
6.  Describe the "Interpolation" technique used on the Rider's application to make a 5-second batched update look perfectly smooth and real-time.
7.  How does writing coordinates to a local Room database prevent data loss and ensure accurate billing when a driver enters a 5-minute cellular dead zone?
8.  Explain why the backend must use Kafka and Redis to handle the incoming coordinate stream, rather than writing directly to a relational SQL database.
9.  Describe the "Urban Canyon" effect and how a Kalman filter or "Snap-to-Road" algorithm mitigates the zig-zagging path problem.
10. How does a Staff Engineer prevent location fraud using `isFromMockProvider()` and physical device sensors (Accelerometer)?

## Further Reading

- [`battery-optimizations.md`](../android/concurrency/battery-optimizations.md) — Deep dive into Doze Mode and Foreground Services.
- [`push-vs-poll-vs-sse-vs-websockets.md`](../backend-for-mobile/push-vs-poll-vs-sse-vs-websockets.md) — The cost of TLS handshakes and why WebSockets are mandatory here.
- [`offline-first-app.md`](../reference-architectures/offline-first-app.md) — The architecture for the local Room buffer.
