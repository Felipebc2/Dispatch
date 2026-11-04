---
id: blockchain-bitcoin-electrum-regtest-seed-recovery
category: WEB
tags: [blockchain, bitcoin, not-evm, electrum, regtest, seed-phrase, mnemonic, wallet-recovery, ssh-tunnel, port-forward, pivot, net, misc, drain-wallet, zero-balance, htb, cyber-apocalypse, recovery]
tools: []
manuals: []
title: "Non-EVM blockchain (Bitcoin/Electrum regtest): SSH pivot + seed phrase → move funds (no Foundry/EVM)"
difficulty: easy
created: 2026-10-08
updated: 2026-10-08
related: [web3-cross-instance-shared-state-economic-gate]
---

> ⚠️ **Non-EVM.** This is **Bitcoin** (Electrum wallet, `regtest` network), not Solidity/EVM. No
> `cast`/`forge`/`solc`. Toolchain = the **Electrum** client + **SSH** for the pivot. Recognizing this
> early keeps you from wasting time hunting for a contract. The real category is closer to **NET/MISC**;
> it lives here just to keep the blockchain writeups together.

## How to recognize this pattern

- The handler talks about **Bitcoin / wallet / seed / Electrum / regtest / Electrum server** and gives
  you **SSH credentials** + ports. Win = "the attacker's wallet must end at balance 0" / "return the
  funds to this address". There is no on-chain `isSolved()` and no `.sol`.
- The Electrum server (port ~`50002`) usually only listens on `127.0.0.1` on the attacker's host → you
  need to **tunnel** via SSH to reach it from your local Electrum.

## Method

Reference case: HTB Cyber Apocalypse 2024, Recovery. Given: SSH (`satoshi` / `L4mb0Pr0j3ct`), an
Electrum server at `0.0.0.0:50002:t` (regtest), and a destination address.

1. **SSH pivot**: forward the Electrum server's port to your localhost:
   ```bash
   ssh -p <ssh_port> -L 50002:127.0.0.1:50002 satoshi@<host>   # password: L4mb0Pr0j3ct
   ```
2. **Recover the seed** of the attacker's wallet (comes from the handout/files on the host: BIP39
   mnemonic).
3. **Import it into Electrum** pointing at the tunneled server and move everything to the requested
   address:
   ```bash
   electrum --regtest --oneserver -s 127.0.0.1:50002:t
   # restore a standard wallet with the seed -> Send -> "Max" -> destination address -> Broadcast
   ```
4. The attacker's wallet zeroes out → `nc <host> <port>` option **Get flag** → flag (`HTB{...}`);
   validate the flag against the CTF's configured flag format before declaring success.

## Gotchas

- **`--regtest --oneserver -s host:port:t`**: the trailing `:t` = TCP without TLS; without `--oneserver`
  Electrum ignores a single custom server. Regtest has its own address prefixes (`bcrt1...`).
- The bottleneck is usually **access** (SSH pivot) + **finding the seed**, not crypto. Don't try to
  "crack" a key: the seed is accessible in the environment.
- Confirm the tx is **mined/confirmed** before asking for the flag (the balance must actually be 0).

## Transferable lesson

"Blockchain" in a CTF isn't always EVM. If the prompt mentions Bitcoin/Electrum/wallet/seed, the game
is **access + wallet handling** (network pivot, import seed, sign tx), not a contract exploit. First
reflex: identify the ecosystem (EVM? Bitcoin? TON? Sui?) before choosing the toolchain; each has a
completely different flow.

## Related / Cross-reference

- Other non-EVM entries in the Arsenal: `Arsenal/WEB/move-sui-*` (Sui/Move),
  `web3-cross-instance-shared-state-economic-gate.md` (TON). Same discipline: find the ecosystem first.
