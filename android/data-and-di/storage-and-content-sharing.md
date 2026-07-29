# Android Storage and Content Sharing

## Overview

Android storage is a capability decision, not a choice between “internal” and “external” paths. The correct primitive depends on who owns the data, who should see it, how long access must last, and whether the user should choose the item. Modern apps should operate on `content://` URIs through `ContentResolver`; broad filesystem access is rarely the right abstraction.

## Decision Matrix

| Need | Primary API | Access model |
|---|---|---|
| App-owned private files | `filesDir`, `cacheDir`, or app-specific external storage | Only this app; removed on uninstall |
| Structured private records | Room | App-owned database and migrations |
| Settings and small state | DataStore | App-owned, typed or key-value state |
| Add app-created photos/video/audio to shared collections | MediaStore | Collection-scoped shared media |
| Let a user choose photos or videos | Photo Picker | User grants selected-item access |
| Let a user open/create arbitrary documents | Storage Access Framework (SAF) | User grants a document or tree URI |
| Share an app-owned file with another app | `FileProvider` | Temporary URI permission |

Do not request media-library permission merely to attach one user-selected photo. The Photo Picker gives access to selected media and can fall back through AndroidX to `ACTION_OPEN_DOCUMENT` where the picker is unavailable. Use SAF when the user is choosing documents or a directory rather than media-library items.

## URI Ownership and Lifetime

A URI is a capability. Receiving it does not mean the app owns the underlying bytes or can turn the URI into a stable filesystem path. Open a stream or file descriptor through `ContentResolver`, tolerate providers backed by cloud storage, and do expensive copying or decoding off the main thread.

Temporary grants may end when the task or process lifecycle ends. If later background work must reopen a SAF/Photo Picker URI, request a persistable grant when the contract and provider support it, record the URI plus the intended operation, and handle revocation or disappearance. Do not assume every provider supports seeking, reports a real size, or returns a useful display name.

For outgoing data, expose only the required file through a narrowly configured `FileProvider`, attach `FLAG_GRANT_READ_URI_PERMISSION` or write permission only when needed, and revoke/expire access through normal task lifetime. Never expose `file://` URIs or configure a provider root broader than necessary.

## Production Design

Treat ingestion as a state machine: `Selected → PermissionRecorded → Copying/Streaming → Validated → Uploaded/Stored`, with terminal failure and cancellation states. Validate MIME type from content, enforce byte and decoded-dimension limits, protect against decompression bombs, and avoid trusting filename extensions. If the product needs durable independent ownership, copy validated content into app storage; if not, retain the URI capability and its grant.

For MediaStore writes, use collection metadata and pending-publication behavior so other apps do not observe partial files. For caches, design eviction because the system may remove cache files. For backup, explicitly decide which private files are user-restorable; exclude device-bound ciphertext and transient material.

## Failure Modes

- A persisted URI is revoked, its provider is removed, or the remote object disappears.
- A worker receives a URI after its temporary grant expired.
- Code resolves a “real path” that never existed for a cloud provider.
- Large media is decoded at full resolution and causes an OOM.
- A broad storage permission is requested for a one-item chooser, increasing privacy and review risk.
- An exported provider or overly broad path configuration exposes unrelated private files.

## Probing Questions

1. When should an app choose Photo Picker over SAF or MediaStore?
2. Why is converting a `content://` URI to a filesystem path incorrect?
3. How do you make a user-selected document available to delayed background work?
4. What validation belongs between URI selection and upload?
5. How should an app share one private PDF with another app?

## Answer Key

1. Photo Picker is for user-selected images/video; SAF is for documents or directory workflows; MediaStore is for publishing/querying shared media under the applicable access rules.
2. The provider may be remote, virtual, or database-backed. The URI is the supported capability; use `ContentResolver` streams/descriptors.
3. Take a persistable URI permission when supported, record it, and still handle later revocation. Otherwise copy the needed bytes while the temporary grant is valid.
4. Check declared and sniffed type, byte/decoded-size limits, malformed content, cancellation, privacy policy, and whether independent ownership requires a safe copy.
5. Configure a narrow `FileProvider`, produce a content URI, and grant temporary read access to the recipient.

## Further Reading

- [Android data and file storage overview](https://developer.android.com/training/data-storage/)
- [Photo Picker](https://developer.android.com/training/data-storage/shared/photo-picker)
- [Storage Access Framework](https://developer.android.com/training/data-storage/shared/documents-files)
- [Sharing files with FileProvider](https://developer.android.com/training/secure-file-sharing)
