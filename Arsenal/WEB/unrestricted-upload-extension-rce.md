---
id: unrestricted-upload-extension-rce
category: WEB
tags: [file-upload, unrestricted-upload, php, extension, webshell, rce, phpinfo, ocr-injection, content-injection, arbitrary-write, apache, octal-escape]
tools: []
manuals: []
title: "Unrestricted upload extension → webshell (incl. OCR / content-injection write)"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [command-injection, ssti-template-injection, error-handler-file-leak]
---

## How to recognize this pattern

- An endpoint lets you **name** a file that then gets written into a web-served directory, and the
  server executes by extension (Apache + `PHP`, etc.). The filename filter blocks `../` and `/` but
  **allows `.php`** (or `.phtml`, `.phar`, `.cgi`). That allowed executable extension is the whole bug.
- The twist is often in **how you control the file's content**: not a raw body field, but an indirect
  sink — an OCR that transcribes an image, a "convert" step, a templating pass, a log you can poison.

## Method

### 1. Probe the two parameters separately
```
name = teste.php              -> saved to /files/<dir>/teste.php   (extension accepted = RCE primitive)
name = ../x / sub/x           -> rejected (charset-restricted to [A-Za-z0-9._-])
injected 'content' field      -> often ignored; the real content comes from the indirect sink
```

### 2. Control the content through the indirect sink
If the body is whatever an **OCR** reads, render your payload as a clean printed image (PIL) and let
the recognizer transcribe it back into source. OCR nails `< ? ; ( ) >`, letters and digits but mangles
`$ _ [ ] " '` — so avoid a `$_GET` webshell and use a **self-contained** payload:
```php
<?php phpinfo(); ?>          # only letters and ();  -> transcribed perfectly
```
`phpinfo()` dumps `$_ENV`/`$_SERVER`, where CTF flags are frequently planted as env vars.

### 3. Save as `.php` and execute
```
reconhecer(image of "<?php phpinfo(); ?>") -> id
salvar(id, name="shell.php")               -> /files/<dir>/shell.php
GET /files/<dir>/shell.php                  -> PHP runs, flag in output
```

### 4. If you need shell but the sink mangles `$ _ [ ]`
Build names/strings with **octal escapes** `"\nnn"` (only `\` + digits), then call as a
variable-function: `$f="\163\171\163\164\145\155"; $f("id");` (`system`). `require"/flag.txt"` needs
no special chars either.

## Gotchas

- Filename/id validators are usually **decoys** that only stop obvious traversal; the real primitive
  is content-control into an attacker-named executable file.
- When the content passes through OCR/convert, **test which characters survive** before building the
  payload — one mangled `$` kills a webshell; a self-contained `phpinfo()`/`system("...")` avoids it.
- Metadata tricks (PNG `tEXt` chunk as fake OCR source) fail against real pixel OCR — the recognizer
  reads pixels, not chunks.
- Huge images can hang/crash the container; a small grayscale PNG is enough.
- If RCE works but the flag file is root-only (`0400`), pivot to privesc (writable cron dir, SUID) —
  RCE is not read.

## Cross-reference

- `command-injection`: once you have code exec, the OS-command half.
- `error-handler-file-leak` / `ssti-template-injection`: other content-into-sink web primitives.
