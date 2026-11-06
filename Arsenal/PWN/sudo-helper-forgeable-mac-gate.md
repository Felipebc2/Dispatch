---
id: sudo-helper-forgeable-mac-gate
category: PWN
tags: [privesc, sudo, hmac, mac, integrity-check, forgery, key-reuse, leaked-key, length-extension, compare-digest, authentication, root]
tools: []
manuals: []
title: "sudo/setuid helper gated by a forgeable HMAC or integrity check"
difficulty: hard
created: 2026-11-06
updated: 2026-11-06
related: [boot2root-methodology-checklist, sudo-nopasswd-writable-input-exec, xor-repeating-key]
---

## How to recognize this pattern

- A root-owned helper you may run (via `sudo NOPASSWD` or setuid) authorizes a privileged action
  only if an integrity check passes: an HMAC, a signature, a keyed hash over a request you supply.
- You control the inputs the check reads (a body file and a MAC file in your home, an argument,
  an environment value), and the key is either weak, hardcoded, or already leaked somewhere else
  on the box or in an earlier stage.

The check looks like authentication but protects nothing, because the verifier and the attacker
share everything needed to produce a valid tag.

## Method

### 1. Read the verifier and locate the key
```bash
sudo -l                       # find the helper
cat /path/to/helper           # how does it compute the expected MAC, and over what?
```
Note the algorithm (`hmac.new(key, body, sha256)`, a raw `sha256(key+body)`, etc.), what counts as
a valid body, and where each input is read from.

### 2. Recover or reuse the key
- Hardcoded in the script or a world-readable config: just read it.
- Reused from the foothold: the same key that decrypted stage-2 creds (see `xor-repeating-key`) is
  a common trap. Try it before anything fancy.
- In a nearby readable file (`/opt/<app>`, docs, `.env`).

### 3. Forge the tag over the body the helper demands
```bash
printf 'RELEASE' > ~/order.txt     # whatever body string the verifier requires
python3 -c 'import hmac,hashlib; b=open("/home/<you>/order.txt","rb").read(); \
open("/home/<you>/order.mac","w").write(hmac.new(b"<key>", b, hashlib.sha256).hexdigest())'
sudo /path/to/helper               # verifier recomputes the same MAC, accepts, acts as root
```

### 4. If the key is unknown but you have a valid (message, MAC) pair
A raw `hash(key || message)` construction (MD5/SHA1/SHA2, not HMAC) is vulnerable to hash length
extension: append data and fix up the MAC without the key.
```bash
hash_extender --data "<known-msg>" --secret <guessed-keylen> --append ";<your-extra>" \
  --signature <known-mac> --format sha256
# sweep the key length; HMAC is NOT extendable, only hash(key||msg) is
```

## Gotchas

- `hmac.compare_digest` only stops timing attacks. It does nothing when you can compute the right
  digest yourself, which is the whole point here.
- Try plain key reuse before length extension. Length extension needs the exact construction
  (`hash(key||msg)`), a known pair, and a short key length; it fails silently against real HMAC.
- The required body is often an exact string (`RELEASE`, `OK`). Match it byte for byte, no trailing
  newline unless the verifier strips it.
- Not this pattern if the key is a real secret the verifier never exposes and you cannot reach it.
  Then the gate may be genuine; look for a different stage-4 misconfig.

## Related / Cross-reference

- `boot2root-methodology-checklist`: this is a stage-4 root step when the sudo rule has a MAC gate.
- `sudo-nopasswd-writable-input-exec`: the sibling shape, a wrapper that runs your input directly.
- `xor-repeating-key`: the foothold cipher whose key is often reused in the root gate.
