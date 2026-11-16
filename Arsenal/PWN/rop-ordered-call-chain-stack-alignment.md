---
id: rop-ordered-call-chain-stack-alignment
category: PWN
tags: [rop, ret2win, call-chain, ordered-calls, forced-order, movaps, stack-alignment, system, segfault, no-pie, gets, ret-gadget, remote-vs-local]
tools: [pwntools]
manuals: ["Manuals/pwntools/3. Contexto para Claude.md"]
title: "ROP chain of ordered calls + the movaps/stack-alignment remote crash"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [stack-bof-ret2win-ret2libc, format-string-leak-write]
---

## How to recognize this pattern

- A classic stack overflow (`gets()`/oversized `read`) with **No PIE** and no canary, but the "win"
  is not a single function: several functions must run **in a forced order**, each refusing unless its
  predecessor already set a global (a "pins in order" / state-machine gate), and one of them also
  *builds* the string/argument the win function uses.
- The chain works **locally** but, on remote, stops silently partway (e.g. after the last setup call,
  no win output). That signature is the **`movaps` / stack-alignment crash inside `system()`**.

## Method

### 1. Find the offset and the ordered entry points
```bash
checksec ./bin          # No PIE, No canary
# offset = buffer + saved rbp (e.g. 64 + 8 = 72)
objdump -d ./bin        # addresses of func_a..func_e (the forced order) and win()
```

### 2. Build the chain in the required order
```python
from pwn import *
rop = b"A"*72 + b"".join(p64(a) for a in [A,B,C,D,E, WIN])   # exact order the gates demand
```
Route through the function that constructs the argument string (it may be mandatory for `system` to
have anything to run).

### 3. Fix remote alignment (the usual remote-only failure)
glibc `system()` does a 16-byte-aligned `movaps`; if `RSP % 16 != 0` at the call it SIGSEGVs. Remote
often has the opposite parity from local. Insert a single `ret` gadget before the win call to shift RSP
by 8:
```python
RET = 0x40101a
rop = b"A"*72 + b"".join(p64(a) for a in [A,B,C,D,E, RET, WIN])
```
If it still stops, sweep parity: try **two** `ret`s, or padding **71/73** instead of 72.

## Gotchas

- Locally aligned ≠ remotely aligned — if the chain is correct but the win line never prints on remote,
  suspect `movaps`, not a logic bug. Adding a `ret` that *desyncs* local alignment makes the flag vanish
  locally, confirming alignment is the lever.
- Buffered stdout means the win `puts` line is lost together with the crash — absence of output is the
  symptom, not proof the chain is wrong.
- Keep the last/padding semantics intact; only nudge alignment, don't reorder the gated calls.
- If no alignment variant works, the remote binary may differ from the handout — re-dump the win path
  and re-confirm addresses.

## Cross-reference

- `stack-bof-ret2win-ret2libc`: the base overflow→control-flow technique and gadget finding.
- `Manuals/pwntools`: `ROP()`, `cyclic`, `process` vs `remote`, `interactive()`.
