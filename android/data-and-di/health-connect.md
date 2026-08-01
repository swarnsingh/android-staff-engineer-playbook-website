# Health Connect Architecture

Health Connect is Android's permissioned data-exchange layer for health and fitness records. It gives apps a common schema and on-device store without making any participating app the owner of every user's data.

---

## Architecture Boundary

Keep the platform client behind a repository boundary:

```kotlin
interface HealthRepository {
    suspend fun readSteps(start: Instant, end: Instant): Long
    suspend fun writeWorkout(workout: Workout)
    suspend fun changesSince(token: String): ChangeBatch
}
```

The repository translates between Health Connect record types and domain models. UI and domain code should not depend directly on `HealthConnectClient`, permission contracts, pagination tokens, or platform availability states.

At startup, call `HealthConnectClient.getSdkStatus(context)` before constructing a client. Treat unavailable, update-required, and available states as product states with explicit UI rather than assuming the provider exists on every supported device.

When targeting Android 11 or later while supporting Android 13 or lower, declare the separately installed Health Connect provider in the manifest's package-visibility queries; otherwise `getSdkStatus()` can report unavailable even when the provider is installed:

```xml
<queries>
    <package android:name="com.google.android.apps.healthdata" />
</queries>
```

## Permission Model

Health permissions are granular by record type and operation. An app that reads steps and writes exercise sessions should request only those specific read and write permissions, declare them in the manifest, and explain their purpose before launching the system permission contract.

Permission state can change outside the app. Re-check it before protected work and handle partial grants: access to one record type does not imply access to another. A denial should degrade the feature, not crash startup or block unrelated app functionality.

Do not request health permissions merely because a screen is reachable. Ask when the user invokes a feature that needs the data, and keep Play policy declarations and the in-app privacy policy aligned with actual access.

## Reads, Aggregation, and Writes

- Use aggregate queries for totals such as step counts or distance. Summing raw records yourself can mishandle platform deduplication and data-origin rules.
- Bound every read by time and page through large result sets. Do not load a user's complete history into memory.
- Include stable client record identifiers when writing data so retries update or deduplicate records rather than creating duplicates.
- Preserve time zones and offsets when converting between domain events and platform records; a local-day report is not equivalent to a UTC-day query.
- Surface data origin when product behavior depends on which device or app supplied a record.

Health Connect is a shared store, not an event bus. A successful local write does not mean a wearable or remote service has synchronized.

## Incremental Synchronization

Seed existing history before switching to the changes API:

1. Obtain a changes token for the record types and data origins in scope immediately before the initial import.
2. Perform a time-bounded, paginated `readRecords` import and upsert the existing records idempotently.
3. Consume every changes page starting from the token captured in step 1, applying upserts and deletions that occurred during the initial import. This closes the race between the snapshot and incremental processing.
4. Persist the latest next token only after its corresponding local transaction succeeds, then use it for steady-state incremental reads.
5. If a token expires or becomes invalid, perform another bounded reconciliation using the same token-before-snapshot sequence.

Ordinary read grants may not expose records from more than 30 days before permission was first granted. Before offering a deeper initial backfill, declare `<uses-permission android:name="android.permission.health.READ_HEALTH_DATA_HISTORY" />`, verify `HealthConnectFeatures.FEATURE_READ_HEALTH_DATA_HISTORY` is available, and request `HealthPermission.PERMISSION_READ_HEALTH_DATA_HISTORY` from the user. If the feature is unsupported or the permission is denied, cap the snapshot at the ordinary accessible window and tell the product layer that historical coverage is partial; a changes token tracks later mutations but cannot recover older records omitted from the snapshot.

Prefer reading Health Connect while the app is in the foreground, committing the results to the app-owned store, and letting `WorkManager` upload that local copy under network and battery constraints. A worker must not read Health Connect directly unless the device exposes the background-read feature **and** the user granted its separate permission:

```kotlin
val canReadHealthDataInBackground =
    healthConnectClient.features.getFeatureStatus(
        HealthConnectFeatures.FEATURE_READ_HEALTH_DATA_IN_BACKGROUND
    ) == HealthConnectFeatures.FEATURE_STATUS_AVAILABLE &&
        HealthPermission.PERMISSION_READ_HEALTH_DATA_IN_BACKGROUND in
            healthConnectClient.permissionController.getGrantedPermissions()
```

Only schedule a Health Connect-reading worker when `canReadHealthDataInBackground` is true. Otherwise, keep ingestion foreground-bound and use background work solely for uploading data already stored by the app.

## Privacy and Security

Health data is sensitive even when it appears harmless. Minimize collection, encrypt any app-owned copy, avoid identifiers and raw measurements in logs, define retention and deletion behavior, and make account deletion cover remote replicas as well as the device-local cache.

Never infer medical conclusions from a missing record: it may mean no measurement, revoked permission, provider unavailability, deletion, or delayed synchronization.

## Failure Modes

- Treating SDK availability as a one-time installation check.
- Assuming requested permissions were all granted.
- Promising a complete older-history backfill without checking the history feature and extended-history permission.
- Scheduling direct Health Connect reads in background work without checking background-read feature availability and permission.
- Summing overlapping raw samples instead of using aggregate APIs.
- Retrying writes without stable client identifiers and creating duplicates.
- Losing a changes token before the related local transaction commits.
- Uploading more health history than the user-facing feature requires.

## Testing Strategy

Unit-test domain behavior behind a fake `HealthRepository`. Instrument the adapter separately for permission denial, partial grants, empty results, pagination, deletions, invalid change tokens, and provider unavailability. Test time-zone and daylight-saving boundaries explicitly.

## Staff-Level Review Questions

1. Which exact record types and operations does the feature need, and why?
2. How does the UI behave when only some permissions are granted?
3. Is aggregation performed by Health Connect or accidentally reimplemented?
4. Can every write and synchronization retry run idempotently?
5. What data is copied off-device, how long is it retained, and how is it deleted?

## References

- [Health Connect overview](https://developer.android.com/health-and-fitness/guides/health-connect)
- [Read and write data](https://developer.android.com/health-and-fitness/guides/health-connect/develop/read-data)
- [Synchronize data](https://developer.android.com/health-and-fitness/guides/health-connect/develop/sync-data)
