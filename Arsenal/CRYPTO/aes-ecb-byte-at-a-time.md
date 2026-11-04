---
id: aes-ecb-byte-at-a-time
category: CRYPTO
tags: [aes, ecb, ecb-penguin, byte-at-a-time, oracle, block-cipher, repeated-blocks, cut-and-paste, ecb-detection]
tools: []
manuals: []
title: "AES-ECB: detection + byte-at-a-time decrypt via oracle"
difficulty: medium
created: 2026-10-04
updated: 2026-10-04
related: []
---

## How to recognize this pattern

- A service/endpoint that **encrypts your input concatenated with a secret** (e.g. `encrypt(input +
  FLAG)`) and returns the ciphertext, and you can call it repeatedly.
- Ciphertext with **two identical 16-byte blocks** when you send repeated input (e.g. 32 bytes of
  'A' → two identical blocks). ECB leaks block equality → that's the signature.
- Classic "ECB penguin": an image encrypted under ECB still shows its outline.

## Method

### 1. Detect ECB
```python
def is_ecb(ct, bs=16):
    blocks = [ct[i:i+bs] for i in range(0, len(ct), bs)]
    return len(blocks) != len(set(blocks))     # any repeated block?
```
Send `b"A"*32` and check whether the first two 16-byte blocks come out identical.

### 2. Byte-at-a-time (oracle `encrypt(input + SECRET)`)
Align the secret on a block boundary and force one unknown byte at a time:
```python
bs = 16
def oracle(data: bytes) -> bytes: ...          # calls the service, returns ct

known = b""
for i in range(len(oracle(b"")) ):             # until the secret runs out
    pad = b"A" * (bs - 1 - (len(known) % bs))
    block_idx = len(known) // bs
    target = oracle(pad)[block_idx*bs:(block_idx+1)*bs]
    for b in range(256):
        guess = oracle(pad + known + bytes([b]))[block_idx*bs:(block_idx+1)*bs]
        if guess == target:
            known += bytes([b]); break
    else:
        break                                   # padding changed → end of secret
print(known)
```

## Gotchas

- **Confirm the block size** first: grow the input one byte at a time and watch when the ciphertext
  "jumps" by 16 bytes. That gives you `bs` (16 = AES).
- Byte-at-a-time **only** works if the secret comes **after** your input in the same buffer. If it
  comes before (`encrypt(SECRET + input)`), it's a different variant (prefix): align it with extra
  padding.
- If there's a fixed-size random prefix before your input, figure out its length (how many 'A' bytes
  until the first pair of repeated blocks shows up) and shift the indices accordingly.
- CBC does **not** produce repeated blocks → `is_ecb` returns false; in that case the vector is
  something else (padding oracle, bit flip), not this one.

## Cross-reference

- If it's CBC with a visible padding error → padding oracle (write your own entry when it comes up).
