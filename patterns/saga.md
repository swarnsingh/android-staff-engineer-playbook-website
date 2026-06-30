# Saga Pattern

> The Saga pattern manages long-running, distributed transactions without using global locks (like two-phase commits). While typically a backend microservices concept, mobile apps orchestrate mini-sagas constantly. A Staff engineer recognizes that a mobile "Checkout Flow" (Validate Cart -> Charge Card -> Upload Receipt -> Update UI) is a Saga. On Android, the Saga pattern is mechanically implemented using **WorkManager Chaining**, and its most critical feature is the **Compensating Action**—the ability to cleanly roll back local device state when step 3 of a 4-step remote process fails.

---

## Overview

In a monolithic database, you wrap multiple operations in a `BEGIN TRANSACTION` and `COMMIT` block. If anything fails, the database rolls back atomically.

In a distributed system (like a mobile app talking to 3 different microservices), there is no global transaction lock. If you successfully charge a user's credit card (Service A), but fail to register their premium account (Service B), you are left in a fractured state.

A Saga solves this by breaking the transaction into a sequence of local transactions. If a step fails, the Saga executes **Compensating Actions**—reverse operations that undo the previous successful steps (e.g., issuing a refund API call to Service A).

---

## 1. Orchestrated vs. Choreographed Sagas

There are two ways to organize a Saga:
1. **Choreography:** Events are published, and services react independently. (e.g., The app fires a "Payment Successful" event, and the UI listens for it to update). This is messy on mobile.
2. **Orchestration:** A central controller explicitly commands the steps. **This is the preferred pattern for Android.** The Android app acts as the Orchestrator for complex user flows.

---

## 2. Core Android Example: WorkManager Chaining

Android's `WorkManager` is the perfect Saga Orchestrator. It allows you to define a strict DAG (Directed Acyclic Graph) of operations that execute sequentially, passing data between steps, even if the app is killed or the network drops.

### The Saga Scenario: A Complex Photo Upload
Imagine a social media app where creating a post requires three distinct API calls to three different microservices:
1. `CompressAndFilterWorker` (Local CPU intensive)
2. `UploadToS3Worker` (Network intensive)
3. `NotifyBackendWorker` (Network intensive, depends on S3 URL)

### Creating the Orchestration (The Saga)
```kotlin
class PostViewModel(private val workManager: WorkManager) : ViewModel() {

    fun createPost(imageUri: Uri, caption: String) {
        // Step 1: Compress
        val compressWork = OneTimeWorkRequestBuilder<CompressWorker>()
            .setInputData(workDataOf("URI" to imageUri.toString()))
            .build()
            
        // Step 2: Upload (Requires output of Step 1)
        val uploadWork = OneTimeWorkRequestBuilder<UploadWorker>()
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .build()
            
        // Step 3: Notify Backend (Requires output of Step 2)
        val notifyWork = OneTimeWorkRequestBuilder<NotifyBackendWorker>()
            .setInputData(workDataOf("CAPTION" to caption))
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .build()

        // The Orchestrator Chaining
        workManager
            .beginWith(compressWork)
            .then(uploadWork)
            .then(notifyWork)
            .enqueue()
    }
}
```

Because WorkManager serializes the inputs/outputs between chained workers, if `uploadWork` succeeds, but `notifyWork` fails due to a network drop, WorkManager will pause the Saga and resume *only* `notifyWork` when the network returns. It will not re-run the compression or the S3 upload.

---

## 3. The Critical Component: Compensating Actions

If a Saga permanently fails in the middle, you must clean up the state. This is the **Compensating Action**.

Imagine a Checkout Saga:
1. Reserve Inventory (Success)
2. Charge Credit Card (Success)
3. Confirm Order (Permanent Failure - HTTP 403)

If the Saga stops here, the user is charged, but the order doesn't exist. The mobile app must orchestrate the rollback.

### Implementing Rollbacks in Android
We can achieve this by observing the terminal states of the WorkManager chain and enqueuing a rollback command if necessary.

