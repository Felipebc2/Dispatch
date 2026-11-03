---
id: web3-spot-price-oracle-amm-flashloan-manipulation
category: WEB
tags: [web3, blockchain, evm, defi, amm, dex, oracle, spot-price, twap-decoy, flash-loan, lending, ltv, price-manipulation, constant-product, uniswap-v2-style, heimdall, cast, foundry]
tools: [Web3]
manuals: ["Manuals/Web3/3. Contexto para Claude.md"]
title: "Web3 — oracle reads spot price straight from AMM reserves: flash-loan pump to inflate collateral and drain the lending desk"
difficulty: medium
created: 2026-10-09
related: [web3-ctf-launcher-ticket-token-flag-retrieval, web3-deployed-bytecode-differs-from-source, web3-mint-on-swap-no-conservation-loop]
---

## How to recognize this pattern

- The prompt mentions "tokens, a pool, a price feed, and a lending desk" (or any combination of AMM +
  oracle + lending desk) with no source — just a `Setup` with getters for each piece (`dex()/pool()`,
  `oracle()/feed()`, `lending()/vault()`, sometimes `flash()`).
- The "oracle" contract has a function whose name suggests robustness (`twapPrice`, `getPrice`) but is
  in practice a **decoy constant** OR reads the price on the fly straight from the AMM's current
  reserves (`usdReserve()*1e18/tokenReserve()`), with no averaging/checkpoints/timelock. Confirm by
  calling the real function (not always the named one — it may be a different "Unresolved_X" selector)
  before/after a test swap: if the value changes immediately, it's pure spot price.
- A **flash loan** is available (a `flash` contract, selector like `flashLoan(uint256,address,bytes)`)
  offering more capital than the pool holds — that's the strongest signal: "fake" capital exists only
  to enable the manipulation within a single tx.
- `isSolved()` compares the lending desk's balance (drained) against a low threshold, **and** the
  flash's balance against the original threshold (repaid) — i.e. the goal is "drain via wrong price
  WITHOUT still owing the flash loan".

## Method

1. **Recon with no source**: `cast call` the Setup getters to find `dex/oracle/lending/flash` (and the
   collateral token, which usually has NO getter on the Setup — it appears only as an argument to
   `transferFrom` in the dex/lending bytecode decompiled via heimdall). See
   `Arsenal/WEB/web3-deployed-bytecode-differs-from-source.md` for the method of interrogating getters/
   storage with no source.
2. **Confirm the AMM formula** (`getAmountOut(amountIn, reserveIn, reserveOut)`, fee 997/1000 = classic
   Uniswap v2) and the current reserves (`reserveA()`, `usdReserve()` or equivalents).
3. **Confirm the oracle reads spot, not a real TWAP** — call the price function before/after simulating
   (local fork) a small swap; if it changes in the same block, confirmed.
4. **Model the pump in Python**: given `X` (USD borrowed via flash), compute
   `amountOut = reserveIn*(X*997)/(X*997+reserveOut*1000)`, the new `price = newUsdReserve*1e18/newTokenReserve`,
   and the `maxDebt = LTV_BPS * (collateral*price/1e18) / 10000` it unlocks. Pick `X` (up to the flash
   limit) that leaves `maxDebt` well above the lending desk's balance, with margin — thin pools
   (100e18/100e18) jump the price 100-400x with a flash loan of ~1500-2000e18.
5. **Attacker contract (1 atomic tx)**:
   - `flash.flashLoan(X, address(this), "")` → callback.
   - In the callback: `usd.approve(dex, X)` + swap USD-in→collateral-out (pump).
   - Deposit the freshly bought collateral into the lending desk (`depositCollateral`).
   - `lending.borrow(amount)` — exploiting the inflated price.
   - Repay the flash loan (`usd.transfer(flash, X)`).
   - **The flash callback selector may have no resolvable name** (e.g. `0x79b2fae8`, no match in
     `onFlashLoan/executeOperation/flashLoanCallback`, etc.) — instead of guessing the name, use a
     `fallback()` that decodes `bytes4(msg.data)` manually and extracts the argument via
     `calldataload`. Don't waste time trying to find the exact textual signature.
6. **ALWAYS test on a local fork first** (`anvil --fork-url $RPC`) — run the full tx without spending
   the remote instance, confirm `isSolved()==true`, only then repeat it on the real RPC.
7. **Flag proof**: same pattern as the launcher (`Arsenal/WEB/web3-ctf-launcher-ticket-token-flag-retrieval.md`)
   — **the exact value `isSolved()` validates, in decimal**. When `isSolved` combines 2 conditions
   (lending drained AND flash repaid), the candidate that matched on the first try was the drained
   desk's final balance (e.g. `usd.balanceOf(lending)` post-exploit, not the flash balance or an
   address).

## Gotchas

- `cast call ... --from <addr>` spoofs `msg.sender` only on **views/eth_call** — it doesn't help build
  the real attack tx (which needs a signature via `cast send`/`forge create`+`cast send`).
- Depositing the collateral BEFORE the pump swap doesn't work — the value is computed with the price at
  the moment of `borrow()`, so the right order is: pump first, deposit with the already-inflated price,
  then borrow.
- Repay the flash loan in the SAME tx (callback) — there's no second chance; if the flash loan's
  external call fails on "unpaid", the whole tx reverts (nothing stays "half" manipulated).
- Watch for underflow/overflow in the AMM calculations in your Python simulation — small divergences
  (operation order, integer-division rounding) don't matter as long as the borrow's safety margin is
  large (take less than the theoretical `maxDebt`, not the exact value).

## Reference case

Carcara Markets — pool 100e18 TKN/100e18 USD, flash of 2000e18 USD, lending with 90% LTV and 10000e18
USD. Pump with `X=1500e18` → price 1e18→~439e18 → borrow 9500e18 → lending left with 500e18 (<1000e18)
with the flash repaid (2000e18, >=2000e18) → `isSolved()==true`. Proof = `"500000000000000000000"`
(lending's final balance, decimal).

## Related / Cross-reference

- `Arsenal/WEB/web3-deployed-bytecode-differs-from-source.md` — getter/storage recon with no source.
- `Arsenal/WEB/web3-ctf-launcher-ticket-token-flag-retrieval.md` — the ticket/token/proof ceremony.
- `Arsenal/WEB/web3-mint-on-swap-no-conservation-loop.md` — another broken DeFi economic-invariant
  pattern, but via supply conservation, not a price oracle.
