# Changelog

All notable changes to CTF Dispatch are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **Toolsets**: `Arsenal/<CAT>/tools/<type>.json`, 167 external tools in 15 files (14 OSINT +
  `NET/vuln-db`), curated from osint.link and checked alive on 2026-11-13. Each tool has a short
  description, tags, access/cost/auth flags and, when possible, a `{q}` URL/command template.
- `arsenal_search.py --tools <query>` (BM25 over tools, one line each) and `--toolset <name>`, with
  `--free` and `--offline` filters. `--emit-index` adds a toolset table (counts only).
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

[0.3.0]: https://github.com/Felipebc2/Dispatch/releases/tag/v0.3.0
[0.2.0]: https://github.com/Felipebc2/Dispatch/releases/tag/v0.2.0
[0.1.0]: https://github.com/Felipebc2/Dispatch/releases/tag/v0.1.0
