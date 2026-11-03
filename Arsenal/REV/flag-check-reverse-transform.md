---
id: flag-check-reverse-transform
category: REV
tags: [reversing, flag-check, xor, decompile, ghidra, constante-hardcoded, strcmp, transform]
tools: [Ghidra]
manuals: ["Manuals/Ghidra/3. Contexto para Claude.md"]
title: "Flag check by reversible transform — recover it from the constant"
difficulty: medium
created: 2026-10-04
updated: 2026-10-04
related: []
---

## How to recognize this pattern

- The binary asks for a password/flag, applies a transform to the input, and compares the result
  against a **hardcoded** byte blob (`memcmp`/`strcmp`/byte-by-byte comparison loop).
- `strings` doesn't give you the flag directly (it's transformed), but a suspicious constant/byte
  array shows up in `.data`/`.rodata`.
- The most common CTF transforms: XOR with a fixed or index-based key, adding/subtracting an offset,
  swapping bytes (permutation), homemade Base64/hex, or a combination of these.

## Method

### 1. Decompile and locate the comparison
In Ghidra (the `ghidra` MCP, see the Manual): find `main`/the check function, identify (a) where the
input is read, (b) the transform loop, (c) the target constant and the `memcmp`.

### 2. Extract the target constant
Read the expected bytes straight from the decompiler or the binary:
```bash
objdump -s -j .rodata ./chall      # dump .rodata with offsets
```

### 3. Invert the transform
```python
target = bytes.fromhex("....")          # extracted constant
# XOR with a fixed key (involutive — invert = reapply):
key = b"\x37"
flag = bytes(b ^ key[0] for b in target)
# index-based XOR / repeating key:
key = b"s3cr3t"
flag = bytes(b ^ key[i % len(key)] for i, b in enumerate(target))
# offset addition: invert = subtract
flag = bytes((b - 13) % 256 for b in target)
print(flag)
```
Validate: run the binary with the recovered flag and confirm the success message.

## Gotchas

- **Non-reversible transform** (hash, lossy modulo, partial comparison): can't be inverted — fall
  back to brute-forcing the input space or modeling it in `z3` (`from z3 import *`, declare the bytes
  as `BitVec`, impose the check's constraints, `solve`).
- Comparison of only the **prefix** (`strncmp(in, const, n)`): recovers only the first `n` bytes —
  the rest can be anything.
- A key derived at runtime (from argv, time, PID) instead of a constant — map the key's origin before
  inverting.
- Endianness when reading constants as integers — check in the decompiler whether it's LE/BE.

## Cross-reference

Full flow for decompiling, renaming symbols, and navigating the binary:
`Manuals/Ghidra/3. Contexto para Claude.md`.
