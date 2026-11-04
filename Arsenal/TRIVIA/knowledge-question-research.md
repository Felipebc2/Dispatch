---
id: knowledge-question-research
category: TRIVIA
tags: [trivia, research, knowledge, security, cve, history, flag-format]
tools: []
manuals: []
title: "Trivia: tackling knowledge questions with targeted research"
difficulty: easy
created: 2026-10-04
updated: 2026-10-04
related: []
---

## How to recognize this pattern

- A factual question, with no exploitable attachment: hacker history/culture, CVEs, RFCs, protocols,
  malware/APT names, dates.
- The answer **is** the flag, or it needs to be transformed into the CTF's configured flag format (read
  the prompt carefully to tell which of the two).

## Method

1. **Classify the question's domain** before searching: CTF history, a specific CVE/vuln, hacker culture
   (films, groups, cases), an RFC/protocol, event OSINT.
2. **Primary source first**: the official event site, NVD/MITRE for a CVE, the original RFC, the vendor
   advisory. Avoid a third-party blog that may be wrong.
3. **Match the answer to the flag format:** check whether the prompt wants the raw value or the wrapped
   value. Sometimes the flag is the answer wrapped in the configured format (e.g. a prefix +
   `md5(answer)`), or the MD5 of a specific string:
   ```bash
   echo -n "exact_answer" | md5sum
   ```
4. Submit respecting **exactly** the case/formatting requested.

## Gotchas

- Trivia usually gets solved by hand (solving by hand is often faster than an AI round-trip). An AI round-trip is only
  worth it when the question is obscure or needs a hash/format computation.
- The answer's format is the most common trap: upper/lower case, with/without space, 2- vs 4-digit year,
  official name vs nickname.
- **Aggressive time-box:** if the answer doesn't show up in a primary source within a few minutes, flag
  it and move on. Trivia rarely scores much.
- Be suspicious of a "too good" answer from an LLM with no source. On historical trivia the model
  hallucinates dates/names; confirm it.

## Cross-reference

Rule on when NOT to use AI: solving by hand is often faster than an AI round-trip.
