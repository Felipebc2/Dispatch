---
id: dotnet-il-static-analysis
category: REV
tags: [dotnet, .net, csharp, cil, msil, il, ilspy, ilspycmd, dnspy, dnspyex, monodis, ildasm, dnfile, de4dot, mono, pe32, clr, assembly, dll, decompile, cctor, static-field, switch, user-strings, decoy, unity, assembly-csharp]
tools: []
manuals: []
title: "REV: .NET assembly (IL) static analysis, answers in code Main never prints"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [static-triage-strings-ltrace, flag-check-reverse-transform, java-classloader-defineclass-hidden-class, decoy-vs-real-checker-what-actually-runs]
---

## How to recognize this pattern

- `file` says `PE32 ... Mono/.Net assembly` (or `.dll` next to a `*.runtimeconfig.json`).
- `strings -el` (UTF-16, the `#US` heap) shows the printed text; plain `strings` shows type,
  field and method names (`#Strings` heap): suspicious methods that `Main` never calls usefully.
- Running it prints a decoy ("posted" value) plus a closing line; the real values are computed
  in methods guarded by some state (static field, switch case) that the normal run never hits.

## Method

### 1. Triage
```bash
file chall.dll
strings -el chall.dll            # user strings (ldstr literals)
strings -n 4 chall.dll | head -80   # type/method/field names
```

### 2. Decompile (preferred)
```bash
dotnet tool install -g ilspycmd
ilspycmd chall.dll -o out/              # C# source
ilspycmd -il chall.dll > chall.il        # raw IL, when C# output hides details
monodis chall.dll > chall.il             # Mono alternative
```
GUI: dnSpyEx (also debugs and lets you edit a method and re-save the assembly).
Obfuscated (ConfuserEx, renamed symbols, string encryption): run `de4dot chall.dll` first.

### 3. Evaluate the hidden path statically
- Read `.cctor` (static constructor): it sets the "initial state" (e.g. `tape = new byte[]{N}`).
- Follow each answer method with THAT state: guards like `if (s != OpenState()) return "decoy"`
  mean any other input returns a plausible wrong value.
- `switch` tables: case index = state; pick the target for your state, not the default.
- Re-implement the arithmetic in Python (`chr(s*MUL + ADD)` per char, etc.).

### 4. No decompiler available: parse IL bytes
`dnfile` (pip) gives the metadata tables and method RVAs. For tiny assemblies a regex over the
raw bytes is enough. Opcodes worth knowing:

| Op | Byte | Op | Byte |
|---|---|---|---|
| `ldarg.0` | `02` | `ldc.i4.0..8` | `16..1e` |
| `ldc.i4.s <i8>` | `1f` | `ldc.i4 <i32>` | `20` |
| `dup` | `25` | `ret` | `2a` |
| `beq.s` | `2e` | `switch <n> <i32 x n>` | `45` |
| `add`/`mul` | `58`/`5a` | `ldstr <token>` | `72` |
| `stsfld` | `80` | `newarr` | `8d` |
| `stelem.i1`/`stelem.i2` | `9c`/`9d` | `conv.u2` | `d1` |

```python
import re
d = open('chall.dll','rb').read()
# static byte[] init in .cctor: newarr; dup; ldc.i4.0; ldc.i4.N; stelem.i1; stsfld
state = re.search(rb'\x8d....\x25\x16([\x16-\x1e])\x9c\x80', d, re.S)[1][0] - 0x16
# switch(n): targets are relative to the end of the switch instruction
s = d.index(b'\x45\x05\x00\x00\x00'); base = s + 5 + 5*4
tgt = base + int.from_bytes(d[s+5+4*state: s+9+4*state], 'little', signed=True)
```

### 5. Dynamic confirmation (optional)
Call the method yourself instead of trusting `Main`: in PowerShell
`[Reflection.Assembly]::LoadFile("$PWD\chall.dll")` then invoke the static method via reflection,
or patch the guard in dnSpyEx and run.

## Gotchas

- Running only prints the decoy: the answer comes from reading the IL, not from executing.
- A `switch` "default" and every non-state case can share the decoy value: check which case
  index matches the state set in `.cctor`.
- `ldc.i4.s` is signed: values above 127 use `ldc.i4` (5 bytes).
- NOT this pattern if `file` says PE32+ with no CLR header, or the .NET app is **Native AOT /
  ReadyToRun-only**: that is native code, go to Ghidra (`flag-check-reverse-transform`).
- Unity game: the logic is in `Managed/Assembly-CSharp.dll`; with IL2CPP there is no IL (use
  Il2CppDumper instead).

## Cross-reference

- `static-triage-strings-ltrace`: generic first pass (remember `strings -el`).
- `java-classloader-defineclass-hidden-class`: same "managed bytecode, decoy output" family on JVM.
- `flag-check-reverse-transform`: once the check is readable, invert the transform.
