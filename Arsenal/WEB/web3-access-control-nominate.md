---
id: web3-access-control-nominate
category: WEB
tags: [web3, evm, solidity, access-control, ownable, ownable2step, nominate, missing-modifier, privilege-escalation, storage-layout]
tools: []
manuals: []
title: "Web3: missing access control (nominate / 2-step owner) + storage reads"
difficulty: medium
created: 2026-10-08
updated: 2026-10-08
related: [web3-setup-issolved-flag-ceremony, web3-storage-mapping-secret]
---

## How to recognize this pattern

A contract with stepwise owner/privilege transfer (Ownable2Step-like): `nominate`/
`acceptOwnership`/`acceptExecutive`, etc. The classic hole: **one of the functions is missing its
modifier** (e.g. `nominate(address)` without `onlyOwner`), letting anyone nominate themselves.

## Method

1. With no source, grab the bytecode (`eth_getCode`), extract selectors (scan the dispatcher for
   `PUSH4`) and match them to names via `keccak(text=sig)[:4]`, brute-forcing a list
   (`nominate(address)`, `acceptOwnership()`, `acceptExecutive(uint256)`, `execute()`, etc).
2. Disassemble the key functions and map the storage (slots: owner, pending, nonce, flags). Find
   which SSTORE sets the flag that `isSolved()` reads (e.g. `STATICCALL wallet.0xXXXX()` →
   `slot & 0xff`).
3. Build the escalation sequence. Example:
   ```
   nominate(player)          # b332180b, NO onlyOwner -> pendingExecutive=player, nonce++
   acceptExecutive(nonce)    # 9f773348, msg.sender==pending && nonce==arg -> owner=player
   execute()                 # ac2f2c9b, onlyOwner -> sets solved=1
   ```
4. Flag: `proof` is usually the player's address (the new owner); see
   `web3-setup-issolved-flag-ceremony`.

## Gotchas

- **Decoys:** `setOwner`/`transferOwnership` that **revert with "disabled"**: they lure you toward
  the "obvious" owner change. The real escalation is in the function with no modifier.
- Read the nonce AFTER `nominate` (it increments) before calling `accept`.
- Decode the revert strings (shifted `PUSH<n>`) to understand each require ("not owner",
  "not nominee", "stale nonce", "already executed").

## Related

- `Arsenal/WEB/web3-setup-issolved-flag-ceremony.md`.
