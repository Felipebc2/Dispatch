---
id: mobile-embedded-key-signed-api-replay
category: REV
tags: [mobile, ios, android, swift, hmac, embedded-key, xor-obfuscation, signed-request, api-replay, protocol, bypass-ui, cryptokit, static-analysis, sensor]
tools: [JVM-Android]
manuals: ["Manuals/JVM-Android/3. Contexto para Claude.md"]
title: "Mobile app signs requests with an embedded key: replay the protocol, skip the UI"
difficulty: hard
created: 2026-11-16
updated: 2026-11-16
related: [apk-jni-native-method-check, dotnet-il-static-analysis, custom-tcp-service-scripting]
---

## How to recognize this pattern

- A mobile app (iOS Swift/CryptoKit, or Android) where the real logic is a **client→server protocol**:
  the app signs each request with an **embedded key** (HMAC-SHA256) and the server returns the flag
  only when the signed values are "correct". The UI (dial, motion, game) is just a way to produce those
  values — it is fully bypassable once you can sign.
- Static strings/symbols reveal the crypto types (`ProtocolMAC`, `SafeStateMachine`, `CofreAPI`) and an
  **obfuscated key** (XOR'd blob deobfuscated at init).

## Method

### 1. Recover the key and the exact MAC message
Find the deobfuscation (a fixed XOR loop over an embedded blob) and apply it to get the raw key bytes.
Nail the **message format** the app signs — field order, separators, encodings:
```
message = "<sid>|<nonce>|<step>|<value>|<direction>"
mac     = hex(HMAC_SHA256(key_raw_bytes, message))
```
Watch for Swift/Kotlin type traps: a `[UInt8]` key is **raw bytes**, not `Data(key.utf8)`.

### 2. Reverse the protocol and its quirks
Map the endpoints and the subtle serialization details — they decide success or a 400:
```
POST /api/session -> {sid, nonce}
POST /api/step    body keys {sid, i, value, dir, mac}   # note: 'i' not 'step', and 1-based
```
Note rate limits (e.g. 10 s/step → one session with delays), direction conventions (`cw/ccw` alternating),
and that the nonce may be tracked server-side (not resent).

### 3. Replay with correct signatures
Open one session and POST the signed steps in order — no device, no sensors, no UI:
```python
mac = hmac.new(key, f"{sid}|{nonce}|{i}|{value}|{dir}".encode(), hashlib.sha256).hexdigest()
```
The server opens and returns the flag.

## Gotchas

- Demangle Swift/Kotlin signatures to get the key **type** right (`[UInt8]` vs `String`); the wrong
  interpretation silently produces a bad MAC.
- The JSON key names and 0- vs 1-based indices are where most replays fail — mirror them exactly; a
  rejection often leaks which value was wrong (learn the direction/step from the error and retry).
- If samples are signed by a **hardware-attested** key (not a static embedded one), replay/emulator
  forgery fails — that is a different pattern (`hardware-attested-sensor-physical-solve`).
- iOS: unzip the `.ipa` (`Payload/App.app/App`), symbol/strings triage; no jailbreak needed for static.

## Cross-reference

- `apk-jni-native-method-check`: Android-native equivalents and JNI checks.
- `dotnet-il-static-analysis`: reversing managed clients without a decompiler.
- `custom-tcp-service-scripting`: scripting the replayed protocol.
