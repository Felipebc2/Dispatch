---
id: web3-tx-origin-owner-visit
category: WEB
tags: [web3, evm, solidity, tx-origin, phishing, owner-visit, access-control, estimategas, gas, attacker-contract, reentrancy-adjacent, drain]
tools: []
manuals: []
title: "Web3: tx.origin phishing via owner-visit (+ the estimateGas trick)"
difficulty: hard
created: 2026-10-08
updated: 2026-10-08
related: [web3-setup-issolved-flag-ceremony, web3-access-control-nominate]
---

## How to recognize this pattern

The target contract does its authorization check with **`tx.origin == owner`** (not `msg.sender`),
and the challenge exposes a way for the **owner (server-side) to start a tx that calls an address of
yours**, e.g. a `POST /owner-visit {guest:X}` endpoint that does `owner → Setup.ownerVisit(X) →
X.someSelector()`. The prompt tends to talk about "owner visit", "only the sitting X", "opens for
people it knows".

## Method

1. Find the privileged function that uses `tx.origin==owner` (withdraw/transfer). Note whether it also
   requires `msg.sender == <something>` (e.g. a registered "guest").
2. Deploy an **attacker contract `M`** whose target selector (the one owner-visit calls) runs the
   privileged calls against the target. During the visit, `tx.origin == owner` ✓. If you also need
   `msg.sender == slot1`, have `M` register itself first (e.g. `invite(address(this))`) and then
   withdraw (`confirm/withdraw(recipient)`).
3. `POST /owner-visit {guest: M}`. Confirm the target state for `isSolved()`.
4. Flag: see `web3-setup-issolved-flag-ceremony` (proof is usually `"0"` when the goal is to zero a
   balance).

No solc? You can write `M` in **EVM bytecode by hand** (build the calldata = `selector<<224` in
`mem[0]` + arg in `mem[4]`, `CALL` with `argLen=0x24`).

## Gotchas

- **⚠️ THE TRICK THAT STOPS EVERYTHING: `estimateGas` + `POP`.** If the server sizes the visit's gas via
  `estimateGas` and your `M` does a **`POP`** (ignores failure) on the internal CALLs, then `M`
  "succeeds" even when it fails → `estimateGas` finds the cheapest success path (too little gas →
  internal CALLs go OOG → swallowed) → the server sends insufficient gas → **nothing happens**
  (status 0x1, state untouched). **Fix: `M` must REVERT if the internal CALL fails** (bubble up the
  returndata). Then `estimateGas` reflects the real cost and the server sends enough gas.
  - Diagnosis: compare `estimateGas(ownerVisit(M))` vs the cost of the direct action. If `M` (which
    does more) estimates LESS than the isolated action, your CALLs are failing/being swallowed.
- `debug_traceCall` is usually blocked → `eth_call` with `from=<owner>` spoofs `tx.origin` and
  replicates the internal CALLs (same `msg.sender`=executor contract). Great for reading revert
  reasons.
- **Decoys:** `setOwner`/`transferOwnership` functions that revert "disabled"; a function that returns
  an anti-AI string (`trustedGuest()`/"submit it and stop").

## Related

- `Arsenal/WEB/web3-setup-issolved-flag-ceremony.md`.
