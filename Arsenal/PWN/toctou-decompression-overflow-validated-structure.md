---
id: toctou-decompression-overflow-validated-structure
category: PWN
tags: [blockchain, bridge, toctou, time-of-check-time-of-use, decompression, packbits, rle, decompression-bomb, output-unbounded, overflow, bind-table, validator-consumer-gap, lcg, xor-keystream, wasm, ghidra, cap-mask, anti-slop, canopy-cache, not-evm]
tools: [Ghidra]
manuals: ["Manuals/Ghidra/3. Contexto para Claude.md"]
title: "TOCTOU validator↔consumer: PackBits decompression (unbounded output) rewrites an already-validated structure"
difficulty: hard
created: 2026-10-08
updated: 2026-10-08
related: [bridge-receipt-local-commitment-forge]
---

> ⚠️ "Blockchain" here is NOT EVM/Solidity: it's a bridge service with a **custom binary**
> (`canopyd`) + a WASM-like module. Solve it with reversing (Ghidra) + protocol assembly, not
> cast/Foundry. Routes to `solver-pwn`/`solver-rev`.

## How to recognize this pattern

- A **two-stage** pipeline over the same memory/buffer: one stage **validates** (decoder/witness/
  audit) a property of the bytes, another **consumes** (patcher/redeem) assuming the property still
  holds. The bug is **always the gap between the stages** (TOCTOU).
- **Two validators disagree** about the same field: e.g. the bind decoder rejects `image_off > 0x0f`,
  but the route patcher requires `> 0x17`. Binding directly to the desired value fails validation.
- There's a **write primitive** that runs BETWEEN check and use: a **decompressor with unbounded
  output** (PackBits/RLE validates the compressed input's size but not the output's) that overflows
  and **rewrites the already-validated structure**.
- PackBits/RLE: the worst case expands **128×** (1 literal byte + 1 control byte 0x80 → 128 output
  bytes).

## Method

Reference case: **Anti-Slop CTF 2026: Canopy Cache**. Artifacts: `canopyd`,
`analysis/canopyd.decomp.c` (Ghidra decompile), `lane_helper.wasm`/`patched_helper.wasm`,
`verify_patch.py`. Interface: `upload/inspect/warm/sync/quote/attest/bless/activate/invoke/flag`.

### 1. Diff the two validators (reversing)

```text
bind decoder : rejects image_off > 0x0f
route patcher: requires image_off > 0x17   → going straight to 0x18 is impossible in one bind
```
The gap is the bug: land `0x18` AFTER the validator accepted a bind with a low offset.

### 2. Recover the session's XOR stream (plumbing, not the bug)

`warm`/`quote`/`attest` use an XOR keystream derived from an **LCG** (`s_{i+1}=a·s_i+c mod m`).
`status` leaks sample(s) of the state (`session_hint`); with `(a,c,m)` from the helper, run the LCG
forward/backward to find the seed and generate the stream at any offset. Only then can you build
valid encrypted payloads.

### 3. Stage the route bytes in the warm image (offset 0x18)

```text
02 01 01 01  = [route_kind=2, quote_idx=1, cap_mask=0x01, flags=0x01]
```
`cap_mask=0x01` is critical: it keeps the slot **blessable**. Without it, `bless` refuses and the
chain dies.

### 4. Build the PackBits overflow + a benign bind (TOCTOU)

Order matters (the validator runs on the bind, not on the expand):
```text
1. add 4 RLE fragments to the arena
2. create a VALID bind with a small image_off (e.g. 0x05)  → the decoder accepts, writes to the bind table
3. trigger expand (PackBits) → the output overflows and rewrites the already-validated entry
4. the entry becomes: [route=1, quote=0, image_off=0x18, flags=0]   (the patcher accepts: looser rules)
```
The RLE fragments are "just offset arithmetic": pad until the output lands exactly on the bind
entry's metadata bytes.

### 5. Final command sequence

```text
upload (patched helper) → warm (route bytes @0x18) → sync → quote → attest (witness w/ overflow)
→ bless → activate → invoke audit → flag
```
`bless` checks `cap_mask & 0x01` (ok, from step 3); `audit` follows route=1 to the controlled image.
Flag `slopped{packbits_lookup_routes_rethread_the_owner_lane}`.

## Gotchas

- **Check-before-use order is everything:** the expand HAS to run between the validated bind and the
  route patcher. Validating the bind with the forbidden offset directly fails.
- **Plumbing before the bug:** without the right LCG keystream, no encrypted command works, so solve the
  XOR first, then the PackBits.
- **Alignment:** the overflow has to land exactly on the entry's `image_off` byte; count the arena
  offsets in the decompile (Ghidra) and pad.
- This challenge is anti-tool/anti-AI: the work is manual reversing of `canopyd.decomp.c`. AI maps it,
  it doesn't guess it.

## Transferable lesson

Two patterns in one: (a) **TOCTOU validator↔consumer**: if two consumers read the same buffer at
different times with different rules, look for a primitive that changes the buffer between them; (b) a
**decompressor with unbounded output** (RLE/PackBits/zip bomb) = a write outside the validated buffer.
Same shape as `phar://` auto-deserialize and JWT alg confusion (one parser trusts the header, another
reinterprets it). Defense: a single shared canonicalization OR an immutable post-validation snapshot.

## Related / Cross-reference

- `Arsenal/REV/bridge-receipt-local-commitment-forge.md`: the 1st from the same track
  (self-consistency ≠ auth).
- `Manuals/Ghidra/3. Contexto para Claude.md`: reversing `canopyd`, finding the two validators and
  the arena offsets.
