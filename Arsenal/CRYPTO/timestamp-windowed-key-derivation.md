---
id: timestamp-windowed-key-derivation
category: CRYPTO
tags: [timestamp, derived-key, aes-cbc, clock-skew, windowed-brute-force, md5]
tools: []
manuals: []
title: "Key derived from a discretized timestamp — window brute force"
difficulty: medium
created: 2026-09-03
updated: 2026-09-03
related: []
---

## How to recognize this pattern

- The application encrypts/signs data using a key derived from a **timestamp discretized into
  blocks** (e.g. `block = timestamp_ms // WINDOW_MS`) instead of a fixed secret — usually visible
  because the payload/request includes a `timestamp` field (or similar) alongside the encrypted
  data.
- Strong signal: decrypting with the timestamp YOU observed at request time fails silently (padding
  error, unreadable text) — this indicates your client's clock diverges from the server's clock by
  more than one window's width.
- Common in challenges that try to "expire" tokens/payloads over time but use weak derivation
  (`md5`/`sha1` of a simple string) instead of a real HMAC/KDF.

## Method

The core idea: **you don't need to hit the server's exact timestamp** — you just test a window of
blocks around the local timestamp until one decrypts successfully (valid padding / plausible text).

1. **Identify the derivation scheme.** Observe/infer: which field is the timestamp, the size of the
   discretization window (`WINDOW_MS`), and the key derivation formula (in this real example:
   `key = md5(str(timestamp_block) + fixed_salt).digest()`, a 16-byte MD5 used directly as the
   AES-128 key).

2. **Reproduce the encryption/request** with the local timestamp, to confirm the payload format
   (AES mode, IV size, base64 encoding, etc.):
   ```python
   import time, json, base64
   from hashlib import md5
   from Crypto.Cipher import AES
   from Crypto.Util.Padding import pad
   from Crypto.Random import get_random_bytes

   WINDOW_MS = 5000  # adjust to the current challenge

   def tb_now():
       return int(time.time() * 1000) // WINDOW_MS

   def derive_key(tb, salt="<observed_or_inferred_salt>"):
       return md5((str(tb) + salt).encode()).digest()

   def encrypt(key, plaintext_bytes):
       iv = get_random_bytes(16)
       cipher = AES.new(key, AES.MODE_CBC, iv)
       ct = cipher.encrypt(pad(plaintext_bytes, AES.block_size))
       return base64.b64encode(ct).decode(), base64.b64encode(iv).decode()
   ```

3. **If decryption with `tb_now()` fails, sweep a window of neighboring blocks** (±N blocks) until
   the unpad works (or the text decodes plausibly as UTF-8):
   ```python
   from Crypto.Util.Padding import unpad

   def try_decrypt(data_b64, iv_b64, tb_candidate, salt="<salt>"):
       key = derive_key(tb_candidate, salt)
       ct = base64.b64decode(data_b64)
       iv = base64.b64decode(iv_b64)
       pt = AES.new(key, AES.MODE_CBC, iv).decrypt(ct)
       try:
           return unpad(pt, AES.block_size).decode("utf-8")
       except ValueError:
           return None  # padding failed = wrong block, try the next one

   def brute_window(data_b64, iv_b64, center_tb, span=20, salt="<salt>"):
       for delta in range(-span, span + 1):
           result = try_decrypt(data_b64, iv_b64, center_tb + delta, salt)
           if result is not None:
               return center_tb + delta, result
       return None, None
   ```

4. **Once you've found the right block (the server's real `tb`)**, you have the key, derivable at
   any nearby moment — use it to **forge** payloads (e.g. a session cookie/token with elevated
   claims), encrypting with the same formula and sending it to the server inside the validity window.

5. If the exact `salt`/formula isn't known up front, first **enumerate valid actions** against the
   endpoint (test requests with "obvious" actions like `get_profile`, `list_x`, `admin_get_flag`) to
   discover, from the response, whether the derivation is right before investing in the window brute
   force.

## Gotchas

- Too small a `span` makes the brute force fail even with the right formula — if the local clock is
  very wrong, widen the window before suspecting the derivation formula.
- Confirm the **exact key size** the algorithm expects (AES-128 = 16 bytes = MD5 directly; AES-256
  would need another hash or concatenation) — using the wrong hash produces a key-size error, not a
  padding failure.
- A padding error isn't 100% reliable as "wrong block" — in ~1/256 cases a wrong block still produces
  valid padding by chance. Also validate that the decrypted text makes sense (parseable JSON,
  contains the expected fields) before accepting it as correct.
- This pattern assumes CBC without authentication (no HMAC/GCM) — if the challenge uses AEAD, the
  payload-forging attack doesn't apply the same way (but the window brute-force technique for finding
  the right timestamp still works for decryption).

## Related / Cross-reference

Cross-references `Arsenal/WEB/` when the final target is forging a web-app session/cookie — the
derivation attack is cryptographic, but the goal is usually an authentication bypass.
