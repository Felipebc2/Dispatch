---
id: read-file-without-coreutils
category: JAIL
tags: [bash, builtins, no-coreutils, minimized-image, cat-not-found, command-substitution, mapfile, read, gtfobins-bash, shell-only, file-read]
tools: []
manuals: []
title: "Read a file with no coreutils: pure Bash builtins ($(<file), mapfile, read)"
difficulty: easy
created: 2026-11-16
updated: 2026-11-16
related: [bash-restricted-shell-escape, python-sandbox-escape]
---

## How to recognize this pattern

- You land in a shell with the flag file right there, but the obvious tool is gone:
  `cat: command not found`, and so are `less`, `head`, `tail`, `more`. It is **not** `rbash`
  (no "restricted" error, `cd`/`pwd` work, `/` allowed) — it is a **minimized container image**
  that stripped coreutils. The banner may even say "This system has been minimized...".
- The lesson/flag theme is often "removing `cat` is not a security boundary".

## Method

Bash can open and read files itself, with zero external binaries:
```bash
echo "$(<flag.txt)"                                   # command substitution file read
mapfile -t x < flag.txt; printf '%s\n' "${x[@]}"      # bash 4+ , multi-line
read -r f < flag.txt; echo "$f"                       # single line
while read -r l; do echo "$l"; done < flag.txt        # loop, any file
```
`printf`, `echo`, `read`, `mapfile`, `$(<...)` are all **builtins** — present even when `/bin` is empty.

## Gotchas

- First tell `rbash` from a minimized image: if `cd`/`/`/variable assignment work and only *binaries*
  are missing, it's minimization — the GTFOBins `rbash` escapes (`vi`, `find -exec`) don't apply and
  those binaries are absent anyway.
- If even `echo` is somehow unavailable, `printf '%s\n' "$(<flag.txt)"` still works; last resort,
  `exec`/redirection tricks or `/dev/stdout`.
- Other shells have equivalents: `zsh` `$(<file)`; in `sh`/dash without `$(<...)`, use
  `while IFS= read -r l; do printf '%s\n' "$l"; done < flag.txt`.
- If the file is readable only by another user, this is the wrong tool — you need privesc, not a reader.

## Cross-reference

- `bash-restricted-shell-escape`: when it really *is* `rbash` and you must break out.
- `python-sandbox-escape`: the equivalent "the filter is a no-op / builtins are enough" mindset.
