---
id: php-type-juggling-magic-hash
category: WEB
tags: [php, type-juggling, loose-comparison, magic-hash, 0e, md5, sha1, hash-compare, auth-bypass, login-bypass, strcmp, spaze-hashes, in-array, scientific-notation]
tools: []
manuals: []
title: "PHP type juggling: magic hash (0e...) auth bypass on loose == comparison"
difficulty: easy
created: 2026-11-17
updated: 2026-11-17
related: [custom-weak-hash-bruteforce-collision, flask-weak-secret-session-forge, jwt-alg-none]
---

## How to recognize this pattern

- PHP source compares a hash (or password/token) with **loose `==`**, not strict `===`:
  ```php
  if (md5($_POST['password']) == $stored)         // vulnerable
  if ($_GET['token'] == $secret)                  // vulnerable
  if (hash('sha256', $x) == hash('sha256', $y))   // vulnerable
  ```
- `==` juggles types. Two strings that both match `^0e\d+$` are read as `0 x 10^n` — **both equal
  `0`** — so any two `0e`-form strings compare **equal**. A hash of that shape is a *magic hash*.
- Strong signal: the stored/target hash is `0e` followed by **only digits**
  (e.g. `0e462097431906509019562988736854`), or the code compares two user-influenced hashes.
- Also fires on loose `in_array($x, $arr)` (no 3rd `true` arg) and `switch ($hash)` with numeric-string cases.

## Method

### 1. Confirm it's loose and 0e-vulnerable
- `===` / `hash_equals()` → **not** vulnerable, stop. Only `==` (and `in_array`/`switch`) juggle.
- Target hash must be `0e` + all digits. If it's `0e` + something with a letter, the magic trick fails.

### 2. Pick a known magic-hash preimage — don't brute force
Use the curated tables in **spaze/hashes** (`https://github.com/spaze/hashes`): per algorithm
(md5, sha1, sha224, sha256, …) they list plaintexts whose digest is `0e[0-9]+`.
```
md5("240610708")  = 0e462097431906509019562988736854
md5("QNKCDZO")    = 0e830400451993494058024219903391
sha1("10932435112") = 0e07766915004133176347055865026311692244
```
Send one magic preimage where the input is hashed. Both sides become `0`, `==` returns true.

### 3. Exploit shapes
- **Both sides hashed, one stored as magic hash:** send any magic preimage for that algorithm.
  `md5($input) == "0e4620974319..."` → `password=240610708`.
- **You control the type (JSON / PHP array in body):** skip hashing entirely — send the integer `0`.
  `"0e123..." == 0` is **true** (string casts to 0). `{"token": 0}` beats a `0e` secret.
  Array where a string is expected: `password[]=1` often makes `md5()` return `NULL` → `NULL == "0e.."`.
- **`strcmp($a, $b)` as an auth check:** pass an array — `strcmp([], $real)` returns `NULL`,
  and `NULL == 0` is true. Payload: `password[]=` (legacy PHP; patched in 8.0).

## Gotchas

- `0e`-magic only works when **both** operands are `0e`-form. A normal hash vs a magic hash is *not* equal.
- Don't confuse `==` (juggles) with `===` (byte-exact, safe). Read the operator before trying.
- Numeric-string juggling bit beyond `0e`: `"1abc" == 1` is true on PHP < 8, but `"abc" == 0` is
  **false** on PHP ≥ 8 (string/number comparison changed in RFC). The `0e == 0e` magic-hash trick
  still holds on all versions, so prefer it.
- If the input is *not* hashed and *not* type-controllable (plain string `==` string), magic hashes
  don't apply — you need the actual value.
- `json_decode` + loose compare is the modern sink: APIs that do `if ($body['sig'] == $expected)`
  let you send a JSON number `0` against a `0e` signature.

## Cross-reference

- `custom-weak-hash-bruteforce-collision`: when the hash is homemade/weak and you must *forge* a
  collision by brute force instead of pulling a known magic preimage.
- `flask-weak-secret-session-forge` / `jwt-alg-none`: sibling auth-bypass patterns on token verification.
- Preimage tables: **spaze/hashes** (`online-web` toolset → `magic-hashes`).
