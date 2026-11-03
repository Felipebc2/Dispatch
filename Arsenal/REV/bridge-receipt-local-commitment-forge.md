---
id: bridge-receipt-local-commitment-forge
category: REV
tags: [blockchain, bridge, relayer, guardian, receipt, commitment, self-consistency, no-mac, no-signature, local-recompute, forge, varint, little-endian, vm-commitment, gdb, ghidra, binary, patch-bytes, anti-slop, finality-cache, not-evm]
tools: [Ghidra]
manuals: ["Manuals/Ghidra/3. Contexto para Claude.md"]
title: "Bridge receipt forge — locally recomputed commitment (self-consistency ≠ authentication) via gdb"
difficulty: medium
created: 2026-10-08
updated: 2026-10-08
related: [toctou-decompression-overflow-validated-structure]
---

> ⚠️ "Blockchain" here is NOT EVM/Solidity. It's a **bridge-protocol** challenge with a **custom
> guardian binary** — the bug is in how the binary validates/consumes bytes, not in an on-chain
> contract. Solve it with reversing (Ghidra) + `gdb`, not with cast/Foundry. Routes to
> `solver-rev`/`solver-pwn`.

## How to recognize this pattern

- A bridge/relayer service that hands you a **local binary** (guardian/verifier) + a **binary blob**
  (receipt/claim) with several fields that must be **consistent with each other**: a value in 2+
  encodings (e.g. varint + little-endian) and a **digest/commitment** over the rest.
- The guardian **recomputes the commitment locally** and compares it against the embedded one.
  There's no MAC key or upstream signature → the commitment is just a **self-consistency check**, not
  authentication.
- Goal: forge a larger value (e.g. claim 20000 → 80000) while keeping the 3 fields consistent.
- Key lesson: **if you have the binary that recomputes it, the commitment authenticates nothing** —
  anyone can run the same routine over mutated data.

## Method

Reference case: **Anti-Slop CTF 2026 — Finality Cache**. Artifacts: `guardian` (stripped),
`sample.receipt`, `BridgeVault.sol` (redeem logic), `patch_receipt.py`. Magic `FCRA`.

### 1. Map the receipt layout (hexdump + README/offset table)

```text
0x20..0x27   committed amount, little-endian uint64   (sample: 204e000000000000 = 20000)
0x3c..0x5b   VM commitment digest (32 bytes)          (sample: ed51...5787)
0x..         lane program(s): each lane has a varint with the amount
```
Confirm the errors the guardian emits (they isolate each field):
- only the header changed → `preview amount mismatch` (the lane/VM doesn't match).
- only the lane changed → `ERR bad vm commitment` (stale digest).

### 2. Patch the lane varint (20000 → 80000)

Varint = 7 data bits per byte, high bit = continuation, LSB-first:
```text
a0 9c 01  -> 20000      |   80 f1 04  -> 80000   (both 3 bytes: overwrite in-place)
```

### 3. Patch the amount in the header (LE)

`0x20`: `80 38 01 00 00 00 00 00` (80000 as uint64 LE).

### 4. Recompute the commitment — let the guardian itself do it (gdb)

The fastest route: the guardian recomputes the digest internally; break at the recomputation point
and dump the resulting 32 bytes.
```bash
gdb ./guardian
(gdb) break *0x401a7a        # address near the recomputation (adjust to the disasm)
(gdb) run --receipt /tmp/patched-receipt.bin
(gdb) x/32xb $rsi            # where the new digest lives (see the disasm)
```
Patch the 32 bytes into `receipt[0x3c:0x5c]` (`patch_receipt.py --digest-hex <hex>` does this).
Reimplementing the routine in Python is possible (a sponge with custom personalization) but costs
hours — gdb takes 5 min.

### 5. Attest → redeem

Submit the repaired receipt to `attest` → the guardian signs → `redeem` the 80000 claim. Flag
`slopped{wrapped_lane_offsets_expose_seal_keys_then_sign_recursive_checkpoints}`.

## Gotchas

- **Triple consistency:** mutating 1 or 2 of the 3 fields always fails with a specific error — use
  the errors to confirm which field is still missing.
- Re-encoding the varint can change its byte length; if it does, it's no longer an in-place overwrite
  (you have to shift). In the 20000/80000 case both came out to 3 bytes.
- The break address (`0x401a7a`) is specific to the binary — find the hash routine in Ghidra
  (`Manuals/Ghidra`), break right after the `store` of the digest.
- This challenge is designed to defeat tool-driven/AI solutions — here the work is manual (reversing +
  gdb). AI helps map it out, not guess it.

## Transferable lesson

`local recompute == self-consistency, NOT authentication`. Whenever a validator proves integrity by
recomputing a hash whose routine lives in the binary/code you have (no MAC key / no upstream
signature), you can mutate the data and re-sign. The golden question: "is the recompute key
accessible to the attacker?". Applies to bridge receipts, "licenses", self-signed tokens, save files.

## Related / Cross-reference

- `Arsenal/PWN/toctou-decompression-overflow-validated-structure.md` — the 2nd from the same track
  (validator-vs-consumer gap).
- `Manuals/Ghidra/3. Contexto para Claude.md` — find the commitment routine and the break address.
