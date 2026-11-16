---
id: aes-ecb-cut-and-paste-block-forge
category: CRYPTO
tags: [aes, ecb, cut-and-paste, block-rearrange, ecb-malleability, no-iv, no-mac, token-forge, payment, status-field, deterministic, block-cipher, 16-byte-block]
tools: []
manuals: []
title: "AES-ECB cut-and-paste: transplant a block to forge a structured token"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [aes-ecb-byte-at-a-time]
---

## How to recognize this pattern

- The app round-trips an **opaque encrypted token** you receive and resend: `?data=<hex>`, a cookie,
  a callback blob encoding a structured record like `{status, order_id, product, price}`. No IV, no
  MAC, length is a clean multiple of 16.
- You can mint tokens for cheap/approved items but the one you want (buy the flag, become admin) comes
  back `declined`. The verdict is **baked into the encrypted blob**; the display endpoint just decrypts
  and shows it.
- Collecting several tokens and diffing them in 16-byte blocks shows some blocks **identical across
  requests** (ECB, deterministic) and one block that changes only when a specific field changes.

## Method

### 1. Detect ECB and map fields to blocks
```python
blocks = [tok[i:i+16] for i in range(0, len(tok), 16)]   # tok = bytes.fromhex(hex)
```
Two tokens for the same item → identical except one random block (that is `order_id`). Compare items
at different prices: if **block 0 is the same** for every *approved* order regardless of product/price
and differs only for the *declined* target, block 0 is a self-contained encryption of the `status`
field. ECB encrypts each block independently, so that block can be transplanted.

### 2. Cut and paste
```
forged = approved.blk0 || target.blk1 || target.blk2 || ... || target.blkN
```
Prefix an "approved" status block onto the declined target's remaining blocks (order_id/product/price/
padding untouched, so PKCS#7 stays valid). No key, no padding oracle needed.
```bash
curl -s "$URL/return?data=$(python3 forge.py <approved_token> <target_token>)"
# -> "approved" + the desired product -> flag
```

## Gotchas

- Identify which field lives in which block by **diffing real tokens**, not by guessing the record
  layout; the status/role field must sit in its own block for a one-block swap to work.
- `blk_a == blk_a` across requests (except a random slot) ⇒ **ECB**, not CBC — that determinism is the
  whole vulnerability.
- Keep the **last block** (valid padding) from the target; only swap the field block.
- If the field you need shares a block with other data, you cannot transplant cleanly — fall back to a
  chosen-plaintext alignment (pad inputs so the field starts on a block boundary).
- Fix for defenders: authenticated encryption (AES-GCM) or encrypt-then-MAC, binding status to
  order/product so blocks can't be reused.

## Cross-reference

- `aes-ecb-byte-at-a-time`: the other ECB primitive — decrypt a secret via a chosen-prefix oracle.
