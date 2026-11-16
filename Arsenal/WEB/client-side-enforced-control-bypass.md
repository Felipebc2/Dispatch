---
id: client-side-enforced-control-bypass
category: WEB
tags: [client-side, proof-of-work, pow, rate-limit, client-throttle, business-logic, automation, nonce, sha256, scripting, server-validation, vote, parallelize]
tools: []
manuals: []
title: "Difficulty enforced only in the client (PoW/throttle) → script it"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [client-side-js-dom-browser-inspection, multiround-timed-service-harness, generic-recon-scanner]
---

## How to recognize this pattern

- An action is **expensive or throttled in `app.js`** (a proof-of-work loop, a client-side counter,
  a self-imposed search cap, a sleep) but the server only checks cheap invariants. Symptom: a goal
  that is "almost impossible by hand" — proposals stuck at 3–7/250, a leaderboard nobody tops.
- The client caps a search space it doesn't have to: `NONCE_SPACE_SIZE = 1_000_000`, a 6-digit nonce
  format, a hard target the honest loop rarely meets.

## Method

### 1. Read the client to find the real invariants
Pull `app.js`. Separate what the **server** enforces from what the **client** self-limits:
```
client: searches only 1e6 nonces, format IDP-CTF-NNNNNN (6 digits), target = 24-bit hash prefix
server: validates ONLY  hash prefix + exactly-6-digit format + single-use challenge
```

### 2. Probe each server check
```
hash correct, wrong nonce format   -> 400  (format enforced)
7-digit nonce (break the cap)      -> 400  (server pins 6 digits)
replay a solved (challenge,nonce)  -> 400  ("request a new proof" = one-time)
new challenge, same session        -> 200  (no per-session/IP dedup -> just need throughput)
```

### 3. Automate within the real rules
Script the PoW, **parallelize the hashing across all cores**, fetch a fresh challenge per attempt,
and submit votes/actions one at a time (normal-looking traffic, not a flood) until the goal
(`count >= required`) is reached and the reward/flag unlocks.

## Gotchas

- The lever is **raw throughput**, not a format bypass — re-read: the server usually re-validates
  the exact nonce format and single-use challenge, so don't waste time on 7-digit or hash-only forgeries.
- Compute the honest success rate to size the work: a 24-bit prefix with a 1e6-nonce space ≈ 5.8%
  solvable per challenge, so budget ~17 challenges per success.
- Keep requests sequential and rate-limited; ephemeral CTF containers fall over under burst load.
- The same shape applies to any client-enforced control: price/quantity computed in JS, a disabled
  button, a client-side "you already voted" guard — trust nothing the browser could lie about.

## Cross-reference

- `client-side-js-dom-browser-inspection`: how to read the front-end and find the self-throttle.
- `multiround-timed-service-harness`: scripting a timed/looped server interaction.
