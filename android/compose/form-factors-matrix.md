# Form Factors Decision Matrix (Wear, TV, Auto, Widgets)

"Should we build for the watch?" is a staff-level question because the honest answer is a cost model, not a yes. Each Android surface has its own UI toolkit, interaction grammar, review pipeline, and — critically — its own denominator of reachable users. This file is the decision matrix; phone/tablet adaptivity is owned by [Adaptive Compose & Large Screens](adaptive-compose-large-screens.md).

## 1. The Matrix

| Surface | Toolkit | Interaction model | What ports from the phone app | Typical cost |
|---|---|---|---|---|
| **Wear OS** | Compose for Wear (`androidx.wear.compose:compose-material3` 1.7.0, stable) | Glanceable, seconds-long sessions; rotary input; round screens | ViewModels, domain, data sync — **not** UI | A real second app, smaller but complete |
| **TV** | Compose for TV (`androidx.tv:tv-material` 1.1.0, stable) | D-pad + focus; 10-foot UI; lean-back | Domain + playback stack ([Media3](../media/media3-player-architecture.md)) | Medium — mostly a new UI shell over shared playback |
| **Auto / Automotive OS** | Car App Library (`androidx.car.app`) templates for driving; approved parked categories can use free-form UI | Driver-distraction-constrained; category-gated | Media session/library and domain logic; template-mapped flows for supported categories | Low for basic media; medium for templated media or navigation/POI; unavailable outside allowed categories |
| **Home-screen widgets** | Glance (`androidx.glance:glance-appwidget` 1.2.0 stable) | Glanceable, tap-through; no scrolling sessions | Data layer; rendering is RemoteViews-translated | Low — days to weeks |

## 2. What Each Surface Really Demands

**Wear OS.** Compose for Wear is a *parallel* Material implementation — `compose-material3` for Wear, `compose-foundation` additive, its own `compose-navigation`. Mixing the mobile Material artifacts in "can result in unexpected behavior" (the docs' words), so the watch UI is a separate module by construction: `ScalingLazyColumn`/`TransformingLazyColumn` instead of `LazyColumn`, `TimeText`, rotary-input handling. Beyond the app there are two more Wear surfaces — **tiles** and watch-face **complications** — which are often higher-value-per-engineering-hour than a full watch app: most watch interactions are single-glance.

**TV.** `androidx.tv` reached stable, and Leanback is formally deprecated in its favor ("This artifact and its classes are deprecated. Use Compose for TV instead"). The engineering center of gravity is **focus management**: every screen must answer "where does focus start, and where does each D-pad direction go" — a dimension phone UI never exercises. If your app is a media app, the [player-as-platform architecture](../media/media3-player-architecture.md) carries over intact; the TV work is the browse/focus shell (immersive lists, featured carousel) plus TV app-quality review.

**Cars.** Two distinct targets share much of the architecture: **Android Auto** projects from the phone, while **Android Automotive OS** runs on the car. Media apps can expose a `MediaLibraryService`/`MediaSession` content tree for the host to render; [Car App Library media templates](https://developer.android.com/training/cars/apps/media) are another supported path for more customized browsing and playback experiences. Navigation, communication, POI, IoT, and weather experiences use their approved category and template paths. Free-form UI belongs to supported parked categories: [games are available on both Android Auto and Automotive OS](https://developer.android.com/training/cars/whats-new), while other parked categories vary by platform. Category gating means some product ideas are *not buildable* in the car, and knowing that before the roadmap commits is the staff contribution.

**Widgets.** Glance offers Compose *syntax*, but it compiles to RemoteViews running in the launcher's process: no real recomposition (updates are explicit and periodic), RemoteViews-limited interactivity and layouts, and **no mixing with actual Compose UI code**. Treat a widget as a rendered projection of your data layer with tap-through intents — never as a mini-app. (Historical trap: `glance-wear-tiles` is deprecated, being replaced by a Glance wear-widgets library — Wear tile investment should target the current stack.)

## 3. The Decision Framework

Work through these in order; most "build it everywhere" proposals die at step 2:

1. **Is there a session that belongs on this surface?** A watch surface earns its keep only if the phone is the wrong device for the moment (workout logging, message triage, media control). Porting the phone journey shrunken is the canonical failure.
2. **What's the reachable-user denominator?** Instrument the overlap: how many of *your* actives have a watch/TV/car? A surface with 2% overlap and a separate UI stack is a maintenance contract, not a growth lever.
3. **What actually shares?** Domain, data, sync, and (for media) the playback stack share cleanly across all surfaces — this is where [modularization](../architecture/modularization-strategies.md) pays out. UI shares almost nothing: Wear and TV have parallel component sets, cars are templates, widgets are RemoteViews. Budget each surface's UI as new code.
4. **Who owns it after launch?** Every surface adds a test matrix ([device strategy](../testing/testing-strategy.md)), a release train, and platform-review requirements (TV quality guidelines, car category review). An unowned form factor decays into a one-star-review generator within a few OS cycles.
5. **Sequence by leverage:** widgets → media surfaces (Auto/TV if you're a media app) → Wear tile/complication → full Wear or TV apps. The early rungs reuse the most and risk the least.

## 4. Review Checklist

- Does the proposal name the *session* the new surface owns, or just the surface?
- Is the shared-module boundary drawn so the new surface consumes domain/data without forking it?
- Is anyone proposing mobile-Compose components on Wear, or free-form UI in a drivable car category? Both are platform-rule violations, not style choices.
- Widget designs that assume live interactivity or scrolling content — RemoteViews won't deliver them.
- Is there an owner and a test-matrix line item for the new surface, or only a launch plan?

## Further Reading

- [Compose for Wear OS](https://developer.android.com/training/wearables/compose) — artifacts, components, Material 3 for Wear
- [Wear Compose releases](https://developer.android.com/jetpack/androidx/releases/wear-compose) — current stable artifact versions
- [Compose for TV releases](https://developer.android.com/jetpack/androidx/releases/tv) — `tv-material`/`tv-foundation` status
- [Android for Cars overview](https://developer.android.com/training/cars) — Auto vs Automotive OS, category matrix, Car App Library
- [Jetpack Glance](https://developer.android.com/develop/ui/compose/glance) — widget architecture and constraints
- [Glance releases](https://developer.android.com/jetpack/androidx/releases/glance) — current stable artifact versions
