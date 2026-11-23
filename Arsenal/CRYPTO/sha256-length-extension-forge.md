---
id: sha256-length-extension-forge
category: CRYPTO
tags: [hash, length-extension, length-extension-attack, sha256, sha1, md5, merkle-damgard, hashpump, hashpumpy, mac, secret-prefix-mac, keyed-hash, signature-forge, append-data]
tools: []
manuals: []
title: "Hash length extension: forge SHA-256(secret || data || append) without the secret"
difficulty: medium
created: 2026-11-23
updated: 2026-11-23
related: [custom-weak-hash-bruteforce-collision, jwt-alg-none, aes-ecb-byte-at-a-time]
---

## How to recognize this pattern

- A tag/MAC is built as `H(secret || message)` with a **Merkle–Damgård hash** (MD5, SHA-1, SHA-256,
  SHA-512) and `H` applied directly — **not** HMAC. Look for `hashlib.sha256(secret + msg).hexdigest()`.
- You are given: the **message**, its **tag**, and usually the **secret length** (or you can brute it).
  You do **not** know the secret, but you want a valid tag for `message || something`.
- The `something` you want to append is an authorization upgrade: `&role=admin`, `&admin=1`,
  `;grant=all`. The server recomputes `H(secret || message || padding || append)` and compares.
- Strong signal in the prompt/name: "length extension", "rallonge", a cookie/token signed by
  concatenation, a provided `sha256ext.py` helper, or a known `longueur_secret = N`.

## Why it works

A Merkle–Damgård hash's output **is its internal state** after the last block. SHA-256 processes data
in 64-byte blocks, appending a known padding (`0x80`, zero bytes, then the 64-bit bit-length). If you
know the digest of `secret || message`, you can **resume** the hash from that state and keep feeding
bytes — producing the valid digest of `secret || message || glue_padding || append`, all without the
secret. You only need the **total length** of `secret || message` to recompute the glue padding.

## Method

### 1. The easy path: hashpumpy
```bash
pip install hashpumpy
python3 -c "
import hashpumpy
# original tag, known message, data to append, length of the secret (bytes)
new_hash, new_msg = hashpumpy.hashpump('<orig_tag_hex>', 'user=guest', '&role=admin', 16)
print(new_hash)
open('forged.bin','wb').write(new_msg)   # message with glue padding baked in
"
```
`new_msg` contains `user=guest` + raw glue padding (`\x80\x00...<bitlen>`) + `&role=admin`. Send it
**URL-encoded** so the padding bytes survive transport.

### 2. Brute the secret length if unknown
Padding depends only on `len(secret || message)`. Try each length and keep the forgery the server
accepts:
```bash
for L in $(seq 8 40); do
  python3 -c "import hashpumpy,urllib.parse,sys
h,m=hashpumpy.hashpump('$TAG','$MSG','&role=admin',$L)
print($L,h,urllib.parse.quote(m))"
done
```

### 3. Pure-Python resume (no library / provided helper)
When the challenge ships a `sha256ext.py` or forbids installs, resume SHA-256 from the tag by loading
the 8 state words and re-running the compression function:
```python
import struct
# pip-free: patch a SHA-256 impl so H[0..7] = tag words, msg length = (secret+msg+glue) bits
def glue_padding(msg_len):
    pad = b"\x80" + b"\x00" * ((55 - msg_len) % 64)
    return pad + struct.pack(">Q", msg_len * 8)

# forged tag = continue_sha256(state_from_tag, append, prior_blocks=(secret+msg+glue))
```
Most CTF setups give the helper; otherwise `hlextend` (SHA-1/SHA-256/512) or hashpumpy are canonical.

### 4. Common twist: the forged digest is then an AES key
In several challenges the tag isn't the goal — the **forged digest** is used as an AES key for a
provided ciphertext. Forge the digest, then:
```python
from Crypto.Cipher import AES
pt = AES.new(bytes.fromhex(new_hash), AES.MODE_ECB).decrypt(open("cipher.bin","rb").read())
print(pt[:-pt[-1]])   # strip PKCS#7
```

## Gotchas

- **HMAC is immune.** `HMAC(secret, msg)` nests two hashes; length extension does not apply. If you see
  `hmac.new(...)`, this attack is the wrong tool.
- Secret **suffix** MACs — `H(message || secret)` — are **not** extendable this way (you'd need to
  append before the secret). Length extension needs the secret as a **prefix**.
- Get the length right: it's `len(secret) + len(message)`, both in bytes, before padding.
- Byte order: the appended length field is **big-endian 64-bit** for SHA-256/SHA-1, **little-endian**
  for MD5. hashpumpy handles this; a hand-rolled impl must match the algorithm.
- Send the forged message as raw bytes (URL-encode, or multipart) — the glue padding contains
  non-printable bytes that a naive string copy will mangle.

## Cross-reference

- `custom-weak-hash-bruteforce-collision`: when the MAC is a *homemade* hash, forge a collision
  instead of extending a standard one.
- `jwt-alg-none` / `jwt-rs256-hs256-key-confusion`: sibling signature-forgery patterns on tokens.
- `aes-ecb-byte-at-a-time`: the forged-digest-as-AES-key twist decrypts an ECB blob the same way.
