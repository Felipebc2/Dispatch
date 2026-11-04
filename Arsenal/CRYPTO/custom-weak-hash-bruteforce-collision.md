---
id: custom-weak-hash-bruteforce-collision
category: CRYPTO
tags: [hash, hash-collision, custom-hash, homemade-hash, non-cryptographic, weak-hash, brute-force, xor, modular-exponentiation, small-modulus, integrity-bypass, blockchain-fake, vcs, bcactf, git-better, rev]
tools: []
manuals: []
title: "Weak homemade hash: forge a colliding input (same hash, different content) by brute force"
difficulty: easy
created: 2026-10-08
updated: 2026-10-08
related: []
---

> Note: the reference challenge sells itself as a "blockchain" (a proprietary block-based VCS), but
> it's **neither EVM nor real crypto**: the "immutability" rests solely on a **hash function the
> author made up**. Recognizing this early (the "blockchain" is a facade) saves hours. The original
> was tagged `blockchain`/`rev`, but the core is a **hash collision** → CRYPTO.

## How to recognize this pattern

- A system proves "integrity"/"immutability" with a **homemade hash function** (not SHA/Keccak):
  a loop over the bytes with `XOR`, additions, multiplications, `**`, all **modulo a small number**
  (e.g. `% 261557`). Short output (fits in a few bytes) → tiny image space.
- You control an input that gets hashed and compared against a fixed value; you win if you **match
  the hash while changing the content** (corrupting an embedded regex/validator/signature without
  changing the digest).
- Weak-hash red flags: small modulus, no real diffusion, no avalanche, a commutative operation
  (`XOR`), position/index entering in a predictable way. The collision becomes a **brute force of
  seconds**.

## Method

Reference case: **BCACTF 4.0: Git Better**. "Blockchain VCS": the server receives a missing block,
reconstructs the repo with it as the 2nd block, runs it as a Deno script (the flag validator), and
returns the output. The flag only appears if the validator **fails** the regex match, and you can
corrupt the regex because the block is yours. The guard: the block has to keep the **same hash** from
the homemade function:

```python
mod_prime = 261557
power_prime = 1933
def my_hash_function(data):
    current_hash = 0
    for i in range(len(data)):
        byte = ord(data[i])
        current_hash ^= (power_prime ** byte * i) % mod_prime   # XOR, tiny modulus
    return current_hash
```

### Exploit (brute-force the collision)

The block has a short free field (e.g. a 2-byte hex `(xxxx)`). Fix the rest (already with the regex
corrupted) and sweep the field until the hash matches the original:

```python
target = my_hash_function(buf_original)            # hash to match
for i in range(0x10000):                            # just the free field
    cand = buf_template.replace("PLACEHOLDER", f"{i:x}")
    if cand != buf_original and my_hash_function(cand) == target:
        print(cand); break                          # collision: same hash, content changed
```
Submit the collided block → the validator runs with the broken regex → flag
(`bcactf{app4r3ntly_y0u_5h0u1dn7_m4k3_y0ur_0wn_h45h_funct10n5}`; validate the flag against the CTF's
configured flag format before declaring success).

## Gotchas

- **Small output space = collision guaranteed fast.** Modulus `261557` → at most ~2^18 images;
  sweeping 2 bytes (`0x10000`) almost always hits. If you don't find one in the obvious field, widen
  the free field.
- `XOR` is commutative/associative and `^=` cancels pairs, so reordering/repeating bytes can preserve
  the hash without brute force. Analyze the structure before brute-forcing.
- Confirm that the mutation **breaks what you want** (here the regex) AND keeps the hash; these are
  two simultaneous goals, test both.
- "Git Even Better" variant: a large prime modulus makes pure brute force infeasible → it turns into
  an **algebraic/crypto** attack on the hash structure (out of scope for this entry).

## Transferable lesson

A homemade hash = fake integrity. If someone validates "immutability"/a signature with a function
that isn't a real cryptographic hash (small modulus, no avalanche, commutative operations),
**collision is brute force**, not heavy math. First reflex on seeing a custom "blockchain/VCS/
anti-tamper": locate the hash function and check whether it's standard (SHA/Keccak) or invented. If
invented, measure the image size and brute-force the free field. Applies to self-signed tokens,
save-file checksums, "licenses", and any homemade anti-tamper.

## Related / Cross-reference

- `Arsenal/REV/bridge-receipt-local-commitment-forge.md`: same lesson ("if you have the routine that
  recomputes the hash, it doesn't authenticate anything"), but there the hash is recomputed by a
  binary (reversing).
- `Arsenal/CRYPTO/xor-repeating-key.md`: another case of XOR misused as if it were security.
