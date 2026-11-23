---
id: sql-injection-second-order
category: WEB
tags: [sql-injection, sqli, second-order, stored-injection, deferred, union-select, persisted-payload, registration, sqlmap-second-order, blind, two-step]
tools: []
manuals: []
title: "Second-order SQL injection: payload stored on one request, fires on a later one"
difficulty: hard
created: 2026-11-23
updated: 2026-11-23
related: [sqli-union-authbypass, php-object-injection-unserialize-pop-chain]
---

## How to recognize this pattern

- The **input sink and the vulnerable query are different requests.** You submit a value (register a
  username, set a profile field, create a ticket) that is stored **safely** (parameterized INSERT), so
  nothing happens there — but a **later** page reads it back out of the DB and **concatenates it raw**
  into a second query.
- Classic tell: registration/signup accepts weird characters without error, injection in the login or
  profile form does nothing, but a status/dashboard/"my account" page misbehaves afterward.
- Prompt hints: "duplicate form", "second order", "the payload sleeps then wakes", a two-step flow
  (register → view).

## Why automated tools miss it

`sqlmap` fuzzes the request it sends and watches **that** response. A second-order bug doesn't trigger
in the injecting request — it triggers in a *different* page later. You must model both steps
(`sqlmap --second-order <url_that_reads_it>` / `--second-req`), or do it by hand.

## Method

### 1. Store the payload where it's later re-queried
Register a username that is itself SQL. The INSERT is parameterized (safe), so it's stored literally:
```bash
B=https://target
curl -s "$B/?action=register&username=zz' UNION SELECT flag FROM secrets-- -&password=x"
# capture the account id / tracking token the response hands back
```
URL-encode the payload (`%27`=`'`, `%20`=space, `--%20-` for the trailing comment).

### 2. Trigger the second query that reads it back
```bash
curl -s "$B/?action=status&id=<id>&t=<token>"   # this page SELECTs the stored username unsafely
```
The stored `UNION SELECT` now executes inside the status page's query; the flag renders in the
username slot.

### 3. Shape the payload to the re-query
You rarely see the second query's text, so iterate:
- Start with a quote and a comment to confirm breakage: username `zz'-- -` → status page errors or
  changes ⇒ injectable.
- Match the column count of the **re-query** (not the insert) for `UNION SELECT`. Fuzz
  `UNION SELECT 1`, `UNION SELECT 1,2`, … until the error clears.
- Blind variants: use conditional/`CASE` or time-based payloads read back in step 2.

## Gotchas

- Quote **escaping on store vs read**: many apps escape on INSERT (so `\'` is stored) but the escaping
  is *undone* or not reapplied when read back — test both a raw `'` and already-escaped forms.
- Length limits on the stored field can truncate your payload; keep it compact (`/**/` for spaces,
  short table/column names, stacked subqueries).
- The injecting request often looks **completely successful** — don't conclude "not injectable" from a
  clean registration response. Always open the downstream page.
- Identify the DBMS from the second page's errors, not the first.

## Cross-reference

- `sqli-union-authbypass`: first-order SQLi (login bypass / inline UNION) — try it first; second-order
  is the fallback when the direct request is parameterized but a later page isn't.
- `php-object-injection-unserialize-pop-chain`: same "payload dormant, fires later" shape in PHP
  deserialization.
