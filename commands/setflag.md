---
description: Set (or show) the flag format that CTF Dispatch solvers validate against
argument-hint: ["<flag format, e.g. HTB{...} or CTF{...}>" — omit to show the current value]
allowed-tools: Bash(mkdir:*), Bash(cat:*), Bash(printf:*), Bash(test:*)
---

Persist the flag format used by this CTF so every `solver-*` validates found flags against it.
The value lives in `${CLAUDE_PLUGIN_DATA}/flag_format.txt` and survives plugin updates.

Raw argument received: $ARGUMENTS

Do exactly this:

1. **If `$ARGUMENTS` is empty** — show the current value and stop:

   ```bash
   cat "${CLAUDE_PLUGIN_DATA}/flag_format.txt" 2>/dev/null \
     || echo "No flag format set yet. Default: ${user_config.flag_format}"
   ```

   Then tell the user the effective format (the file's value if present, otherwise the install
   default `${user_config.flag_format}`) and that they can change it with
   `/ctf-dispatch:setflag "<format>"`.

2. **If `$ARGUMENTS` is non-empty** — treat the entire argument as the flag format and persist it:

   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}"
   printf '%s\n' '<the exact argument text>' > "${CLAUDE_PLUGIN_DATA}/flag_format.txt"
   cat "${CLAUDE_PLUGIN_DATA}/flag_format.txt"
   ```

   Substitute the argument text verbatim (do not strip surrounding braces or wildcards — the user
   may want a literal pattern like `HTB{...}` or a prefix like `HIK_`). Confirm to the user what was
   saved and that `/dispatch` will now inject this format into every solver.

Keep the output to one or two lines. Do not run anything else.
