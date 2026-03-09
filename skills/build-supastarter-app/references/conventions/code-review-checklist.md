# Code Review Checklist

> Pre-commit quality checklist. Run through this before submitting changes.

## TypeScript

- [ ] No `any` types without justification
- [ ] Interfaces for object shapes, types for unions
- [ ] `as const` for constant objects (no enums)
- [ ] Zod schemas for runtime validation at system boundaries
- [ ] Proper null/undefined handling (optional chaining, nullish coalescing)

## React Components

- [ ] Server Components by default; `"use client"` only when required
- [ ] Named exports with `function` keyword (no default exports)
- [ ] Forms use `react-hook-form` + `zod` + Shadcn Form
- [ ] No `useEffect` for data fetching (use server components or TanStack Query)
- [ ] Client components are small and focused
- [ ] `Suspense` boundaries around async client components

## API Layer

- [ ] Correct procedure tier (`publicProcedure` / `protectedProcedure` / `adminProcedure`)
- [ ] Input validated with Zod schema
- [ ] Route metadata present (`method`, `path`, `tags`, `summary`)
- [ ] Procedure wired into the module router → root router
- [ ] Error handling uses `ORPCError` with appropriate codes

## Database

- [ ] Queries go in `packages/database/prisma/queries/`
- [ ] New models added to `schema.prisma` with proper relations
- [ ] Indexes on foreign keys
- [ ] Generated client updated (`pnpm generate`)
- [ ] Exports wired through barrel `index.ts`

## Imports

- [ ] Package imports use `@repo/*` aliases (not relative paths)
- [ ] UI components use deep imports (`@repo/ui/components/button`)
- [ ] Cross-module imports use `@shared/`, `@saas/`, `@marketing/` aliases
- [ ] No unused imports (Biome enforces this)

## Styling

- [ ] Mobile-first responsive design (`flex-col` then `md:flex-row`)
- [ ] Uses design tokens from `theme.css` (not hardcoded colors)
- [ ] `cn()` for conditional class names
- [ ] No inline styles

## i18n

- [ ] User-facing strings use translation keys (`t("key")`)
- [ ] New keys added to translation files
- [ ] Locale-aware date/number formatting

## Security

- [ ] No secrets in `NEXT_PUBLIC_*` variables
- [ ] Auth checks on protected routes/procedures
- [ ] Input sanitization for user-provided data
- [ ] No `dangerouslySetInnerHTML` without sanitization

## Performance

- [ ] Images use `next/image` with width/height
- [ ] Heavy client components use `dynamic()` imports
- [ ] No unnecessary re-renders (stable references, proper deps)
- [ ] Data prefetching for server → client hydration

## Linting

- [ ] `pnpm lint` passes
- [ ] `pnpm format` applied
- [ ] `pnpm type-check` passes
- [ ] No `console.log` in production code (use `logger` from `@repo/logs`)

---

**Related references:**
- `references/conventions/naming.md` — Naming standards
- `references/conventions/typescript-patterns.md` — TypeScript patterns
- `references/conventions/component-patterns.md` — Component patterns
