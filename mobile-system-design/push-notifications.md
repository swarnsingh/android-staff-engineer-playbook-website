# Platform Design: Push Notifications (FCM Architecture)

## The Prompt

*"Design the Push Notification architecture for an E-Commerce app. The backend must be able to send a 'Flash Sale' notification to 10 million users simultaneously. The mobile app must receive the notification, download an image of the product in the background, and display a rich notification to the user. Handle the scenario where the user gets a new phone."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Send broadcast notifications (1-to-Millions).
- Display rich notifications (Images, Action Buttons) on the device.
- Background execution (app is closed/swiped away when the push arrives).

### Non-Functional Requirements (NFRs)
- **Delivery Reliability:** Android OS heavily restricts background execution (Doze Mode). The architecture must guarantee delivery without destroying the battery.
- **Scale:** 10 million payloads sent instantly without crashing the backend or the CDN (when 10M devices try to download the image).
- **Token Management:** The system must perfectly track which device belongs to which user.

## 2. High-Level Architecture (FCM & Data Payloads)

A Junior engineer sends notifications using FCM (Firebase Cloud Messaging) "Notification Payloads". The OS displays them automatically, providing zero control to the app.
A Staff engineer uses FCM **"Data Payloads"** to wake up the app and execute custom logic (downloading images, updating local DBs) before showing the notification.

```mermaid
graph TD
    subgraph Mobile Device (Android)
        FCM_SDK[FCM SDK] -->|Wakes Up| Service[FirebaseMessagingService]
        Service -->|1. HTTP GET| CDN[(Image CDN)]
        CDN --> Service
        Service -->|2. Build| NotificationManager[Android NotificationManager]
    end
    
    subgraph Backend
        Campaign[Marketing Tool] -->|Trigger| Sender[Push Microservice]
        Sender -->|Batch Post| Google[Google FCM Server]
        Google -.->|TCP Keep-Alive| FCM_SDK
    end
    
    App_Startup -->|Sync Token| Sender
```

## 3. The Core Flows (Deep Dive)

### Flow 1: Device Token Management (The "New Phone" Problem)
*Interviewer:* "The user deletes your app. A month later, they buy a new phone and install it. How does your backend know where to send the notifications?"

**Staff Answer:**
"Push Notifications rely on an **FCM Registration Token** (a unique String identifying that specific installation on that specific device).
1. When the app launches, it asks the FCM SDK for its token.
2. The app sends `POST /users/me/device-tokens` with the token.
3. The backend stores this in a `user_device_tokens` table. (1 User -> N Devices).
4. **The Stale Token Problem:** When a user uninstalls the app, the token dies. When the backend tries to send a push to that dead token, Google FCM replies with a `NotRegistered` error. The backend MUST immediately delete that token from the database.
5. When the user installs on the new phone, FCM generates a *new* token, the app syncs it, and the backend routes pushes correctly."

### Flow 2: Data Payloads vs Notification Payloads
*Interviewer:* "You send a Flash Sale notification. You want the app to download a picture of the shoes and show it in the notification. But when the app is in the background, the notification just shows text and your code never runs. Why?"

**Staff Answer:**
"You sent an FCM **Notification Payload**.
If the JSON contains the `"notification"` key, the Android OS intercepts it. If the app is in the background, the OS displays the text instantly and *never* wakes up the app's code.
**The Fix:** The backend must send a **Data Payload** (JSON containing only the `"data"` key).
```json
{
  "to": "device_token",
  "data": {
    "title": "Flash Sale!",
    "image_url": "https://cdn.com/shoes.jpg"
  }
}
```
When a Data Payload arrives, the OS wakes up the app's `FirebaseMessagingService.onMessageReceived()`. We now have ~10 seconds of background execution time. We use `Coil/Glide` to download the image, construct a custom `NotificationCompat.Builder`, set the `LargeIcon` and `BigPictureStyle`, and manually trigger the `NotificationManager.notify()`."

### Flow 3: The Thundering Herd (The 10 Million User DDoS)
*Interviewer:* "You send the Flash Sale push to 10 million users instantly. 10 million Android phones wake up in the background at the exact same second. They all execute `onMessageReceived` and fire an HTTP GET to download `shoes.jpg`. Your servers catch on fire."

