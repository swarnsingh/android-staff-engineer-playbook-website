# Native Memory and Bitmaps

## Overview

Android memory problems are not only Java heap leaks. Images, graphics buffers, native allocations, hardware bitmaps, JNI references, mmap files, database pages, and GPU resources can push a process into memory pressure even when the Kotlin heap looks reasonable.

Staff-level memory work requires reading both managed heap and native/system memory signals.

## Memory Buckets

| Bucket | Examples | Failure mode |
|---|---|---|
| Java/Kotlin heap | data classes, lists, lambdas, ViewModels | GC churn, OOM, leaks |
| Native heap | JNI libs, image decoders, SQLite, OkHttp native pieces | Native OOM, LMK pressure |
| Graphics/GPU | textures, hardware bitmaps, render buffers | jank, LMK, upload stalls |
| Ashmem/mmap | shared memory, mapped files | process RSS growth |
| Thread stacks | many threads, native recursion | memory pressure and scheduling overhead |
| Code/artifacts | dex, oat, native libraries | startup and resident memory cost |

Android kills processes based on total system pressure and process importance, not only Java heap exceptions.

## Bitmaps

Bitmap memory cost is roughly:

```text
width * height * bytesPerPixel
```

Common configs:

| Config | Bytes/pixel | Use |
|---|---:|---|
| `ARGB_8888` | 4 | Default high-quality images |
| `RGB_565` | 2 | No alpha, lower quality, legacy/limited use |
| Hardware bitmap | GPU-backed | Rendering efficiency, less mutable/flexible |

A 4000 x 3000 ARGB image is about 48 MB before overhead. A feed with several such images can destroy a low-end device.

## Decode to Display Size

Do not decode full-resolution images for small UI slots.

```kotlin
AsyncImage(
    model = ImageRequest.Builder(LocalContext.current)
        .data(url)
        .size(width = 320, height = 180)
        .crossfade(true)
        .build(),
    contentDescription = null,
    contentScale = ContentScale.Crop
)
```

The exact API depends on the image library, but the principle is constant: request the size you need.

## Compose Image Stability

Passing `Painter` through public composable APIs can defeat stability and cause unnecessary recomposition because image/painter equality is often not cheap or meaningful.

Prefer stable inputs:

```kotlin
@Composable
fun Avatar(
    imageUrl: String,
    contentDescription: String?,
    modifier: Modifier = Modifier
) {
    AsyncImage(
        model = imageUrl,
        contentDescription = contentDescription,
        modifier = modifier
    )
}
```

Avoid:

```kotlin
@Composable
fun Avatar(painter: Painter) {
    Image(painter = painter, contentDescription = null)
}
```

Use a `Painter` parameter only when the caller truly owns rendering behavior.

## GPU Upload Cost

Decoded bitmap memory is only part of the cost. The image may also need to upload to GPU memory before drawing.

If you manually use `ImageBitmap`, call `prepareToDraw()` before it enters a critical draw path.

```kotlin
LaunchedEffect(imageBitmap) {
    imageBitmap.prepareToDraw()
}
```

Most mature image loading libraries already optimize this path. Be careful when building custom image systems.

## Caching Strategy

Image caching has three budgets:

- Memory cache.
- Disk cache.
- Network cache.

Staff-level questions:

- Is cache keyed by stable content identity?
- Does URL include size or transformation parameters?
- Is memory cache sized by device tier?
- Are prefetches cancelled when UI interest disappears?
- Are animated images capped or avoided in lists?
- Is cache invalidation tied to content version?

Do not prefetch an infinite feed. Prefetch distance is a battery and memory policy.

## Native Memory Debugging

Use:

- Android Studio Memory Profiler for Java heap, allocations, and native memory view.
- Heap dumps for duplicate bitmaps and retained objects.
- `adb shell dumpsys meminfo <package>` for PSS/RSS-style process memory.
- Perfetto for memory pressure, GC, and frame correlation.
- Native heap tools for NDK-heavy apps.

Useful local command:

```bash
adb shell dumpsys meminfo com.example.app
```

Look for:

- Native heap growth after repeated navigation.
- Graphics memory growth while scrolling images.
- Allocations per frame.
- GC frequency during scroll.
- Large duplicate bitmaps.
- JNI global references.

## Low Memory Killer Signals

LMKs can look like crashes to users but bypass normal crash reporting. Android vitals tracks user-perceived LMK rate, where the app is killed in a way the user likely notices.

Treat LMK as a product reliability metric:

- Segment by device RAM.
- Segment by feature flow.
- Watch after image-heavy releases.
- Correlate with foreground service and camera/media sessions.
- Verify process death restoration because LMK can bypass graceful lifecycle paths.

## Bitmap Failure Modes

- Full-size camera images rendered in thumbnails.
- Image prefetch not cancelled when scrolling fast.
- Hardware bitmaps used where software mutation is needed.
- Animated GIF/WebP in unbounded feed.
- Passing unstable image objects through composable parameters.
- Duplicate cached images under different URL variants.
- Large images decoded on Main.
- Using `remember` to retain large bitmaps longer than the screen needs.
- Not testing low-RAM devices.

## Staff Engineer Review Checklist

- Are images decoded to display size?
- Are image requests stable and cacheable?
- Is memory cache sized by device tier?
- Are GPU upload and draw costs considered?
- Are animated and very large images constrained?
- Are duplicate bitmaps inspected in heap dumps?
- Is native memory monitored, not only Java heap?
- Are LMK rates monitored in Android vitals?
- Does process death restoration cover memory pressure kills?
- Are low-RAM devices included in performance tests?

## Further Reading

- [Android Developers: Optimizing bitmap images in Compose](https://developer.android.com/develop/ui/compose/graphics/images/optimization)
- [Android Developers: Low memory killers](https://developer.android.com/topic/performance/vitals/lmk)
- [Android Developers: Memory Profiler](https://developer.android.com/studio/profile/memory-profiler)
- [`memory-management-and-leaks.md`](memory-management-and-leaks.md) - managed memory and leaks.
- [`../compose/compose-performance-tooling.md`](../compose/compose-performance-tooling.md) - Compose performance measurement.
