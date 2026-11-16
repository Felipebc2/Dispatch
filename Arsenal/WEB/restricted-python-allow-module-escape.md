---
id: restricted-python-allow-module-escape
category: WEB
tags: [restricted-python, restrictedpython, tales, zope, plone, sandbox-escape, allow-module, guarded-getattr, import-graph, n-day, hotfix, cmfeditions, xml-rpc]
tools: []
manuals: []
title: "Zope/Plone restricted-Python escape via allow_module import graph (n-day)"
difficulty: hard
created: 2026-11-16
updated: 2026-11-16
related: [ssti-template-injection, command-injection, generic-recon-scanner]
---

## How to recognize this pattern

- A Zope/Plone target (`Server: waitress`, `X-Powered-By: Zope`, Barceloneta theme) and a prompt
  hinting **"n-day with no public PoC"** — match it to a recent security hotfix released days before
  the event, not to an old numbered CVE.
- You reach a **TALES / RestrictedPython** expression sink (e.g. an anonymous `portal_modifier`
  conditional modifier `edit` that compiles `python:<expr>` and evaluates it on read-back). A
  round-trip test confirms it: `python:42` → `42`.

## Method

### 1. Confirm the stored, read-back expression primitive
The write often must go over **XML-RPC** with `REQUEST=None` (a plain HTTP POST renders the protected
edit *form* and rolls back, so nothing persists):
```
POST /portal_modifier/<Modifier>   (text/xml)   methodName=edit  params=(True,"python:<TALES>","x",None)
GET  /portal_modifier/<Modifier>/isApplicable?obj=x            # public -> returns the evaluated value
```
The condition must carry the `python:` prefix or Zope's `Expression()` raises `CompilerError`.

### 2. Understand why `modules['os'].popen(...)` fails
- `os`/`sys`/`subprocess` are **not public** in the sandbox → `modules['os']` is denied (302).
- A broad `allow_module('M')` publishes **every name in M, including everything M imported** at module
  top level. So if M did `import os`, then `M.os` hands you the **os module object** — that part works.
- But reading `os.popen` off it goes through `guarded_getattr(os,'popen')` → `popen` has no security
  declaration → **302 Unauthorized**. Holding the module ≠ calling its guarded attributes.

### 3. The escape: a directly-bound callable in a public namespace
Find a module in the exposed set (or in its transitively-imported, now-public modules) that did
`from os import system` / `from subprocess import check_output` / `from os import popen`. A
`from ... import <callable>` binding is a *name in that module's namespace*, public via `allow_module`
and **directly callable** with no second `guarded_getattr`. Then:
```
python:modules['<that.module>'].<that_callable>('cat /flag* 2>/dev/null')
```
Find the name by **static source enumeration offline** (walk the imports of the exposed packages for
the exact version pins and grep for `from {os,subprocess,shutil,posix} import <callable>`), not by
blind guessing against the short-lived container.

## Gotchas

- Match the prompt to the **right subsystem**: an authenticated portlet-TALES CVE is a different,
  `Manager`-only path; the anonymous chain is the CMFEditions modifier one.
- Reaching the `os` *module* is progress but not RCE; the missing piece is a *directly-imported
  callable*, not "which package re-enables os".
- Version endpoints usually 404 — pin the version by behaviour and do the import-graph walk offline.
- Container TTLs (~20 min) punish live enumeration; prepare the payload from source first, fire once.

## Cross-reference

- `ssti-template-injection`: the general template-eval-to-RCE family; this is its sandboxed cousin.
- `command-injection`: the end goal once a callable is reached.
