---
id: mt19937-state-recovery-untemper
category: CRYPTO
tags: [prng, mersenne-twister, mt19937, untemper, state-recovery, clone-rng, 624-outputs, python-random, getrandbits, predict, xor-keystream, tempering]
tools: []
manuals: []
title: "MT19937 state recovery: clone the RNG from 624 outputs and predict the next draws"
difficulty: medium
created: 2026-11-23
updated: 2026-11-23
related: [predictable-seeded-prng-replay, lcg-truncated-output-state-recovery, ecdsa-nonce-reuse-key-recovery]
---

## How to recognize this pattern

- You can collect a run of outputs from Python's `random`, PHP's `mt_rand`, or any **MT19937** Mersenne
  Twister: session tokens, "random" IDs, a keystream. The values are **32-bit** (or built from 32-bit
  draws), consecutive, and **unseeded by you** (you can't just replay a known seed).
- You have (or can gather) **624 consecutive 32-bit outputs** — exactly the size of the internal state.
  The prompt hints: "624 tokens", "session jetons", "predict the next", "clone".
- Difference from seed-replay: here the seed is unknown/strong, so you **reconstruct the state** from
  outputs instead of reproducing a weak seed. If the seed is a timestamp, use `predictable-seeded-prng-replay`
  instead — it's cheaper.

## Why 624

MT19937 keeps 624 32-bit words of state. Each output is one state word passed through an invertible
**tempering** function (shifts + ANDs). Invert tempering on 624 consecutive outputs ⇒ you recover the
full state ⇒ you can seed a local generator identically and produce every subsequent draw.

## Method

### 1. Untemper and rebuild the generator (Python)
```python
import random, struct

def untemper(y):
    y ^= y >> 18
    y ^= (y << 15) & 0xEFC60000
    for _ in range(7):                       # invert the 7-bit left shift step by step
        y ^= (y << 7) & 0x9D2C5680
    y ^= (y >> 11) ^ (y >> 22)
    return y & 0xFFFFFFFF

leak = [int(x) for x in open("tokens.txt").read().split()]   # >= 624 consecutive 32-bit outputs
state = tuple(untemper(v) for v in leak[:624])
rng = random.Random()
rng.setstate((3, state + (624,), None))      # (version, 625-tuple, gauss_next); index 624 = "spent"
```
Now `rng.getrandbits(32)` reproduces the 625th, 626th… outputs the server will emit.

### 2. Use the predicted stream
Typical endings:
- **XOR keystream**: the next draws were the key for `secret.bin`:
  ```python
  c = open("secret.bin","rb").read(); key = b""
  while len(key) < len(c): key += struct.pack(">I", rng.getrandbits(32))
  print(bytes(a ^ b for a, b in zip(c, key)))
  ```
- **Predict next token** to forge a session / win a bet: just call `rng.getrandbits(32)` the right
  number of times to skip to the target draw.

### 3. Partial / shuffled outputs
- If outputs are **truncated** (only some bits per draw) you need a symbolic/Z3 or GF(2) linear solve
  over the state bits (`cracker` tools like `mersenne-twister-predictor` handle the full-word case;
  `kmyk/mersenne-twister` for exotic ones).
- If you have the 624 but not the alignment, slide a 624-window until the predicted next value matches
  a held-out output.

## Gotchas

- Need **624 full 32-bit words**, consecutive, from the **same** generator instance (no reseed between).
  `random.random()` yields 53-bit floats = **two** 32-bit draws each; account for that when counting.
- `setstate` index must be `624` (all words consumed) so the next `getrandbits` triggers a twist and
  continues correctly. Using `0` desynchronizes you by one full block.
- `getrandbits(k)` for `k<32` or `k>32` consumes words differently; match the server's exact call to
  stay aligned. `randbelow`/`randint` add rejection sampling — mirror the same API, not raw words.
- PHP's `mt_rand` tempers slightly differently and (pre-7.1) had a seeding bug; use a PHP-aware
  untemper for those.

## Cross-reference

- `predictable-seeded-prng-replay`: weak/timestamp seed — replay directly, no 624 outputs needed.
- `lcg-truncated-output-state-recovery`: the LCG analogue (lattice/brute the hidden bits).
- `ecdsa-nonce-reuse-key-recovery`: when a predicted MT draw was used as the ECDSA nonce `k`.
