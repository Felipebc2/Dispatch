---
id: hidden-check-off-main-path
category: REV
tags: [hidden-check, decoy, control-flow, signal-handler, sigaction, sigtrap, int3, ucontext, gregs, sa-siginfo, vectored-exception-handler, veh, seh, raiseexception, addvectoredexceptionhandler, exception-handler, anti-disassembly, overlapping-instructions, mid-instruction, junk-byte, linear-sweep, stack-pivot, rop-chain, gadgets, mov-rsp-ret, dead-code]
tools: [Ghidra]
manuals: ["Manuals/Ghidra/3. Contexto para Claude.md"]
title: "REV: real check hidden off the obvious path (signal/exception handler, mid-instruction jump, stack pivot)"
difficulty: hard
created: 2026-11-06
updated: 2026-11-06
related: [self-modifying-code-mprotect-xor-decrypt, flag-check-reverse-transform, static-triage-strings-ltrace, decoy-vs-real-checker-what-actually-runs]
---

## How to recognize this pattern

- `main` prints a "posted" answer, maybe compares against it (`strcmp` chain, `argc == 1000`
  path), but that compare is never reached on normal input or contradicts the prompt.
- Prompt mentions a "signal", "exception", "trap", "jumps into the middle", "pivots", "gadgets".
- Imports/opcodes that redirect control: `sigaction`/`signal`, `AddVectoredExceptionHandler`,
  `SetUnhandledExceptionFilter`, `RaiseException`, raw `int3` (`cc`), `ud2`, `mov rsp, X ; ret`,
  or a short `jmp` over a single byte.

## Method: decision tree

First rule: **find who reads the input and who prints pass/fail**. Then follow that, not `main`.
```bash
objdump -d -M intel ./chall | grep -nE 'int3|ud2|mov +rsp,|jmp +[0-9a-f]+ <[^>]*\+0x[1-3]>'
nm -n ./chall      # symbols like handler, mid, g_pop_rdi, chain are giveaways
```

### A. Signal handler (Linux: `sigaction` + `int3`/`ud2`/divide-by-zero)
- `main` registers `sa_sigaction = handler`, `sa_flags = SA_SIGINFO` (4) for SIGTRAP (5),
  SIGILL (4), SIGFPE (8) or SIGSEGV (11), loads input pointers into registers, then traps.
  Code after the trap is dead decoy (handler `_exit`s).
- Handler signature `handler(int sig, siginfo_t *si, ucontext_t *uc)`: `uc` arrives in `rdx`.
  On x86-64 glibc, `uc_mcontext.gregs[i]` is at `uc + 0x28 + 8*i`:

| offset | gregs | register |
|--------|-------|----------|
| `+0x68` | 8  | RDI |
| `+0x70` | 9  | RSI |
| `+0x78` | 10 | RBP |
| `+0x88` | 12 | RDX |
| `+0x90` | 13 | RAX |
| `+0x98` | 14 | RCX |
| `+0xa8` | 16 | RIP |

- Map those loads back to what `main` put in each register, then read the compares.
- Handlers that modify `gregs[REG_RIP]` resume elsewhere: follow the new RIP.

### B. Windows exception path (VEH/SEH)
- `AddVectoredExceptionHandler(1, handler)` then `RaiseException(code, ...)`, a deliberate
  access violation, or `int3`. `main` compares nothing; the handler reads input and decides.
- In Ghidra, open the function passed to `AddVectoredExceptionHandler`/`SetUnhandledExceptionFilter`;
  for SEH (`__try`) check `.pdata`/`.xdata` unwind handlers and the `__except` filter.
- Handler gets `EXCEPTION_POINTERS*`; `ContextRecord->Rip/Rcx/Rdx` play the role of `gregs`.

### C. Jump into the middle of an instruction (anti-disassembly)
- Stub like `eb 01 e8 ...` (`jmp +1` over a junk byte that starts a fake 5-byte `call`): a linear
  sweep decodes garbage and hides the real code. Also `74 xx 75 xx` (jz/jnz to the same target)
  followed by a junk byte.
- Fix: disassemble from the jump target.
```bash
objdump -d -M intel --start-address=0x128f ./chall | head -60
```
In Ghidra: clear the code at the junk byte (C), then disassemble (D) at the jump target; or
patch the junk byte to `90` (nop). Symbols like `mid` at `func+3` give it away when not stripped.

### D. Stack pivot onto a data chain (ROP as the checker)
- `lea rax, [chain] ; mov rsp, rax ; ret` (or `xchg rsp, rax`, `leave ; ret` with a forged rbp):
  a `.data` array becomes the instruction stream. Small gadget functions (`pop rdi ; ret`,
  `mov [rdi], sil ; ret`) plus a final "check/finish" function.
- Read the array as qwords and emulate: gadget address means "do this", the next qwords are
  popped operands.
```python
import struct
gad = {0x401182: 'pop_rdi', 0x401184: 'pop_rsi', 0x401186: 'pop_rdx',
       0x401188: 'write', 0x40118c: 'finish'}       # from nm
q = struct.unpack('<32Q', chain_bytes)               # chain_bytes read from .data via PT_LOAD
regs, mem, i = {}, {}, 0
while i < len(q):
    g = gad.get(q[i]); i += 1
    if g and g.startswith('pop_'): regs[g[4:]] = q[i]; i += 1
    elif g == 'write': mem[regs['rdi']] = regs['rsi'] & 0xff
    elif g == 'finish': break
print(regs, bytes(mem[k] for k in sorted(mem)))
```
- The answers are what the final function checks (written buffer, register values).

## Gotchas

- Decoys: the visible `strcmp` against a "posted" value, and code after the trap, are dead.
  Confirm with `printf '<decoy>\n' | ./chall` printing `fail`.
- `gdb` intercepts SIGTRAP itself: use `handle SIGTRAP nostop noprint pass` (and same for
  SIGILL/SIGSEGV) or the handler never runs under the debugger.
- In the handler, inputs come from saved registers in `ucontext`, not from the stack: read the
  `gregs` offsets carefully (RDI=8, RSI=9, RDX=12, not in push order).
- Stripped binaries hide `mid`/gadget names: look for `jmp` targets that land inside another
  instruction, and for `mov rsp` anywhere outside a function epilogue.
- After locating the real check, the transform is usually invertible (e.g. `rol8(c,4) ^ (k+K)`
  = nibble swap): continue with `flag-check-reverse-transform`.
- NOT this pattern: if the real code is encrypted on disk (garbage, `mprotect`), see
  `self-modifying-code-mprotect-xor-decrypt`; if the real checker runs before `main` or in a
  different file, see `decoy-vs-real-checker-what-actually-runs`.

## Cross-reference

- `flag-check-reverse-transform`: inverting the comparison once found.
- `self-modifying-code-mprotect-xor-decrypt`, `decoy-vs-real-checker-what-actually-runs`.
- `stack-bof-ret2win-ret2libc` (PWN): ROP chain mechanics from the exploitation side.
- `Manuals/Ghidra/3. Contexto para Claude.md`: clear/disassemble at a chosen address.
