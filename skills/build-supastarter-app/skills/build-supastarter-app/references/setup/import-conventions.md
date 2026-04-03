# Import Conventions

> Path alias reference and import patterns. Consult this when importing across packages, adding new modules, or encountering module resolution errors.

> ⚠️ **Never use `@repo/database/prisma/client` or raw `@prisma/client`.** Always import from `@repo/database`.

## Path Aliases

Configured in `apps/web/tsconfig.json`:

| Alias | Resolves To | Use For |
|-------|-------------|---------|
| `@/*` | `apps/web/*` | App-level files (config, root utilities) |
| `@repo/*` | `packages/*` | All shared packages |
| `@repo/ui/*` | `packages/ui/*` | UI component deep imports |
| `@shared/*` | `apps/web/modules/shared/*` | Cross-cutting components and utilities |
| `@saas/*` | `apps/web/modules/saas/*` | SaaS feature modules |
| `@marketing/*` | `apps/web/modules/marketing/*` | Marketing page modules |
| `@i18n` / `@i18n/*` | `apps/web/modules/i18n` | i18n utilities |
| `@analytics` | `apps/web/modules/analytics` | Analytics module |
| `content-collections` | `.content-collections/generated` | MDX content collections |

## Import Patterns

### Package imports (always use barrel exports)

```typescript
// ✅ Correct — use package alias
import { auth } from "@repo/auth";
import { db } from "@repo/database";
import { sendEmail } from "@repo/mail";
import { logger } from "@repo/logs";
import { getBaseUrl } from "@repo/utils";
import { config as i18nConfig } from "@repo/i18n/config";

// ❌ Wrong — never use relative paths to packages
import { auth } from "../../../packages/auth/auth";
```

### UI component imports (use deep paths)

```typescript
// ✅ Correct — deep import for tree-shaking
import { Button } from "@repo/ui/components/button";
import { Input } from "@repo/ui/components/input";
import { Form, FormField, FormItem } from "@repo/ui/components/form";

// ✅ Also correct — cn() utility from barrel
import { cn } from "@repo/ui";

// ❌ Wrong — importing all components from barrel
import { Button, Input } from "@repo/ui";
```

### Module imports (use alias for cross-module)

```typescript
// ✅ From a SaaS component, importing shared utilities
import { orpcClient } from "@shared/lib/orpc-client";
import { orpc } from "@shared/lib/orpc-query-utils";

// ✅ From a page, importing SaaS modules
import { useSession } from "@saas/auth/hooks/use-session";
import { useActiveOrganization } from "@saas/organizations/hooks/use-active-organization";

// ✅ App-level config
import { config } from "@/config";
```

### Within the same module (use relative paths)

```typescript
// ✅ Within apps/web/modules/saas/auth/
import { getSession } from "../lib/server";
import { LoginForm } from "../components/LoginForm";

// ✅ Within packages/api/modules/payments/
import { createCheckoutLink } from "./procedures/create-checkout-link";
```

## Package Export Conventions

Each package exports through its `index.ts` barrel:

```typescript
// packages/auth/index.ts
export { auth, type Session, type ActiveOrganization } from "./auth";

// packages/database/index.ts (for Prisma)
export * from "./prisma";

// packages/utils/index.ts
export * from "./lib/base-url";
```

When adding new exports to a package, always wire them through the barrel `index.ts`.

## Common Mistakes

1. **Importing generated files directly** — Import from `@repo/database`, not from `packages/database/prisma/generated`
2. **Using `@repo/ui` barrel for components** — Use deep imports like `@repo/ui/components/button`
3. **Cross-module relative paths** — Use `@shared/`, `@saas/`, `@marketing/` aliases instead
4. **Importing server code in client components** — Auth helpers like `getSession` are server-only

---

**Related references:**
- `references/setup/monorepo-structure.md` — Full directory tree
- `references/cheatsheets/imports.md` — Most common imports cheatsheet
- `references/conventions/typescript-patterns.md` — Type export patterns
