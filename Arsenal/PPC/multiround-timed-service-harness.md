---
id: multiround-timed-service-harness
category: PPC
tags: [ppc, programacao-competitiva, harness, pwntools, remote, multi-round, cronometrado, regex, parse, proof-of-work, loop]
tools: [pwntools]
manuals: ["Manuals/pwntools/3. Contexto para Claude.md"]
title: "PPC: generic harness for a timed, multi-round service"
difficulty: medium
created: 2026-10-04
updated: 2026-10-04
related: [single-digit-expression-solver]
---

## How to recognize this pattern

- A service (`nc host port`) that sends **N problems in sequence** and demands a fast answer (time/round
  limit). Solving one by hand is trivial; the problem is **automating the loop** and parsing under
  pressure. "Solve 100 of these", "you have 10 seconds per question".
- Each round's algorithm is simple (arithmetic, string, a small search). The challenge is throughput.

## Method

### Skeleton (parse → compute → send → repeat)
```python
from pwn import *
context.log_level = "error"                      # don't spam; switch to "debug" if it stalls
io = remote("host", 1337)

# (if there's a proof-of-work in the banner, solve it first, see custom-tcp-service-scripting)

import re
for _ in range(1000):                            # or while True until the flag arrives
    line = io.recvline(timeout=5).decode(errors="ignore")
    if "flag{" in line:                           # flag arrived
        print(line); break
    m = re.search(r"(\d+)\s*([+\-*/])\s*(\d+)", line)   # adapt the regex to the round's wording
    if not m:
        continue                                 # noise/prompt line, next
    a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
    ans = {"+":a+b, "-":a-b, "*":a*b, "/":a//b}[op]
    io.sendline(str(ans).encode())
io.interactive()                                 # grab the final flag
```

### Robustness tips
- `recvuntil(b">")`/`recvline` depending on the prompt; log the first 2-3 rounds in `debug` to get the
  regex right before releasing the loop.
- If the compute is heavy, precompute/memoize outside the loop.

## Gotchas

- **Per-round timeout:** keep the parse cheap; avoid rebuilding the connection. If the round demands a
  response in ms, print/log overhead kills you. Silence it (`log_level="error"`).
- **Off-by-one on recv:** the server may send multi-line instructions before the 1st problem. Consume
  with `recvuntil` up to the real marker, don't assume 1 line.
- Division/quotient: confirm whether it's integer (`//`), float, or modulo. Read the round's wording.
- A proof-of-work in the handshake is common before the problems unlock → solve it first
  (`custom-tcp-service-scripting` has the pattern).

## Cross-reference

- `single-digit-expression-solver`: a specific instance (expression with a repeated digit / DP).
- `custom-tcp-service-scripting` (NET): enumerate the protocol and solve the handshake proof-of-work.
- `Manuals/pwntools/3. Contexto para Claude.md`: `remote`, `recvuntil`, `sendline`.
