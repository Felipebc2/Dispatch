# Changelog

All notable changes to CTF Dispatch are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project uses
[Semantic Versioning](https://semver.org/).

## [1.0.3] (2026-11-16)

Directory listing polish.

### Added
- `plugin.json`: `documentationUrl`, `supportUrl` and `privacyPolicyUrl` so the directory listing
  shows Documentation, Support and Privacy-policy links (the privacy link points to the README's
  Security & privacy section).

## [1.0.2] (2026-11-16)

Further hardening for the plugin-directory submission. No behavior change for users.

### Changed
- `commands/dispatch.md` and `commands/setflag.md`: removed the pre-approved `Bash(...)` entries from
  `allowed-tools` entirely (superseding the narrower scoping in 1.0.1), so neither command
  pre-approves shell access — the user approves each call, consistent with the human-checkpoint model.
- `README.md`: added a **Security & privacy** section disclosing what the plugin runs and that it
  never reads, stores, or transmits credentials.

## [1.0.1] (2026-11-16)

Hardening for the Anthropic plugin-directory submission. No behavior change for users.

### Changed
- `commands/dispatch.md`: narrowed `allowed-tools` — `Bash(cat:*)` scoped to the plugin's own
  `flag_format.txt`.
- `agents/solver-pwn.md` and `agents/solver-web.md`: dropped any assumption of reading a credential
  from the user's machine (a tunnel authtoken, a wallet key). The plugin never reads or stores one;
  Web3 keys are challenge-issued per instance, not keys from your machine.
- Quoted frontmatter values that a strict YAML reader could misparse: `argument-hint` in
  `commands/setflag.md` and the `description` in `solver-for`, `solver-llm`, `solver-misc`,
  `solver-net` and `solver-trivia` (colons inside the text).

## [1.0.0] (2026-11-16)

**First stable release.** The base is complete and the interface is stable: the `/dispatch`
orchestrator with its mandatory human checkpoint, 13 agents, ~121 Arsenal entries and 20 toolsets
(194 external tools) across the 12 categories, the Manuals, and a validated track record. From here
the Arsenal grows release by release without breaking what exists. This release also brings:

### Added
- **Toolsets for 5 more categories** (27 external tools; 194 total across 20 toolsets):
  - `crypto/online-crypto`: FactorDB, Alpertron ECM, YAFU, RsaCtfTool, dCode, quipqiup, CyberChef,
    SageMath Cell, WolframAlpha.
  - `rev/online-rev`: Decompiler Explorer (dogbolt), Compiler Explorer (godbolt), defuse.ca asm/disasm.
  - `pwn/online-pwn`: libc-database (blukat), libc.rip, GTFOBins, shell-storm shellcodes.
  - `web/online-web`: crt.sh, HackTricks, PayloadsAllTheThings, revshells, Webhook.site, interactsh.
  - `for/online-for`: Aperi'Solve, StegOnline, file signatures (Kessler), Jimpl, VirusTotal.
- **README Track record**: a scoreboard of the CTFs played with Dispatch (2 podiums in 3 CTFs: 🥈 2nd
  8th IDP, 🥉 3rd Centinela Digital I, 4th Ekoparty 2026) and a "Won a podium with Dispatch?"
  contribution flow; mirrored in `CONTRIBUTING.md`. New `podiums` badge.

### Changed
- Every category solver that now has a toolset (CRYPTO, REV, PWN, WEB, FOR, NET) pulls external
  tools via `--tools`/`--toolset` instead of from memory, matching `solver-osint`. REV/PWN tools stay
  the local Manuals (Ghidra, pwntools); the toolsets only add genuine web services.
- `/dispatch` checkpoint pulls the `--tools` lines for any category that has a toolset, not just OSINT.
- `README.md`: toolset count 15 → 20 (167 → 194 tools).

## [0.5.0] (2026-11-16)

Harvest from an on-site 24h jeopardy + KotH CTF: 19 Arsenal entries (102 to 121) for patterns
not previously covered, generalized into reusable techniques.

### Added
- **WEB (7)**: `stored-xss-admin-bot-cookie-exfil` (the first XSS entry: blind/stored XSS fired by a
  HeadlessChrome admin bot + non-HttpOnly cookie theft), `flask-weak-secret-session-forge`
  (`flask-unsign` + authz split/IDOR on `uid`), `archive-extract-symlink-traversal` (TarSlip/ZipSlip:
  `extractall` follows a symlink member), `unrestricted-upload-extension-rce` (attacker-named `.php`
  + OCR/content-injection write, octal-escape webshell), `client-side-enforced-control-bypass`
  (client-only PoW/throttle → script it), `restricted-python-allow-module-escape` (Zope/Plone TALES
  sandbox escape via the `allow_module` import graph), `nginx-map-cookie-magic-value` (cookie-routed
  static responses + the no-blind-wordlist rule for magic-value challenges).
- **CRYPTO (2)**: `aes-ecb-cut-and-paste-block-forge` (transplant a status/role block to forge a
  structured token — distinct from byte-at-a-time), `predictable-seeded-prng-replay` (reproduce a
  timestamp-seeded `System.Random`/Mersenne draw offline and win the live window).
- **NET (2)**: `dns-record-chain-exfil` (data in TXT/MX, enumerate every record type and follow the
  chain), `voip-rtp-dtmf-extraction` (undissected RTP/G.711 in a pcap → DTMF → zip/doc password).
- **FOR (1)**: `office-maldoc-vba-static-extraction` (`olevba`, decode `Chr()` flags without running
  the macro).
- **PWN (2)**: `setuid-path-hijack-relative-command` (GTFOBins-style PATH hijack of a setuid helper),
  `rop-ordered-call-chain-stack-alignment` (forced-order call chain + the `movaps`/alignment remote crash).
- **REV (2)**: `mobile-embedded-key-signed-api-replay` (iOS/Android client signs requests with an
  embedded key → replay the protocol, skip the UI), `hardware-attested-sensor-physical-solve` (reverse
  the server-enforced physical rule when samples are hardware-attested and cannot be forged).
- **JAIL (1)**: `read-file-without-coreutils` (pure Bash builtins: `$(<file)`, `mapfile`, `read`).
- **MISC (1)**: `code-exec-exfil-one-way-channel` (output only over a screen/livestream: render text
  and QR, auto-paging xterm, test both flag forms per run).
- **PPC (1)**: `custom-isa-assembly-koth-optimization` (TIS-100-style KotH: local simulator, cycle/
  instruction Pareto, duplicate-scoring rule).

### Changed
- `Manuals/Wireshark/3. Contexto para Claude.md`: VoIP/RTP section (force the RTP dissector,
  `-z rtp,streams`, µ-law → PCM), a filters-table row and cross-links to Audio-Signals and the new
  NET entry.
- `README.md`: Arsenal count ~102 → ~121.

## [0.4.0] (2026-11-13)

### Added
- **Toolsets**: `Arsenal/<CAT>/tools/<type>.json`, 167 external tools in 15 files (14 OSINT +
  `NET/vuln-db`), curated from osint.link and checked alive on 2026-11-13. Each tool has a short
  description, tags, access/cost/auth flags and, when possible, a `{q}` URL/command template.
- `arsenal_search.py --tools <query>` (BM25 over tools, one line each) and `--toolset <name>`, with
  `--free`, `--offline` and `--top` filters. `--emit-index` adds a toolset table (counts only).
- Optional `toolsets:` frontmatter field, shown by `--graph` and checked by the validator.
- 5 OSINT entries (97 to 102): `username-pivot-cross-platform`, `email-pivot-account-discovery`,
  `domain-recon-certificates-dns`, `wayback-archived-site-recovery`,
  `transport-tracking-aircraft-ship-aprs`.
- **Web Check** (by Alicia Sykes, MIT): `Manuals/web-check/` (3 files) and a `web-check` tool in
  `osint/domain-infra`. Used through the browser export only; the agent filters the JSON with `jq`
  (721 KB raw to about 12 KB) and never reads it raw. README gains a Credits section.

### Changed
- `generic-recon-scanner` (WEB) and `domain-recon-certificates-dns` (OSINT) start from a Web Check
  report when one is available.
- `validate_arsenal.py` validates toolset JSON (schema, enums, unique ids, `{q}` templates).
- `/dispatch` pulls `--tools` lines for OSINT and shows them at the checkpoint; `solver-osint`
  picks external tools through the toolsets instead of from memory.
- CI: smoke test for `--tools` / `--toolset`.

## [0.3.0] (2026-11-06)

### Added
- 22 Arsenal entries (75 to 97), from patterns seen at Centinela Digital I:
  - **REV**: `elf-hidden-section-foreign-arch-firmware`, `dotnet-il-static-analysis`,
    `java-classloader-defineclass-hidden-class`, `wasm-module-static-analysis`,
    `self-modifying-code-mprotect-xor-decrypt`, `hidden-check-off-main-path`,
    `decoy-vs-real-checker-what-actually-runs`, `apk-jni-native-method-check`.
  - **CRYPTO**: `rsa-franklin-reiter-related-message`, `lcg-truncated-output-state-recovery`,
    `shamir-secret-sharing-lagrange-interpolation`, `discrete-log-pohlig-hellman-smooth-order`.
  - **FOR**: `sqlite-deleted-record-freeblock-carving`, `fat32-unallocated-cluster-recovery`,
    `registry-shimcache-appcompatcache`, `tcp-overlapping-segment-conflict`,
    `large-artifact-gigabyte-triage`.
  - **MISC**: `afsk-bell202-audio-demodulation`, `git-bundle-tagged-vs-tampered-revision`.
  - **PWN**: `boot2root-methodology-checklist`, `sudo-nopasswd-writable-input-exec`,
    `sudo-helper-forgeable-mac-gate`.
- 5 tool Manuals: `ffuf`, `WebAssembly`, `JVM-Android`, `Windows-Registry`, `Audio-Signals`.

### Changed
- `rsa-common-attacks`: Franklin-Reiter row in the decision table and a link to the new entry.
- `command-injection`: gotcha on filtering the wrong representation (blocklist on encoded input).
- `Manuals/Wireshark`: added TCP stream reassembly and overlapping-segment coverage for tshark.
- CI and contributor docs no longer reject em-dashes or en-dashes in Markdown.

## [0.2.0] (2026-11-04)

Architecture and polish pass. No breaking changes.

### Added
- Arsenal navigation that scales without loading the corpus: `--tag`, `--graph`, `--list` and `--emit-index` in `arsenal_search.py`.
- `Arsenal/INDEX.md`: a per-category listing plus a Mermaid relationship graph, regenerated from the entries.
- Codex plugin adapter (`.codex-plugin/plugin.json`).
- `docs/ARCHITECTURE.md`: the model-facing vs infra split and the context rule.
- Vector logo (`assets/logo.svg`).

### Changed
- `ctf-solve` now routes through search instead of reading a whole category folder, keeping context small.
- README rewritten with a hero, badges, how-it-works, a Codex install section, and an FAQ.
- Removed em-dashes repo-wide, recomposed for natural reading.

## [0.1.0] (2026-11-04)

First public release.

### Added
- **`/dispatch`** orchestrator: triage → Arsenal lookup → human checkpoint → solver.
- **13 agents**: `brainstormer` (triage) + 12 category solvers (CRYPTO, REV, PWN, FOR, JAIL,
  OSINT, NET, WEB, PPC, MISC, TRIVIA, LLM).
- **`/ctf-dispatch:ctf-solve`** skill: per-category shortcut into the dispatch flow.
- **`/ctf-dispatch:setflag`**: configure the flag format at runtime; also settable at install
  via the `flag_format` plugin option.
- **Arsenal**: ~75 problem-pattern → method entries across the 12 categories, searched with a
  stdlib-only SQLite FTS5 index (`scripts/arsenal_search.py`).
- **Manuals**: per-tool references (Ghidra, CyberChef, JWT, pwntools, Wireshark, sqlmap, …).
- Human-checkpoint safety model: no solver runs without explicit user approval.
- Plugin + marketplace manifests, brand assets (banner, icon, emblem, diagram).

[1.0.3]: https://github.com/Felipebc2/Dispatch/releases/tag/v1.0.3
[1.0.2]: https://github.com/Felipebc2/Dispatch/releases/tag/v1.0.2
[1.0.1]: https://github.com/Felipebc2/Dispatch/releases/tag/v1.0.1
[1.0.0]: https://github.com/Felipebc2/Dispatch/releases/tag/v1.0.0
[0.4.0]: https://github.com/Felipebc2/Dispatch/releases/tag/v0.4.0
[0.3.0]: https://github.com/Felipebc2/Dispatch/releases/tag/v0.3.0
[0.2.0]: https://github.com/Felipebc2/Dispatch/releases/tag/v0.2.0
[0.1.0]: https://github.com/Felipebc2/Dispatch/releases/tag/v0.1.0
