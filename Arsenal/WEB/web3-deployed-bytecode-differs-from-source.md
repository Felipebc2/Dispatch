---
id: web3-deployed-bytecode-differs-from-source
category: WEB
tags: [web3, blockchain, evm, solidity, deception, source-vs-bytecode, decompile, trust-the-chain, read-deployed, getter, cast-call, cast-storage, eth-call-spoof-from, onlyowner-view-bypass, keccak-preimage, crewctf, foundry, cast]
tools: [Web3]
manuals: ["Manuals/Web3/3. Contexto para Claude.md"]
title: "Web3: deployed bytecode ≠ the source you were given; interrogate the live contract (getter/storage) instead of trusting the .sol"
difficulty: easy
related: [web3-commit-secret-msgsender-gated, web3-constructor-typo-exposed-initializer]
created: 2026-10-08
updated: 2026-10-08
---

## How to recognize this pattern

- You're given a `.sol` and a deployed address, and the "obvious" exploit from the source **doesn't
  work** (a `require`/hash that should pass reverts). The challenge name/theme hints at deception
  ("deception", "mirror", "fake", "trust"). → suspect that **the live bytecode ≠ the shown code**.
- The pattern: the source has a getter that "reveals" a value (`password()` returns `"secret"`) and a
  check on it (`keccak(secret) == 0x...`), but the **real constant/return are different** in the
  deployed contract. The source is a decoy.
- General web3-CTF reflex: the **source of truth is the chain**, not the file. Read the deployed
  contract's state/return before trusting the `.sol`.

## Method

Reference case: CrewCTF 2023, deception (`solved = true`). The source says `solve(string)` requires
`keccak(secret) == 0x6546...c41b` and `password()` returns `"secret"`, but `solve("secret")` reverts
`invalid`. The real secret is in the live contract:
```bash
CAST=~/.config/.foundry/bin/cast
# 1) call the getter ON THE DEPLOYED contract (don't trust the source)
$CAST call <TARGET> "password()(string)" --rpc-url $RPC --from <OWNER>   # -> "xyzabc" (≠ source!)
# 2) use the real value
$CAST send <TARGET> "solve(string)" "xyzabc" --rpc-url $RPC --private-key $PK
$CAST call <SETUP> "isSolved()(bool)" --rpc-url $RPC                      # true
```
`password()` is `onlyOwner`, but `cast call --from <OWNER>` **gets through**: `eth_call` is simulated
off-chain and doesn't authenticate who you claim to be (no signature); the `require(msg.sender==owner)`
sees whatever `from` you send. Works to read any view with "access control".

### When there's no getter: read storage / decompile

```bash
$CAST storage <TARGET> 0 --rpc-url $RPC        # slot 0, 1, ... ("private" secrets are public)
$CAST code <TARGET> --rpc-url $RPC | <heimdall/decompile>   # find the real constant/logic
```
Any `private` variable is readable by slot; constants live in the bytecode. See
`Manuals/Web3/3. Contexto para Claude.md` (heimdall/decompile).

## Gotchas

- **`--from` on `cast call` is free and spoofable** → bypasses `onlyOwner`/`require(msg.sender==X)` on
  **views**. It doesn't work for writing (a real tx needs a signature), only for reading.
- Keccak preimage: if the real value is short/ASCII, `cast keccak "<attempt>"` confirms it; here you
  don't even need to crack a hash; the getter hands you the secret on a plate.
- The slot order follows the source's declaration **if** the layout matches; if the bytecode is
  different, confirm by reading several slots (`cast storage <addr> <n>`) and decoding.
- Just because the source is "verified" on an explorer doesn't guarantee it's the one at your instance's
  address; always validate against YOUR instance's chain.

## Transferable lesson

In web3-CTF, **the chain is the source of truth, not the `.sol`**. Before building an exploit from the
source: (1) call the getters on the deployed contract (with `--from` to get past auth'd views), (2) read
the storage of the "privates", (3) decompile if needed. A deception-themed challenge + a theoretical
exploit that reverts = almost always **source ≠ bytecode**. Rule: trust what the contract DOES on-chain,
not what the file SAYS it does.

## Related / Cross-reference

- `Arsenal/WEB/web3-commit-secret-msgsender-gated.md`: another case of reading the bytecode (a planted
  decoy in it) instead of trusting appearances.
- `Arsenal/WEB/web3-constructor-typo-exposed-initializer.md`: another "the source looks safe but…".
- `Manuals/Web3/3. Contexto para Claude.md`: `cast call/storage/code`, heimdall/decompile.
