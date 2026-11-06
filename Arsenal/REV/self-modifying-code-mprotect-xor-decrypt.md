---
id: self-modifying-code-mprotect-xor-decrypt
category: REV
tags: [self-modifying-code, smc, mprotect, virtualprotect, rwx, xor, encrypted-function, runtime-decrypt, code-decryption, custom-section, bad-opcodes, objdump, ghidra, gdb, static-decrypt, pyelftools, page-align]
tools: [Ghidra]
manuals: ["Manuals/Ghidra/3. Contexto para Claude.md"]
title: "REV: self-modifying code (function encrypted on disk, decrypted at runtime via mprotect + XOR)"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [static-triage-strings-ltrace, flag-check-reverse-transform, decoy-vs-real-checker-what-actually-runs, hidden-check-off-main-path]
---

## How to recognize this pattern

- Imports include `mprotect` (Linux) or `VirtualProtect` (Windows); prompt says the binary
  "rewrites", "patches" or "decrypts" itself before running.
- A named function (often in its own section, e.g. `readelf -S` shows a non-standard executable
  section) disassembles to garbage: `(bad)`, `int1`, `in`/`out`, random `jmp far`.
- `main` computes `addr & ~0xfff`, calls `mprotect(page, len, 7)` (PROT_RWX), loops `*p ^= key[i % n]`
  over a range, then `mprotect(page, len, 5)` (PROT_RX) and calls the function.
- A visible plaintext compare elsewhere (e.g. `argc == 1000` path with `strcmp`) is usually a decoy.

## Method

### 1. Find the key and the range
```bash
readelf -SW ./chall | grep -vE '\.(text|data|bss|rodata|plt|got)'   # odd exec sections
nm ./chall | sort                      # function start, next symbol / _fini = end of range
objdump -d -M intel ./chall --disassemble=main | grep -E 'mprotect|xor|mov +DWORD'
```
The key is usually an immediate (`mov DWORD [rsp+0xc], 0x512c7a13` = bytes `13 7a 2c 51`
little-endian) or a `.rodata` array. The range is `[func, end)` where `end` is the next symbol,
`_fini`, or a length constant.

### 2. Decrypt statically (vaddr to file offset)
```python
import sys
from elftools.elf.elffile import ELFFile
f = open(sys.argv[1], 'rb'); elf = ELFFile(f)
def off(va):
    for s in elf.iter_segments():
        if s['p_type'] == 'PT_LOAD' and s['p_vaddr'] <= va < s['p_vaddr'] + s['p_filesz']:
            return va - s['p_vaddr'] + s['p_offset']
START, END = 0x1322, 0x13a4            # function start, end of decrypted range
KEY = (0x512c7a13).to_bytes(4, 'little')
f.seek(off(START)); enc = f.read(END - START)
dec = bytes(b ^ KEY[i % len(KEY)] for i, b in enumerate(enc))
assert dec[:4] == b'\x55\x48\x89\xe5' or dec[:4] == b'\xf3\x0f\x1e\xfa', dec[:8].hex()
data = bytearray(open(sys.argv[1], 'rb').read()); o = off(START)
data[o:o + len(dec)] = dec
open(sys.argv[1] + '.dec', 'wb').write(data)      # patched copy: open it in Ghidra/objdump
```
Sanity check: a decrypted function starts with a normal prologue (`55 48 89 e5`, `f3 0f 1e fa`
endbr64, or `48 83 ec ..`). If not, the key index or range start is wrong.

### 3. Or let the binary decrypt itself (dynamic)
```bash
gdb -q ./chall
(gdb) break *<addr of call to the decrypted function>   # after the second mprotect
(gdb) run
(gdb) x/40i <func>                                       # now plaintext
(gdb) dump binary memory dec.bin <func> <end>
```
Use a hardware breakpoint (`hbreak`) if the breakpoint address is inside the encrypted range: a
software `int3` written there gets XORed and corrupts the code.

### 4. Read the decrypted check
Usually a byte-by-byte compare (`movzx eax, BYTE [rax] ; cmp al, imm8`) or a reversible
transform: continue with `flag-check-reverse-transform`.

## Gotchas

- When extracting `cmp al, imm8` (`3c xx`) by regex, anchor on the preceding load
  (`0f b6 00 3c xx`): a bare `3c` also matches jump displacements like `75 3c`.
- PIE: `nm` gives offsets relative to base 0; vaddr often equals file offset for small binaries,
  but always map through `PT_LOAD` as above.
- The key index may be `(p - func) & 3` (relative to function) or `p & 3` (absolute address).
  Try both if the prologue check fails.
- Multi-layer: the decrypted function may decrypt another one. Repeat, or go dynamic.
- Do not set software breakpoints inside a range before it is decrypted; also watch for
  checksums over `.text` that detect `int3` (anti-debug).
- NOT this pattern: garbage disassembly with no `mprotect`/write loop may be a packer
  (`self-extracting-packer-memfd-unpack`) or overlapping-instruction anti-disassembly
  (`hidden-check-off-main-path`).
- If a hint says an init/constructor installs a different checker, the decrypted function itself
  can be the decoy: see `decoy-vs-real-checker-what-actually-runs`.

## Cross-reference

- `static-triage-strings-ltrace`: first pass (spot `mprotect` in imports).
- `flag-check-reverse-transform`: inverting the decrypted check.
- `hidden-check-off-main-path`: other tricks that hide the real check from a linear read.
- `Manuals/Ghidra/3. Contexto para Claude.md`: load the patched `.dec` copy.
