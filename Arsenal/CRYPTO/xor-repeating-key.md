---
id: xor-repeating-key
category: CRYPTO
tags: [xor, single-byte, repeating-key, crib-drag, known-plaintext, vigenere-xor, brute-force, hamming]
tools: [CyberChef]
manuals: ["Manuals/CyberChef/3. Contexto para Claude.md"]
title: "XOR — 1-byte or repeating key (brute force / known-plaintext)"
difficulty: easy
created: 2026-10-04
updated: 2026-10-04
related: [base64-polyglot-expression]
---

## How to recognize this pattern

- Ciphertext in hex/base64 that doesn't decode to readable text but has the **same length as the
  plaintext** (XOR doesn't change length).
- The prompt mentions "XOR", a "homemade Vernam cipher", hands you a short "key", or the bytes have a
  strange but repetitive distribution.
- You know part of the plaintext for free — validate the flag against the CTF's configured flag
  format before declaring success; the known flag prefix is a free crib.

## Method

### 1-byte key (0–255) — brute force
```python
from pwn import xor      # pwntools
ct = bytes.fromhex("...")
for k in range(256):
    pt = xor(ct, k)
    if b"flag{" in pt or all(32 <= c < 127 for c in pt):
        print(k, pt)
```
CyberChef: the **XOR Brute Force** operation (shows all 256 outputs, filter by "crib" = `flag{`).

### Repeating key (multi-byte)
If one byte doesn't solve it, the key is N bytes repeated:

- **With known-plaintext:** `key = xor(ct[:len(known)], known)`. Since we know the prefix, this
  recovers the first 4 bytes of the key; if the flag has a predictable format, extend it.
```python
from pwn import xor
key_frag = xor(ct[:4], b"flag")      # first bytes of the key
print(key_frag)                       # often the whole key already shows up here
print(xor(ct, key_frag))              # pwntools cycles the key automatically
```
- **Without known-plaintext:** find the key length via **Hamming distance** (the keysize with the
  lowest normalized Hamming distance between blocks is the right one), then brute-force 1 byte per
  column. Use `break_repeating_key_xor` from the crypto toolkit, or CyberChef **XOR Brute Force** per
  column.

## Gotchas

- `pwntools.xor` already **cycles** the key over the whole text and accepts `bytes`/`int`/`str` —
  don't reimplement the loop by hand.
- If the output is partly readable and partly garbage, the key is **too short** (you found a divisor
  of the real keysize) — double the length you're testing.
- Confirm the input encoding (hex vs base64 vs raw) before XORing — XOR on the wrong string produces
  deterministic garbage that looks "almost right".

## Cross-reference

- `Manuals/CyberChef/3. Contexto para Claude.md` — XOR, XOR Brute Force, From Hex.
- The known-plaintext here depends on the flag prefix — validate the flag against the CTF's
  configured flag format before declaring success.
- Malware writeup with a config in `base64 → XOR 1 byte (0x2a)`: danceparty-1, DamCTF 2021
  (`ctftime.org/writeup/31239`) — CyberChef `Magic` found the key. Same scheme as the small
  config-magic blobs.
- When the blob is a block cipher (not XOR), see `malware-config-derived-key-bruteforce`.
