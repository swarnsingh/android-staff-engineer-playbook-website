# CameraX Capture Architecture

## Overview

CameraX is the default starting point for most new Android camera features. It supplies a lifecycle-aware API over Camera2, normalizes many device differences, and organizes work into use cases. Drop to Camera2 only when a required control, sensor mode, or device workflow cannot be expressed or supported through CameraX; that decision carries a much larger compatibility and testing burden.

## Use-Case Model

- `Preview` produces frames for a `PreviewView` or another surface.
- `ImageCapture` optimizes still capture and returns an in-memory image or writes an output target.
- `ImageAnalysis` delivers frames to application code for ML, scanning, or measurement.
- `VideoCapture` manages recording through the video API.

Obtain a `ProcessCameraProvider`, select a camera, and bind a compatible group of use cases to a `LifecycleOwner`. Binding makes camera ownership explicit: CameraX opens and closes resources with the lifecycle. Unbind before replacing a use-case graph, and treat binding failure as a supported outcome because not every device supports every resolution, format, frame rate, and simultaneous-use combination.

## Analysis Pipeline

Image analysis must have a bounded latency budget. With `STRATEGY_KEEP_ONLY_LATEST`, CameraX can drop intermediate frames while the analyzer is busy, which is normally correct for real-time UI. Blocking mode preserves frames by applying backpressure to the camera pipeline and can stall preview if the analyzer is slow.

Always close each `ImageProxy`, including error and cancellation paths. Move inference off the main thread, bound concurrency, reuse buffers/models, and measure end-to-end age rather than only inference duration. A fast model processing old queued frames still produces a bad scanner.

Rotation and crop rectangles are metadata contracts. Test portrait, landscape, front-camera mirroring, display rotation, and output rotation independently. Do not assume preview coordinates equal sensor or analysis coordinates; use CameraX transformation information when mapping detection boxes onto UI.

## Production Architecture

Keep camera plumbing behind a controller or feature boundary. UI sends intents such as `Start`, `SwitchLens`, `Capture`, and `Stop`; the controller owns provider state, use-case binding, executors, and recoverable errors. Persist captured output only after completion, and expose an explicit capture state rather than letting Composables manipulate the provider.

Test on a device matrix: API levels, low-memory devices, front/rear cameras, rotations, fold/unfold transitions, permission denial, background/foreground, interrupted recording, and devices with limited supported combinations. Camera availability can change when another app or system component holds the camera. Make retry user-driven and observable rather than spinning an open loop.

Track bind failures, time-to-preview, capture latency, analyzer latency and frame age, dropped-frame ratio, recording failures, lens/device model, thermal state, and app lifecycle transitions. These fields turn “camera is black” into a diagnosable class of incidents.

## Failure Modes

- An `ImageProxy` is not closed and the pipeline stops delivering frames.
- Multiple analyzers or unbounded executors create memory pressure and stale results.
- The requested use-case combination is unsupported on a device.
- Permission is granted once, then revoked while the feature assumes permanence.
- Preview transforms and analysis coordinates diverge after rotation.
- Rebinding on every recomposition repeatedly opens the camera.

## Probing Questions

1. When is Camera2 justified instead of CameraX?
2. Why is “keep only latest” usually correct for a barcode scanner?
3. What happens if the analyzer never closes `ImageProxy`?
4. Where should use-case binding live in a Compose feature?
5. What metrics distinguish slow inference from a backed-up analysis pipeline?

## Answer Key

1. Only when required low-level controls or supported modes are unavailable through CameraX and the team accepts device-compatibility ownership.
2. The user needs the newest view of the world; queued frames increase decision age without improving correctness.
3. CameraX cannot recycle the buffer and eventually stops or blocks frame delivery.
4. In a lifecycle-aware controller/effect boundary with stable ownership, not directly in ordinary recomposition.
5. Measure analyzer duration, frame timestamp-to-result age, queue/drop behavior, and preview/capture latency together.

## Further Reading

- [CameraX overview](https://developer.android.com/media/camera/camerax)
- [CameraX architecture](https://developer.android.com/media/camera/camerax/architecture)
- [CameraX configuration](https://developer.android.com/media/camera/camerax/configuration)
- [CameraX lab-tested devices](https://developer.android.com/media/camera/camerax/devices)
