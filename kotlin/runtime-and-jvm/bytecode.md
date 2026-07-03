# Kotlin: Bytecode and Decompilation

> Real `javap -c` output, the JVM stack model, what Kotlin compiler tricks look like in instructions, and how to read R8-mapped stack traces back to source.

---

## 1. The Compilation Pipeline

```
.kt files
   │ kotlinc → .class (Java bytecode)
   ▼
.class files
   │ d8 / r8 → .dex (Dalvik bytecode)
   ▼
classes.dex in the APK
   │ on-device: ART loads .dex
   ▼
Cloud / on-device AOT (optional)
   │ baseline profile → AOT-compiled hot paths
   ▼
Runs in ART
```

You read **Java bytecode** (not DEX) for almost all Kotlin reasoning. DEX is the device-format conversion. The compiler tricks happen at `kotlinc` time; nothing about Kotlin's design is DEX-specific.

---

## 2. The JVM Stack Machine

The JVM is a stack machine, not a register machine. Every operation either:

- Pushes a value onto the operand stack.
- Pops one or more values and replaces them with a result.
- Reads/writes a local variable slot (numbered 0, 1, 2...).

```
fun add(a: Int, b: Int): Int = a + b
```

Compiles to:

```
public static int add(int, int);
  Code:
     0: iload_0       // push the int in local slot 0 (a)
     1: iload_1       // push the int in local slot 1 (b)
     2: iadd          // pop two ints, push their sum
     3: ireturn       // pop int and return it
```

Two local slots are taken by parameters. Three instructions do the work. No registers; just a stack.

The mnemonic prefix tells you the type: `i` int, `l` long, `f` float, `d` double, `a` reference. So `aload_0` pushes the reference in slot 0, `iload_0` pushes the int in slot 0.

---

## 3. Tools To Read Bytecode

| Tool | What it shows | When |
|---|---|---|
| `javap -c` | Method bytecode | First instinct |
| `javap -c -v` | Constant pool, attributes, stack-map frames | Deep dive |
| `javap -p -c` | Private members too | Reading optimized code |
| Android Studio: Tools → Kotlin → Show Kotlin Bytecode | Same as `javap` in the IDE | Quick check |
| Decompile button (Android Studio / IntelliJ) | Converts bytecode back to Java source | Understanding *what* Kotlin does |
| ASM (org.objectweb.asm) | Programmatic | Build-time analysis, custom transformers |

```bash
# Compile a Kotlin file
kotlinc Foo.kt -d Foo.jar

# Disassemble
javap -c -p Foo.jar FooKt
```

> **Show Kotlin Bytecode** vs **Decompile**: the first shows the actual JVM bytecode (the `iload_0` lines); the second runs it back through a decompiler (typically Fernflower) to recover Java-ish source. Use both. Bytecode shows truth; decompiled Java shows intent.

---

## 4. Constant Pool

Every `.class` file has a constant pool: strings, class names, method references, all numbered. Bytecode instructions reference these by index.

```
Constant pool:
   #1 = Methodref     #2.#3   // java/lang/Object."<init>":()V
   #2 = Class         #4      // java/lang/Object
   #3 = NameAndType   #5:#6   // "<init>":()V
   #4 = Utf8          java/lang/Object
   #5 = Utf8          <init>
   #6 = Utf8          ()V
   #7 = String        #8      // "Hello"
   #8 = Utf8          Hello
```

`ldc #7` pushes the string "Hello" — `ldc` ("load constant") references the constant-pool slot.

`javap -v` prints the pool. Useful when chasing down "what method is this calling?" — the descriptor `(Ljava/lang/String;)V` decodes as "takes a `String`, returns `void`."

---

## 5. Bytecode For Common Kotlin Constructs

### Property access

```kotlin
class User(val name: String) {
    fun greeting() = "Hi $name"
}
```

```
public final java.lang.String getName();
  Code:
     0: aload_0                    // push this
     1: getfield     #2 // Field name:Ljava/lang/String;
     4: areturn

public final java.lang.String greeting();
  Code:
     0: new          #3 // class java/lang/StringBuilder
     3: dup
     4: invokespecial #4 // Method java/lang/StringBuilder."<init>":()V
     7: ldc          #5 // String "Hi "
     9: invokevirtual #6 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
    12: aload_0
    13: invokevirtual #7 // Method getName:()Ljava/lang/String;
    16: invokevirtual #6 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
    19: invokevirtual #8 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
    22: areturn
```

