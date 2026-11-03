---
id: web3-storage-mapping-secret
category: WEB
tags: [web3, evm, solidity, storage, mapping, keccak, slot, eth-call-oracle, commitment, preimage, recover-secret]
tools: []
manuals: []
title: "Web3 — recover a mapping secret (keccak slot) + eth_call as an oracle"
difficulty: medium
created: 2026-10-08
updated: 2026-10-08
related: [web3-setup-issolved-flag-ceremony, web3-access-control-nominate]
---

## How to recognize this pattern

The solve function requires an argument that matches a hash of values stored in a **mapping**
(`require(x == keccak256(v0‖v1))`), where `v0,v1` are read from `storage[keccak(prefix ‖
msg.sender)]` — and the Setup **pre-populates** that mapping for the player. The "secret" sits in
public storage the whole time.

## Method

1. Disassemble the solve function; identify the **mapping slot** = `keccak256(abi.encodePacked(
   prefix, msg.sender))`. The prefix may be obfuscated as `PUSH5 <const> << <shift>` — decode it
   to ASCII (e.g. `0x1d985d5b1d << 0xda` = `"vault"`).
2. Compute the slot and read the values:
   ```python
   h1 = int.from_bytes(keccak(b'vault'+bytes.fromhex(player[2:])),'big')
   v0 = w.eth.get_storage_at(target, h1); v1 = w.eth.get_storage_at(target, h1+1)
   x  = keccak(v0 + v1)      # solve argument
   ```
3. **Confirm the preimage layout with `eth_call` as a revert oracle:** test candidate values of `x`;
   the one that does NOT revert (e.g. `"not the board minutes"`) is the right one. This avoids
   `debug_traceCall` (usually blocked).
4. Send the solve tx. Flag: raw `proof = x.hex()` (see `web3-setup-issolved-flag-ceremony`).

## Gotchas

- An **obfuscated prefix** (shifted PUSH) is ASCII — decode it before computing the slot.
- **Commitment getters** (exposed `storage[0]`) are usually a **decoy** — they don't enter the check.
- `proof` is the RAW value (`x.hex()`), NOT `sha256(x.hex())`.

## Related

- `Arsenal/WEB/web3-setup-issolved-flag-ceremony.md`.
