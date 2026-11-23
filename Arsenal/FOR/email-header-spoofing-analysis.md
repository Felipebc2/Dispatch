---
id: email-header-spoofing-analysis
category: FOR
tags: [forensics, email, eml, headers, spoofing, phishing, spf, dkim, dmarc, received, reply-to, return-path, mime, base64-attachment, header-analysis]
tools: []
manuals: []
title: "Email forensics: spot a spoofed sender and decode the attachment from .eml headers"
difficulty: easy
created: 2026-11-23
updated: 2026-11-23
related: [email-pivot-account-discovery, pcap-extract-credentials-files]
---

## How to recognize this pattern

- You're handed a raw email (`.eml`/`.msg`/`.mbox`) and asked who really sent it, whether it's spoofed,
  or to recover an attachment. The flag is in the **headers** or a **MIME part**, not the visible body.
- Prompt hints: "mail du DRH", "phishing", "spoof", "verify the sender", a message whose `From` looks
  internal but whose content is suspicious (surveillance order, wire request, credential prompt).

## Method

### 1. Read the trust headers, top to bottom
```bash
# headers only, in order (Received stacks newest-on-top)
sed -n '1,/^$/p' note.eml
grep -iE '^(From|Reply-To|Return-Path|Received|Authentication-Results|Received-SPF|X-):' note.eml
```
Spoofing tells:
- **`From` vs `Return-Path`/`Reply-To` mismatch** — reply goes to the attacker, not the claimed sender.
- **`Received` chain** originates from an unrelated/foreign relay (`mail-cheap-relay.ru`) rather than
  the claimed org's mail infra. The **bottom** `Received` is the true origin.
- **`Authentication-Results`**: `spf=fail`, `dkim=fail`, `dmarc=fail` → not sent by the real domain.
- Odd `X-` headers often carry the planted flag or the attacker's note.

### 2. Decode MIME parts / attachments
Parts are often base64 (`Content-Transfer-Encoding: base64`) or quoted-printable:
```bash
python3 - <<'PY'
import email
m = email.message_from_file(open("note.eml"))
for p in m.walk():
    ct, fn = p.get_content_type(), p.get_filename()
    print("--", ct, fn)
    if p.get_payload(decode=True):
        data = p.get_payload(decode=True)          # auto base64/QP decode
        if fn: open(fn, "wb").write(data)
        else:  print(data[:500])
PY
```
Carve attachments with `ripmime -i note.eml` or `munpack` as a fallback.

### 3. Pivot on what the headers reveal
- `X-Originating-IP` / bottom `Received` IP → geolocate, WHOIS.
- `Message-ID` domain, mailer (`X-Mailer`), timestamps for timeline.
- Links in the body: defang and inspect (`urlscan`, don't click).

## Gotchas

- `Received` headers read **top = most recent, bottom = origin** — trace from the bottom to find who
  actually injected the mail.
- `From` is trivially forgeable; **never** trust it alone. SPF/DKIM/DMARC results in
  `Authentication-Results` are the real verdict — but confirm that header was added by the *receiving*
  server, not forged by the attacker (it should be the topmost, from your own domain).
- Display name spoofing: `From: "DRH <drh@corp.fr>" <attacker@evil.ru>` — read the actual address, not
  the display name.
- `.msg` (Outlook) needs `msgconvert` → `.eml` first. `.mbox` holds many messages; split before parsing.
- Attachments are untrusted malware — decode and analyze statically (see `office-maldoc-vba-static-extraction`),
  never open.

## Cross-reference

- `email-pivot-account-discovery`: OSINT pivot from the sender address to the person and their accounts.
- `pcap-extract-credentials-files`: when the mail is captured on the wire (SMTP/IMAP) rather than given
  as a file.
