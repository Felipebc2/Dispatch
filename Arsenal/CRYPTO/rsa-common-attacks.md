---
id: rsa-common-attacks
category: CRYPTO
tags: [rsa, fermat, common-modulus, low-exponent, cube-root, small-e, wiener, boneh-durfee, small-d, hastad, e-3]
tools: [RsaCtfTool]
manuals: ["Manuals/RsaCtfTool/3. Contexto para Claude.md"]
title: "RSA: decision tree for the common attacks (Fermat / common modulus / low-e / Wiener)"
difficulty: medium
created: 2026-10-04
updated: 2026-10-04
related: [rsa-small-n-factorization]
---

## How to recognize this pattern

`n` is too large to factor directly (it's past `rsa-small-n-factorization`), but **some parameter
looks off**. The right attack is dictated by the parameters, so read them before guessing:

| Signal in the parameters | Attack | Why |
|---|---|---|
| `p` and `q` close (or a hint that "the primes were generated together") | **Fermat** | `n = a²-b²`, `a` near `√n` |
| same `n`, two different `e` (`gcd(e1,e2)=1`), two `c` | **common modulus** | Bézout: `m = c1^s · c2^t mod n` |
| small `e` (`e=3`) and `m^e < n` (short msg) | **cube root / low-exponent** | `c = m^e` without wrap → integer root |
| small `e` (`e=3`), the same `m` encrypted under `k≥e` different keys | **Håstad broadcast** | CRT + e-th root |
| huge `e` (near `n`) → small `d` | **Wiener / Boneh-Durfee** | continued fractions |

## Method

First let RsaCtfTool sweep: it covers all these attacks automatically:
```bash
~/ctf-venv/bin/RsaCtfTool --publickey key.pem --private          # try everything
~/ctf-venv/bin/RsaCtfTool -n <N> -e <E> --uncipher <C>           # loose n/e/c
~/ctf-venv/bin/RsaCtfTool -n <N> -e <E> --private --attack fermat # target one attack (faster)
```
See `Manuals/RsaCtfTool/2. Guia Passo a Passo.md` for the multi-key cases (`-e2`, `--uncipher2`).

If the tool fails or you want to understand/force it by hand:

**Fermat (p,q close):**
```python
from gmpy2 import isqrt
a = isqrt(n) + 1
while True:
    b2 = a*a - n
    b = isqrt(b2)
    if b*b == b2: break
    a += 1
p, q = a+b, a-b
```

**Common modulus (same n, e1≠e2):**
```python
from Crypto.Util.number import long_to_bytes
from sympy import gcdex
s, t, _ = gcdex(e1, e2)                       # s*e1 + t*e2 = 1
s, t = int(s), int(t)
m = (pow(c1, s, n) * pow(c2, t, n)) % n        # invert c if the exponent is negative
print(long_to_bytes(m))
```

**Cube root (e=3, m³<n):**
```python
from gmpy2 import iroot
m, exact = iroot(c, 3)
```

## Gotchas

- Fermat **only** works with `p`,`q` close. If `a` runs past ~millions of iterations without
  finding anything, this isn't the vector (stop; it's not slow, it's wrong).
- Common modulus requires `gcd(e1,e2)=1`; if an `s`/`t` is negative, use the modular inverse of the
  corresponding `c` (`pow(c, -s, n)`).
- Cube root only applies if the message **did not wrap** (`m^e < n`); if it did, it's Håstad (needs
  ≥e encryptions) or padding, so reconsider.
- A huge `e` is not a "challenge bug": it's the classic signal of a small `d` → Wiener.

## Cross-reference

- `rsa-small-n-factorization`: try factoring/factordb BEFORE these (cheaper).
- `Manuals/RsaCtfTool/3. Contexto para Claude.md`: flags and the signal→attack table.
