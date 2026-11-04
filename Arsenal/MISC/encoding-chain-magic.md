---
id: encoding-chain-magic
category: MISC
tags: [encoding, cadeia, multi-camada, base64, base32, base58, base85, hex, cyberchef, magic, morse, esoteric, decode]
tools: [CyberChef]
manuals: ["Manuals/CyberChef/3. Contexto para Claude.md"]
title: "MISC: multi-layer encoding chain (CyberChef Magic)"
difficulty: easy
created: 2026-10-04
updated: 2026-10-04
related: [base64-polyglot-expression]
---

## How to recognize this pattern

- An "almost text" string that decodes into another encoded blob, which decodes into another... These
  are stacked layers (base64 → hex → base32 → rot13...). A MISC/warmup classic.
- The alphabet gives away the encoding: only `A-Za-z0-9+/=` (base64), `A-Z2-7=` (base32), `0-9a-f` (hex),
  `.-/ ` (Morse), punctuation-only (Brainfuck/esoteric).

## Method

### 1. Let CyberChef guess
- The **Magic** operation (with "Intensive mode" + a crib set to the flag prefix) detects and unrolls
  several layers on its own. It's the first shot. See `Manuals/CyberChef/3. Contexto para Claude.md`.

### 2. By hand / CLI when you want control
```bash
echo "<blob>" | base64 -d | xxd | head          # see what comes in the next layer
echo "<blob>" | base64 -d | base32 -d
python3 -c "import base64;print(base64.b85decode(open('f').read()))"
```
```python
# identify and unroll programmatically
import base64, binascii
s = "..."
for dec in (base64.b64decode, base64.b32decode, bytes.fromhex, base64.b85decode):
    try: print(dec.__name__, dec(s)[:60])
    except Exception: pass
```

### 3. Clues for less obvious encodings
- `.- / .-.` → Morse. `+++...` / `><][` → Brainfuck (run it in an interpreter).
- Large separated numbers → decimal/charcode (`chr`). Base58 (no `0OIl`) → addresses/crypto.
- `=` at the end and length a multiple of 4 → base64/32.

## Gotchas

- **Stop at readable text**: the last layer is the flag; don't "keep decoding" text that already makes
  sense (it turns to garbage).
- Magic misfires on custom layers/swapped alphabets. In that case identify by the alphabet and decode by
  hand.
- Stray spaces/newlines break the decode. `tr -d ' \n'` first.
- If the chain includes compression (gzip/zlib) in the middle, `xxd` shows the magic (`1f 8b`).
  Decompress and continue.

## Cross-reference

- `Manuals/CyberChef/3. Contexto para Claude.md`: Magic, From Base64/32/85, From Hex, From Charcode.
- `base64-polyglot-expression` (CRYPTO): when the base64 is part of a scheme, not just a layer.