Two observations:
1. `val name` becomes a **field** (`getfield`) **plus** a getter method. Accessing `user.name` from Kotlin calls `getName()`, not the field directly.
2. String templates compile to `StringBuilder` chains. `"Hi $name"` is not a runtime template — it's three `StringBuilder` calls at compile time.

### Null safety

```kotlin
fun length(s: String?): Int = s?.length ?: 0
```

```
public static final int length(java.lang.String);
  Code:
     0: aload_0
     1: ifnull        12              // if s == null, jump to 12
     4: aload_0
     5: invokevirtual #2 // Method java/lang/String.length:()I
     8: goto          13
    12: iconst_0                       // push 0
    13: ireturn
```

The `?.` becomes a simple `ifnull` branch. No reflection, no overhead. The Elvis (`?:`) becomes the fallback at offset 12.

### `data class`

```kotlin
data class User(val name: String, val age: Int)
```

Generates 4 free methods. Look at `equals`:

```
public boolean equals(java.lang.Object);
  Code:
     0: aload_0
     1: aload_1
     2: if_acmpeq     46                       // same reference? skip
     5: aload_1
     6: instanceof    #5 // class User
     9: ifeq          44                       // not a User? return false
    12: aload_1
    13: checkcast     #5
    16: astore_2
    17: aload_0
    18: getfield      #2 // name
    21: aload_2
    22: getfield      #2
    25: invokestatic  #6 // kotlin.jvm.internal.Intrinsics.areEqual
    28: ifeq          44
    31: aload_0
    32: getfield      #3 // age
    35: aload_2
    36: getfield      #3
    39: if_icmpne     44                       // primitive int compare
    42: iconst_1
    43: ireturn
    44: iconst_0
    45: ireturn
    46: iconst_1
    47: ireturn
```

Every `val` in the data class produces a field comparison. With 10 fields you'd see 10 such blocks. This is why "10 fields × 5,000 data classes" inflates `classes.dex`.

### `lateinit var`

```kotlin
class A {
    lateinit var name: String
}
```

```
public final java.lang.String getName();
  Code:
     0: aload_0
     1: getfield     #2 // Field name
     4: dup
     5: ifnull        11
     8: areturn
    11: pop
    12: ldc          #3 // String "name"
    14: invokestatic #4 // Method kotlin/jvm/internal/Intrinsics.throwUninitializedPropertyAccessException
    17: athrow
```

If the field is null, throws `UninitializedPropertyAccessException`. The cost over a plain `String?` is the extra `ifnull/throw` block per access.

### Coroutines

```kotlin
suspend fun fetch(): String {
    delay(1000)
    return "done"
}
```

The compiler rewrites this into a state machine. The signature changes (extra `Continuation` parameter), and the method becomes a `switch` over the saved state:

```
public static final java.lang.Object fetch(kotlin.coroutines.Continuation);
  Code:
     0: aload_0
     1: instanceof    #2 // class FetchKt$fetch$1
     4: ifeq          ...                       // first call vs resume?
     ...
    21: iload         11                        // load saved 'label'
    23: tableswitch   { ... }                   // jump to state 0 or state 1
    ...
    50: invokestatic  #4 // delay(JLkotlin/coroutines/Continuation;)Ljava/lang/Object;
    53: dup
    54: getstatic     #5 // COROUTINE_SUSPENDED
    57: if_acmpne     61                        // if not suspended, continue
    60: areturn                                 // suspend! return COROUTINE_SUSPENDED
```

The `delay(1000)` call either returns immediately (and execution continues) or returns the `COROUTINE_SUSPENDED` sentinel, in which case the function unwinds back to its caller without finishing. A separate generated class (`FetchKt$fetch$1`) holds the saved state.

This is why coroutines are not threads. The "suspended" state is an object on the heap + a label int; resuming = re-entering the method with the saved continuation.

---

## 6. Inlining Bytecode Evidence

For `inline` functions, see `inline-functions.md` for full evidence. The short version:

```kotlin
inline fun doMath(op: (Int, Int) -> Int): Int = op(5, 10)

fun calc() = doMath { x, y -> x + y }
```

Without `inline`, the bytecode for `calc()` constructs a `Function2` object. With `inline`, the bytecode for `calc()` directly contains `iconst_5`, `bipush 10`, `iadd`. No object allocation; the lambda evaporated.

---

## 7. R8 / ProGuard Bytecode Transformations

R8 (the default Android shrinker) does several things visible in bytecode:

1. **Renaming.** `com.example.User` becomes `a.b.c`. Class name + field names shortened.
2. **Inlining.** Trivial methods become inlined into callers.
3. **Dead-code elimination.** Unused classes/methods stripped.
4. **Class merging.** Sealed hierarchies sometimes flattened.

