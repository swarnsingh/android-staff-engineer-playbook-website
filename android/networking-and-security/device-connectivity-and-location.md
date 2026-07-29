# Device Connectivity and Location

## Overview

Bluetooth Low Energy (BLE) and location features are long-lived interactions with radios, permissions, device state, and background policy. A working API call is not a production architecture. The feature must define why access is needed, when scanning or updates stop, how reconnection behaves, and what survives process death.

## BLE Architecture

Separate discovery, connection, service discovery, subscription, and data transfer into explicit states. A useful model is `Idle → Scanning → CandidateFound → Connecting → Discovering → Ready → Disconnecting`, with timeout and failure transitions from every active state. Serialize GATT operations because many device stacks behave poorly when reads, writes, and descriptor operations overlap.

Scan with filters, stop as soon as the product goal is met, and impose a deadline. Continuous unfiltered scanning burns battery and may be throttled. Treat advertised identity as untrusted; authenticate at the application protocol when the device controls something sensitive. A bonded link does not automatically prove that application data or commands are authorized.

Permission behavior depends on OS and target level. Modern Android uses nearby-device Bluetooth permissions such as `BLUETOOTH_SCAN` and `BLUETOOTH_CONNECT`; older releases coupled discovery to location permissions. Build a version-aware permission policy from the official guide, request access in context, and support denial without trapping the user. Do not claim `neverForLocation` if scan results are used to infer location.

## Location Architecture

Ask first whether the feature can work with coarse location, a one-shot current location, or user-entered context. Continuous precise updates are the most expensive and privacy-sensitive option. Model accuracy, maximum acceptable age, update interval, displacement, timeout, and foreground/background state as product requirements rather than hard-coded defaults.

Background location is subject to platform restrictions and store policy. Request it only when the user-visible core feature needs it, after foreground access and education, and design for reduced delivery. A foreground service is not a loophole: it needs the correct service type, a visible notification, and compliance with launch restrictions. For deferrable work, persist intent and use the appropriate scheduler instead of keeping a radio session alive.

## Reliability and Observability

Radio and provider callbacks end unexpectedly: Bluetooth turns off, permissions auto-reset, the peripheral leaves range, location settings change, the process dies, or an OEM stack wedges. Recreate runtime connections from durable intent; do not persist a live GATT/client object. Reconnect with bounded exponential backoff and jitter only when the product still needs the connection.

Measure scan duration and success, connection/state-transition latency, GATT status, retries, disconnect reason, device model, permission state, Bluetooth/location settings, location age and accuracy, background delivery gaps, and battery impact. Redact device identifiers and coordinates unless strictly required, and apply retention controls.

## Failure Modes

- An infinite scan or high-rate location loop drains battery.
- Concurrent GATT operations produce intermittent failures.
- Code treats permission grant as permanent and crashes after auto-reset.
- Reconnect loops continue after the user leaves the feature.
- A background design works on a development phone but violates newer platform/store restrictions.
- Logs expose stable device identifiers or precise location.

## Probing Questions

1. Why should GATT operations be serialized?
2. What conditions terminate a BLE scan?
3. How do nearby-device permissions differ across Android versions?
4. When is background location justified?
5. What state should survive process death for a connected-device feature?

## Answer Key

1. The protocol/device stack expects ordered operations and often allows only one outstanding transaction; overlap creates ambiguous callbacks and vendor-specific failure.
2. Success, explicit cancellation, lifecycle loss, permission/radio loss, or a bounded timeout.
3. Newer Android versions use dedicated scan/connect/advertise runtime permissions; older discovery behavior was tied to location. Branch from the official target/version rules.
4. Only for a disclosed, user-visible core feature that cannot be delivered with foreground or one-shot access and satisfies distribution policy.
5. Persist user intent and stable identifiers/configuration, not a live connection object; rebuild the state machine after restart.

## Further Reading

- [Bluetooth Low Energy overview](https://developer.android.com/develop/connectivity/bluetooth/ble/ble-overview)
- [Bluetooth permissions](https://developer.android.com/develop/connectivity/bluetooth/bt-permissions)
- [Background location access](https://developer.android.com/develop/sensors-and-location/location/background)
- [Optimize location for battery](https://developer.android.com/develop/sensors-and-location/location/battery)
