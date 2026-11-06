---
id: rsa-franklin-reiter-related-message
category: CRYPTO
tags: [rsa, franklin-reiter, related-message, related-plaintext, gcd-polynomial, polynomial-gcd, linear-padding, known-offset, small-e, e-3, same-modulus, ciphertext-difference, coppersmith, sage]
tools: [RsaCtfTool]
manuals: ["Manuals/RsaCtfTool/3. Contexto para Claude.md"]
title: "RSA related messages: Franklin-Reiter polynomial GCD (and the integer-difference shortcut)"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [rsa-common-attacks, rsa-small-n-factorization]
---

## How to recognize this pattern

- Same `n`, same (usually small) `e`, **two ciphertexts** `c1`, `c2`, and a stated relation between the
  plaintexts: "the second is the first plus k", "messages differ by a constant", a counter or
  padding byte that differs by a known amount, `m2 = a*m1 + b` with known `a`, `b`.
- Plain cube root of `c1` is not exact (`m^e` wrapped mod `n`), so low-exponent alone fails.
- Any "sample root" or "posted value" line pushing toward a direct `iroot` is usually a decoy.

## Method

**1. Integer shortcut (try first, `e = 3`, `m2 = m1 + d`).** Each cube wraps, but the difference
`(m+d)^3 - m^3 = 3d*m^2 + 3d^2*m + d^3` may stay below `n` (small `d`, `m` around `n^(1/2)` or less).
Then `(c2 - c1) mod n` equals it over the integers and you just solve a quadratic:
```python
from math import isqrt
D = (c2 - c1) % n
A, B, C = 3*d, 3*d*d, d**3 - D
disc = B*B - 4*A*C
s = isqrt(disc)
assert s*s == disc, "difference wrapped: use the general GCD below"
m1 = (-B + s) // (2*A)
assert pow(m1, 3, n) == c1 and pow(m1 + d, 3, n) == c2
```

**2. Franklin-Reiter (general).** `m1` is a common root of `f1 = x^e - c1` and
`f2 = (a*x + b)^e - c2` over `Z_n`; their GCD is almost always the linear `x - m1`.
Pure Python (fine up to `e` of a few hundred):
```python
from math import comb
def prem(a, b, n):                       # a mod b, coeff lists low->high, over Z_n
    a = a[:]; inv = pow(b[-1], -1, n)    # ValueError here = gcd(lead, n) > 1, which factors n
    while len(a) >= len(b):
        f, s = a[-1] * inv % n, len(a) - len(b)
        for i, co in enumerate(b): a[s + i] = (a[s + i] - f * co) % n
        while a and a[-1] == 0: a.pop()
    return a

def franklin_reiter(c1, c2, e, n, a=1, b=0):    # m2 = a*m1 + b
    f1 = [(-c1) % n] + [0] * (e - 1) + [1]                                       # x^e - c1
    f2 = [comb(e, k) * pow(a, k, n) * pow(b, e - k, n) % n for k in range(e + 1)]  # (a*x+b)^e
    f2[0] = (f2[0] - c2) % n
    while f2: f1, f2 = f2, prem(f1, f2, n)
    assert len(f1) == 2, "gcd is not linear: relation wrong or e too big"
    return -f1[0] * pow(f1[1], -1, n) % n
```
Sage equivalent (Sage has no built-in GCD over `Zmod(n)`, so run Euclid by hand):
```python
def franklin_reiter_sage(c1, c2, e, n, a=1, b=0):
    R.<x> = PolynomialRing(Zmod(n))
    f, g = x^e - c1, (a*x + b)^e - c2
    while g: f, g = g, f % g
    return int(-f.monic()[0])
```
Decode with `long_to_bytes(m)`; if it is not printable, the integer itself may be the answer.

## Gotchas

- Euclid on degree-`e` polynomials is `O(e^2)`: `e = 3..257` is instant in pure Python, `e = 65537`
  needs Sage (minutes) or a half-GCD implementation.
- The relation must be exact, including direction (`m2 = m1 + d` vs `m1 = m2 + d`) and any padding
  shift (`m2 = m1 + d * 2^k` when the counter sits in high bytes). A non-linear GCD means a wrong relation.
- NOT this pattern: unknown but small difference between paddings is Coppersmith short-pad
  (resultant + small root); different moduli with the same `m` is Hastad; same `n` with different `e` and
  the same `m` is common modulus (see `rsa-common-attacks`).
- If the shortcut discriminant is not a perfect square, the difference wrapped; do not fiddle, go to GCD.

## Cross-reference

- `rsa-common-attacks`: decision tree for the other parameter-driven RSA attacks.
- `rsa-small-n-factorization`: if `n` factors, none of this is needed.
- `Manuals/RsaCtfTool/3. Contexto para Claude.md`: its `common_modulus_related_message` attack is the
  same-message / different-`e` case, not a known-offset relation; solve Franklin-Reiter by hand.
