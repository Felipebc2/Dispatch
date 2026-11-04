---
id: web3-bridge-fake-token-pair-spoof-drain
category: WEB
tags: [web3, blockchain, evm, solidity, bridge, cross-chain, l1, l2, relayer, token-pair, fake-token, spoof, il2standarderc20, mint, burn, no-op, deposits-mapping, drain, weth, withdraw, finalize-withdrawal, real-world-ctf, safebridge, foundry, cast]
tools: [Web3]
manuals: ["Manuals/Web3/3. Contexto para Claude.md"]
title: "Web3: an L1/L2 bridge that doesn't validate the token pair; a fake token mapped to real WETH drains the bridge"
difficulty: hard
related: [web3-cross-instance-shared-state-economic-gate, web3-signed-int-cast-unsigned-underflow]
created: 2026-10-08
updated: 2026-10-08
---

> EVM/Solidity, but an **advanced** pattern (cross-chain). Normal Foundry toolchain (`forge`/`cast`),
> but with **2 RPCs** (L1 and L2) and an **off-chain relayer** in the middle. Distinct from
> `Arsenal/REV/bridge-receipt-local-commitment-forge.md` (that one is reversing a guardian binary; this
> one is token-pair spoofing in an on-chain Solidity contract).

## How to recognize this pattern

- A challenge with **two chains** (L1 and L2), **two bridges**, and an **off-chain relayer**
  (`relayer.py`) that passes messages between them. Intended flow: `deposit` on L1 → relayer → `mint`
  on L2; `withdraw` on L2 (`burn`) → relayer → L1 returns the deposited token. Goal: **drain** the
  bridge (e.g. L1 starts with 2 ETH / WETH).
- The typical hole: the bridge **trusts the `(l1Token, l2Token)` pair without validating it's a legit
  registered pair**. Any L2 contract that *claims* to represent a given `l1Token` is accepted. The
  accounting uses a mapping like `deposits[l1Token][l2Token]` that the attacker can reference with an L2
  token they control themselves.
- Red flag in the L2 token's code: an `IL2StandardERC20` interface with `l1Token()` **returned by the
  token itself** (not checked against a registry) + `mint`/`burn` that the bridge calls trusting the
  return.

## Method

Reference case: Real World CTF 2024, SafeBridge (the writeup's first blood). L1 has WETH and the bridge
with `2 ETH` deposited; the goal is to zero the L1 bridge.

1. **Deploy a `FakeToken` on L2** implementing `IL2StandardERC20`, with:
   - `l1Token()` pointing at the **real WETH** on L1 (makes the pair `(WETH, FakeToken)` look valid);
   - `mint`/`burn` as **no-ops** (empty body, they just can't revert); you control the token, so the
     `burn` the bridge calls on `withdraw` never fails, even without any balance.
2. **`withdraw` on the L2 bridge** requesting the real deposit's value, using your FakeToken:
   ```bash
   CAST=~/.config/.foundry/bin/cast
   $CAST send <L2_BRIDGE> "withdraw(address,uint256)" -r <RPC_L2> --private-key $PK \
       -- <FAKE_TOKEN> 2000000000000000000      # 2 ETH; -- for positional args
   ```
   The no-op `burn()` passes → the L2 bridge emits the withdrawal message.
3. **Relayer finalizes on L1**: the L1 bridge decrements `deposits[WETH][FakeToken]` and **transfers
   real WETH/ETH** to you. L1 bridge zeroes → challenge solved (`isSolved()`/the *get flag* option in
   the launcher; validate the flag against the CTF's configured flag format before declaring success).

Deploy the FakeToken: `forge create src/FakeToken.sol:FakeToken --rpc-url <RPC_L2> --private-key $PK
--broadcast --constructor-args <WETH_L1>`. See `Manuals/Web3/3. Contexto para Claude.md`.

## Gotchas

- **Two RPCs:** deposit/finalize is on L1, withdraw is on L2. Don't swap the endpoints (silent error or
  revert). Check `$CAST chain-id` on each.
- The **relayer is off-chain and asynchronous**: after the `withdraw` on L2, wait for the relayer to
  process before you see the balance change on L1 (it's not atomic; it can take a few seconds/blocks).
- The FakeToken's `_l1Token` **must be exactly the WETH** the bridge accounts for; that's what makes
  `deposits[WETH][...]` match. Wrong address = the pair doesn't match = nothing drains.
- `mint`/`burn` only need to **not revert** (an empty body is enough). No need to implement a real ERC20;
  the bridge just calls those functions trusting the return/effect.
- You need gas on both chains (faucet/pre-funded by the launcher). The PK stays only in the terminal.

## Transferable lesson

A bridge that decides "how much to return" from a **`(tokenA, tokenB)` pair the attacker can forge**
(one side is a contract they deploy that *claims* the mapping) is broken: the source of truth has to be
a **registry/allowlist of pairs** in the bridge itself, not the token's self-report. Golden question for
any bridge/wrapper: "who decides this L2 token corresponds to THAT L1 asset: a trusted registry, or the
token itself?". If it's the token, you can spoof and drain. Same family as "trusting the self-report of
an object the attacker controls".

## Related / Cross-reference

- `Arsenal/REV/bridge-receipt-local-commitment-forge.md`: another broken "bridge", but via local
  commitment recompute in a binary (reversing), not an on-chain token pair.
- `Arsenal/WEB/web3-cross-instance-shared-state-economic-gate.md`: another cross-scope economic gate.
- `Manuals/Web3/3. Contexto para Claude.md`: `forge`/`cast`, deploying the attacker contract, 2 RPCs.
