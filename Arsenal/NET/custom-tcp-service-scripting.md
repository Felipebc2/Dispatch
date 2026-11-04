---
id: custom-tcp-service-scripting
category: NET
tags: [net, socket, tcp, protocol, nc, pwntools, automation, banner, proof-of-work]
tools: [pwntools]
manuals: ["Manuals/pwntools/3. Contexto para Claude.md"]
title: "Custom TCP service: enumerate the protocol and automate interaction"
difficulty: easy
created: 2026-10-04
updated: 2026-10-04
related: [base64-polyglot-expression]
---

## How to recognize this pattern

- The challenge gives a `host:port` and expects interaction with a hand-made service (menu, prompt, a
  sequence of questions, a proof-of-work challenge before it unlocks).
- Solving it "by hand" with `nc` is impractical when there are many rounds, a short timeout, or an
  account/PoW to compute per message. You need to script it.

## Method

### 1. Manual recon
```bash
nc <host> <porta>            # read the banner, understand the protocol (line? binary? menu?)
```
Note: is the service line-oriented (`\n`) or byte-oriented? Does it expect something before it responds?
Is there a proof-of-work in the banner (e.g. *"give S such that sha256(S).startswith('00000')"*)?

### 2. Automate with pwntools
```python
from pwn import *
io = remote("HOST", PORT)
io.recvuntil(b"> ")                 # sync on the prompt
io.sendline(b"1")                   # pick a menu option
data = io.recvline()                # read the response
# typical loop of N rounds (solve a little computation/conversion and send it back):
for _ in range(100):
    q = io.recvline().decode()
    ans = str(eval(q.split("=")[0].strip()))   # adapt to the real question format
    io.sendline(ans.encode())
print(io.recvall(timeout=3))        # flag at the end
```

### 3. Proof-of-work (common gate pattern)
```python
import itertools, hashlib, string
prefix = io.recvline()              # extract the challenge (prefix + number of zeros/condition)
# e.g. find a suffix such that sha256(challenge+suffix) starts with N hex zeros
for n in itertools.count():
    s = str(n).encode()
    if hashlib.sha256(challenge + s).hexdigest().startswith("00000"):
        io.sendline(s); break
```

## Gotchas

- **Bytes vs text:** pwntools works in bytes. `sendline` already adds `\n`; don't double it.
- Sync with `recvuntil(prompt)` instead of a fixed `recv(n)`. A custom service rarely sends a
  predictable size.
- Short server timeout: build the loop to respond fast; only raise `io.timeout` for the final read of the
  flag.
- If the service drops a shell (e.g. post-exploitation), use `io.interactive()`.
- PoW: read the condition carefully (hex zeros vs binary zeros, hash of `challenge+suffix` vs
  `suffix+challenge`). Getting the order wrong invalidates the whole search.

## Related / Cross-reference

A service that `eval`s/`b64decode`s the input and demands a numeric result →
`Arsenal/CRYPTO/base64-polyglot-expression.md` (has a ready-made socket helper).
