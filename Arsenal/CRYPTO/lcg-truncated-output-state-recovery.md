---
id: lcg-truncated-output-state-recovery
category: CRYPTO
tags: [lcg, linear-congruential-generator, truncated-lcg, truncated-output, top-bits, high-bits, state-recovery, prng, rng-prediction, predict-next, lattice, lll, babai, cvp, brute-force-low-bits, numerical-recipes, sage]
tools: []
manuals: []
title: "LCG with truncated output: recover the state (brute force hidden bits or lattice/LLL)"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [timestamp-windowed-key-derivation, custom-weak-hash-bruteforce-collision]
---

## How to recognize this pattern

- A generator `s_{i+1} = (a*s_i + c) mod m` with known `a`, `c`, `m` (common constants:
  `1664525 / 1013904223 / 2^32` Numerical Recipes, `1103515245 / 12345 / 2^31` glibc-style,
  `6364136223846793005 / 1442695040888963407 / 2^64` Knuth MMIX) and outputs like `s >> k` or `s // 2^k`.
- Task: give the initial/current state, or predict the next output(s).
- A "if the reading is the whole state, the next is X" line is a decoy: outputs are only the top bits.

## Method

**1. Small hidden part (up to about 2^28 to 2^32 candidates): brute force.** The first output fixes the
top bits; enumerate the low ones and filter with the following outputs (each output removes about
`2^visible_bits` candidates).
```python
a, c, m, k = 1664525, 1013904223, 2**32, 20      # k = hidden low bits (output = s >> k)
ys = [...]                                        # observed outputs, in order
step = lambda s: (a * s + c) % m
for low in range(1 << k):
    s0 = s = (ys[0] << k) | low
    for y in ys[1:]:
        s = step(s)
        if s >> k != y: break
    else:
        print("s0 =", s0, "next output =", step(s) >> k)
```
Slow in Python past ~2^26; port the loop to C or numpy, or go to the lattice.

**2. Large state (e.g. 64-bit, top 32 visible): lattice + Babai (Sage).** With `b_i` the additive
part (`b_0 = 0`, `b_{i+1} = a*b_i + c`), the vector `(s_i - b_i)` lies in the lattice
`{v : v_i = a^i * v_0 mod m}` and sits within `2^k` of the known `(y_i << k) - b_i`:
```python
def truncated_lcg(ys, a, c, m, k):
    n = len(ys)
    b = [0]
    for _ in range(n - 1): b.append((a * b[-1] + c) % m)
    B = matrix(ZZ, n, n)
    B[0] = [pow(a, i, m) for i in range(n)]
    for i in range(1, n): B[i, i] = m
    L = B.LLL()
    w = vector(ZZ, [(y << k) + (1 << (k - 1)) - bi for y, bi in zip(ys, b)])
    u = vector(ZZ, [round(t) for t in L.solve_left(w)]) * L   # Babai rounding
    return int(u[0]) % m                                     # s0
```
Six outputs recover a 64-bit state with 32 hidden bits reliably. Always verify by regenerating
all outputs from `s0`, then step forward to predict.

**Unknown `a`, `c`, `m` but full outputs:** `t_i = x_{i+1} - x_i`, `m = gcd(t_{i+2}*t_i - t_{i+1}^2, ...)`,
then `a = t_1 * inverse(t_0, m)`, `c = x_1 - a*x_0` (all mod `m`).

## Gotchas

- Check the exact output map: `s >> k`, `s % 2^j` (low bits), `s // d`, or `s mod r` change the method.
  Low bits of a power-of-two LCG are weak on their own: bit `j` has period `2^(j+1)`.
- Off-by-one in indexing: is the first output taken from `s0` or from `step(s0)`? Test both.
- Several brute-force survivors means too few outputs; add more before guessing.
- Babai fails with too few outputs or too many hidden bits: add outputs, or use Kannan embedding.
- NOT this pattern: Mersenne Twister (`random` module, 624 x 32-bit outputs, untemper and clone) or
  xorshift (linear over GF(2): solve with z3 or GF(2) linear algebra, not modular lattices).

## Cross-reference

- `timestamp-windowed-key-derivation`: when the seed itself is a guessable time.
- `custom-weak-hash-bruteforce-collision`: same "enumerate the small hidden space" mindset.
