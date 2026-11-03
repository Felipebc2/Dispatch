---
id: rsa-small-n-factorization
category: CRYPTO
tags: [rsa, factorization, fermat, pollard-rho, factordb, small-n]
tools: []
manuals: []
title: "RSA — small or factorable N (Fermat / Pollard rho / factordb)"
difficulty: easy
created: 2026-09-03
updated: 2026-09-03
related: []
---

## How to recognize this pattern

- The challenge provides `n`, `e`, `c` (ciphertext) for RSA and `n` has few digits (< ~256 bits) or
  looks "too small" for real RSA.
- The prompt mentions a "weak key", "generated quickly", or hints that `p` and `q` are close to each
  other (the Fermat case) or small enough that factordb already has them on record.

## Method

1. Try a direct lookup: paste `n` into https://factordb.com — if it's already factored, done, skip
   to step 4.
2. If `p` and `q` are suspected to be close (Fermat): local Fermat factorization.
3. Otherwise, Pollard rho (via `sympy.factorint`, which already covers both cases automatically).
4. With `p`, `q` in hand: compute `phi = (p-1)*(q-1)`, `d = pow(e, -1, phi)`, `m = pow(c, d, n)`,
   convert `m` from int to bytes.

```python
from sympy import factorint
from Crypto.Util.number import long_to_bytes

n = ...  # from the challenge
e = 65537
c = ...

factors = factorint(n)
p, q = list(factors.keys())[:2]
phi = (p - 1) * (q - 1)
d = pow(e, -1, phi)
m = pow(c, d, n)
print(long_to_bytes(m))
```

## Gotchas

- `sympy.factorint` can hang on a large, genuinely non-weak `n` — if it takes more than ~30s, this
  probably isn't the vector (n isn't actually weak), reconsider the hypothesis.
- Confirm the challenge's `e` — it isn't always 65537.
- If `long_to_bytes(m)` doesn't come out readable, check whether the expected padding is PKCS#1 or
  whether the message needs additional decoding.

## Related

- If the problem is a small `e` (`e=3`) with multiple encryptions of the same text, rather than a
  small N → Håstad's attack (not yet documented in this Arsenal — create a new entry when it comes
  up).
