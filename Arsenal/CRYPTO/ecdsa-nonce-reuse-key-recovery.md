---
id: ecdsa-nonce-reuse-key-recovery
category: CRYPTO
tags: [ecdsa, dsa, nonce, nonce-reuse, repeated-nonce, k-reuse, same-r, private-key-recovery, secp256k1, p256, signature, lattice, biased-nonce, psychic-signatures]
tools: []
manuals: []
title: "ECDSA/DSA nonce reuse: recover the private key from two signatures sharing r"
difficulty: medium
created: 2026-11-23
updated: 2026-11-23
related: [rsa-common-attacks, predictable-seeded-prng-replay, mt19937-state-recovery-untemper]
---

## How to recognize this pattern

- You're given **two or more ECDSA (or DSA) signatures** of **different messages** where the **`r`
  component is identical** across them. `r` is derived only from the nonce `k` (`r = (k·G).x`), so
  equal `r` ⇒ the **same `k` was reused**.
- Signature data as `{r, s1, s2, msg1, msg2}` or a `signatures.json`. Curve is usually `secp256k1`
  (Bitcoin/Ethereum) or `P-256` (NIST). The prompt hints "unique", "signature", "nonce", "reused dice".
- Variant: a single signer with a **biased / low-entropy `k`** (top bits zero, time-seeded) — then use
  a lattice (LLL) instead; but exact `r` collision is the textbook, no-lattice case.

## The algebra

For messages with hashes `z1, z2` (as integers mod the curve order `n`):
```
s1 = k⁻¹ (z1 + r·d)      s2 = k⁻¹ (z2 + r·d)   (mod n)
⇒ k = (z1 − z2) / (s1 − s2)              (mod n)
⇒ d = (s1·k − z1) / r                    (mod n)
```
`d` is the private key. `n` is the curve's **group order** (not the field prime `p`).

## Method

### 1. Pin the curve order and the hash reduction
```python
import hashlib
# secp256k1 order:
n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
# P-256 order:  0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
inv = lambda a: pow(a % n, -1, n)
# z = leftmost bit_len(n) bits of H(msg); for sha256 + 256-bit n, just the full digest mod n:
h = lambda m: int.from_bytes(hashlib.sha256(m).digest(), "big") % n
```

### 2. Recover k, then d
```python
r, s1, s2 = R, S1, S2
z1, z2 = h(MSG1), h(MSG2)
k = (z1 - z2) * inv(s1 - s2) % n
d = (s1 * k - z1) * inv(r) % n
print("priv:", hex(d))
```
Verify: re-sign `MSG1` with recovered `d` and `k`, confirm you get `(r, s1)`.

### 3. Use the key
The private key is usually the final goal, or it keys the flag. Common endings:
- **AES key = SHA-256 of `d`** (as decimal string or 32-byte big-endian):
  ```python
  from Crypto.Cipher import AES
  key = hashlib.sha256(str(d).encode()).digest()
  pt = AES.new(key, AES.MODE_ECB).decrypt(open("vault.bin","rb").read())
  print(pt[:-pt[-1]])
  ```
- **Bitcoin/Ethereum**: derive the WIF/address from `d` and sweep, or sign an authorizing message.

## Gotchas

- Use the **order `n`**, never the prime `p`, for every mod inverse and reduction. Mixing them silently
  yields garbage.
- `z` is the hash **reduced mod n** and, for curves where `bit_len(n)` < digest size, **truncated** to
  the leftmost `bit_len(n)` bits first. For sha256 + 256-bit order the truncation is a no-op.
- There are **two** valid `k` sign conventions; if `d` doesn't verify, try `k = (z1 − z2)/(s1 + s2)` or
  negate `s`. Low-`s` normalization (BIP-62) can flip a sign.
- Same `r` across signatures by **different keys** does not help — the reuse must be the **same signer**
  (same `d`).
- Biased-but-not-equal nonces → this closed form fails; switch to an LLL/HNP lattice (e.g. `lattice-attacks`
  from `minerva`/`ecdsa-nonce` toolkits). That's a different, heavier technique.

## Cross-reference

- `predictable-seeded-prng-replay` / `mt19937-state-recovery-untemper`: when `k` comes from a broken
  PRNG you can predict rather than a literal collision.
- `rsa-common-attacks`: sibling "one broken parameter leaks the whole key" crypto decision tree.
