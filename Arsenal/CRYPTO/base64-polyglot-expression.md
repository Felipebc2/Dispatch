---
id: base64-polyglot-expression
category: CRYPTO
tags: [base64, eval, polyglot, expressao-matematica, encoding, notacao-cientifica]
tools: []
manuals: []
title: "Base64-as-code — generate an expression whose encoding is also valid"
difficulty: hard
created: 2026-09-03
updated: 2026-09-03
related: [single-digit-expression-solver]
---

## How to recognize this pattern

- A service (usually over `nc`/socket) reads an input line `L`, does something like
  `result = eval(base64.b64decode(L))` (or decodes first and then evaluates), and requires that
  `result` be an exact numeric value (e.g. `1337`, `3.14`, `pi`).
- The catch: you're not free to send any Python expression — the **string `L` you send MUST itself
  be valid base64** (alphabet `A-Za-z0-9+/=`, length a multiple of 4). In other words, you're
  looking for a string that is simultaneously (a) syntactically valid base64 and (b) when decoded, an
  expression that evaluates to the right value.
- Observed variant: the same problem using an **octal representation** (`0o472`) instead of pure
  base64, combining digits valid in both alphabets.

## Method

The general technique has two parts: **generate the target expression** and **make sure its encoding
is also a syntactically accepted base64/octal**. Rather than manually trying dozens of variant
scripts (that's what happened the first time around — 12+ nearly identical files), consolidate into a
single parameterized flow:

### 1. Generate expression candidates that evaluate to the target value

For a numeric target `TARGET` (integer or float):
- **Equivalent fractions:** `NUM/DEN` where `NUM/DEN == TARGET` (e.g. `3140/1e3` for `3.14`,
  or scaling by `k`: `NUM=TARGET_num*k, DEN=TARGET_den*k` to find a representation of the right
  length).
- **Scientific notation:** suffixes `e0`, `e-3`, etc., which preserve the value but change the
  length/characters of the string.
- **Neutral suffixes** (don't change the value, only the length so it matches base64's multiple of
  4): `+0`, `+00`, `/1`.
- **Python octal representation** (`0o472`) combined with decimal, when the challenge accepts/expects
  octal literals in the expression.

### 2. Filter candidates whose string is also a valid encoding

```python
import base64, binascii

def is_valid_base64_and_utf8(L: str) -> str | None:
    """Return the decoded text if L is valid base64 AND decodes as UTF-8, else None."""
    if len(L) % 4 != 0:
        return None
    if not all(c.isalnum() or c in '+/' for c in L):
        return None
    try:
        raw = base64.b64decode(L, validate=True)
        return raw.decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None
```

### 3. Search systematically: generate the target expression while varying scale/suffix, test whether the string itself matches the required encoding format

```python
def find_polyglot(target_num: int, target_den: int, k_max: int = 200_000,
                   suffixes=("", "+0", "+00", "/1"), max_suffix_len: int = 8):
    for k in range(1, k_max + 1):
        num, den = target_num * k, target_den * k
        if num > 10**9 or den > 10**9:
            continue
        for base_expr in (f"{num}/{den}",):
            for suf in suffixes:
                L = base_expr + suf
                if len(L) > max_suffix_len + len(base_expr):
                    continue
                if is_valid_base64_and_utf8(L) is not None:
                    return L  # L already IS both the expression AND valid base64
    return None
```

### 4. Send over a socket (common protocol: line + newline, read response)

```python
import socket

def send_line(host, port, line: str, timeout=6):
    with socket.create_connection((host, port), timeout=timeout) as s:
        s.settimeout(2)
        try:
            print(s.recv(4096).decode(errors="replace"))  # banner, if any
        except socket.timeout:
            pass
        s.sendall(line.encode() + b"\n")
        s.settimeout(3)
        out = b""
        try:
            while chunk := s.recv(4096):
                out += chunk
        except socket.timeout:
            pass
        return out.decode(errors="replace")
```

If the server decodes the input as **base64** (send `base64.b64decode(L)` as raw bytes, not `L` as
text) — check which of the two protocols the challenge actually expects before blindly repeating
attempts.

## Gotchas

- Watch the decode→eval vs eval→decode order — your script has to mirror exactly what the server
  does, otherwise the whole search is pointless.
- A multiple of 4 is mandatory for base64 without padding to work without error — always check
  `len(L) % 4 == 0` before considering a candidate valid.
- The search space can get large (high `k_max`) — start with low `k_max`/`max_suffix_len` and ramp
  up gradually, rather than running the heaviest version right away.
- **Don't reuse the original scripts 1:1** — they had the host/port/target hardcoded; the value is in
  the generation+filter logic above, parameterized for the current challenge.

## Related / Cross-reference

If the target asks for an integer expression instead of a fraction (e.g. using a single repeated
digit), see `Arsenal/PPC/single-digit-expression-solver.md` — same "generate an expression that
evaluates to the target" family, a PPC problem rather than an encoding bypass.
