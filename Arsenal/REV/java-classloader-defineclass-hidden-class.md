---
id: java-classloader-defineclass-hidden-class
category: REV
tags: [java, jar, jvm, class-file, bytecode, javap, cfr, procyon, jd-gui, recaf, classloader, defineclass, custom-classloader, hidden-class, second-stage, embedded-class, cafebabe, reflection, getmethod, invoke, xor, byte-array, bastore, java-agent, classfiletransformer, jdb, decoy]
tools: [JVM-Android]
manuals: ["Manuals/JVM-Android/3. Contexto para Claude.md"]
title: "REV: hidden Java class decrypted and loaded at runtime (ClassLoader.defineClass)"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [dotnet-il-static-analysis, elf-hidden-section-foreign-arch-firmware, apk-jni-native-method-check, flag-check-reverse-transform]
---

## How to recognize this pattern

- A `.jar` with very few classes, but the prompt says it "loads another class" / "second class".
- A class `extends ClassLoader` (or uses `URLClassLoader`, `MethodHandles.Lookup.defineClass`,
  `Unsafe.defineAnonymousClass`) and calls `defineClass(name, bytes, 0, len)`.
- A class file much bigger than its logic: a huge `byte[]` literal compiled to hundreds of
  `dup / push idx / push val / bastore` sequences, or a resource blob read via
  `getResourceAsStream`.
- Then `Class.getMethod(...).invoke(...)` on methods that do not exist in the jar.
- Running it prints a decoy because `main` passes a fixed dummy argument to the hidden checks.

## Method

### 1. Inspect the jar
```bash
unzip -l chall.jar; unzip -o chall.jar -d ex/
cat ex/META-INF/MANIFEST.MF                      # Main-Class
javap -c -p -constants ex/Main.class | less      # look for defineClass, xor (ixor), bastore
java -jar cfr.jar ex/Main.class                  # readable Java with the array literal
```

### 2. Reconstruct the array and the key
- From CFR output: copy the `byte[]` literal and the decrypt loop.
- From bytecode (decompiler chokes or is absent): parse the initializer directly.
```python
import re, zipfile
c = zipfile.ZipFile('chall.jar').read('Main.class')
push = rb'([\x02-\x08]|\x10.|\x11..)'            # iconst_m1..5 | bipush | sipush
def val(op):
    return int.from_bytes(op[1:], 'big', signed=True) if op[0] in (0x10, 0x11) else op[0] - 3
enc = {val(i): val(v) & 0xff for i, v in re.findall(rb'\x59' + push + push + rb'\x54', c, re.S)}
assert sorted(enc) == list(range(len(enc)))
# key constants: e.g. "bipush A; istore_1; bipush B; istore_2" in main
a, b = (x[0] for x in re.search(rb'\x10(.)\x3c\x10(.)\x3d', c, re.S).groups())
blob = bytes(enc[i] ^ ((a + b * (i & 7)) & 0xff) for i in range(len(enc)))   # adapt to the loop
assert blob[:4] == b'\xca\xfe\xba\xbe'
open('Hidden.class', 'wb').write(blob)
```

### 3. Read the hidden class
```bash
javap -c -p -constants Hidden.class    # ldc "..." + String.equals = the accepted value
java -jar cfr.jar Hidden.class
```

### 4. Dynamic alternative: dump every defined class
Java agent (works for any loader, including encrypted resources):
```java
import java.lang.instrument.*; import java.nio.file.*;
public class Dump { public static void premain(String a, Instrumentation inst) {
  inst.addTransformer(new ClassFileTransformer() { public byte[] transform(ClassLoader l,
    String n, Class<?> c, java.security.ProtectionDomain p, byte[] b) {
      try { Files.write(Paths.get(n.replace('/', '_') + ".class"), b); } catch (Exception e) {}
      return null; } }); } }
```
```bash
javac Dump.java && printf 'Premain-Class: Dump\n' > m.txt && jar cfm dump.jar m.txt Dump*.class
java -javaagent:dump.jar -jar chall.jar        # run in a disposable dir: it executes the code
```
Or `jdb`: `stop in java.lang.ClassLoader.defineClass` and dump the `byte[]` argument.

## Gotchas

- Java bytes are **signed**: `-35` is `0xdd`; mask with `& 0xff` before XOR.
- Keys built from `(a + b*(i&7)) & 0xff` repeat every 8 bytes: check by XORing the first 4
  ciphertext bytes with `CA FE BA BE` to recover/confirm the key stream.
- `main` calling the hidden check with a constant like `"x"` is why running never reveals it.
- If the decrypted blob starts with `1f 8b` (gzip) or `PK` decompress first; if it starts with
  `dex\n` it is Android (`DexClassLoader` / `InMemoryDexClassLoader`): use jadx, not javap (and see `apk-jni-native-method-check` if the check is native).
- Class file major version > your JDK: `javap` still works on newer JDKs; CFR handles all.
- NOT this pattern if the jar simply ships all classes: then it is plain decompile plus
  `flag-check-reverse-transform`.

## Cross-reference

- `dotnet-il-static-analysis`: same decoy-output family for .NET IL.
- `elf-hidden-section-foreign-arch-firmware`: second program hidden inside a native carrier.
- `flag-check-reverse-transform`: when the hidden class transforms input instead of `equals`.
