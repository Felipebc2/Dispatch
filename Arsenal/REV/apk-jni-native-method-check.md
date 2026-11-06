---
id: apk-jni-native-method-check
category: REV
tags: [android, apk, dex, classes-dex, jni, native-method, jni-onload, registernatives, jninativemethod, java-prefix, libso, lib-x86-64, arm64-v8a, jadx, apktool, baksmali, ctypes, unicorn, frida, decoy]
tools: [JVM-Android, Ghidra]
manuals: ["Manuals/JVM-Android/3. Contexto para Claude.md", "Manuals/Ghidra/3. Contexto para Claude.md"]
title: "REV: APK whose real check is a JNI native method in lib/*.so"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [flag-check-reverse-transform, static-triage-strings-ltrace, decoy-vs-real-checker-what-actually-runs, java-classloader-defineclass-hidden-class]
---

## How to recognize this pattern

- `unzip -l app.apk` shows `classes.dex` plus `lib/<abi>/libX.so`.
- Java side declares `native` methods (`public native int accept(String s, int n);`) and calls
  `System.loadLibrary("X")`; the Java logic itself only prints a "posted" decoy.
- The `.so` exports `JNI_OnLoad` (dynamic registration) or `Java_<pkg>_<Class>_<method>` (static).

## Method

### 1. Unpack and read the Java side
```bash
mkdir apk && cd apk && unzip -q ../app.apk
jadx -d out ../app.apk           # or: apktool d ../app.apk ; baksmali d classes.dex
grep -rn 'native\|loadLibrary' out/sources | head
strings -n 4 classes.dex         # tiny dex: the string table already shows methods + signatures
```
Note each native method's name and JNI signature, e.g. `(Ljava/lang/String;I)I` = takes
`String, int`, returns `int`.

### 2. Find the native implementation
```bash
nm -D lib/x86_64/libX.so | grep -E 'Java_|JNI_OnLoad'
nm lib/x86_64/libX.so            # if not stripped: local symbols such as native_accept, table
readelf -x .data lib/x86_64/libX.so
```
- Static binding: function named `Java_com_pkg_Class_method`.
- Dynamic binding: `JNI_OnLoad` calls `(*env)->RegisterNatives(env, cls, table, n)` with a
  `JNINativeMethod[] = { char *name; char *signature; void *fnPtr; }` (3 pointers, 24 bytes on
  64-bit). Dump the table: name string, signature string, function address.
- Pick the ABI you can read best (`x86_64` over `arm64-v8a` if both exist; same logic).

### 3. Reverse the native function
In Ghidra, retype args: real JNI functions are `(JNIEnv *env, jobject thiz, jstring s, jint n)`
and get the C string via `env->GetStringUTFChars` (vtable call `[rax+0x548]` on 64-bit). Import a
`jni.h` GDT or define `JNIEnv` to make the vtable calls readable. Then invert the compare
(`flag-check-reverse-transform`).

### 4. Verify by calling it from the host (x86_64 lib only)
If the function takes plain C types (no `JNIEnv*`) and imports only libc:
```python
import ctypes
lib = ctypes.CDLL('./lib/x86_64/libX.so')
base = ctypes.cast(lib.JNI_OnLoad, ctypes.c_void_p).value - 0x1170   # JNI_OnLoad offset from nm
f = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int)(base + 0x1109)  # target offset
print(f(b'GUESS', 6))
```
If it needs `JNIEnv`, emulate with Unicorn/Qiling with a fake env, or run on an emulator/device
and hook with Frida:
```js
Java.perform(() => {
  const C = Java.use('com.pkg.Class');
  C.accept.implementation = function (s, n) { const r = this.accept(s, n); console.log(s, n, r); return r; };
});
```

## Gotchas

- The dex method returning the "posted" answer is the decoy; the native method is the check.
- Stripped `.so` with dynamic registration: find `JNI_OnLoad`, follow the `RegisterNatives`
  vtable call (offset `0x6b8` on 64-bit `JNINativeInterface`), and read its table argument.
- ARM-only libs cannot be loaded with `ctypes` on x86: solve statically or use
  `qemu-aarch64`/Unicorn.
- `jint` is 32-bit, `jboolean` is 8-bit: watch truncation in the compare.
- Obfuscated native strings (XORed names/signatures) are decrypted in `JNI_OnLoad` before
  `RegisterNatives`: break there or emulate it.
- NOT this pattern: no `lib/` folder and no `native` keyword means the check is in Java/Kotlin
  bytecode (read with jadx); a `.so` that only wraps crypto may be a library, not the checker.

## Cross-reference

- `flag-check-reverse-transform`: inverting the native compare.
- `decoy-vs-real-checker-what-actually-runs`: when several libs/builds compete.
- `Manuals/Ghidra/3. Contexto para Claude.md`: decompiling the `.so`.
