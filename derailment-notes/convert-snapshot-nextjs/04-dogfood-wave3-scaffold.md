# Derailment Test: convert-snapshot-nextjs — Wave 3 (Scaffold)

Date: 2025-07-15
Skill under test: convert-snapshot-nextjs (system-template.md)
Test task: Scaffold Next.js project from Acme homepage extraction
Method: Follow system-template.md steps literally

---

## Friction points

### Package Configuration

**F-20 — `"tailwindcss": "latest"` installs v4** (P0)
Tailwind v4 uses CSS-based config (`@theme` directive). The template generates
`tailwind.config.ts` which is v3-only JS config format. `npm run build` fails
with cryptic errors about missing theme configuration.
Fix: Pin to `"tailwindcss": "^3"`.

**F-21 — No TypeScript strict mode flag** (P2)
Template tsconfig doesn't set `strict: true`. Some type errors only surface later.
Fix: Acceptable; Next.js defaults are reasonable.

### Project Structure

**F-22 — No `public/fonts/` directory guidance** (P1)
When fonts are downloaded, no clear path for where to put them.
Fix: Add to Setup section and missing-resource recovery.

**F-23 — Tailwind config uses hex values instead of CSS variables** (P2)
Template shows hardcoded hex colors in tailwind.config.ts instead of
`var(--color-*)` references. Works but loses the design token layer.
Fix: Acceptable for MVP; direct hex values are simpler and work.

**F-24 — No `.gitignore` in template** (P2)
Template package.json doesn't mention creating `.gitignore`. `npx create-next-app`
normally handles this, but manual scaffold doesn't.
Fix: Acceptable; this is standard Next.js setup knowledge.

---

## What worked well

1. The directory structure template is clear and complete
2. Component naming conventions (PascalCase files, kebab-case CSS) are stated
3. The `layout.tsx` → `page.tsx` → section component hierarchy is sound
4. Global CSS import chain is well-documented

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 1 | F-20 |
| P1 | 1 | F-22 |
| P2 | 3 | F-21, F-23, F-24 |