```kotlin
// In an application-scoped component or repository
workManager.getWorkInfoByIdLiveData(notifyWork.id).observeForever { workInfo ->
    if (workInfo != null && workInfo.state == WorkInfo.State.FAILED) {
        
        // The Saga failed at the final step! We must execute a compensating action.
        val transactionId = workInfo.outputData.getString("TXN_ID")
        
        if (transactionId != null) {
            val refundWork = OneTimeWorkRequestBuilder<RefundWorker>()
                .setInputData(workDataOf("TXN_ID" to transactionId))
                .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
                .build()
                
            workManager.enqueue(refundWork)
        }
    }
}
```
**Staff Insight:** While mobile clients *can* orchestrate distributed sagas, doing so for financial transactions is incredibly dangerous (the user might delete the app before the compensating action fires). Critical sagas (like payments) must be orchestrated entirely on the backend. The mobile app should only orchestrate non-critical sagas (like uploading media or syncing local databases).

---

## 4. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **Dangling Sagas** | A compensating action (like a refund API call) fails permanently. The system is permanently fractured. | Compensating actions must be aggressively retried and designed to be strictly idempotent. If they fail completely, they must trigger an alert to a human operator. |
| **App Uninstalls** | The user initiates a purchase Saga, the app charges the card, the network drops, and the user gets angry and uninstalls the app. The Saga stops permanently on the phone. | Never orchestrate financial or critical state changes on the mobile client. The client should issue a single `StartCheckoutCommand` to the backend, and let a backend Saga Orchestrator handle the multi-step transaction. |
| **UI Desync** | The UI updates optimistically, but the background WorkManager Saga fails an hour later. | If a Saga has compensating actions, the UI must also be "compensated". If a "Like" fails to sync, the local Room database must be updated to remove the "Like", and the UI will reflect this. |

---

## 5. Common Pitfalls

### Pitfall 1: Leaking Output Data in WorkManager Chains
In WorkManager, the output data of Step 1 is merged with the input data of Step 2, which is merged with the output of Step 3. If you use generic keys like `"ID"`, Step 3 might accidentally overwrite the ID from Step 1.
*Fix:* Use highly specific keys for WorkManager data payloads (`"POST_ID"`, `"IMAGE_S3_URL"`). Use an `InputMerger` (like `OverwritingInputMerger`) deliberately.

### Pitfall 2: Sync vs Async Sagas
Users expect a checkout flow to be synchronous (blocking the screen with a spinner). WorkManager is asynchronous.
*Fix:* Do not use WorkManager for user-blocking Sagas. Use Kotlin Coroutines in the `ViewModel` for synchronous sagas, falling back to WorkManager *only* for the compensating actions if the app is killed during a failure.

---

## Probing Questions

1.  **Choreography vs Orchestration:** EventBus implementations (where `Worker A` broadcasts an event, and `Worker B` listens for it to start) represent Choreographed Sagas. Why is Choreography considered an anti-pattern for mobile apps compared to WorkManager's Orchestration?
2.  **ACID Properties:** Sagas sacrifice one of the ACID properties of traditional databases to achieve availability in distributed systems. Which property is sacrificed, and how do compensating actions attempt to simulate it?
3.  **WorkManager Cancellation:** You orchestrate a 5-step Saga. The user presses a "Cancel" button in the UI during Step 2. You call `workManager.cancelUniqueWork()`. Does WorkManager automatically execute compensating actions for Step 1? How must you architect manual cancellation?
4.  **Idempotency:** Why is it absolutely critical that the API endpoints used in a Compensating Action (e.g., `POST /api/refund`) are idempotent? What happens if the network drops during the refund response?
5.  **BFF Synergy:** How does the Backend-for-Mobile (BFF) pattern completely eliminate the need for Saga Orchestration on the Android client?

## Further Reading

- [`command.md`](command.md) — The foundation of WorkManager; a Saga is just a chained sequence of Commands.
- [`retry.md`](retry.md) — Why Sagas and Compensating Actions must utilize durable retries.
- [`../android/concurrency/workmanager.md`](../android/concurrency/workmanager.md) — Deep dive into the SQLite-backed engine that powers Android Sagas.
- [`../backend-for-mobile/bff-pattern.md`](../backend-for-mobile/bff-pattern.md) — How to move orchestration off the phone and onto a dedicated server.
