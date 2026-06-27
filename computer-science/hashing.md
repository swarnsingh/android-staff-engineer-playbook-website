# Computer Science: Hashing (Applied to Mobile)

## The Theory
Hashing is the process of mapping data of arbitrary size to fixed-size values. A good hash function is deterministic (same input always yields same output), fast to compute, and uniformly distributed (minimizes collisions).

## Staff-Level Application in Mobile

### 1. Deterministic A/B Testing
Instead of asking the server "Which A/B test bucket is User 123 in?" and waiting 200ms for a network response, a Staff engineer uses **MurmurHash3**.
```kotlin
val hash = MurmurHash3.hashString("user_123" + "experiment_blue_button")
val bucketIndex = Math.abs(hash) % 100 
// If bucketIndex < 50, show Blue. Else show Red.
```
This is an `O(1)` synchronous evaluation. It allows UI rendering to remain unblocked while mathematically guaranteeing a perfect 50/50 split and extreme consistency (User 123 will *always* hash to the exact same bucket across sessions).

### 2. Cache Keys and ETags
When downloading a 4MB image, we don't save it as `image.jpg`. We hash the URL using SHA-256 to generate the filename: `sha256(url) + ".jpg"`.
When the server sends an HTTP response, it sends an `ETag` (a hash of the response body). On the next request, the mobile app sends `If-None-Match: <ETag>`. The server calculates the hash of the current database state; if it matches, it returns HTTP `304 Not Modified`, saving 4MB of bandwidth.

### 3. Deep Link Verification (assetlinks.json)
Android OS uses cryptographic hashing (SHA-256) to verify App Links. The `assetlinks.json` file hosted on your website contains the SHA-256 fingerprint of your App Signing Certificate. When the user taps a link, the OS hashes the installed APK's certificate. If the hashes match, the OS bypasses the disambiguation dialog and opens the app instantly, preventing phishing attacks.

## Common Pitfalls
-   **Security vs Speed:** Do not use `SHA-256` or `BCrypt` for A/B testing or HashMaps; they are designed to be slow to prevent brute forcing. Use `MurmurHash` or `CityHash` when you need speed and don't care about cryptographic security.
-   **Overriding `hashCode()`:** If you override `equals()` in a Kotlin data class, you *must* override `hashCode()`. If you don't, two identical objects will have different hashes, and if you place them in a `HashSet` or a Compose `LazyColumn` key, the system will fail to recognize them as duplicates, causing massive memory leaks or UI re-renders.
