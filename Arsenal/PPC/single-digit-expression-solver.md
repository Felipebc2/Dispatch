---
id: single-digit-expression-solver
category: PPC
tags: [dp, memoizacao, fracoes, expressao-aritmetica, protocolo-nc, socket]
tools: []
manuals: []
title: "Generate an expression with a repeated digit that hits a target (DP/Fraction)"
difficulty: medium
created: 2026-09-03
updated: 2026-09-03
related: [base64-polyglot-expression]
---

## How to recognize this pattern

- A PPC challenge (over `nc`/socket) that sends a target number and a digit `D`, and asks for an
  arithmetic expression using **only that digit repeated** (`+`, `-`, `*`, `/`, `%`, concatenation) that
  evaluates exactly to the target.
- Usually in a loop: solve one, the server sends another (target, digit) pair, repeat N times against the
  clock.
- Signal that it's solvable by search: the target fits in a reasonable range (not astronomically large)
  and the wording allows the basic operations.

## Method

Two independent parts: **generating the expression** (algorithm) and **speaking the server's protocol**
(text parsing + timing). Neither depends on the old challenge's host/port, only the logic.

### 1. Expression generator via DP over exact fractions

Idea: for each "number of digits used" `k`, keep the set of values reachable using exactly `k` copies of
the digit, combining sub-results of size `a + b = k` with the 5 operations. Using `Fraction` avoids
floating-point error on divisions.

```python
from fractions import Fraction
from collections import defaultdict

def generate_expression(target: int, digit: str, max_digits: int = 12, max_magnitude: int = 10_000):
    D = digit
    target_f = Fraction(target, 1)
    if target == 0:
        return f"{D}-{D}"

    sets = [defaultdict(str) for _ in range(max_digits + 1)]
    for k in range(1, max_digits + 1):
        s = D * k
        sets[k][Fraction(int(s), 1)] = s

    for total in range(1, max_digits + 1):
        if target_f in sets[total]:
            return sets[total][target_f]
        for a in range(1, total):
            b = total - a
            for lv, ls in list(sets[a].items()):
                for rv, rs in list(sets[b].items()):
                    for op, expr_fmt, value in _try_ops(lv, rv, ls, rs):
                        if value is None or abs(value) > max_magnitude:
                            continue
                        cur = sets[total].get(value)
                        if cur is None or len(expr_fmt) < len(cur):
                            sets[total][value] = expr_fmt
                            if value == target_f:
                                return expr_fmt
    # fallback: simple repeated sum if the digit divides the target
    d = int(D)
    if d != 0 and target % d == 0:
        times = abs(target) // d
        if times <= 20:
            sign = "-" if target < 0 else ""
            return sign + "+".join([D] * times)
    return None

def _try_ops(lv, rv, ls, rs):
    yield "+", f"({ls}+{rs})", lv + rv
    yield "-", f"({ls}-{rs})", lv - rv
    yield "*", f"({ls}*{rs})", lv * rv
    if rv != 0:
        yield "/", f"({ls}/{rs})", lv / rv
    if lv.denominator == 1 and rv.denominator == 1 and rv != 0:
        yield "%", f"({ls}%{rs})", Fraction(int(lv) % int(rv), 1)
```

### 2. Socket interaction template (protocol parsing in a loop)

PPC servers over `nc` usually follow a loose text protocol: banner → waits for "ready" → sends the
prompt with target+digit → waits for the answer → confirms right/wrong → repeats or gives the flag.

```python
import socket, re, time

RE_READY   = re.compile(r"\bready\b", re.I)
RE_CHALL   = re.compile(r"number\s+([+-]?\d+)\s+use", re.I)
RE_DIGIT   = re.compile(r"digit\s+([0-9])", re.I)
RE_CORRECT = re.compile(r"(correct|\bOK\b)", re.I)
RE_FLAG    = re.compile(r"<FLAG_PREFIX>\{[^}]*\}")  # adjust to the real CTF format

def recv_until(sock, patterns, total_timeout=20.0, per_recv_timeout=2.0):
    sock.settimeout(per_recv_timeout)
    buf, start = "", time.time()
    while True:
        for i, p in enumerate(patterns):
            if p.search(buf):
                return i, buf
        if time.time() - start > total_timeout:
            return None, buf
        try:
            data = sock.recv(8192)
            if not data:
                return None, buf
            buf += data.decode(errors="ignore")
        except socket.timeout:
            continue

def solve_loop(host, port, max_digits=8):
    with socket.create_connection((host, port), timeout=15) as s:
        sent_ready = False
        while True:
            idx, buf = recv_until(s, [RE_READY, RE_CHALL, RE_FLAG])
            if idx is None:
                break
            if RE_FLAG.search(buf):
                print("FLAG:", RE_FLAG.search(buf).group(0))
                break
            if idx == 0 and not sent_ready:
                s.sendall(b"ready\n")
                sent_ready = True
                continue
            m_target, m_digit = RE_CHALL.search(buf), RE_DIGIT.search(buf)
            if not (m_target and m_digit):
                continue
            target, digit = int(m_target.group(1)), m_digit.group(1)
            expr = generate_expression(target, digit, max_digits=max_digits) or digit
            s.sendall((expr + "\n").encode())
```

## Gotchas

- A high `max_digits` makes the DP slow (it grows combinatorially). Start low (6-8) and only raise it if
  the server rejects for "no expression found".
- The parsing regexes (`RE_CHALL`, `RE_DIGIT`, etc.) are specific to the prompt's text. **Adjust them to
  the real wording of the current challenge**, don't copy the example literally.
- `RE_FLAG` must match the current CTF's flag format. Validate the flag against the CTF's configured
  flag format before declaring success.
- The repeated-sum fallback only works if `digit` divides `target` exactly. It's not a general
  guarantee, just a last resort before giving up on that target.

## Related / Cross-reference

`Arsenal/CRYPTO/base64-polyglot-expression.md`: same family of "generate an expression that evaluates to
the target", but there the goal is for the string itself to be a valid encoding, not to use a single
digit.
