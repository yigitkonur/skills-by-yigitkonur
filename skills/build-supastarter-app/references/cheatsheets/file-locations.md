# File Locations: "Where Do I Put...?"

> Quick reference for where to place new files in the Supastarter monorepo.

## New SaaS Page

```
apps/web/app/(saas)/app/[organizationSlug]/your-page/page.tsx
```

If it doesn't need org scoping:
```
apps/web/app/(saas)/app/your-page/page.tsx
```

## New Marketing Page

```
apps/web/app/(marketing)/[locale]/your-page/page.tsx
```

## New API Endpoint

```
packages/api/modules/your-module/procedures/your-action.ts   # Procedure
packages/api/modules/your-module/router.ts                    # Module router
packages/api/orpc/router.ts                                   # Wire into root router
```

## New Database Model

```
packages/database/prisma/schema.prisma      # Add model
packages/database/prisma/queries/your-model.ts  # Add queries
packages/database/prisma/index.ts           # Export queries
```

## New React Component

### Shared across SaaS and marketing:
```
apps/web/modules/shared/components/YourComponent.tsx
```

### SaaS-only:
```
apps/web/modules/saas/your-feature/components/YourComponent.tsx
```

### Marketing-only:
```
apps/web/modules/marketing/your-section/components/YourComponent.tsx
```

### UI library component (Shadcn):
```
packages/ui/components/your-component.tsx
```

## New React Hook

```
apps/web/modules/saas/your-feature/hooks/use-your-hook.ts
```

## New Email Template

```
packages/mail/emails/YourTemplate.tsx       # React Email template
packages/mail/util/templates.ts             # Register template
```

## New Translation Keys

```
packages/i18n/translations/en.ts            # English strings
packages/i18n/translations/de.ts            # German strings
```

## New Blog Post

```
apps/web/content/posts/your-post-slug/index.mdx
```

## New Legal Page

```
apps/web/content/legal/your-page/index.mdx
```

## New Payment Provider

```
packages/payments/provider/your-provider/index.ts
packages/payments/provider/index.ts          # Switch active provider
```

## New Mail Provider

```
packages/mail/provider/your-provider.ts
packages/mail/provider/index.ts              # Switch active provider
```

## New Playwright Test

```
apps/web/tests/your-feature.spec.ts
```

## Environment Variables

```
.env.local.example     # Add template entry
.env.local             # Set actual value (never committed)
```

## Configuration

| What | Where |
|------|-------|
| App feature flags | `apps/web/config.ts` |
| Auth feature flags | `packages/auth/config.ts` |
| Payment plans | `packages/payments/config.ts` |
| i18n locales | `packages/i18n/config.ts` |
| Storage buckets | `packages/storage/config.ts` |
| Tailwind theme | `tooling/tailwind/theme.css` |
| TypeScript base | `tooling/typescript/base.json` |
| Biome rules | `biome.json` |
| Turbo pipeline | `turbo.json` |
| Next.js config | `apps/web/next.config.ts` |

---

**Related references:**
- `references/setup/monorepo-structure.md` — Full directory tree
- `references/setup/import-conventions.md` — How to import new files
