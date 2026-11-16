---
id: hardware-attested-sensor-physical-solve
category: REV
tags: [android, attestation, key-attestation, hardware-backed, sensor, gravity, tilt, server-enforced, cannot-forge, rev-to-learn-rules, physical-solve, emulator-reject, root-reject]
tools: [JVM-Android]
manuals: []
title: "Hardware-attested sensor samples: reverse the rule, then satisfy it physically"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [mobile-embedded-key-signed-api-replay, apk-jni-native-method-check]
---

## How to recognize this pattern

- A mobile app streams **signed sensor samples** (tilt, gravity, location, motion) to a server, and the
  signing key is **hardware-attested** (AndroidKeyStore attestation; the server rejects emulators and
  rooted devices with 403 "attestation rejected"). There is **no `IDP{` in the APK** — the flag only
  exists server-side.
- The server grants the reward when the phone has held a **physical condition** for a duration (e.g.
  inclination 13–14° and rotation 37–38° for 133.7 s — "1337"). Forging samples fails because each one
  must be signed by the real hardware key.

## Method

### 1. Decompile to learn the exact rule (you cannot skip this)
```bash
jadx -d out app.apk
# read ApiClient/ChallengeClient/AttestedKey and the logic/* rule classes
```
Extract the precise thresholds and timing from the client — it ships the same check the server enforces:
```java
TARGET_INCL_CD = 1300; TARGET_ROT_CD = 3700; WINDOW_CD = 100;   // [13.00,14.00) x [37.00,38.00)
HOLD_MS = 133700; MAX_GAP_MS = 2500;                            // hold 133.7 s, no 2.5 s gap
```
Confirm what each sample contains (only the two angles leave the device; position/score do not) and
that the on-screen HUD is a **direct readout of the value the server checks**.

### 2. Satisfy the condition on real hardware
Install the original APK on a **real, non-rooted** phone with network, disable auto-lock, and physically
hold the device at the window's midpoint (prop it on a wedge) until the HUD reads the target, longer
than the hold time. The server issues the reward.

## Gotchas

- **Rev to learn the rules, not to extract the flag** — static analysis yields the condition, never the
  flag. Don't burn time hunting an embedded `IDP{`.
- Forging via patched APK/emulator/spoofed sensor is defeated by hardware attestation — don't attempt it
  against the server; satisfy the condition for real.
- Find what *stops* sampling (usually `onPause` — screen off / backgrounded); the in-game pause or the
  "game over" may **not** stop it, so you can ignore the game and just hold the pose.
- The decompiled HUD proving the readout == the checked value is what makes a wedge-and-wait reliable.

## Cross-reference

- `mobile-embedded-key-signed-api-replay`: the replayable cousin, when the key is a **static embedded**
  one rather than hardware-attested.
- `apk-jni-native-method-check`: Android static-analysis groundwork.