```
// Before R8
public final class com.example.UserRepository {
    public final getUser(Ljava/lang/String;)Lcom/example/User;
}

// After R8
public final class a.b.c {
    public final a(Ljava/lang/String;)La/b/d;
}
```

The mapping file (`mapping.txt`) records the rename:

```
com.example.UserRepository -> a.b.c:
    com.example.User getUser(java.lang.String) -> a
com.example.User -> a.b.d:
    java.lang.String name -> a
```

Crash reports show `a.b.c.a(...)`. Upload `mapping.txt` to Crashlytics/Sentry and the symbolicator reverses it.

---

## 8. Reading An Obfuscated Stack Trace

```
java.lang.NullPointerException
  at a.b.c.a(SourceFile:42)
  at d.e.f.b(SourceFile:18)
```

With `mapping.txt`:

```
com.example.UserRepository -> a.b.c:
    com.example.User getUser(java.lang.String) -> a
com.example.MainActivity -> d.e.f:
    void onCreate(android.os.Bundle) -> b
```

Re-symbolicated:

```
java.lang.NullPointerException
  at com.example.UserRepository.getUser(SourceFile:42)
  at com.example.MainActivity.onCreate(SourceFile:18)
```

Tools: `retrace` (R8 CLI), Crashlytics/Sentry auto-upload mapping during build, manual via `mapping.txt` + the `proguard-retrace` jar.

---

## 9. DEX Specifics (Briefly)

Same bytecode, different encoding. JVM stack-based; DEX register-based. `iadd` (JVM) ≈ `add-int` (DEX); `aload_0` ≈ `move-object v0, p0`.

To read DEX:

```bash
# Disassemble a .dex
$ANDROID_HOME/build-tools/35.0.0/dexdump -d classes.dex

# Or with baksmali (smali syntax)
java -jar baksmali.jar disassemble classes.dex -o smali_out/
```

You rarely need DEX. The optimizations you care about happen at JVM bytecode time before D8/R8.

---

## 10. Practical Workflow: Investigating "Why Is This Slow?"

```kotlin
// Suspect: this loop in a hot scroll path
list.map { it.title }.filter { it.startsWith("X") }.firstOrNull()
```

Investigation:

1. Open `Tools → Kotlin → Show Kotlin Bytecode`.
2. See three calls: `Iterable.map`, `Iterable.filter`, `Iterable.firstOrNull`. Each allocates an intermediate `ArrayList`.
3. Decompile: confirms three intermediate lists.
4. Refactor to `asSequence().map { }.filter { }.firstOrNull()` and check bytecode again — now uses `Sequence` which fuses operations into a single pass.
5. Macrobenchmark the change. Allocation count drops; scroll improves.

The cycle: bytecode → understand cost → refactor → re-check bytecode → measure.

---

## 11. Common Pitfalls

- **Trusting decompiled Java for performance reasoning.** Decompiled is best-effort source; bytecode is truth.
- **Reading bytecode without `-c` flag.** `javap` alone shows method signatures only.
- **Ignoring the constant pool.** Many "what does this call?" questions answered by reading the pool.
- **Confusing `invokevirtual` (instance dispatch) with `invokestatic` (no `this`) and `invokeinterface` (interface dispatch).**
- **Forgetting `getter` overhead.** `user.name` ≠ field read; it's a method call.
- **Believing reflection on Kotlin properties just works after R8.** Names mangled; need keep rules.
- **Skipping the mapping file.** Production stack traces unreadable without it.
- **Counting decompiled Java lines as APK cost.** Bytecode line count + constant pool size is closer to truth.

---

## 12. Further Reading

- [JVM Specification — Chapter 6: Instructions](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-6.html) — official mnemonic reference.
- [`javap` man page](https://docs.oracle.com/en/java/javase/21/docs/specs/man/javap.html) — disassembler options.
- [ASM library](https://asm.ow2.io/) — programmatic bytecode manipulation.
- [Android Developers — R8 mapping files](https://developer.android.com/build/shrink-code#decode-stack-trace) — symbolication.
- [Kotlin under the hood](https://kotlinlang.org/docs/) — official docs, look for "Kotlin/JVM" sections.

---

> **In short:** the JVM is a stack machine; `javap -c` shows the truth; Kotlin's compiler magic (data classes, suspend, inline) leaves visible fingerprints in bytecode; R8 transforms class names + inlines + DCE; mapping files reverse the obfuscation. Read bytecode first, decompiled Java second, intent third.
