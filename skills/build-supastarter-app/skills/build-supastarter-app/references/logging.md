# Logging

> Overview of the shared logger package. Consult this before introducing ad-hoc `console.log()` calls in app or package code.

## Shared logger

`packages/logs/lib/logger.ts` exports the app logger using `consola`.

## Practical rule

Use the shared logger for structured server-side diagnostics rather than scattering raw console statements across the codebase.

## Why the package exists

Centralizing logging keeps formatting and environment behavior consistent and gives packages a single import path: `@repo/logs`.

---

**Related references:**
- `references/setup/import-conventions.md` — Importing shared packages through barrels
- `references/conventions/code-review-checklist.md` — Reminder to avoid stray console logs
- `references/utils.md` — Small shared utilities often used alongside logging
- `references/cheatsheets/imports.md` — Common import patterns
