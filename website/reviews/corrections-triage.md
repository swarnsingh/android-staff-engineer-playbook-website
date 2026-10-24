# Corrections Triage

Codex proposed 292 corrections to the original chapters, stored in `website/content/corrections-*.json`. None is applied until the owner approves it. Approved corrections appear on the website only, visibly marked; the original Markdown is never edited.

**Verdicts**

- **Approve:** the original is wrong or misleading, and the proposed text is right.
- **Approve with edit:** the original is wrong, but the proposed text needs the change shown.
- **Reject:** the original is fine, or the change is only rewording.

**Evidence** means the claim was compiled and run locally (Kotlin 2.4.21, kotlinx.coroutines 1.11.0, JDK 17), or checked against the current official source named.

To approve, mark the row. Approved rows get `"status": "approved"` in the JSON; "with edit" rows also get the amended text.

## Variables — 16 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| V1 | A `val xs: List<Int>` is safe to share because `listOf(...)` is immutable | `listOf` returns a read-only view, not an immutable list | Approve | Run: `(listOf(1,2,3) as MutableList)[0] = 99` gives `[99, 2, 3]` |
| V2 | "To get full immutability, both must apply" | The objects inside must be immutable too | Approve | Follows from V1 |
| V3 | `List<T>` over `MutableList<T>` gives value-level immutability | Read-only and immutable are different contracts | Approve | Kotlin collections overview |
| V4 | `lateinit` is not allowed on top-level properties | It is allowed | Approve | Run: top-level `lateinit var` compiles and works |
| V5 | Full immutability: use `List`, `Map`, `Set`, data classes | Those types alone do not guarantee it | Approve | Follows from V1 |
| V6 | Reflection won't show `const val`s as ordinary fields | They are `public static final` fields | Approve | Run: reflection lists `public static final BASE_URL` |
| V7 | Changing a `const val` value is binary-incompatible | Old binaries keep the old value; linking does not break | Approve | Kotlin properties docs |
| V8 | `by lazy` synchronizes on every read | After initialization, it reads a volatile field without locking | Approve with edit | Current `SynchronizedLazyImpl` source |
| V9 | Same claim, in Performance Considerations | Same | Approve | Same |
| V10 | Same claim, in Common Misconceptions | Same | Approve | Same |
| V11 | Any change to a `const val` is binary-incompatible | Renaming or removing breaks linking; a value change gives stale values | Approve | Kotlin properties docs |
| V12 | `val A = B + 1; val B = A * 2` can deadlock or NPE; fix with `by lazy` | In one file the compiler rejects it; across files it silently reads 0; lazy does not fix a cycle | Approve with edit | Run: compile error in one file; `A=1 B=2` across two files |
| V13 | Fix the cycle with `by lazy` | Two lazies that read each other overflow the stack | Approve | Run: `StackOverflowError` |
| V14 | A 200 ms build on the main thread causes an ANR | 200 ms is jank; the input ANR threshold is 5 seconds | Approve | Android vitals ANR page |
| V15 | Hilt sets the field in `…KeyModule_BindUseInstance` | Field injection happens in `onAttach` | Approve with edit | Hilt docs: injected on the first `onAttach` |
| V16 | `Room.databaseBuilder(…, AppDatabase::class.java)` inside `object AppDatabase` | The builder needs the `RoomDatabase` subclass, not the holder object | Approve | Room docs |

**Amended text**

- **V8:** "Con: delegate access has a small overhead; on the JVM, `SYNCHRONIZED` reads a volatile field after initialization instead of locking. Not usable on `var`; the standard lazy delegate cannot be reset and does not support coroutine cancellation." This keeps the original's true point that lazy is not usable on `var`, which the proposed text dropped.
- **V12:** "**Top-level `val` circular dependency.** In one file, the compiler rejects `val A = B + 1` before `B` is initialized. Split across files, it compiles and one value silently reads `0`; with several threads, class initialization can deadlock. Remove the cycle. `by lazy` only moves it: two lazies that read each other overflow the stack."
- **V15:** "Hilt injects the Fragment's fields in `onAttach`, before this `onViewCreated` use."

**Summary:** 13 approve, 3 approve with edit, 0 reject.