**Staff Answer:**
"This is a self-inflicted DDoS attack.
1.  **The Backend Fix (Jitter & Spreading):** The backend must *never* send 10 million pushes at once. It must 'smear' the sends over a 15-minute window (e.g., sending 10,000 per second).
2.  **The CDN Fix:** The `image_url` must point to an Edge CDN (Cloudflare), absolutely never to the core AWS S3 bucket. The CDN will cache `shoes.jpg` at the edge, trivially absorbing millions of requests without hitting the origin.
3.  **The Client Fix:** The Android app must implement a short timeout (e.g., 3 seconds) on the image download. If the image fails to download, it catches the exception and displays a text-only notification as a fallback. It must *never* retry in an infinite loop."

## 4. Failure Modes & Bottlenecks

### Bottleneck: Doze Mode & Battery Restrictions
*Interviewer:* "The user puts their phone on their desk for 4 hours. It goes into deep Doze Mode. Your backend sends a critical 'Order Delivered' push notification. It doesn't arrive until the user turns their screen on 2 hours later."

**Staff Answer:**
"FCM categorizes pushes into two priorities: **Normal** and **High**.
By default, Data payloads are `Normal` priority. The OS will batch them and hold them until a maintenance window to save battery.
If the notification is critical (e.g., Chat Message, Delivery Alert), the backend must add `"priority": "high"` to the FCM JSON. This breaks through Doze Mode and wakes the device instantly. However, if you abuse High Priority for marketing spam, Google will throttle your app's pushes back to Normal priority as a penalty."

### Bottleneck: Notification Channels (Android 8.0+)
*Interviewer:* "A user gets annoyed by your daily 'Flash Sale' pushes. They go to OS settings and block notifications for your app. Now they can't receive 'Order Shipped' notifications. They call customer support angry."

**Staff Answer:**
"This happens when you dump all pushes into a single channel.
Android 8.0 introduced **Notification Channels**. We must create semantic channels:
1. `Channel ID: marketing` (Name: "Promotions & Sales")
2. `Channel ID: transactional` (Name: "Order Updates") - *Critical Priority*
When we build the notification in `onMessageReceived`, we assign it to the correct channel. The user can now navigate to the OS settings and turn off 'Promotions' while keeping 'Order Updates' turned on. We respect their intent without breaking core app functionality."

## 5. Staff Engineer Thinking: Silent Pushes for Sync

A Staff Engineer knows Push Notifications aren't just for UI. They are the ultimate trigger for **Offline-First Synchronization**.

If the backend database updates (e.g., the user's friend changes their profile picture), the backend sends a *Silent* Data Payload to the device (`"type": "sync_request"`). 
The `FirebaseMessagingService` wakes up in the background. It does *not* show a UI notification. Instead, it triggers the Room Database to sync with the server. When the user eventually opens the app 3 hours later, the new profile picture is already on disk, rendering instantly. 
*(Note: Android severely limits background execution time. For long syncs, the Push must delegate the work to Android's `WorkManager`.)*

## 6. Probing Questions (For Practice)

1.  Explain the fundamental difference in Android OS behavior between receiving an FCM "Notification Payload" versus a "Data Payload".
2.  Describe the exact steps an Android app must take to display an image inside a notification when it receives a Data Payload in the background.
3.  How does a backend handle the "Stale Token Problem" when a user uninstalls the app and FCM returns a `NotRegistered` error?
4.  Why must an E-Commerce backend "smear" or add jitter to a 10-million user broadcast campaign rather than submitting them to Google all at once?
5.  Explain how Android Doze Mode impacts FCM delivery. What is the difference between `Normal` and `High` priority, and what happens if you abuse High priority?
6.  Walk through the implementation of Android Notification Channels. How do they prevent users from blanket-blocking all notifications from your app?
7.  Describe the concept of a "Silent Push" (Tickle Push). How can it be used to keep a local SQLite database perfectly synchronized with the cloud?
8.  If `onMessageReceived` is executing in the background and the image download takes 15 seconds, what will the Android OS do to your app? How do you fix it?
9.  Why is it crucial that the CDN URL provided in the push payload includes standard HTTP Cache-Control headers?
10. If a user owns a Phone and a Tablet, explain the database schema the backend requires to ensure both devices receive the notification.

## Further Reading

- [`offline-sync.md`](offline-sync.md) — How Silent Pushes trigger background synchronization.
- [`battery-optimizations.md`](../android/concurrency/battery-optimizations.md) — Deep dive into Doze Mode and `WorkManager` handoffs.
- [`caching.md`](../engineering-fundamentals/caching.md) — How Edge CDNs absorb the image download Thundering Herd.
