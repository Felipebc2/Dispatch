---
id: discrete-log-pohlig-hellman-smooth-order
category: CRYPTO
tags: [discrete-log, dlog, dlp, pohlig-hellman, smooth-order, smooth-p-minus-1, b-smooth, bsgs, baby-step-giant-step, crt, diffie-hellman, dh, elgamal, shared-secret, primitive-root, generator-order, ecdlp, sympy, sage]
tools: []
manuals: []
title: "Discrete log with a smooth group order: Pohlig-Hellman + BSGS + CRT (DH / ElGamal)"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [rsa-small-n-factorization]
---

## How to recognize this pattern

- `p`, `g`, `h = g^x mod p` (often a DH/ElGamal public key plus a peer key); asked for `x` or the
  shared secret.
- `p` is not a safe prime: `p - 1` factors into small primes (hints like "every prime factor of p-1
  is small"). Same idea for elliptic curves with a smooth `E.order()`.

## Method

1. Factor the group order and look at the largest prime factor:
   `sympy.factorint(p - 1)` (or `factor(p - 1)` in Sage). Feasible if it is below about `2^40`.
2. Off-the-shelf: `sympy.discrete_log(p, h, g)` or Sage `discrete_log(Mod(h, p), Mod(g, p))`;
   both run Pohlig-Hellman automatically. Elliptic curves: `P.discrete_log(Q)` in Sage.
3. Dependency-free version (BSGS per prime, digit lifting per prime power, CRT):
```python
from math import isqrt
def bsgs(g, h, p, q):                    # x in [0, q) with g^x = h (mod p)
    m = isqrt(q) + 1
    table = {pow(g, j, p): j for j in range(m)}
    step, y = pow(g, -m, p), h
    for i in range(m):
        if y in table: return i * m + table[y]
        y = y * step % p
    raise ValueError("no log in this subgroup")

def pohlig_hellman(g, h, p, order, factors):   # factors = {q: e} of order
    xs, ms = [], []
    for q, e in factors.items():
        gq = pow(g, order // q, p)           # element of order q
        x = 0
        for k in range(e):                    # lift digit by digit: x mod q^(k+1)
            hk = pow(h * pow(g, -x, p) % p, order // q**(k + 1), p)
            x += bsgs(gq, hk, p, q) * q**k
        xs.append(x); ms.append(q**e)
    x, M = 0, 1                               # CRT
    for r, m in zip(xs, ms):
        x += M * ((r - x) * pow(M, -1, m) % m); M *= m
    return x, M                               # x is unique mod M
```
4. Use `order = ord(g)`, not blindly `p - 1`: start from `p - 1` and divide out each `q` while
   `pow(g, order // q, p) == 1`. Then `x, M = pohlig_hellman(g, h, p, order, factorint(order))`,
   check `pow(g, x, p) == h`, and for DH the shared secret is `pow(peer, x, p)`.

## Gotchas

- If `g` is not a primitive root, `x` is only defined mod `ord(g)`; every `x + k*ord(g)` is valid.
  The canonical answer is the smallest non-negative one unless the task bounds `x` otherwise.
- Partially smooth order with a large leftover prime: if `x` is known to be small (`x < 2^b`), solve
  mod the smooth part `M` and finish with BSGS over `x = x0 + k*M`, `k < 2^b / M`.
- A "posted log" in the prompt costs one `pow` to verify; check it before trusting it.
- NOT this pattern: safe prime `p = 2q + 1` with large `q`, or a large prime-order subgroup (then it
  is index calculus / NFS, rarely the intended CTF path). Also check the cheap traps first: `h` in a
  tiny subgroup, `x` small enough for plain BSGS, or `g` / `h` equal to `1` or `p - 1`.
- Composite modulus `n`: the group order is `lcm(p-1, q-1)`; factor `n` first, solve per prime, CRT.

## Cross-reference

- `rsa-small-n-factorization`: factordb / sympy tricks to factor the group order or a composite modulus.
