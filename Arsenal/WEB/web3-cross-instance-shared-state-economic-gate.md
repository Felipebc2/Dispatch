---
id: web3-cross-instance-shared-state-economic-gate
category: WEB
tags: [web3, blockchain, ton, tolk, jetton, cross-instance, instance-isolation, shared-world, launcher, uuid, economic-gate, token-economy, transfer-initiator, donor-target, logic-bug, sekaictf, open-world, instancer]
tools: [TON]
manuals: ["Manuals/TON/3. Contexto para Claude.md"]
title: "Web3 — broken cross-instance isolation + economic-gate bypass (fund the target wallet from another instance)"
difficulty: medium
created: 2026-10-08
updated: 2026-10-08
related: [web3-reentrancy-checks-effects-interactions]
---

> ⚠️ **TON** chain (non-EVM). Toolchain = the TON SDK (`Manuals/TON/3. Contexto para Claude.md`):
> Node `@ton/ton`+`@ton/crypto`+`@ton/core`, **not** Foundry/cast. The pattern (isolation + economy)
> transfers to any multi-instance launcher, EVM included.

## How to recognize this pattern

- A multi-instance launcher (Paradigm/instancer style): each request spins up a new `Challenge`, a
  player wallet, and an API endpoint **scoped by UUID**. Goal: `isSolved()==true` → ask the launcher
  for the flag with the UUID.
- Two clues combined:
  1. An **economic gate** that looks infeasible within a single instance (the available flows don't
     add up to what the solve requires).
  2. **Isolation only in the API, not in on-chain state**: wallets from different instances live in the
     same "world" (same local chain) → one instance can **fund/transfer** to another's wallet.
- The solve handler checks only **who initiated** the transfer (`transferInitiator == player`), not
  **where** the money/value came from.

## Method

Reference case: SekaiCTF — Open World (TON). `Solve` requires 1 transfer of 100 jettons initiated by
the player wallet. Economy (confirmed in `Challenge.tolk`):

- `FLAG_PRICE = 100` jettons · `TOKEN_PRICE = 2 TON`/jetton · `BUY_MINT_TON_AMOUNT = 0.12 TON`.
- `PlayerBonus` (op `0x13370002`) → mints `FLAG_PRICE/2 = 50` jettons, **once** (`remainingPlayerBonus`).
- `Sell` (op `0x13370004`, via forwardPayload) → pays `jettonAmount * 2 TON`.
- `Buy` (op `0x13370003`) → `assert in.valueCoins > amount*2 + 0.12` and mints `amount` jettons.
- `Solve` (op `0x13370005`, via forwardPayload) → only checks `transferInitiator == player` and
  `jettonAmount >= 100`. A jetton transfer = op `0x0f8a7ea5`.

### 1. Read the solve condition, literally

```
Solve: if transferInitiator == storage.player && jettonAmount >= FLAG_PRICE(100) -> isSolved=true
```
It checks the initiator, **not the origin of the funds**. That's the hole.

### 2. Map the gates and prove 1 instance doesn't add up

`PlayerBonus(50) → Sell(→100 TON) → Buy(50)` = net **50 jettons** (the Sell consumes the bonus).
Solve asks for **100 in one transfer** → infeasible in a single instance.

### 3. Exploit the cross-instance (donor/target)

Two instances; the donor monetizes its bonus and funds the missing half on the target:
```
donor:  PlayerBonus → 50 jettons → Sell → ~100 TON
target: PlayerBonus → 50 jettons
donor:  transfer ~99.75 TON → target's wallet      # same TON world, API-scope doesn't isolate state
target: Buy 50 jettons  (costs 100 TON + ~0.12 gas)
target: Solve transfer (100 jettons → target's challenge wallet)
```
The final transfer is initiated by the target's player wallet → it passes `transferInitiator ==
player`. The contract doesn't see where the TON came from.

### 4. Run the solver (TON SDK)

Structure of the reference solver (SekaiCTF repo): `solve.py` (launcher wrapper: TLS + **PoW** + creates
2 instances) → `solve_open_world_full.py` (launcher/PoW helpers) → `solve_open_world_cross.js` (builds
the TON txs, deps `@ton/ton`+`@ton/crypto`+`@ton/core`).

Exact message sequence (from `solve_open_world_cross.js`):
```javascript
ensureJettons(donor, 50)                      // donor PlayerBonus -> 50 jettons
sendFrom(donor, donorJetton, OP_SELL, 50)     // donor sells -> ~100 TON
ensureJettons(target, 50)                     // target PlayerBonus -> 50 jettons
sendFrom(donor, target.wallet, EMPTY, ~99.75) // DONOR funds the TARGET (cross-instance!)
sendFrom(target, target.challenge, OP_BUY, 50)// target buys +50 jettons (costs 100 TON + gas)
sendFrom(target, targetJetton, OP_SOLVE, 100) // target transfers 100 jettons -> Solve
```

```bash
cd blockchain/open-world/exploit && npm install   # @ton/ton, @ton/crypto, @ton/core
python3 solve.py --host open-world-<instance>.instancer.sekai.team --port 1337
```
Launcher: `nc` TLS on port 1337, menu `new`/`flag`/`kill`, solves PoW (sha256(prefix+suffix) with N
zeros) before creating an instance; `flag <uuid>` only returns if `isSolved()` on-chain. Checkpoints:
donor 50 jettons → ~100 TON; target 50 → +~100 TON (funding) → Buy → 100 jettons → `isSolved()` true →
flag `SEKAI{3Xp1or1ng-An-0pen-W0rld-15-FUN}`.

## Gotchas

- The vector is **not the contract**, it's the **launcher architecture**: "is the isolation between
  instances real?" Always test whether wallets/state from different instances can see each other.
- An economic gate that's "impossible" within one instance is a **signal** that the solution uses an
  external resource (another instance, another account, a flash loan on EVM).
- Reusable on EVM: if a multi-instance challenge shares a global contract/state, a cheap instance can
  prep the state the expensive one requires.
- Validate `isSolved()` on-chain before asking the instancer for the flag.

## Related / Cross-reference

- `Arsenal/WEB/web3-reentrancy-checks-effects-interactions.md` — another SekaiCTF blockchain (EVM).
- (pending) `Manuals/TON/` if TON enters scope — SDK, wallets, jettons, instancer.
