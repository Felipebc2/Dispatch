---
id: mtls-client-cert-exchange-chain
category: WEB
tags: [mtls, client-certificate, tls, two-way-ssl, cert-chain, xor, known-plaintext, pem, tokenizer, gpt2, t5, llm-token-ids, curl-cert]
tools: []
manuals: []
title: "mTLS — client-cert exchange chain (+ XOR known-plaintext on the next package)"
difficulty: medium
created: 2026-10-07
updated: 2026-10-07
related: [xor-repeating-key]
---

## How to recognize this pattern

- The prompt talks about a **client certificate**, mTLS, "two-way SSL", "self-signed; expect a cert
  warning", or an HTTPS service on a high port (e.g. `:1337`) separate from the normal site.
- The service answers requests with no cert with something like `403 "no means of authentication"`, and
  with an **invalid** cert it drops the handshake (`TLS alert, unknown CA (560)`) → the server
  **validates** the client cert against an internal CA. So you need a cert signed by that CA (the
  "package").
- An "exchange/trade" theme: presenting a valid cert returns the **next** cert, climbing levels
  (`level-1` → `level-2` → flag).

## Method

### 1. TLS recon (confirm mTLS and read the server's chain)

```bash
# server chain/subject/issuer + whether it asks for a client cert
echo | openssl s_client -connect HOST:1337 -servername HOST 2>/dev/null \
  | grep -iE "subject|issuer|Certificate Request|Acceptable client"
# test with a self-signed cert: unknown CA => server validates against its own CA
openssl req -x509 -newkey rsa:2048 -keyout ck.key -out ck.crt -days 2 -nodes -subj "/O=X/CN=x"
curl -skv --cert ck.crt --key ck.key https://HOST:1337/ 2>&1 | grep -i "alert\|unknown ca\|403"
```

### 2. Recover the first package (initial client cert)

The path to the first cert usually comes from another step (a puzzle, a leak, a directory). Download the
`.pem` — it usually carries **cert + private key** together; use the same file for both curl fields:

```bash
curl -sk https://HOST:1337/<path>/firstexchange.pem -o pkg1.pem
openssl x509 -in pkg1.pem -noout -subject -issuer -ext extendedKeyUsage   # TLS Web Client Auth
curl -sk --cert pkg1.pem --key pkg1.pem https://HOST:1337/exchange         # authenticates
```

### 3. Next cert XOR-masked → known-plaintext

An authenticated `POST /exchange` returns the next credential in base64, "masked with XOR". Don't guess
the key: the plaintext is a **PEM with a known prefix** → the repeating key falls out instantly.

```python
import base64
kp=b"-----BEGIN CERTIFICATE-----\n"          # crib
data=base64.b64decode(blob)
key=bytes(data[i]^kp[i] for i in range(len(kp)))   # repeating key (find the period)
pt =bytes(data[i]^key[i%len(key)] for i in range(len(data)))   # next PEM
```

### 4. Loop until the flag

Re-authenticate with each new cert (`curl --cert pkgN.pem --key pkgN.pem -X POST .../exchange`), decrypt
the next, repeat. The flag shows up when the final level is accepted ("Mutual trust established").

### Recon sub-technique: interleaved LLM token IDs

If the puzzle that hands over the path is a list of numbers ("two models, lost tokenizers, output
intertwined"): they're **token IDs** from two different tokenizers, interleaved by parity. Image hints
like "EVEN" (roulette) and "T5" (nmap `-T5`) tell you the split and the models.

```python
import tiktoken, sentencepiece as spm   # pip in a venv; t5-base's spiece.model from HF
g=tiktoken.get_encoding("gpt2"); sp=spm.SentencePieceProcessor(model_file='spiece.model')
print(g.decode(ids[0::2]))   # even indices = GPT-2
print(sp.decode(ids[1::2]))  # odd = T5
# joining the two outputs word-by-word (even-first) forms the sentence/instruction
```

GPT-2: vocab ~50257, low ids common (15496="Hello"). T5/SentencePiece: id 3 = pad/unk (becomes "").

## Gotchas

- `curl --cert`/`--key` can point to the same PEM if it holds both cert+key.
- `-k` only skips verification of the **server's** cert; the server still validates **your** cert.
- The port matters (site on 443, mTLS service on 1337). A catch-all on 443 returns the landing page for
  any path — don't mistake `200` for "the file exists"; check size/content-type.
- XOR with a fixed key + structured plaintext (PEM/JSON/known header) is always known-plaintext, you
  never need the "hint" about where the key is.

## Related / Cross-reference

- `Arsenal/CRYPTO/xor-repeating-key.md` — crib-drag / known-plaintext of a repeating-key XOR.
